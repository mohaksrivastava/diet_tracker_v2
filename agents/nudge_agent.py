# agents/nudge_agent.py
#
# For each user:
#   1. Fetch last ≤5 days of logged data (days with 0 entries skipped)
#   2. Compute rolling macro surplus/deficit
#   3. Identify worst single macro deviation
#   4. Compute adjusted today's targets (clamped ±20% of baseline)
#   5. Run the optimizer with adjusted targets → candidate plan
#   6. Build context and call Ollama → get nudge text
#   7. Store nudge in DB
#
# Called by: schedulers/generate_nudges.py (Windows Task Scheduler, ~04:00)

import json
import logging
from datetime import date

import pandas as pd
import numpy as np
import ollama

from db.connection import get_connection
from db.users      import get_all_users
from db.logs       import get_last_n_days_logs
from db.recipes    import get_all_recipes
from db.nudges     import store_nudge, nudge_exists_for_today
from optimizer.meal_optimizer import run_optimizer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [NUDGE-AGENT] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

MODEL        = "qwen2.5:7b"
MAX_DAYS     = 5
CLAMP_FACTOR = 0.20   # max ±20% adjustment from baseline
MACRO_TARGETS = {"carb_pct": 40, "prot_pct": 40, "fat_pct": 20}


# ── Stage 1: Adjusted target computation ──────────────────────────────────────

def compute_adjusted_targets(history_df: pd.DataFrame, baseline: dict) -> dict:
    """
    history_df: columns [log_date, total_cal, total_prot, total_carb, total_fat]
    baseline: {daily_cal, daily_prot_g, daily_carb_g, daily_fat_g}

    Returns adjusted targets for today and a deviation summary.
    """
    n = len(history_df)
    if n == 0:
        return {
            "adjusted_cal":  baseline["daily_cal"],
            "adjusted_prot": baseline["daily_prot_g"],
            "adjusted_carb": baseline["daily_carb_g"],
            "adjusted_fat":  baseline["daily_fat_g"],
            "n_days":        0,
            "deviations":    {},
            "worst_macro":   None,
        }

    # Rolling deficit per macro
    target_total = {
        "cal":  baseline["daily_cal"]    * n,
        "prot": baseline["daily_prot_g"] * n,
        "carb": baseline["daily_carb_g"] * n,
        "fat":  baseline["daily_fat_g"]  * n,
    }
    actual_total = {
        "cal":  float(history_df["total_cal"].sum()),
        "prot": float(history_df["total_prot"].sum()),
        "carb": float(history_df["total_carb"].sum()),
        "fat":  float(history_df["total_fat"].sum()),
    }

    # Deficit = positive → under-eaten; spread over 3 days
    correction = {k: (target_total[k] - actual_total[k]) / 3 for k in target_total}

    def clamp(baseline_val, delta):
        adj = baseline_val + delta
        lo  = baseline_val * (1 - CLAMP_FACTOR)
        hi  = baseline_val * (1 + CLAMP_FACTOR)
        return float(np.clip(adj, lo, hi))

    adj = {
        "cal":  clamp(baseline["daily_cal"],    correction["cal"]),
        "prot": clamp(baseline["daily_prot_g"], correction["prot"]),
        "carb": clamp(baseline["daily_carb_g"], correction["carb"]),
        "fat":  clamp(baseline["daily_fat_g"],  correction["fat"]),
    }

    # Compute per-macro deviation % from ideal macro ratios
    avg_mc = max(actual_total["prot"]*4 + actual_total["carb"]*4 + actual_total["fat"]*9, 1)
    deviations = {
        "protein":      round(actual_total["prot"]*4 / avg_mc * 100 - 40, 1),
        "carbohydrates": round(actual_total["carb"]*4 / avg_mc * 100 - 40, 1),
        "fat":           round(actual_total["fat"]*9  / avg_mc * 100 - 20, 1),
        "calories":      round((actual_total["cal"]/n - baseline["daily_cal"])
                               / baseline["daily_cal"] * 100, 1),
    }
    worst_macro = max(deviations, key=lambda k: abs(deviations[k]))

    return {
        "adjusted_cal":  round(adj["cal"]),
        "adjusted_prot": round(adj["prot"], 1),
        "adjusted_carb": round(adj["carb"], 1),
        "adjusted_fat":  round(adj["fat"], 1),
        "n_days":        n,
        "deviations":    deviations,
        "worst_macro":   worst_macro,
    }


def _baseline_from_user(user: dict) -> dict:
    """Derive gram targets from user's daily_cal and standard macro split 40C/40P/20F."""
    cal = user["daily_cal"]
    return {
        "daily_cal":    cal,
        "daily_prot_g": round(cal * 0.40 / 4, 1),
        "daily_carb_g": round(cal * 0.40 / 4, 1),
        "daily_fat_g":  round(cal * 0.20 / 9, 1),
    }


# ── Stage 2: Ollama nudge generation ─────────────────────────────────────────

