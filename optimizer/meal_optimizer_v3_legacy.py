# optimizer/meal_optimizer.py  -  v3
#
# Algorithm: Two-Phase Constrained Vectorised Enumeration
#
# Phase 1 - Per-slot candidate generation:
#   - Calorie target from nutrition matrix (interpolated, not fixed %)
#   - Anchor role enforcement: lunch/dinner must have anchor_protein + anchor_starch
#     (or a solo complete_meal)
#   - Min/max recipe count per slot type
#   - Food group uniqueness within a slot
#   - Per-recipe portion envelopes (portion_min / typical / max)
#
# Phase 2 - Global scoring:
#   - Asymmetric macro penalty against per-user nutrition targets
#   - Portion deviation penalty
#   - Cuisine coherence penalty
#   - Hard feasibility filter with relaxation cascade
#   - Cross-slot duplicate rejection for non-staples
#   - Diversity filter: top-3 plans differ in >= 2 slots
#
# Algorithm rationale:
#   MILP was considered but rejected: macro balance objective is quadratic,
#   linearisation loses exactness and adds solver dependencies. CP-SAT requires
#   OR-Tools (200MB). Genetic algorithms are non-deterministic. At 63 recipes
#   with M_CANDS=12 per slot, the global expansion is 12^5 = 248K combinations,
#   vectorised-scored by NumPy in ~10ms — exact optimality at zero extra cost.

import time
import numpy as np
import pandas as pd
from itertools import combinations, product as iproduct

# -- Nutrition matrix from Excel ------------------------------------------------
# Source: nutrition_matrix.xlsx — slot calorie targets per daily calorie level.
# For calorie targets outside [1200, 2500], np.interp clamps to boundary values.
# K=5 has 2 snack slots (both use the "snack" row); slot_seq handles duplication.

CAL_LEVELS = [1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900,
              2000, 2100, 2200, 2300, 2400, 2500]

# Raw values from the spreadsheet, indexed by K ? slot_type ? list(14 values)
SLOT_CAL_TABLE = {
    2: {
        "lunch":     [600,650,700,750,800,850,900,950,1000,1050,1100,1150,1200,1250],
        "dinner":    [600,650,700,750,800,850,900,950,1000,1050,1100,1150,1200,1250],
        "breakfast": [0]*14,
        "snack":     [0]*14,
    },
    3: {
        "lunch":     [450,480,510,540,570,600,630,660,690,720,750,780,900,930],
        "dinner":    [450,480,510,540,570,600,630,660,690,720,750,780,900,930],
        "breakfast": [300,340,380,420,460,500,540,580,620,660,700,740,600,640],
        "snack":     [0]*14,
    },
    4: {
        "lunch":     [400,425,450,475,500,525,550,575,600,625,650,675,700,725],
        "dinner":    [400,425,450,475,500,525,550,575,600,625,650,675,700,725],
        "breakfast": [250,275,300,325,350,375,400,425,450,475,500,525,550,575],
        "snack":     [150,175,200,225,250,275,300,325,350,375,400,425,450,475],
    },
    5: {
        "lunch":     [350,370,390,410,430,450,470,490,510,530,550,570,590,610],
        "dinner":    [350,370,390,410,430,450,470,490,510,530,550,570,590,610],
        "breakfast": [200,220,240,260,280,300,320,340,360,380,400,420,440,460],
        "snack":     [150,170,190,210,230,250,270,290,310,330,350,370,390,410],
    },
}

def get_slot_target(K: int, slot_type: str, daily_cal: float) -> float:
    """Interpolate slot calorie target from the nutrition matrix."""
    table = SLOT_CAL_TABLE[K][slot_type]
    return float(np.interp(daily_cal, CAL_LEVELS, table))


# -- Static config --------------------------------------------------------------

SLOT_SEQ = {
    2: ["lunch", "dinner"],
    3: ["lunch", "dinner", "breakfast"],
    4: ["lunch", "dinner", "breakfast", "snack"],
    5: ["lunch", "dinner", "breakfast", "snack", "snack"],
}

SLOT_PARAMS = {
    # kw: keyword to match meal_type column
    # min_n: minimum recipes per slot
    #   - lunch/dinner: 2 required (complete_meal is the only valid solo exception)
    #   - breakfast: 1 required
    #   - snack: 1 required
    # max_n: maximum recipes per slot
    "lunch":     {"kw": "Lunch",     "min_n": 2, "max_n": 4},
    "dinner":    {"kw": "Dinner",    "min_n": 2, "max_n": 4},
    "breakfast": {"kw": "Breakfast", "min_n": 1, "max_n": 3},
    "snack":     {"kw": "Snack",     "min_n": 1, "max_n": 2},
}

