# app.py  -  Call Bhaiya  -  Streamlit + Supabase  -  v2
# Deployment: Hugging Face Spaces (free, always-on, public URL)
# Cron jobs:  Windows Task Scheduler on local Dell Precision

import streamlit as st
import pandas as pd
import altair as alt
from datetime import date, datetime

from db.connection        import get_connection
from db.users             import (get_user_by_name, verify_password,
                                  update_user_settings, update_password)
from db.recipes           import (get_all_recipes, get_recipe_detail,
                                  add_custom_recipe, get_custom_recipes_for_user,
                                  log_optimizer_run)
from db.logs              import (log_meal, get_today_logs, get_logs_for_date,
                                  get_week_summary, compute_streak,
                                  update_log_entry, delete_log_entry,
                                  get_last_n_days_logs)
from db.nudges            import get_all_nudges, get_latest_nudge, mark_nudge_seen
from db.nutrition_targets import (load_or_default_target, save_nutrition_target,
                                  get_default_target, blend_macro_targets)
from optimizer.meal_optimizer import run_optimizer, ALLOWED_TYPES

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Call Bhaiya",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styles ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=DM+Serif+Display&display=swap');

  :root {
    --green-deep:   #1D4A2F;
    --green-mid:    #2D6A4F;
    --green-light:  #52B788;
    --linen:        #F0EFE9;
    --linen-dark:   #E8E6DE;
    --text-primary: #1a1a1a;
    --text-muted:   #6B7280;
    --card-bg:      #FFFFFF;
    --card-radius:  14px;
    --card-shadow:  0 2px 12px rgba(29,74,47,0.08);
  }

  html, body, [class*="css"], .stApp { font-family: 'DM Sans', sans-serif !important; }
  h1, h2 { font-family: 'DM Serif Display', serif !important; }

  /* ── Sidebar ── */
  [data-testid="stSidebar"] { background: var(--green-deep) !important; }
  [data-testid="stSidebar"] * { color: #fff !important; }
  [data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.2) !important; }

  /* ── Primary button ── */
  .stButton > button[kind="primary"] {
    background: var(--green-deep) !important;
    color: #fff !important;
    border-radius: 8px !important;
  }
  .stButton > button[kind="primary"]:hover { background: var(--green-mid) !important; }

  /* ── Card utility ── */
  .cb-card {
    background: var(--card-bg);
    border-radius: var(--card-radius);
    box-shadow: var(--card-shadow);
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
  }

  /* ── Responsive grids ── */
  .cb-grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
  .cb-grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; }
  @media (max-width: 900px) {
    .cb-grid-2 { grid-template-columns: 1fr; }
    .cb-grid-4 { grid-template-columns: 1fr 1fr; }
  }

  /* ── Stat card (dashboard + diary) ── */
  .stat-card  { background: var(--card-bg); border-radius: var(--card-radius);
                padding: 14px 12px; text-align: center;
                box-shadow: var(--card-shadow); }
  .stat-val   { font-size: 22px; font-weight: 800; color: var(--green-deep); }
  .stat-lbl   { font-size: 12px; color: var(--text-muted); margin-top: 2px; }

  /* ── Sidebar brand header ── */
  .cb-brand {
    text-align: center; padding: 4px 8px 18px;
    border-bottom: 1px solid rgba(255,255,255,0.15); margin-bottom: 10px;
  }
  .cb-brand-icon { font-size: 38px; line-height: 1.2; }
  .cb-brand-name {
    font-size: 22px; font-weight: 800; color: #fff;
    letter-spacing: -0.5px; margin: 4px 0 2px;
  }
  .cb-brand-tag { font-size: 11px; color: rgba(255,255,255,0.6); letter-spacing: 0.3px; }

  /* ── User avatar ── */
  .cb-avatar-wrap { text-align: center; padding: 6px 0 18px; }
  .cb-avatar {
    width: 44px; height: 44px; border-radius: 50%;
    background: rgba(255,255,255,0.2);
    color: white; font-size: 20px; font-weight: 800;
    display: inline-flex; align-items: center; justify-content: center;
    margin-bottom: 6px;
  }
  .cb-uname { font-weight: 700; font-size: 14px; }

  /* ── Login hero ── */
  .cb-login-hero { text-align: center; padding: 28px 0 20px; }
  .cb-login-title {
    font-size: 36px; font-weight: 800; letter-spacing: -1px;
    color: #1a1a1a; margin: 6px 0 4px; line-height: 1.1;
  }
  .cb-login-tagline { font-size: 14px; color: #999; margin-bottom: 0; font-weight: 500; }

  /* ── Slot cards ── */
  .slot-card      { padding: 16px 18px; border-radius: 14px; margin-bottom: 14px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.06); }
  .breakfast-card { background: #FFF8F0; border-left: 4px solid #FF6B35; }
  .lunch-card     { background: #F0FBF0; border-left: 4px solid #43A047; }
  .snack-card     { background: #FFF0F5; border-left: 4px solid #E91E8C; }
  .dinner-card    { background: #F0F4FF; border-left: 4px solid #3D5AF1; }

  /* ── Macro bar ── */
  .macro-bar-bg   { background: #e0e0e0; border-radius: 4px; height: 8px; margin-top: 4px; }
  .macro-bar-fill { height: 8px; border-radius: 4px; }

  /* ── Deviation colours ── */
  .dev-ok   { color: #2e7d32; font-weight: 700; }
  .dev-warn { color: #e65100; font-weight: 700; }
  .dev-bad  { color: #c62828; font-weight: 700; }

  /* ── Plan quality badges ── */
  .badge-good { background: #E8F5E9; color: #1B5E20; padding: 3px 12px;
                border-radius: 20px; font-size: 12px; font-weight: 700; }
  .badge-ok   { background: #E3F2FD; color: #0D47A1; padding: 3px 12px;
                border-radius: 20px; font-size: 12px; font-weight: 700; }
  .badge-fair { background: #FFF3E0; color: #E65100; padding: 3px 12px;
                border-radius: 20px; font-size: 12px; font-weight: 700; }

  /* ── Nudge cards ── */
  .nudge-new  { background: white; border: 1.5px solid rgba(29,74,47,0.3);
                border-radius: 12px; padding: 14px 18px; margin-bottom: 12px; }
  .nudge-seen { background: white; border: 1.5px solid rgba(0,0,0,0.08);
                border-radius: 12px; padding: 14px 18px; margin-bottom: 12px; opacity: 0.7; }

  /* ── Disclaimer ── */
  .disclaimer { background: #fff8e1; border: 1px solid #ffe082; border-radius: 12px;
                padding: 14px 18px; font-size: 13px; color: #795548; margin-top: 24px; }

  /* ── Slot recipe list (replaces table on mobile) ── */
  .recipe-row { display: flex; justify-content: space-between; align-items: baseline;
                padding: 5px 0; border-bottom: 1px solid rgba(0,0,0,0.05);
                gap: 8px; flex-wrap: wrap; }
  .recipe-row:last-child { border-bottom: none; }
  .recipe-name { font-size: 14px; font-weight: 500; color: #1a1a1a; flex: 1; min-width: 0; }
  .recipe-macros { font-size: 12px; color: var(--text-muted); white-space: nowrap; }

  /* ── Form widget contrast on linen background ── */
  /* Text inputs and number inputs */
  [data-testid="stTextInput"] input,
  [data-testid="stNumberInput"] input,
  [data-testid="stTextArea"] textarea {
    background: white !important;
    color: #1a1a1a !important;
    border: 1px solid #ccc !important;
  }
  /* Select boxes */
  [data-testid="stSelectbox"] > div > div,
  [data-testid="stSelectbox"] > div > div > div {
    background: white !important;
    color: #1a1a1a !important;
  }
  /* Select box dropdown options */
  [data-testid="stSelectbox"] li { color: #1a1a1a !important; }
  /* Multiselect */
  [data-testid="stMultiSelect"] > div > div {
    background: white !important;
    color: #1a1a1a !important;
  }
  /* All widget labels in main area */
  [data-testid="stWidgetLabel"] p,
  [data-testid="stWidgetLabel"] label,
  .stRadio label, .stCheckbox label,
  .stSlider label,
  [data-baseweb="select"] { color: #1a1a1a !important; }
  /* Slider track text */
  [data-testid="stSlider"] [data-testid="stWidgetLabel"] { color: #1a1a1a !important; }
  /* Caption / small text */
  [data-testid="stCaptionContainer"] p { color: var(--text-muted) !important; }
  /* Dataframe text */
  [data-testid="stDataFrame"] * { color: #1a1a1a !important; }

  /* ── Sidebar secondary button (Log Out) ── */
  [data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,0.12) !important;
    color: #fff !important;
    border: 1px solid rgba(255,255,255,0.3) !important;
    border-radius: 8px !important;
  }
  [data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,255,255,0.22) !important;
  }
</style>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────────
SLOT_COLORS = {"lunch":"lunch-card", "dinner":"dinner-card",
               "breakfast":"breakfast-card", "snack":"snack-card"}
SLOT_ICONS  = {"lunch":"☀️", "dinner":"🌙", "breakfast":"🌅", "snack":"🍎"}
SLOT_LABELS = {"lunch":"Lunch", "dinner":"Dinner",
               "breakfast":"Breakfast", "snack":"Snack"}
FOOD_PREFS  = {"vegan":"🌱 Vegan", "veg":"🧀 Vegetarian",
               "egg":"🥚 Egg allowed", "non-veg":"🍗 Non-vegetarian"}
PORTIONS    = {"0.5×":0.5, "1×":1.0, "1.5×":1.5, "2×":2.0}

RELAX_MESSAGES = {
    "strict":    None,
    "relaxed":   ("ℹ️ Plans shown at **relaxed** nutrition tolerance. "
                  "Your recipe pool may be too narrow for strict targets — "
                  "try broadening your food preference or adjusting targets in Settings."),
    "loose":     ("⚠️ Plans shown at **loose** nutrition tolerance. "
                  "Consider adding more recipes or widening your calorie target."),
    "soft_only": ("⚠️ Could not satisfy hard nutrition limits at any tolerance level. "
                  "Showing best available plans — macro targets may not be met. "
                  "Review your nutrition targets in Settings."),
}


# ── DB / data helpers ──────────────────────────────────────────────────────────
@st.cache_resource
def _conn_pool():
    return get_connection()

def conn():
    return _conn_pool()

@st.cache_data(ttl=300)
def load_recipes():
    return get_all_recipes(conn())


# ═══════════════════════════════════════════════════════════════════════════════
# AUTH
# ═══════════════════════════════════════════════════════════════════════════════

def login_page():
    col1, col2, col3 = st.columns([1, 1.1, 1])
    with col2:
        st.markdown("""
        <div class="cb-login-hero">
            <div style="width:80px;height:80px;border-radius:24px;
                background:#1D4A2F;
                display:flex;align-items:center;justify-content:center;
                font-size:40px;margin:0 auto 14px;
                box-shadow:0 10px 28px rgba(29,74,47,0.4);">🔥</div>
            <div class="cb-login-title">Call Bhaiya</div>
            <div class="cb-login-tagline">Only if required, baaki trust this web app</div>
        </div>
        """, unsafe_allow_html=True)
        with st.form("login"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            if st.form_submit_button("Log In →", use_container_width=True, type="primary"):
                user = get_user_by_name(conn(), username)
                if user and verify_password(password, user["password_hash"]):
                    st.session_state.logged_in = True
                    st.session_state.user_id   = user["id"]
                    st.session_state.username  = user["name"]
                    st.session_state.user_data = dict(user)
                    st.rerun()
                else:
                    st.error("Incorrect username or password.")

        st.markdown("""
        <div style="margin-top:24px;background:white;border:1.5px solid rgba(29,74,47,0.15);
            border-radius:14px;padding:18px 20px;">
          <div style="font-size:13px;font-weight:700;color:#1D4A2F;
              letter-spacing:0.3px;margin-bottom:12px;">
            A few pointers before you start
          </div>
          <ul style="margin:0;padding-left:18px;display:flex;flex-direction:column;gap:9px;">
            <li style="font-size:12.5px;color:#444;line-height:1.5;">
              The app is optimized to best meet your nutrition target and not for your tongue.
              Some pairings may feel weird to eat — swap them out yourself to see how it
              affects your daily nutrition targets.
            </li>
            <li style="font-size:12.5px;color:#444;line-height:1.5;">
              Don't stress on achieving the perfect balance every day. Follow the nudges
              (activates once you've entered data for 4 days) and let the weekly averages
              work it out.
            </li>
            <li style="font-size:12.5px;color:#444;line-height:1.5;">
              Can't find the dish you want? Add it in <strong>Add Recipe</strong>.
              It'll be there from next time.
            </li>
            <li style="font-size:12.5px;color:#444;line-height:1.5;">
              Don't add alcoholic beverages for now. Will add that as soon as I figure
              it out myself.
            </li>
            <li style="font-size:12.5px;color:#444;line-height:1.5;">
              Use diligently for best results. You miss out, you go farther from your
              goals. Your loss in the end — the world will keep spinning the same anyway.
            </li>
          </ul>
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD (HOME)
# ═══════════════════════════════════════════════════════════════════════════════

def home_page():
    uid   = st.session_state.user_id
    uname = st.session_state.username
    ud    = st.session_state.user_data

    hour = datetime.now().hour
    greeting = "Good morning" if hour < 12 else ("Good afternoon" if hour < 18 else "Good evening")
    st.markdown(
        f"<h1 style='margin-bottom:2px'>{greeting}, {uname} 👋</h1>"
        f"<p style='color:var(--text-muted);margin-top:0'>Here's your nutrition snapshot for today.</p>",
        unsafe_allow_html=True
    )

    # ── Today's macros ────────────────────────────────────────────────────────
    today_df = get_today_logs(conn(), uid)
    nt        = load_or_default_target(conn(), uid, int(ud.get("daily_cal", 1800)))
    cal_tgt   = int(nt.get("cal_target", ud.get("daily_cal", 1800)))
    prot_tgt  = int(nt.get("protein_g", 90))
    carb_tgt  = int(nt.get("carb_g", 225))
    fat_tgt   = int(nt.get("fat_g", 60))

    if today_df.empty:
        tc = tp = tcarb = tf = 0
    else:
        tc    = int(today_df["calories"].sum())
        tp    = round(today_df["protein_g"].sum(), 1)
        tcarb = round(today_df["carb_g"].sum(), 1)
        tf    = round(today_df["fat_g"].sum(), 1)

    c1, c2, c3, c4 = st.columns(4)
    for col, val, tgt, lbl, unit in [
        (c1, tc,    cal_tgt,  "Calories",  "kcal"),
        (c2, tp,    prot_tgt, "Protein",   "g"),
        (c3, tcarb, carb_tgt, "Carbs",     "g"),
        (c4, tf,    fat_tgt,  "Fat",       "g"),
    ]:
        with col:
            st.markdown(
                f'<div class="stat-card">'
                f'<div class="stat-val">{val}<span style="font-size:11px;font-weight:400;'
                f'color:var(--text-muted)"> {unit}</span></div>'
                f'<div class="stat-lbl">{lbl} <span style="color:var(--text-muted)">/ {tgt} {unit}</span></div>'
                f'</div>',
                unsafe_allow_html=True
            )
    st.markdown("")

    # ── Streak + week avg ─────────────────────────────────────────────────────
    streak   = compute_streak(conn(), uid)
    week_df  = get_week_summary(conn(), uid)
    week_avg = int(week_df["total_cal"].mean()) if not week_df.empty and "total_cal" in week_df.columns else 0

    sc1, sc2 = st.columns(2)
    with sc1:
        st.markdown(
            f'<div class="cb-card" style="text-align:center">'
            f'<div style="font-size:2rem;font-weight:600;color:var(--green-deep)">'
            f'🔥 {streak}</div>'
            f'<div style="font-size:0.75rem;color:var(--text-muted);text-transform:uppercase;'
            f'letter-spacing:0.05em">Day streak</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    with sc2:
        st.markdown(
            f'<div class="cb-card" style="text-align:center">'
            f'<div style="font-size:2rem;font-weight:600;color:var(--green-deep)">'
            f'📅 {week_avg}</div>'
            f'<div style="font-size:0.75rem;color:var(--text-muted);text-transform:uppercase;'
            f'letter-spacing:0.05em">7-day avg kcal</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    # ── Latest nudge ──────────────────────────────────────────────────────────
    nudges = get_all_nudges(conn(), uid, limit=1)
    if nudges:
        n = nudges[0]
        st.markdown("#### Latest Nudge")
        css_cls = "nudge-new" if not n["seen"] else "nudge-seen"
        st.markdown(
            f'<div class="{css_cls}">'
            f'<div style="font-size:11px;color:var(--text-muted);margin-bottom:6px">'
            f'Generated {n["generated_on"]} · {n.get("days_analyzed","?")} day(s) of data</div>'
            f'<div style="font-size:15px;line-height:1.6">{n["nudge_text"]}</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    else:
        st.info("No nudges yet — they appear after the nightly analysis (requires at least 1 day of data).")


# ═══════════════════════════════════════════════════════════════════════════════
# SHARED UI HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _quality_badge(score):
    if score < 500:
        return '<span class="badge-good">Excellent</span>'
    if score < 2000:
        return '<span class="badge-ok">Good</span>'
    return '<span class="badge-fair">Fair</span>'

def _macro_bar(pct, color="#43a047"):
    pct = min(100, max(0, pct))
    return (f'<div class="macro-bar-bg">'
            f'<div class="macro-bar-fill" style="width:{pct}%;background:{color};"></div>'
            f'</div>')

def _target_color(pct):
    if pct < 80:   return "#ff9800"
    if pct <= 110: return "#43a047"
    return "#e53935"

def _dev_class(dev_pct: float, soft: float, hard: float) -> str:
    """Return CSS class based on how far deviation is from target."""
    abs_dev = abs(dev_pct)
    if abs_dev <= soft * 100:  return "dev-ok"
    if abs_dev <= hard * 100:  return "dev-warn"
    return "dev-bad"

def _dev_symbol(dev_pct: float) -> str:
    if abs(dev_pct) < 2:   return "✓"
    if dev_pct > 0:        return f"+{dev_pct:.1f}%"
    return f"{dev_pct:.1f}%"


@st.dialog("Recipe Details", width="large")
def show_recipe_modal(recipe_name: str):
    det = get_recipe_detail(conn(), recipe_name)
    if not det:
        st.warning("No details found for this recipe.")
        return
    st.subheader(recipe_name)
    st.markdown(f"**Serving:** {det.get('serving_note', '')}")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Ingredients**")
        for ing in (det.get("ingredients") or "").split("|"):
            if ing.strip():
                st.markdown(f"- {ing.strip()}")
    with c2:
        st.markdown("**Method**")
        for i, step in enumerate((det.get("steps") or "").split("|"), 1):
            if step.strip():
                st.markdown(f"{i}. {step.strip()}")


@st.dialog("Review My Diet", width="large")
def review_modal(plan_idx: int):
    ud  = st.session_state.user_data
    df  = st.session_state.customize_state[plan_idx]
    nt  = st.session_state.get("nutrition_target",
                               get_default_target(int(ud.get("daily_cal", 1800))))

    if df.empty:
        st.warning("Nothing in the plan yet.")
        return

    tc    = (df["base_cal"]  * df["portion"]).sum()
    tp    = (df["base_prot"] * df["portion"]).sum()
    tcarb = (df["base_carb"] * df["portion"]).sum()
    tf    = (df["base_fat"]  * df["portion"]).sum()
    mc    = max(tp * 4 + tcarb * 4 + tf * 9, 1)
    pct   = int(min(100, tc / max(nt["cal_target"], 1) * 100))

    st.markdown(
        f"### Macro Summary\n"
        f"**{int(tc)} kcal** &nbsp;|&nbsp; "
        f"Protein: {tp:.1f}g ({tp*4/mc*100:.0f}%) &nbsp;|&nbsp; "
        f"Carbs: {tcarb:.1f}g ({tcarb*4/mc*100:.0f}%) &nbsp;|&nbsp; "
        f"Fat: {tf:.1f}g ({tf*9/mc*100:.0f}%)"
    )
    st.markdown(f"_{pct}% of your {nt['cal_target']} kcal target_")
    st.markdown(_macro_bar(pct, _target_color(pct)), unsafe_allow_html=True)
    st.divider()

    for slot_type in ["lunch", "dinner", "breakfast", "snack"]:
        sdf = df[df["slot_type"] == slot_type]
        if sdf.empty:
            continue
        slot_cal = int((sdf["base_cal"] * sdf["portion"]).sum())
        st.markdown(f"#### {SLOT_ICONS[slot_type]} {SLOT_LABELS[slot_type]} — {slot_cal} kcal")
        for _, row in sdf.iterrows():
            det    = get_recipe_detail(conn(), row["name"])
            cal_p  = int(row["base_cal"]  * row["portion"])
            prot_p = round(row["base_prot"] * row["portion"], 1)
            carb_p = round(row["base_carb"] * row["portion"], 1)
            fat_p  = round(row["base_fat"]  * row["portion"], 1)
            with st.expander(
                f"**{row['name']}** — {row['portion']}× | "
                f"{cal_p} kcal | P:{prot_p}g C:{carb_p}g F:{fat_p}g"
            ):
                if det:
                    st.write(f"**Serving:** {det.get('serving_note', '')}")
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write("**Ingredients**")
                        for ing in (det.get("ingredients", "") or "").split("|"):
                            if ing.strip(): st.write(f"- {ing.strip()}")
                    with c2:
                        st.write("**Steps**")
                        for i, s in enumerate(
                            (det.get("steps", "") or "").split("|"), 1
                        ):
                            if s.strip(): st.write(f"{i}. {s.strip()}")

    st.divider()
    # Daily total footer
    st.caption(
        f"Estimated daily totals: **{int(tc)} kcal** · "
        f"{tp:.0f}g protein · {tcarb:.0f}g carbs · {tf:.0f}g fat"
    )
    if st.button("✅ Confirm & Log All", type="primary", use_container_width=True):
        uid = st.session_state.user_id
        for _, row in df.iterrows():
            meal_type = SLOT_LABELS[row["slot_type"]]
            log_meal(conn(), uid, date.today(), row["name"], meal_type,
                     int(row["base_cal"]  * row["portion"]),
                     round(row["base_prot"] * row["portion"], 1),
                     round(row["base_carb"] * row["portion"], 1),
                     round(row["base_fat"]  * row["portion"], 1))
        st.success(f"✓ {len(df)} items logged!")
        st.balloons()
        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# GET A PLAN PAGE
# ═══════════════════════════════════════════════════════════════════════════════

def plan_page():
    st.title("🗓️ Meal Plan")
    ud  = st.session_state.user_data
    uid = st.session_state.user_id

    CUISINE_LABELS = {
        "north_indian":   "🇮🇳 North Indian",
        "south_indian":   "🌴 South Indian",
        "indo_chinese":   "🥢 Indo-Chinese",
        "east_asian":     "🍱 East Asian",
        "continental":    "🌍 Continental",
        "mediterranean":  "🫒 Mediterranean",
        "middle_eastern": "🧆 Middle Eastern",
        "mexican":        "🌮 Mexican",
        "parsi":          "🔥 Parsi",
        "unknown":        "Other",
    }

    with st.sidebar:
        st.markdown("### ⚙️ Plan Settings")
        num_meals  = st.slider("Meals per day", 2, 5, int(ud.get("num_meals", 3)))
        food_pref  = st.selectbox(
            "Food preference", list(FOOD_PREFS.keys()),
            index=list(FOOD_PREFS.keys()).index(ud.get("food_pref", "veg")),
            format_func=lambda k: FOOD_PREFS[k]
        )
        target_cal = st.number_input(
            "Daily calorie target", 1000, 3500, int(ud.get("daily_cal", 1800)), 50
        )
        cuisine_filter = st.multiselect(
            "Cuisine (optional — leave blank for all)",
            options=list(CUISINE_LABELS.keys()),
            format_func=lambda k: CUISINE_LABELS[k],
            key="plan_cuisine_filter",
        )
        gen = st.button("🎯 Generate Plans", type="primary", use_container_width=True)

    if gen:
        recipes_df = load_recipes()
        if cuisine_filter:
            recipes_df = recipes_df[
                recipes_df["cuisine"].fillna("unknown").isin(cuisine_filter) |
                (recipes_df["role"].fillna("") == "gap_filler")
            ].copy()
        # Load stored targets (for band widths, penalty weights, and macro split)
        nt = load_or_default_target(conn(), uid, target_cal)

        # BUG FIX: always recompute gram targets from the CURRENT cal_target.
        # The stored protein_g / fat_g / carb_g may be based on a different
        # calorie level.  We keep the stored macro SPLIT PERCENTAGES but
        # re-derive the gram targets each time plan generation is triggered.
        #
        # Stored targets contain cal_target from when they were seeded.
        # Derive the macro split % from that seeded row, then apply to
        # the user's current cal_target from the sidebar.
        stored_cal = float(nt.get("cal_target") or target_cal)

        # Recover macro split % from stored grams (fall back to defaults)
        if stored_cal > 0:
            prot_pct = float(nt.get("protein_g", 0)) * 4 / stored_cal
            fat_pct  = float(nt.get("fat_g",     0)) * 9 / stored_cal
            carb_pct = float(nt.get("carb_g",    0)) * 4 / stored_cal
        else:
            prot_pct, fat_pct, carb_pct = 0.0, 0.0, 0.0

        # Sanity check: if percentages are unreasonable, fall back to defaults
        if not (0.10 <= prot_pct <= 0.50 and
                0.10 <= fat_pct  <= 0.50 and
                0.20 <= carb_pct <= 0.70 and
                0.70 <= prot_pct + fat_pct + carb_pct <= 1.10):
            prot_pct, fat_pct, carb_pct = 0.20, 0.30, 0.50

        # Now recompute gram targets from the CURRENT sidebar calorie target
        nt["cal_target"] = target_cal
        nt["protein_g"]  = round(target_cal * prot_pct / 4, 1)
        nt["fat_g"]      = round(target_cal * fat_pct  / 9, 1)
        nt["carb_g"]     = round(target_cal * carb_pct / 4, 1)

        # Blend fat/carb targets with historical intake (up to 7 days)
        try:
            hist_df = get_last_n_days_logs(conn(), uid, n=7)
            if not hist_df.empty:
                nt = blend_macro_targets(nt, hist_df, len(hist_df))
        except Exception:
            pass  # Fall back to unblended targets on DB failure

        st.session_state.nutrition_target = nt

        with st.spinner("Optimising your meals…"):
            try:
                result = run_optimizer(recipes_df, num_meals, nt, food_pref)
                st.session_state.plans            = result["plans"]
                st.session_state.relax_level      = result["relaxation_level"]
                st.session_state.optimizer_meta   = {
                    "num_candidates": result["num_candidates"],
                    "num_feasible":   result["num_feasible"],
                    "runtime_ms":     result["runtime_ms"],
                }
                # Log the run (non-critical)
                try:
                    log_optimizer_run(
                        conn(), uid, num_meals,
                        result["num_candidates"], result["num_feasible"],
                        result["relaxation_level"], result["runtime_ms"], food_pref
                    )
                except Exception:
                    pass

                # Initialise customize state
                st.session_state.customize_state = {}
                for pi, plan in enumerate(result["plans"]):
                    rows = []
                    for slot in plan["slots"]:
                        for r in slot["recipes"]:
                            rows.append({
                                "name":      r["name"],
                                "slot_type": slot["type"],
                                "food_type": r.get("food_type", ""),
                                "base_cal":  r["calories"],
                                "base_prot": r["protein"],
                                "base_carb": r["carbohydrate"],
                                "base_fat":  r["fat"],
                                "portion":   r["portion"],
                            })
                    st.session_state.customize_state[pi] = pd.DataFrame(rows)

            except ValueError as e:
                st.error(str(e))
                return

    if "plans" not in st.session_state:
        st.info("👈 Set your preferences in the sidebar and click **Generate Plans** to get started.")
        return

    # Relaxation warning
    relax = st.session_state.get("relax_level", "strict")
    msg   = RELAX_MESSAGES.get(relax)
    if msg:
        st.warning(msg)

    plans       = st.session_state.plans
    plan_labels = ["A", "B", "C"]
    nt          = st.session_state.get(
        "nutrition_target",
        get_default_target(int(ud.get("daily_cal", 1800)))
    )

    for pi, plan in enumerate(plans):
        badge = _quality_badge(plan["score"])
        st.markdown(
            f"### Plan {plan_labels[pi]} &nbsp; {badge} &nbsp; "
            f"<span style='color:#6c757d;font-size:14px;'>"
            f"{plan['total_cal']} kcal &nbsp;|&nbsp; "
            f"C {plan['carb_pct']}% · P {plan['prot_pct']}% · F {plan['fat_pct']}%"
            f"</span>",
            unsafe_allow_html=True
        )

        # ── Macro deviation row ────────────────────────────────────────────────
        devs = plan.get("macro_deviations", {})
        soft = {"calories": nt.get("cal_soft_pct", 0.08),
                "protein":  nt.get("protein_soft_lo", 0.05),
                "fat":      nt.get("fat_soft_hi", 0.10),
                "carbs":    nt.get("carb_soft_pct", 0.15)}
        hard = {"calories": nt.get("cal_hard_pct", 0.20),
                "protein":  nt.get("protein_hard_lo", 0.20),
                "fat":      nt.get("fat_hard_hi", 0.25),
                "carbs":    nt.get("carb_hard_pct", 0.35)}

        macro_items = [
            ("Calories", "calories", f"{plan['total_cal']}", "kcal", "#1D4A2F"),
            ("Protein",  "protein",  f"{plan['protein_g']}", "g",    "#3D5AF1"),
            ("Carbs",    "carbs",    f"{plan['carb_g']}",    "g",    "#43A047"),
            ("Fat",      "fat",      f"{plan['fat_g']}",     "g",    "#E91E8C"),
        ]
        row1, row2 = st.columns(2), st.columns(2)
        for i, (label, key, val_str, unit, mc) in enumerate(macro_items):
            dev = devs.get(key, 0.0)
            cls = _dev_class(dev, soft.get(key, 0.1), hard.get(key, 0.25))
            sym = _dev_symbol(dev)
            col = (row1 if i < 2 else row2)[i % 2]
            with col:
                st.markdown(
                    f"<div style='background:#fff;border-radius:12px;padding:12px 10px;"
                    f"box-shadow:0 2px 8px rgba(0,0,0,0.06);text-align:center;margin-bottom:8px'>"
                    f"<div style='font-size:11px;color:#999;font-weight:600;margin-bottom:4px'>{label}</div>"
                    f"<div style='font-size:18px;font-weight:800;color:{mc}'>{val_str}"
                    f"<span style='font-size:11px;font-weight:500;color:#aaa'> {unit}</span></div>"
                    f"<div class='{cls}' style='font-size:11px;margin-top:3px'>{sym}</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )

        st.markdown("")

        # ── Slot cards ────────────────────────────────────────────────────────
        for slot in plan["slots"]:
            st_type    = slot["type"]
            css        = SLOT_COLORS[st_type]
            rows_html  = ""
            for r in slot["recipes"]:
                port_label = f" &nbsp;<small style='color:#888'>{r['portion']}×</small>" \
                             if r["portion"] != 1.0 else ""
                rows_html += (
                    f"<div class='recipe-row'>"
                    f"<span class='recipe-name'>{r['name']}{port_label}</span>"
                    f"<span class='recipe-macros'>"
                    f"{r['calories_shown']} kcal &nbsp;·&nbsp; "
                    f"P:{r['protein_shown']}g &nbsp;·&nbsp; "
                    f"C:{r['carb_shown']}g &nbsp;·&nbsp; "
                    f"F:{r['fat_shown']}g"
                    f"</span></div>"
                )
            st.markdown(
                f'<div class="slot-card {css}">'
                f'<div style="font-weight:700;margin-bottom:10px">'
                f'{SLOT_ICONS[st_type]} {SLOT_LABELS[st_type]}'
                f'<span style="color:#666;font-size:13px;font-weight:400">'
                f' &nbsp;— {slot["total_cal"]} kcal</span></div>'
                f'{rows_html}</div>',
                unsafe_allow_html=True
            )

        # Recipe detail buttons
        all_recipes = [r for slot in plan["slots"] for r in slot["recipes"]]
        n_cols      = min(max(len(all_recipes), 1), 4)
        cols        = st.columns(n_cols)
        for ri, r in enumerate(all_recipes):
            with cols[ri % n_cols]:
                if st.button(f"📖 {r['name'][:22]}", key=f"det_{pi}_{ri}",
                             use_container_width=True):
                    show_recipe_modal(r["name"])

        with st.expander(f"✏️ Customize Plan {plan_labels[pi]}"):
            _customize_panel(pi, nt, food_pref)

        st.markdown("---")

    st.markdown(
        '<div class="disclaimer">⚠️ <strong>Note:</strong> Plans are optimised '
        'for calorie and macro targets. Add raw fruits, salads, or grilled '
        'vegetables for micronutrients and fibre.</div>',
        unsafe_allow_html=True
    )


def _customize_panel(pi: int, nt: dict, food_pref: str):
    df  = st.session_state.customize_state.get(pi, pd.DataFrame())
    rdf = load_recipes()

    # Live macro totals
    if not df.empty:
        tc    = (df["base_cal"]  * df["portion"]).sum()
        tp    = (df["base_prot"] * df["portion"]).sum()
        tcarb = (df["base_carb"] * df["portion"]).sum()
        tf    = (df["base_fat"]  * df["portion"]).sum()
        mc    = max(tp * 4 + tcarb * 4 + tf * 9, 1)
        pct   = int(min(100, tc / max(nt["cal_target"], 1) * 100))
        col = _target_color(pct)
        # 2×2 macro summary grid (readable on mobile)
        r1c1, r1c2 = st.columns(2)
        r2c1, r2c2 = st.columns(2)
        for mcol, lbl, mval, munit, mcolor in [
            (r1c1, "Calories", f"{int(tc)}",   "kcal", "#1D4A2F"),
            (r1c2, "Protein",  f"{tp:.1f}",    "g",    "#3D5AF1"),
            (r2c1, "Carbs",    f"{tcarb:.1f}", "g",    "#43A047"),
            (r2c2, "Fat",      f"{tf:.1f}",    "g",    "#E91E8C"),
        ]:
            with mcol:
                st.markdown(
                    f'<div class="stat-card">'
                    f'<div class="stat-val" style="color:{mcolor};font-size:16px">{mval}'
                    f'<span style="font-size:10px;color:#aaa;font-weight:500"> {munit}</span></div>'
                    f'<div class="stat-lbl">{lbl}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
        st.markdown(_macro_bar(pct, col), unsafe_allow_html=True)
        st.markdown("")

    # ── Current items — card-per-row layout (mobile-friendly) ───────────────
    if not df.empty:
        for row_i, row in df.iterrows():
            cal_p  = int(row["base_cal"]  * row["portion"])
            prot_p = round(row["base_prot"] * row["portion"], 1)
            carb_p = round(row["base_carb"] * row["portion"], 1)
            fat_p  = round(row["base_fat"]  * row["portion"], 1)

            c_name, c_port, c_rm = st.columns([4, 2, 1])
            with c_name:
                st.markdown(
                    f"**{row['name']}** &nbsp;"
                    f"<span style='background:var(--linen-dark);padding:1px 7px;"
                    f"border-radius:10px;font-size:11px'>"
                    f"{SLOT_LABELS.get(row['slot_type'], row['slot_type'])}</span><br>"
                    f"<small style='color:var(--text-muted)'>"
                    f"{cal_p} kcal · P:{prot_p}g · C:{carb_p}g · F:{fat_p}g</small>",
                    unsafe_allow_html=True
                )
            with c_port:
                cur_port_label = next(
                    (k for k, v in PORTIONS.items() if abs(v - row["portion"]) < 0.01),
                    "1×"
                )
                new_p = st.selectbox(
                    "", list(PORTIONS.keys()),
                    index=list(PORTIONS.keys()).index(cur_port_label)
                          if cur_port_label in PORTIONS else 1,
                    key=f"port_inline_{pi}_{row_i}",
                    label_visibility="collapsed"
                )
                if PORTIONS[new_p] != row["portion"]:
                    df.at[row_i, "portion"] = PORTIONS[new_p]
                    st.session_state.customize_state[pi] = df
                    st.rerun()
            with c_rm:
                if st.button("🗑️", key=f"rm_{pi}_{row_i}", help=f"Remove {row['name']}"):
                    st.session_state.customize_state[pi] = (
                        df.drop(row_i).reset_index(drop=True)
                    )
                    st.rerun()

        st.markdown("")

    st.divider()
    st.markdown("**➕ Add a recipe or ingredient**")
    c1, c2 = st.columns(2)
    with c1:
        add_slot = st.selectbox("Add to slot", ["lunch","dinner","breakfast","snack"],
                                format_func=lambda x: SLOT_LABELS[x], key=f"add_slot_{pi}")
    with c2:
        port_f = st.selectbox("Portion", list(PORTIONS.keys()), index=1, key=f"port_new_{pi}")
    c3, c4 = st.columns(2)
    with c3:
        diff_f = st.selectbox("Difficulty", ["All","Easy","Medium","Hard"], key=f"diff_{pi}")
    with c4:
        time_f = st.selectbox("Cook time", ["All","≤15 min","15-30 min","30+ min"], key=f"time_{pi}")

    kw        = SLOT_LABELS[add_slot]
    allowed   = ALLOWED_TYPES.get(food_pref, ALLOWED_TYPES["non-veg"])
    filt      = rdf[rdf["meal_type"].str.contains(kw, case=False, na=False)]
    rec_pool  = filt[filt["food_type"].isin(allowed)]

    if diff_f != "All":
        rec_pool = rec_pool[rec_pool["difficulty"] == diff_f]
    if time_f == "≤15 min":
        rec_pool = rec_pool[rec_pool["cook_time_mins"] <= 15]
    elif time_f == "15-30 min":
        rec_pool = rec_pool[(rec_pool["cook_time_mins"] > 15) &
                            (rec_pool["cook_time_mins"] <= 30)]
    elif time_f == "30+ min":
        rec_pool = rec_pool[rec_pool["cook_time_mins"] > 30]

    ingr_pool = rdf[rdf["category"] == "ingredient"]
    all_opts  = (["--- select ---"] +
                 sorted(rec_pool["name"].tolist()) +
                 ["-- Raw Ingredients --"] +
                 sorted(ingr_pool["name"].tolist()))

    chosen = st.selectbox("Recipe", all_opts, key=f"add_recipe_{pi}")

    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        if st.button("➕ Add", key=f"add_btn_{pi}", use_container_width=True):
            if chosen and chosen not in ("--- select ---", "-- Raw Ingredients --"):
                r = rdf[rdf["name"] == chosen]
                if not r.empty:
                    r = r.iloc[0]
                    new_row = pd.DataFrame([{
                        "name":      chosen,
                        "slot_type": add_slot,
                        "food_type": r.get("food_type", ""),
                        "base_cal":  r["calories"],
                        "base_prot": r["protein"],
                        "base_carb": r["carbohydrate"],
                        "base_fat":  r["fat"],
                        "portion":   PORTIONS[port_f],
                    }])
                    st.session_state.customize_state[pi] = (
                        pd.concat([df, new_row], ignore_index=True)
                        if not df.empty else new_row
                    )
                    st.rerun()
    with c2:
        if st.button("📋 Review My Diet", key=f"review_{pi}", use_container_width=True):
            review_modal(pi)

    log_target_date = st.date_input(
        "Log for date",
        value=date.today(),
        max_value=date.today(),
        key=f"logall_date_{pi}",
    )
    btn_label = (f"⚡ Log All for {log_target_date.strftime('%d %b')}"
                 if log_target_date < date.today() else "⚡ Log All Now")

    if st.button(btn_label, key=f"logall_{pi}", type="primary", use_container_width=True):
        if not df.empty:
            uid = st.session_state.user_id
            existing = get_logs_for_date(conn(), uid, log_target_date)
            if not existing.empty:
                st.warning(
                    f"{log_target_date.strftime('%d %b %Y')} already has "
                    f"{len(existing)} log(s). Adding on top."
                )
            for _, row in df.iterrows():
                meal_type = SLOT_LABELS[row["slot_type"]]
                log_meal(conn(), uid, log_target_date, row["name"], meal_type,
                         int(row["base_cal"]  * row["portion"]),
                         round(row["base_prot"] * row["portion"], 1),
                         round(row["base_carb"] * row["portion"], 1),
                         round(row["base_fat"]  * row["portion"], 1))
            st.success(f"✓ {len(df)} items logged for {log_target_date.strftime('%d %b %Y')}!")


# ═══════════════════════════════════════════════════════════════════════════════
# LOG A MEAL
# ═══════════════════════════════════════════════════════════════════════════════

def log_page():
    st.title("✍️ Log Meal")
    st.caption("What did you eat?")
    rdf = load_recipes()
    with st.form("log_form"):
        meal_type = st.radio(
            "Meal type", ["Breakfast", "Lunch", "Snack", "Dinner"],
            horizontal=True
        )
        recipe  = st.selectbox("Recipe / Ingredient", sorted(rdf["name"].tolist()))
        portion = st.select_slider("Portion", options=["0.5×", "1×", "1.5×", "2×"], value="1×")
        log_date = st.date_input("Logging for", value=date.today(), max_value=date.today())
        submit   = st.form_submit_button("✓ Log Meal", type="primary", use_container_width=True)

    if submit:
        r = rdf[rdf["name"] == recipe].iloc[0]
        p = PORTIONS[portion]
        if log_date < date.today():
            existing = get_logs_for_date(conn(), st.session_state.user_id, log_date)
            if not existing.empty:
                st.warning(
                    f"{log_date.strftime('%d %b %Y')} already has "
                    f"{len(existing)} log(s). Adding on top."
                )
        log_meal(conn(), st.session_state.user_id, log_date, recipe, meal_type,
                 int(r["calories"] * p), round(r["protein"] * p, 1),
                 round(r["carbohydrate"] * p, 1), round(r["fat"] * p, 1))
        st.success(f"✓ Logged: {recipe} ({portion}) for {log_date.strftime('%d %b %Y')}")


# ═══════════════════════════════════════════════════════════════════════════════
# MY LOGS
# ═══════════════════════════════════════════════════════════════════════════════

@st.dialog("Edit Log Entry", width="small")
def _edit_log_dialog(log_id: int, recipe_name: str, current_meal_type: str,
                     calories: int, protein_g: float, carb_g: float, fat_g: float):
    st.markdown(f"**{recipe_name}**")
    meal_types = ["Breakfast", "Lunch", "Snack", "Dinner"]
    idx = meal_types.index(current_meal_type) if current_meal_type in meal_types else 1
    new_meal_type = st.selectbox("Meal type", meal_types, index=idx)

    rdf   = load_recipes()
    match = rdf[rdf["name"] == recipe_name]

    if not match.empty:
        r        = match.iloc[0]
        base_cal = float(r["calories"]) or 1.0
        approx   = calories / base_cal
        closest  = min(PORTIONS.keys(), key=lambda k: abs(PORTIONS[k] - approx))
        new_port = st.select_slider("Portion", options=["0.5×", "1×", "1.5×", "2×"],
                                    value=closest)
        p        = PORTIONS[new_port]
        new_cal  = int(r["calories"]       * p)
        new_prot = round(r["protein"]      * p, 1)
        new_carb = round(r["carbohydrate"] * p, 1)
        new_fat  = round(r["fat"]          * p, 1)
        st.caption(f"{new_cal} kcal · P:{new_prot}g · C:{new_carb}g · F:{new_fat}g")
    else:
        # Recipe no longer in DB — edit macros directly
        new_cal  = st.number_input("Calories",    value=int(calories),      min_value=0)
        new_prot = st.number_input("Protein (g)", value=float(protein_g),   min_value=0.0, step=0.5)
        new_carb = st.number_input("Carbs (g)",   value=float(carb_g),      min_value=0.0, step=0.5)
        new_fat  = st.number_input("Fat (g)",     value=float(fat_g),       min_value=0.0, step=0.5)

    if st.button("Save", type="primary", use_container_width=True):
        update_log_entry(conn(), log_id, new_meal_type, new_cal, new_prot, new_carb, new_fat)
        st.rerun()


def logs_page():
    st.title("📖 Food Diary")
    uid = st.session_state.user_id

    selected_date = st.date_input(
        "Select date",
        value=date.today(),
        max_value=date.today(),
        key="logs_page_date",
    )
    label = "Today" if selected_date == date.today() else selected_date.strftime("%A, %d %b %Y")
    st.subheader(label)

    day_df = get_logs_for_date(conn(), uid, selected_date)

    if day_df.empty:
        st.info("Nothing logged for this date.")
    else:
        # ── Per-row display with edit / delete ────────────────────────────────
        for _, row in day_df.iterrows():
            c_info, c_edit, c_del = st.columns([6, 1, 1])
            with c_info:
                st.markdown(
                    f"**{row['recipe_name']}** &nbsp;"
                    f"<span style='background:var(--linen-dark);padding:2px 9px;"
                    f"border-radius:12px;font-size:12px;color:var(--text-primary)'>"
                    f"{row['meal_type']}</span><br>"
                    f"<small style='color:var(--text-muted)'>"
                    f"{row['calories']} kcal &nbsp;·&nbsp; "
                    f"P:{row['protein_g']}g &nbsp;·&nbsp; "
                    f"C:{row['carb_g']}g &nbsp;·&nbsp; "
                    f"F:{row['fat_g']}g</small>",
                    unsafe_allow_html=True
                )
            with c_edit:
                if st.button("✏️", key=f"edit_{row['id']}", help="Edit"):
                    _edit_log_dialog(int(row["id"]), row["recipe_name"],
                                     row["meal_type"], row["calories"],
                                     row["protein_g"], row["carb_g"], row["fat_g"])
            with c_del:
                if st.button("🗑️", key=f"del_{row['id']}", help="Delete"):
                    delete_log_entry(conn(), int(row["id"]))
                    st.rerun()

        st.markdown("")

        # ── Daily totals ──────────────────────────────────────────────────────
        tc    = day_df["calories"].sum()
        tp    = day_df["protein_g"].sum()
        tcarb = day_df["carb_g"].sum()
        tf    = day_df["fat_g"].sum()
        mc    = max(tp*4 + tcarb*4 + tf*9, 1)
        sc1, sc2, sc3, sc4 = st.columns(4)
        for col, val, lbl in [
            (sc1, f"{int(tc)}",                         "kcal"),
            (sc2, f"{tp:.1f}g ({tp*4/mc*100:.0f}%)",   "Protein"),
            (sc3, f"{tcarb:.1f}g ({tcarb*4/mc*100:.0f}%)", "Carbs"),
            (sc4, f"{tf:.1f}g ({tf*9/mc*100:.0f}%)",   "Fat"),
        ]:
            with col:
                st.markdown(
                    f'<div class="stat-card">'
                    f'<div class="stat-val">{val}</div>'
                    f'<div class="stat-lbl">{lbl}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

    # ── Add a meal ────────────────────────────────────────────────────────────
    st.markdown("")
    with st.expander(f"➕ Add a meal to {label.lower()}"):
        rdf = load_recipes()
        with st.form(f"add_log_{selected_date}"):
            new_meal_type = st.radio(
                "Meal type", ["Breakfast", "Lunch", "Snack", "Dinner"], horizontal=True
            )
            new_recipe  = st.selectbox("Recipe / Ingredient", sorted(rdf["name"].tolist()))
            new_portion = st.select_slider("Portion", options=["0.5×", "1×", "1.5×", "2×"],
                                           value="1×")
            if st.form_submit_button("➕ Add", type="primary", use_container_width=True):
                r = rdf[rdf["name"] == new_recipe].iloc[0]
                p = PORTIONS[new_portion]
                log_meal(conn(), uid, selected_date, new_recipe, new_meal_type,
                         int(r["calories"] * p), round(r["protein"] * p, 1),
                         round(r["carbohydrate"] * p, 1), round(r["fat"] * p, 1))
                st.success(f"✓ Added: {new_recipe} ({new_portion})")
                st.rerun()

    # ── 7-day chart ───────────────────────────────────────────────────────────
    st.divider()
    st.subheader("7-Day Calories")
    week_df = get_week_summary(conn(), uid)
    if week_df.empty:
        st.info("No data for the past 7 days.")
    else:
        if "total_cal" in week_df.columns:
            wdf = week_df.copy()
            wdf["is_today"] = wdf["log_date"].astype(str) == str(date.today())
            chart = (
                alt.Chart(wdf)
                .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
                .encode(
                    x=alt.X("log_date:O", title="Date", axis=alt.Axis(labelAngle=-30)),
                    y=alt.Y("total_cal:Q", title="Calories"),
                    color=alt.condition(
                        alt.datum.is_today,
                        alt.value("#1D4A2F"),
                        alt.value("#52B788")
                    ),
                    tooltip=["log_date:O", "total_cal:Q",
                             alt.Tooltip("total_prot:Q", title="Protein (g)"),
                             alt.Tooltip("total_carb:Q", title="Carbs (g)"),
                             alt.Tooltip("total_fat:Q",  title="Fat (g)")]
                )
                .properties(height=220)
            )
            st.altair_chart(chart, use_container_width=True)
        st.dataframe(week_df, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════════
# ADD CUSTOM RECIPE
# ═══════════════════════════════════════════════════════════════════════════════

def add_recipe_page():
    st.title("➕ Add Recipe")
    st.markdown(
        "Submit a recipe name and the AI will fill in nutritional details overnight. "
        "Once approved, it becomes available to all users."
    )

    with st.form("add_recipe_form"):
        name   = st.text_input("Recipe name", placeholder="e.g. Sabudana Khichdi, Grilled Chicken, Pasta Primavera")
        st.caption("Be specific — include cuisine or cooking method if helpful.")
        submit = st.form_submit_button("Submit Recipe", type="primary")

    if submit:
        if not name.strip():
            st.error("Please enter a recipe name.")
        else:
            add_custom_recipe(conn(), st.session_state.user_id, name.strip())
            st.success(
                f"✓ **{name}** submitted! "
                "Check your submissions below for the status after tonight's run."
            )

    st.divider()
    st.subheader("My Submissions")
    subs = get_custom_recipes_for_user(conn(), st.session_state.user_id)
    if not subs:
        st.info("You haven't submitted any recipes yet.")
    else:
        df = pd.DataFrame(subs)
        df["Status"] = df["status"].map({
            "pending":  "⏳ Pending AI review",
            "filled":   "✅ Available in app",
            "rejected": "❌ Rejected",
        })
        df["Note"] = df["reject_reason"].fillna("")
        st.dataframe(
            df[["name","Status","Note","created_at"]].rename(
                columns={"name":"Recipe","created_at":"Submitted"}),
            use_container_width=True, hide_index=True
        )


# ═══════════════════════════════════════════════════════════════════════════════
# NOTIFICATIONS
# ═══════════════════════════════════════════════════════════════════════════════

def notifications_page():
    st.title("🔔 Nudges")
    uid    = st.session_state.user_id
    nudges = get_all_nudges(conn(), uid, limit=10)

    if not nudges:
        st.info(
            "No nudges yet. They appear here after the nightly analysis "
            "(runs at 4:00 AM when you have at least 1 day of logged data)."
        )
        return

    for nudge in nudges:
        unseen  = not nudge["seen"]
        css_cls = "nudge-new" if unseen else "nudge-seen"
        days    = nudge.get("days_analyzed", "?")
        gdate   = nudge["generated_on"]
        prefix  = "🆕 " if unseen else ""

        st.markdown(
            f'<div class="{css_cls}">'
            f'<div style="font-size:12px;color:#666;margin-bottom:6px;">'
            f'{prefix}Generated on {gdate} &nbsp;·&nbsp; Based on {days} day(s)</div>'
            f'<div style="font-size:15px;line-height:1.6;">{nudge["nudge_text"]}</div>'
            f'</div>',
            unsafe_allow_html=True
        )
        if unseen:
            if st.button("Mark as read", key=f"mark_{nudge['id']}"):
                mark_nudge_seen(conn(), nudge["id"])
                st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# SETTINGS  (updated with Nutrition Targets section)
# ═══════════════════════════════════════════════════════════════════════════════

def settings_page():
    st.title("⚙️ Settings")
    ud  = st.session_state.user_data
    uid = st.session_state.user_id
    uname   = st.session_state.username
    initial = uname[0].upper()
    cal_goal = int(ud.get("daily_cal", 1800))
    food_label = FOOD_PREFS.get(ud.get("food_pref", "veg"), "Vegetarian")

    st.markdown(
        f'<div style="background:linear-gradient(135deg,#1D4A2F,rgba(45,106,79,0.85));'
        f'border-radius:20px;padding:20px 22px;margin-bottom:24px;'
        f'display:flex;align-items:center;gap:16px;'
        f'box-shadow:0 8px 24px rgba(29,74,47,0.35);">'
        f'<div style="width:54px;height:54px;border-radius:16px;'
        f'background:rgba(255,255,255,0.25);display:flex;align-items:center;'
        f'justify-content:center;font-size:24px;font-weight:800;color:#fff;'
        f'flex-shrink:0">{initial}</div>'
        f'<div>'
        f'<div style="font-size:18px;font-weight:800;color:#fff">{uname}</div>'
        f'<div style="font-size:12px;color:rgba(255,255,255,0.8);margin-top:2px">'
        f'Goal: {cal_goal} kcal/day &nbsp;·&nbsp; {food_label}</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    # ── Profile ───────────────────────────────────────────────────────────────
    with st.form("settings_form"):
        st.subheader("Profile")
        daily_cal = st.number_input("Daily calorie target", 1000, 3500,
                                    int(ud.get("daily_cal", 1800)), 50)
        num_meals = st.slider("Default meals per day", 2, 5, int(ud.get("num_meals", 3)))
        food_pref = st.selectbox(
            "Food preference", list(FOOD_PREFS.keys()),
            index=list(FOOD_PREFS.keys()).index(ud.get("food_pref", "veg")),
            format_func=lambda k: FOOD_PREFS[k]
        )
        if st.form_submit_button("Save Profile", type="primary"):
            update_user_settings(conn(), uid, daily_cal, num_meals, food_pref)
            st.session_state.user_data["daily_cal"] = daily_cal
            st.session_state.user_data["num_meals"] = num_meals
            st.session_state.user_data["food_pref"] = food_pref
            st.success("✓ Profile saved.")

    st.divider()

    # ── Nutrition Targets ─────────────────────────────────────────────────────
    st.subheader("🎯 Nutrition Targets")
    st.caption(
        "These targets drive the optimizer. The defaults are calculated from your "
        "calorie goal using a 20% protein / 30% fat / 50% carb split. "
        "Adjust them if you have specific macro goals."
    )

    nt = load_or_default_target(conn(), uid, int(ud.get("daily_cal", 1800)))

    with st.form("nutrition_form"):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            prot_g = st.number_input("Protein (g)", 30, 300,
                                     int(nt.get("protein_g", 90)))
        with c2:
            fat_g  = st.number_input("Fat (g)", 20, 200,
                                     int(nt.get("fat_g", 60)))
        with c3:
            carb_g = st.number_input("Carbs (g)", 50, 600,
                                     int(nt.get("carb_g", 225)))
        with c4:
            fiber_g = st.number_input("Fibre (g)", 10, 60,
                                      int(nt.get("fiber_g", 30)))

        with st.expander("⚙️ Advanced — soft bands and penalty weights"):
            st.markdown(
                "**Soft band:** deviation inside this range costs zero penalty. "
                "**Hard limit:** candidates outside this range are rejected outright. "
                "Values are fractions of your target (e.g. 0.10 = 10%)."
            )
            ac1, ac2 = st.columns(2)
            with ac1:
                cal_soft  = st.slider("Calorie soft band",   0.02, 0.30,
                                      float(nt.get("cal_soft_pct", 0.08)),    0.01)
                cal_hard  = st.slider("Calorie hard limit",  0.10, 0.50,
                                      float(nt.get("cal_hard_pct", 0.20)),    0.01)
                prot_soft = st.slider("Protein soft (under)",0.02, 0.30,
                                      float(nt.get("protein_soft_lo", 0.05)), 0.01)
                prot_hard = st.slider("Protein hard (under)",0.10, 0.60,
                                      float(nt.get("protein_hard_lo", 0.20)), 0.01)
            with ac2:
                fat_soft  = st.slider("Fat soft (over)",     0.02, 0.30,
                                      float(nt.get("fat_soft_hi", 0.10)),     0.01)
                fat_hard  = st.slider("Fat hard (over)",     0.10, 0.50,
                                      float(nt.get("fat_hard_hi", 0.25)),     0.01)
                carb_soft = st.slider("Carb soft band",      0.05, 0.40,
                                      float(nt.get("carb_soft_pct", 0.15)),   0.01)
                carb_hard = st.slider("Carb hard limit",     0.15, 0.60,
                                      float(nt.get("carb_hard_pct", 0.35)),   0.01)

            st.markdown("**Penalty weights** (higher = optimizer cares more about this macro):")
            pc1, pc2 = st.columns(2)
            with pc1:
                k_cal  = st.slider("Calorie weight",        200, 3000,
                                   int(nt.get("k_cal", 1000)),         100)
                k_prot = st.slider("Protein under weight",  500, 5000,
                                   int(nt.get("k_protein_under", 2000)), 100)
            with pc2:
                k_fat  = st.slider("Fat over weight",       500, 5000,
                                   int(nt.get("k_fat_over", 1500)),    100)
                k_carb = st.slider("Carb weight",           100, 2000,
                                   int(nt.get("k_carb", 400)),          100)

        if st.form_submit_button("Save Nutrition Targets", type="primary"):
            new_nt = dict(nt)
            new_nt.update({
                "cal_target":      int(ud.get("daily_cal", 1800)),
                "protein_g":       float(prot_g),
                "fat_g":           float(fat_g),
                "carb_g":          float(carb_g),
                "fiber_g":         float(fiber_g),
                "cal_soft_pct":    cal_soft,
                "cal_hard_pct":    cal_hard,
                "protein_soft_lo": prot_soft,
                "protein_hard_lo": prot_hard,
                "fat_soft_hi":     fat_soft,
                "fat_hard_hi":     fat_hard,
                "carb_soft_pct":   carb_soft,
                "carb_hard_pct":   carb_hard,
                "k_cal":           k_cal,
                "k_protein_under": k_prot,
                "k_fat_over":      k_fat,
                "k_carb":          k_carb,
            })
            try:
                save_nutrition_target(conn(), uid, new_nt)
                st.success("✓ Nutrition targets saved.")
            except Exception as e:
                # nutrition_targets table may not exist yet (pre-migration)
                st.warning(
                    f"Could not save to database ({e}). "
                    "Run migration_v2_optimizer.sql in Supabase first. "
                    "Your targets will be used for this session only."
                )
            st.session_state.nutrition_target = new_nt

    st.divider()

    # ── Password ──────────────────────────────────────────────────────────────
    with st.form("password_form"):
        st.subheader("Change Password")
        new_pw  = st.text_input("New password", type="password")
        confirm = st.text_input("Confirm password", type="password")
        if st.form_submit_button("Update Password"):
            if not new_pw:
                st.error("Password cannot be empty.")
            elif new_pw != confirm:
                st.error("Passwords do not match.")
            elif len(new_pw) < 6:
                st.error("Must be at least 6 characters.")
            else:
                update_password(conn(), uid, new_pw)
                st.success("✓ Password updated.")


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        login_page()
        return

    with st.sidebar:
        st.markdown("""
        <div class="cb-brand">
            <div class="cb-brand-icon">🔥</div>
            <div class="cb-brand-name">Call Bhaiya</div>
            <div class="cb-brand-tag">your calorie buddy</div>
        </div>
        """, unsafe_allow_html=True)
        initial = st.session_state.username[0].upper()
        st.markdown(
            f'<div class="cb-avatar-wrap">'
            f'<div class="cb-avatar">{initial}</div>'
            f'<div class="cb-uname">{st.session_state.username}</div>'
            f'</div>',
            unsafe_allow_html=True
        )
        page = st.radio("", [
            "🏠 Home",
            "🗓️ Meal Plan",
            "✍️ Log Meal",
            "📖 Food Diary",
            "➕ Add Recipe",
            "🔔 Nudges",
            "⚙️ Settings",
        ], label_visibility="collapsed")
        st.divider()
        if st.button("🚪 Log Out", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    {
        "🏠 Home":       home_page,
        "🗓️ Meal Plan":  plan_page,
        "✍️ Log Meal":   log_page,
        "📖 Food Diary": logs_page,
        "➕ Add Recipe": add_recipe_page,
        "🔔 Nudges":     notifications_page,
        "⚙️ Settings":   settings_page,
    }[page]()


if __name__ == "__main__":
    main()