def _build_nudge_prompt(user_name: str, n_days: int, history_df: pd.DataFrame,
                        deviations: dict, worst_macro: str,
                        adj_targets: dict, plan: dict,
                        recipe_names: list[str],
                        missing_day_count: int, baseline: dict) -> str:

    # History summary
    if not history_df.empty:
        history_lines = []
        for _, row in history_df.iterrows():
            mc = max(row["total_prot"]*4 + row["total_carb"]*4 + row["total_fat"]*9, 1)
            history_lines.append(
                f"  {row['log_date']}: {int(row['total_cal'])} kcal | "
                f"P:{row['total_prot']:.1f}g ({row['total_prot']*4/mc*100:.0f}%) "
                f"C:{row['total_carb']:.1f}g ({row['total_carb']*4/mc*100:.0f}%) "
                f"F:{row['total_fat']:.1f}g ({row['total_fat']*9/mc*100:.0f}%)"
            )
        history_summary = "\n".join(history_lines)
    else:
        history_summary = "  No data available"

    # Today's suggested plan
    plan_lines = []
    for slot in plan.get("slots", []):
        for r in slot["recipes"]:
            plan_lines.append(f"  [{slot['type'].title()}] {r['name']} "
                              f"({r['portion']}× = {r['calories_shown']} kcal)")
    plan_text = "\n".join(plan_lines)

    # Deviation context
    dev_text = "\n".join(
        f"  {k.title()}: {v:+.1f}% vs target" for k, v in deviations.items()
    )

    return f"""You are a compassionate, expert Indian diet coach helping {user_name} maintain their nutritional goals.

CONTEXT:
- Daily calorie target: {baseline['daily_cal']} kcal
- Macro targets: 40% carbs / 40% protein / 20% fat
- Days analysed: {n_days} (out of last 5 days; {missing_day_count} days had no logged meals)

LAST {n_days} DAYS OF DATA:
{history_summary}

MACRO DEVIATIONS (actual vs ideal ratio):
{dev_text}
→ Biggest concern: {worst_macro} (deviation: {deviations.get(worst_macro, 0):+.1f}%)

TODAY'S ADJUSTED TARGETS (correcting for recent history):
- Calories: {adj_targets['adjusted_cal']} kcal
- Protein:  {adj_targets['adjusted_prot']}g
- Carbs:    {adj_targets['adjusted_carb']}g
- Fat:      {adj_targets['adjusted_fat']}g

TODAY'S OPTIMISED MEAL PLAN (generated from our recipe database):
{plan_text}

AVAILABLE RECIPES (you may only suggest from this list):
{', '.join(recipe_names[:60])}{'...' if len(recipe_names) > 60 else ''}

TASK:
Write a short, friendly, practical diet recommendation for {user_name}. Your response must:
1. Acknowledge what they are doing well (1 sentence)
2. Identify the biggest nutritional gap from the data above (1-2 sentences)
3. Suggest 1-2 SPECIFIC recipe swaps from the available recipes list to fix the gap (be concrete: "replace X with Y" or "add Z to your breakfast")
4. If {missing_day_count} > 0: gently remind them that {missing_day_count} day(s) had no logged meals and consistent logging leads to better recommendations
5. Keep the whole message under 120 words, warm and encouraging

Write only the recommendation text — no headers, no JSON, no markdown formatting.
"""


def run_nudge_agent():
    log.info("=" * 60)
    log.info("Nudge Agent starting")
    conn = get_connection()

    users      = get_all_users(conn)
    recipes_df = get_all_recipes(conn)
    recipe_names = sorted(recipes_df["name"].tolist())

    generated = 0
    for user in users:
        uid  = user["id"]
        name = user["name"]
        log.info(f"Processing user: {name} (id={uid})")

        # Skip if nudge already generated today
        if nudge_exists_for_today(conn, uid):
            log.info(f"  → Already has nudge for today, skipping")
            continue

        history_df = get_last_n_days_logs(conn, uid, MAX_DAYS)
        n_days     = len(history_df)

        if n_days == 0:
            log.info(f"  → No logged data at all, skipping")
            continue

        baseline   = _baseline_from_user(dict(user))
        adj        = compute_adjusted_targets(history_df, baseline)

        # Days in the window that had no entries
        missing_days = MAX_DAYS - n_days

        # Run optimizer with adjusted calorie target
        try:
            plans = run_optimizer(
                recipes_df,
                K=int(user["num_meals"]),
                target_cal=adj["adjusted_cal"],
                food_pref=user["food_pref"]
            )
            best_plan = plans[0]
        except Exception as e:
            log.error(f"  → Optimizer failed: {e}")
            continue

        # Build prompt and call Ollama
        prompt = _build_nudge_prompt(
            user_name=name,
            n_days=n_days,
            history_df=history_df,
            deviations=adj["deviations"],
            worst_macro=adj["worst_macro"],
            adj_targets=adj,
            plan=best_plan,
            recipe_names=recipe_names,
            missing_day_count=missing_days,
            baseline=baseline,
        )

        try:
            response = ollama.chat(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.4, "num_predict": 300}
            )
            nudge_text = response["message"]["content"].strip()
            # Strip any accidental prefix
            if nudge_text.lower().startswith("here"):
                lines = nudge_text.split("\n")
                nudge_text = "\n".join(lines[1:]).strip() if len(lines) > 1 else nudge_text

        except Exception as e:
            log.error(f"  → Ollama error: {e}")
            continue

        # Store in DB
        store_nudge(
            conn, uid,
            days_analyzed=n_days,
            adjusted_cal=adj["adjusted_cal"],
            adjusted_prot=adj["adjusted_prot"],
            adjusted_carb=adj["adjusted_carb"],
            adjusted_fat=adj["adjusted_fat"],
            nudge_text=nudge_text,
        )
        generated += 1
        log.info(f"  → Nudge stored ({len(nudge_text)} chars)")
        log.info(f"     Preview: {nudge_text[:100]}...")

    conn.close()
    log.info(f"Done — Nudges generated: {generated}")
    log.info("=" * 60)
    return {"generated": generated}


if __name__ == "__main__":
    run_nudge_agent()