# Slot calorie acceptance window: ±SLOT_WINDOW fraction of matrix target.
# Tighter than v2 (was ±65%) because the matrix target is now authoritative.
# ±30% allows realistic portion variation while keeping meals on-spec.
SLOT_WINDOW = 0.30

EXTRA_PENALTY   = 200    # per recipe beyond the 1st in a slot (favours simpler meals)
M_CANDS         = 12     # per-slot candidates kept after pruning
STAPLE_GROUPS   = {"rice", "roti"}
PORTION_DEV_K   = 50     # weight for deviation from portion_typical
CUISINE_CLASH_P = 1.5    # penalty per incompatible cuisine pair in a slot
CUISINE_MATCH_R = 0.5    # reward per matching cuisine pair in a slot

# Anchor role sets
ANCHOR_PROTEIN_ROLES = {"anchor_protein"}
ANCHOR_STARCH_ROLES  = {"anchor_starch"}
COMPLETE_MEAL_ROLE   = "complete_meal"

ALLOWED_TYPES = {
    "vegan":   ["vegan"],
    "veg":     ["vegan", "veg"],
    "dairy":   ["vegan", "veg", "dairy"],
    "egg":     ["vegan", "veg", "dairy", "egg"],
    "non-veg": ["vegan", "veg", "dairy", "egg", "non-veg"],
}

CUISINE_FAMILY = {
    "north_indian":  "indian",
    "south_indian":  "indian",
    "indo_chinese":  "fusion",
    "east_asian":    "asian",
    "continental":   "western",
    "mediterranean": "western",
    "mexican":       "western",
    "unknown":       "any",
}

RELAXATION_LEVELS = [
    ("strict",    1.0),
    ("relaxed",   1.5),
    ("loose",     2.0),
    ("soft_only", None),
]


# -- Public API -----------------------------------------------------------------

def run_optimizer(
    recipes_df: pd.DataFrame,
    K: int,
    nutrition_target: dict,
    food_pref: str = "non-veg",
) -> dict:
    """
    Generate up to 3 diverse meal plans using the Two-Phase Constrained
    Vectorised Enumeration algorithm.

    Parameters
    ----------
    recipes_df       : DataFrame from db.recipes.get_all_recipes()
    K                : number of meals per day (2–5)
    nutrition_target : dict from db.nutrition_targets.load_or_default_target()
    food_pref        : one of ALLOWED_TYPES keys

    Returns
    -------
    {
        "plans":            list[dict],   # up to 3 plans
        "relaxation_level": str,
        "runtime_ms":       int,
        "num_candidates":   int,
        "num_feasible":     int,
    }
    """
    t0 = time.monotonic()
    K  = int(K)
    if K not in range(2, 6):
        raise ValueError("K must be 2–5.")

    allowed = ALLOWED_TYPES.get(food_pref, ALLOWED_TYPES["non-veg"])
    df = recipes_df[
        (recipes_df["category"] == "recipe") &
        (recipes_df["food_type"].isin(allowed)) &
        (recipes_df["calories"].notna())
    ].copy().reset_index(drop=True)

    if df.empty:
        raise ValueError("No eligible recipes for this food preference.")

    # Fill v2/v3 columns with safe defaults if DB migration hasn't run yet
    for col, default in [("portion_min", 0.5), ("portion_typical", 1.0),
                         ("portion_max", 1.5), ("role", "side"),
                         ("cuisine", "unknown")]:
        if col not in df.columns:
            df[col] = default
        else:
            df[col] = df[col].fillna(default)

    daily_cal = float(nutrition_target["cal_target"])
    slot_seq  = SLOT_SEQ[K]

    # Compute slot targets from the nutrition matrix
    slot_targets = {
        s_type: get_slot_target(K, s_type, daily_cal)
        for s_type in ["lunch", "dinner", "breakfast", "snack"]
    }

    # -- Phase 1: per-slot candidate generation --------------------------------
    slot_cands = []
    for s_type in slot_seq:
        target = slot_targets[s_type]
        cands  = _gen_slot_cands(df, s_type, target, nutrition_target)
        if not cands:
            raise ValueError(
                f"No valid meals could be constructed for the '{s_type}' slot. "
                "This usually means no recipe combination meets the anchor "
                "requirements (protein + starch) for this slot. "
                "Try a different food preference or check recipe tags."
            )
        slot_cands.append(cands)

    # -- Phase 2: global expansion and scoring ---------------------------------
    ns   = [len(sc) for sc in slot_cands]
    flat = [g.ravel() for g in
            np.meshgrid(*[np.arange(n) for n in ns], indexing="ij")]
    num_candidates = len(flat[0])

    def _arr(si, key):
        return np.array([c[key] for c in slot_cands[si]], dtype=float)

    tc_arrs = [_arr(si, "total_cal")   for si in range(K)]
    pc_arrs = [_arr(si, "prot_cal")    for si in range(K)]
    cc_arrs = [_arr(si, "carb_cal")    for si in range(K)]
    fc_arrs = [_arr(si, "fat_cal")     for si in range(K)]
    ep_arrs = [_arr(si, "extra_pen")   for si in range(K)]
    pp_arrs = [_arr(si, "portion_pen") for si in range(K)]
    cp_arrs = [_arr(si, "cuisine_pen") for si in range(K)]

    total_cal = sum(tc_arrs[si][flat[si]] for si in range(K))
    total_pc  = sum(pc_arrs[si][flat[si]] for si in range(K))
    total_cc  = sum(cc_arrs[si][flat[si]] for si in range(K))
    total_fc  = sum(fc_arrs[si][flat[si]] for si in range(K))
    total_ep  = sum(ep_arrs[si][flat[si]] for si in range(K))
    total_pp  = sum(pp_arrs[si][flat[si]] for si in range(K))
    total_cp  = sum(cp_arrs[si][flat[si]] for si in range(K))

    total_pg = total_pc / 4.0
    total_cg = total_cc / 4.0
    total_fg = total_fc / 9.0

    # Relaxation cascade: try strict limits first, loosen if no feasible plans
    relaxation_level = "strict"
    feasible_mask    = np.zeros(num_candidates, dtype=bool)

    for level_name, multiplier in RELAXATION_LEVELS:
        if multiplier is None:
            feasible_mask = np.ones(num_candidates, dtype=bool)
        else:
            t_adj = _scale_hard_limits(nutrition_target, multiplier)
            feasible_mask = _hard_feasible(total_cal, total_pg, total_fg, total_cg, t_adj)
        if feasible_mask.sum() > 0:
            relaxation_level = level_name
            break

    num_feasible = int(feasible_mask.sum())

    # Score feasible candidates
    feas_cal = total_cal[feasible_mask]
    feas_pg  = total_pg[feasible_mask]
    feas_fg  = total_fg[feasible_mask]
    feas_cg  = total_cg[feasible_mask]

    macro_pen   = _macro_penalty(feas_cal, feas_pg, feas_fg, feas_cg, nutrition_target)
    scores_feas = (macro_pen
                   + total_ep[feasible_mask]
                   + total_pp[feasible_mask]
                   + total_cp[feasible_mask])

    feas_positions = np.where(feasible_mask)[0]
    ranked_local   = np.argsort(scores_feas)
    ranked_global  = feas_positions[ranked_local]

    # Select 3 diverse plans
    selected = []
    for local_i, global_i in zip(ranked_local, ranked_global):
        if len(selected) >= 3:
            break

        combo  = tuple(flat[si][global_i] for si in range(K))
        chosen = [slot_cands[si][combo[si]] for si in range(K)]

        # Cross-slot non-staple duplicate rejection
        all_idx = [idx for c in chosen for idx in c["indices"]]
        all_fg  = [fg  for c in chosen for fg  in c["food_groups"]]
        ns_idx  = [i   for i, fg in zip(all_idx, all_fg) if fg not in STAPLE_GROUPS]
        if len(ns_idx) != len(set(ns_idx)):
            continue

        # Diversity: must differ from all selected plans in >= 2 slots
        too_similar = any(
            sum(a == b for a, b in zip(combo, prev)) >= K - 1
            for _, prev, _ in selected
        )
        if too_similar:
            continue

        selected.append((float(scores_feas[local_i]), combo, chosen))

    # Fallback: if strict diversity left < 3, relax the diversity check
    if len(selected) < 3:
        for local_i, global_i in zip(ranked_local, ranked_global):
            if len(selected) >= 3:
                break
            combo = tuple(flat[si][global_i] for si in range(K))
            if any(combo == prev for _, prev, _ in selected):
                continue
            chosen = [slot_cands[si][combo[si]] for si in range(K)]
            selected.append((float(scores_feas[local_i]), combo, chosen))

    # Format output
    plans = _format_plans(selected, slot_seq, df, nutrition_target)

    return {
        "plans":            plans,
        "relaxation_level": relaxation_level,
        "runtime_ms":       round((time.monotonic() - t0) * 1000),
        "num_candidates":   num_candidates,
        "num_feasible":     num_feasible,
    }


# -- Anchor role checker --------------------------------------------------------

def _check_anchors(roles: list, slot_type: str, nr: int) -> bool:
    """
    Enforce structural composition rules for meal slots.

    Lunch / Dinner:
      - nr == 1: ONLY allowed if the single recipe is a complete_meal
      - nr >= 2: must include at least one anchor_protein AND one anchor_starch
                 (a complete_meal in the combo satisfies both requirements)

    Breakfast / Snack: no structural requirements — any valid recipe(s) allowed.
    """
    if slot_type not in ("lunch", "dinner"):
        return True

    if nr == 1:
        return roles[0] == COMPLETE_MEAL_ROLE

    # nr >= 2
    has_protein  = any(r in ANCHOR_PROTEIN_ROLES for r in roles)
    has_starch   = any(r in ANCHOR_STARCH_ROLES  for r in roles)
    has_complete = any(r == COMPLETE_MEAL_ROLE    for r in roles)

    return has_complete or (has_protein and has_starch)


# -- Cuisine coherence ----------------------------------------------------------

def _cuisine_penalty(cuisines: list) -> float:
    valid = [c for c in cuisines if c != "unknown"]
    if len(valid) < 2:
        return 0.0
    total = 0.0
    for a, b in combinations(valid, 2):
        fa = CUISINE_FAMILY.get(a, "other")
        fb = CUISINE_FAMILY.get(b, "other")
        if fa == fb:
            total -= CUISINE_MATCH_R
        else:
            total += CUISINE_CLASH_P
    return total


# -- Portion deviation ----------------------------------------------------------

def _portion_pen(portions: list, typicals: list) -> float:
    return sum(
        PORTION_DEV_K * ((p - t) / t) ** 2
        for p, t in zip(portions, typicals) if t > 0
    )


# -- Hard feasibility -----------------------------------------------------------

def _hard_feasible(cal, prot_g, fat_g, carb_g, t) -> np.ndarray:
    return (
        (cal    >= t["cal_target"]  * (1 - t["cal_hard_pct"]))    &
        (cal    <= t["cal_target"]  * (1 + t["cal_hard_pct"]))    &
        (prot_g >= t["protein_g"]   * (1 - t["protein_hard_lo"])) &
        (fat_g  >= t["fat_g"]       * (1 - t["fat_hard_lo"]))     &
        (fat_g  <= t["fat_g"]       * (1 + t["fat_hard_hi"]))     &
        (carb_g >= t["carb_g"]      * (1 - t["carb_hard_pct"]))   &
        (carb_g <= t["carb_g"]      * (1 + t["carb_hard_pct"]))
    )


def _scale_hard_limits(target: dict, multiplier: float) -> dict:
    out = dict(target)
    for key in ["cal_hard_pct", "protein_hard_lo", "fat_hard_hi",
                "fat_hard_lo", "carb_hard_pct", "fiber_hard_lo"]:
        out[key] = target.get(key, 0.25) * multiplier
    return out


# -- Macro penalty --------------------------------------------------------------

def _macro_penalty(cal, prot_g, fat_g, carb_g, t) -> np.ndarray:
    """Asymmetric quadratic penalty. Protein undershoot and fat overshoot are
    penalised more heavily; calorie and carb deviations are symmetric."""
    pen = np.zeros(len(cal))

    cal_dev = np.maximum(
        0, np.abs(cal - t["cal_target"]) / t["cal_target"] - t.get("cal_soft_pct", 0.08)
    )
    pen += t.get("k_cal", 1000) * cal_dev ** 2

    prot_under = np.maximum(
        0,
        (t["protein_g"] * (1 - t.get("protein_soft_lo", 0.05)) - prot_g) / t["protein_g"]
    )
    pen += t.get("k_protein_under", 2000) * prot_under ** 2

    fat_over = np.maximum(
        0,
        (fat_g - t["fat_g"] * (1 + t.get("fat_soft_hi", 0.10))) / t["fat_g"]
    )
    pen += t.get("k_fat_over", 1500) * fat_over ** 2

    carb_dev = np.maximum(
        0,
        np.abs(carb_g - t["carb_g"]) / t["carb_g"] - t.get("carb_soft_pct", 0.15)
    )
    pen += t.get("k_carb", 400) * carb_dev ** 2

    return pen


# -- Per-slot candidate generation (Phase 1) ------------------------------------

def _gen_slot_cands(df: pd.DataFrame, s_type: str,
                    s_target: float, nutrition_target: dict) -> list:
    """
    Generate and rank meal candidates for one slot.

    Key constraints applied here (before global scoring):
      1. Calorie acceptance window: ±SLOT_WINDOW of matrix target
      2. Min/max recipe count per slot type
      3. Anchor role enforcement (lunch/dinner only)
      4. Food group uniqueness within slot
      5. Per-recipe portion envelopes
    """
    sp     = SLOT_PARAMS[s_type]
    min_n  = sp["min_n"]
    max_n  = sp["max_n"]
    has_fg = "food_group" in df.columns

    elig = df[df["meal_type"].str.contains(sp["kw"], case=False, na=False)].copy()
    ne   = len(elig)
    if ne == 0:
        return []

    # Slot calorie acceptance window
    cal_lo = s_target * (1 - SLOT_WINDOW)
    cal_hi = s_target * (1 + SLOT_WINDOW)

    all_cands = []

    # -- Single-recipe candidates -----------------------------------------------
    # For lunch/dinner, only complete_meal qualifies as a solo slot.
    # For breakfast and snack, any recipe qualifies.
    allow_solo = (s_type not in ("lunch", "dinner"))

    for iloc_i in range(ne):
        r     = elig.iloc[iloc_i]
        role  = str(r.get("role", "side"))
        p_min = float(r.get("portion_min",     0.5))
        p_typ = float(r.get("portion_typical", 1.0))
        p_max = float(r.get("portion_max",     1.5))
        cal   = float(r["calories"])

        # Skip this recipe as a solo lunch/dinner unless it's a complete_meal
        if not allow_solo and role != COMPLETE_MEAL_ROLE:
            continue

        if min_n > 1 and role != COMPLETE_MEAL_ROLE:
            # Slot requires >= 2 recipes; skip single-recipe unless complete_meal
            continue

        port_opts = np.unique(np.clip(
            [p_min, p_typ, (p_typ + p_max) / 2.0, p_max], p_min, p_max
        ))
        best_p = port_opts[np.argmin(np.abs(cal * port_opts - s_target))]
        tc     = cal * best_p

        if tc < cal_lo or tc > cal_hi:
            continue

        all_cands.append({
            "indices":    [int(elig.index[iloc_i])],
            "portions":   [float(best_p)],
            "n":          1,
            "total_cal":  float(tc),
            "prot_cal":   float(r["protein"]      * best_p * 4),
            "carb_cal":   float(r["carbohydrate"] * best_p * 4),
            "fat_cal":    float(r["fat"]           * best_p * 9),
            "food_groups": [str(r.get("food_group", "misc"))],
            "extra_pen":   0.0,
            "portion_pen": float(_portion_pen([best_p], [p_typ])),
            "cuisine_pen": 0.0,
            "score":       float((tc - s_target) ** 2 / max(s_target, 1)),
        })

    # -- Multi-recipe candidates ------------------------------------------------
    for nr in range(max(min_n, 2), min(max_n, ne) + 1):
        per_tgt    = s_target / nr
        top_n      = min({2: 20, 3: 16, 4: 12}[min(nr, 4)], ne)
        deviations = np.abs(elig["calories"].values.astype(float) - per_tgt)
        top_ilocs  = np.argsort(deviations)[:top_n]

        if top_n < nr:
            continue

        for combo_locs in combinations(range(top_n), nr):
            elig_ilocs = top_ilocs[list(combo_locs)]
            rr         = elig.iloc[elig_ilocs]

            # Food group uniqueness
            fgs = rr["food_group"].tolist() if has_fg else ["misc"] * nr
            if len(set(fgs)) < nr:
                continue

            # Anchor role enforcement
            roles = rr["role"].tolist() if "role" in rr.columns else ["side"] * nr
            if not _check_anchors(roles, s_type, nr):
                continue

            # Build per-recipe portion grids
            port_grids = []
            typicals   = []
            for il in elig_ilocs:
                rx    = elig.iloc[il]
                p_min = float(rx.get("portion_min",     0.5))
                p_typ = float(rx.get("portion_typical", 1.0))
                p_max = float(rx.get("portion_max",     1.5))
                opts  = np.unique(np.clip(
                    [p_min, p_typ, (p_typ + p_max) / 2.0, p_max], p_min, p_max
                ))
                port_grids.append(opts)
                typicals.append(p_typ)

            port_matrix = np.array(list(iproduct(*port_grids)))
            cals        = rr["calories"].values.astype(float)
            total_opts  = port_matrix @ cals
            best_gi     = int(np.argmin(np.abs(total_opts - s_target)))
            best_ports  = port_matrix[best_gi].tolist()
            tc          = float(total_opts[best_gi])

            if tc < cal_lo or tc > cal_hi:
                continue

            ep   = (nr - 1) * EXTRA_PENALTY
            pp   = _portion_pen(best_ports, typicals)
            cuis = rr["cuisine"].tolist() if "cuisine" in rr.columns else ["unknown"] * nr
            cp   = _cuisine_penalty(cuis)

            all_cands.append({
                "indices":    [int(elig.index[i]) for i in elig_ilocs],
                "portions":   best_ports,
                "n":          nr,
                "total_cal":  tc,
                "prot_cal":   float(np.sum(rr["protein"].values      * best_ports) * 4),
                "carb_cal":   float(np.sum(rr["carbohydrate"].values * best_ports) * 4),
                "fat_cal":    float(np.sum(rr["fat"].values           * best_ports) * 9),
                "food_groups": fgs,
                "extra_pen":   float(ep),
                "portion_pen": float(pp),
                "cuisine_pen": float(cp),
                "score":       float((tc - s_target) ** 2 / max(s_target, 1) + ep + pp + cp),
            })

    all_cands.sort(key=lambda c: c["score"])
    return all_cands[:M_CANDS]


# -- Output formatter -----------------------------------------------------------

def _format_plans(selected: list, slot_seq: list,
                  df: pd.DataFrame, nt: dict) -> list:
    plans = []
    for score, combo, chosen in selected:
        slots_out = []
        tp_g = tc_g = tf_g = 0.0

        for si, cand in enumerate(chosen):
            recipes_in_slot = []
            for idx, port in zip(cand["indices"], cand["portions"]):
                r = df.iloc[idx].to_dict()
                r["portion"]        = port
                r["calories_shown"] = round(r["calories"]     * port)
                r["protein_shown"]  = round(r["protein"]      * port, 1)
                r["carb_shown"]     = round(r["carbohydrate"] * port, 1)
                r["fat_shown"]      = round(r["fat"]          * port, 1)
                recipes_in_slot.append(r)
                tp_g += r["protein_shown"]
                tc_g += r["carb_shown"]
                tf_g += r["fat_shown"]

            slots_out.append({
                "type":      slot_seq[si],
                "recipes":   recipes_in_slot,
                "total_cal": sum(r["calories_shown"] for r in recipes_in_slot),
                "n_recipes": len(recipes_in_slot),
            })

        total_c = round(sum(s["total_cal"] for s in slots_out))
        mc      = max(tp_g * 4 + tc_g * 4 + tf_g * 9, 1)

        plans.append({
            "slots":     slots_out,
            "total_cal": total_c,
            "protein_g": round(tp_g, 1),
            "carb_g":    round(tc_g, 1),
            "fat_g":     round(tf_g, 1),
            "score":     round(score, 1),
            "prot_pct":  round(tp_g * 4 / mc * 100),
            "carb_pct":  round(tc_g * 4 / mc * 100),
            "fat_pct":   round(tf_g * 9 / mc * 100),
            "macro_deviations": {
                "calories": round((total_c - nt["cal_target"]) / nt["cal_target"] * 100, 1),
                "protein":  round((tp_g - nt["protein_g"])     / nt["protein_g"]  * 100, 1),
                "fat":      round((tf_g - nt["fat_g"])         / nt["fat_g"]      * 100, 1),
                "carbs":    round((tc_g - nt["carb_g"])        / nt["carb_g"]     * 100, 1),
            },
        })
    return plans
