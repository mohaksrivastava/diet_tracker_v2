# optimizer/meal_optimizer.py  -  v4
#
# Changes from v3:
#   1. Wider portion envelopes — anchors now reach 2.5x
#   2. Anchor pairing REWARD (-300) for 1 protein + 1 starch in a slot
#   3. Stronger cuisine coherence — CUISINE_CLASH_P 1.5 -> 4.0
#   4. Phase 3: Residual Gap Filler — closes remaining macro deficit
#
# Macro split: 30% protein / 50% carbs / 20% fat

import time
import numpy as np
import pandas as pd
from itertools import combinations, product as iproduct

# ── Nutrition matrix ───────────────────────────────────────────────────────────
CAL_LEVELS = [1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900,
              2000, 2100, 2200, 2300, 2400, 2500]

SLOT_CAL_TABLE = {
    2: {
        "lunch":     [600,650,700,750,800,850,900,950,1000,1050,1100,1150,1200,1250],
        "dinner":    [600,650,700,750,800,850,900,950,1000,1050,1100,1150,1200,1250],
        "breakfast": [0]*14, "snack": [0]*14,
    },
    3: {
        "lunch":     [450,480,510,540,570,600,630,660,690,720,750,780,810,840],
        "dinner":    [450,480,510,540,570,600,630,660,690,720,750,780,810,840],
        "breakfast": [300,340,380,420,460,500,540,580,620,660,700,740,780,820],
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
    return float(np.interp(daily_cal, CAL_LEVELS, SLOT_CAL_TABLE[K][slot_type]))


# ── Config ─────────────────────────────────────────────────────────────────────
SLOT_SEQ = {
    2: ["lunch","dinner"],
    3: ["lunch","dinner","breakfast"],
    4: ["lunch","dinner","breakfast","snack"],
    5: ["lunch","dinner","breakfast","snack","snack"],
}
SLOT_PARAMS = {
    "lunch":     {"kw":"Lunch",     "min_n":2, "max_n":4},
    "dinner":    {"kw":"Dinner",    "min_n":2, "max_n":4},
    "breakfast": {"kw":"Breakfast", "min_n":1, "max_n":3},
    "snack":     {"kw":"Snack",     "min_n":1, "max_n":2},
}

SLOT_WINDOW          = 0.30
EXTRA_PENALTY        = 200
M_CANDS              = 12
STAPLE_GROUPS        = {"rice","roti"}
PORTION_DEV_K        = 50
CUISINE_CLASH_P      = 4.0    # raised from 1.5
CUISINE_MATCH_R      = 0.5
ANCHOR_PAIR_BONUS    = -300   # reward for protein+starch combo

ANCHOR_PROTEIN_ROLES  = {"anchor_protein"}
ANCHOR_STARCH_ROLES   = {"anchor_starch"}
COMPLETE_MEAL_ROLE    = "complete_meal"
GAP_FILLER_ROLE       = "gap_filler"

GAP_FILLER_MAX_OVERSHOOT = 80  # kcal over target allowed for gap filler
GAP_FILLER_MIN_GAP_G    = 5.0  # minimum gram deficit to trigger filler

ALLOWED_TYPES = {
    "vegan":   ["vegan"],
    "veg":     ["vegan","veg"],
    "dairy":   ["vegan","veg","dairy"],
    "egg":     ["vegan","veg","dairy","egg"],
    "non-veg": ["vegan","veg","dairy","egg","non-veg"],
}
CUISINE_FAMILY = {
    "north_indian":"indian", "south_indian":"indian",
    "indo_chinese":"fusion", "east_asian":"asian",
    "continental":"western", "mediterranean":"western",
    "mexican":"western",     "unknown":"any",
    "indian":"indian",       "chinese":"asian",
    "middle_eastern":"western", "japanese":"asian",
    "global":"any",
}
RELAXATION_LEVELS = [
    ("strict",    1.0),("relaxed",1.5),("loose",2.0),("soft_only",None),
]


# ── Public API ─────────────────────────────────────────────────────────────────
def run_optimizer(recipes_df: pd.DataFrame, K: int,
                  nutrition_target: dict, food_pref: str="non-veg") -> dict:
    t0 = time.monotonic()
    K  = int(K)
    if K not in range(2,6): raise ValueError("K must be 2-5.")

    allowed = ALLOWED_TYPES.get(food_pref, ALLOWED_TYPES["non-veg"])

    elig_mask = (
        (recipes_df["category"]=="recipe") &
        (recipes_df["food_type"].isin(allowed)) &
        (recipes_df["calories"].notna())
    )
    filler_mask = elig_mask & (recipes_df["role"].fillna("")==GAP_FILLER_ROLE)
    main_mask   = elig_mask & ~filler_mask

    df         = recipes_df[main_mask].copy().reset_index(drop=True)
    fillers_df = recipes_df[filler_mask].copy().reset_index(drop=True)

    if df.empty:
        raise ValueError("No eligible recipes for this food preference.")

    for col, default in [("portion_min",0.5),("portion_typical",1.0),
                         ("portion_max",2.5),("role","side"),("cuisine","unknown")]:
        if col not in df.columns: df[col] = default
        else:                      df[col] = df[col].fillna(default)

    daily_cal    = float(nutrition_target["cal_target"])
    slot_seq     = SLOT_SEQ[K]
    slot_targets = {s: get_slot_target(K,s,daily_cal)
                    for s in ["lunch","dinner","breakfast","snack"]}

    # Phase 1
    slot_cands = []
    for s_type in slot_seq:
        cands = _gen_slot_cands(df, s_type, slot_targets[s_type], nutrition_target)
        if not cands:
            raise ValueError(
                f"No valid meals for '{s_type}'. Check recipe tags "
                "(anchor_protein+anchor_starch required for lunch/dinner).")
        slot_cands.append(cands)

    # Phase 2
    ns   = [len(sc) for sc in slot_cands]
    flat = [g.ravel() for g in
            np.meshgrid(*[np.arange(n) for n in ns], indexing="ij")]
    N    = len(flat[0])

    def _arr(si, key):
        return np.array([c[key] for c in slot_cands[si]], dtype=float)

    tc = sum(_arr(si,"total_cal")[flat[si]]   for si in range(K))
    pc = sum(_arr(si,"prot_cal")[flat[si]]    for si in range(K))
    cc = sum(_arr(si,"carb_cal")[flat[si]]    for si in range(K))
    fc = sum(_arr(si,"fat_cal")[flat[si]]     for si in range(K))
    ep = sum(_arr(si,"extra_pen")[flat[si]]   for si in range(K))
    pp = sum(_arr(si,"portion_pen")[flat[si]] for si in range(K))
    cp = sum(_arr(si,"cuisine_pen")[flat[si]] for si in range(K))
    ab = sum(_arr(si,"anchor_bonus")[flat[si]]for si in range(K))

    pg = pc/4.0; cg = cc/4.0; fg = fc/9.0

    relax_level = "strict"; feas = np.zeros(N, dtype=bool)
    for name, mult in RELAXATION_LEVELS:
        if mult is None:
            feas = np.ones(N, dtype=bool)
        else:
            t_adj = _scale_hard(nutrition_target, mult)
            feas  = _hard_feasible(tc, pg, fg, cg, t_adj)
        if feas.sum()>0: relax_level=name; break

    f_tc=tc[feas]; f_pg=pg[feas]; f_fg=fg[feas]; f_cg=cg[feas]
    scores = (_macro_pen(f_tc,f_pg,f_fg,f_cg,nutrition_target)
              + ep[feas] + pp[feas] + cp[feas] + ab[feas])

    feas_pos = np.where(feas)[0]
    rl = np.argsort(scores); rg = feas_pos[rl]

    selected = []
    for li, gi in zip(rl, rg):
        if len(selected)>=3: break
        combo  = tuple(flat[si][gi] for si in range(K))
        chosen = [slot_cands[si][combo[si]] for si in range(K)]
        all_idx = [i for c in chosen for i in c["indices"]]
        all_fg  = [g for c in chosen for g in c["food_groups"]]
        ns_idx  = [i for i,g in zip(all_idx,all_fg) if g not in STAPLE_GROUPS]
        if len(ns_idx)!=len(set(ns_idx)): continue
        if any(sum(a==b for a,b in zip(combo,p))>=K-1 for _,p,_ in selected): continue
        selected.append((float(scores[li]), combo, chosen))

    if len(selected)<3:
        for li, gi in zip(rl, rg):
            if len(selected)>=3: break
            combo = tuple(flat[si][gi] for si in range(K))
            if any(combo==p for _,p,_ in selected): continue
            chosen=[slot_cands[si][combo[si]] for si in range(K)]
            selected.append((float(scores[li]),combo,chosen))

    plans = _format(selected, slot_seq, df, nutrition_target)

    # Phase 3
    if not fillers_df.empty:
        plans = [_gap_fill(plan, fillers_df, nutrition_target, food_pref)
                 for plan in plans]

    return {
        "plans": plans,
        "relaxation_level": relax_level,
        "runtime_ms": round((time.monotonic()-t0)*1000),
        "num_candidates": N,
        "num_feasible": int(feas.sum()),
    }


# ── Phase 3 ────────────────────────────────────────────────────────────────────
def _gap_fill(plan, fillers_df, nt, food_pref):
    gap_cal  = nt["cal_target"] - plan["total_cal"]
    gap_prot = nt["protein_g"]  - plan["protein_g"]
    gap_carb = nt["carb_g"]     - plan["carb_g"]
    gap_fat  = nt["fat_g"]      - plan["fat_g"]

    if gap_cal < -GAP_FILLER_MAX_OVERSHOOT: return plan
    if gap_prot > GAP_FILLER_MIN_GAP_G:
        dominant = "protein"
    else:
        deficits = {"carb": gap_carb, "fat": gap_fat}
        if max(deficits.values()) < GAP_FILLER_MIN_GAP_G: return plan
        dominant = max(deficits, key=lambda k: deficits[k])

    allowed = set(ALLOWED_TYPES.get(food_pref, ALLOWED_TYPES["non-veg"]))
    pool    = fillers_df[fillers_df["food_type"].isin(allowed)]
    if pool.empty: return plan

    best, best_score = None, -np.inf
    for _, r in pool.iterrows():
        p_typ = float(r.get("portion_typical",1.0))
        p_max = float(r.get("portion_max",2.0))
        cal   = float(r["calories"])
        for port in [0.5, 1.0, p_typ, (p_typ+p_max)/2, p_max]:
            port = round(min(port, p_max), 3)
            fc   = cal * port
            if fc > gap_cal + GAP_FILLER_MAX_OVERSHOOT or fc < 20: continue
            fp = float(r["protein"])      * port
            fc2= float(r["carbohydrate"]) * port
            ff = float(r["fat"])           * port
            mv = {"protein":fp, "carb":fc2, "fat":ff}
            if mv[dominant] <= 0: continue
            score = mv[dominant]/max(fc,1)
            # Protein-density bonus: prefer high-protein fillers when closing protein gap
            if dominant == "protein":
                prot_per_100kcal = float(r["protein"]) * 100 / max(float(r["calories"]), 1)
                if prot_per_100kcal > 6.0:
                    score *= 2.0
            if score > best_score:
                best_score = score
                best = (r, port, round(fc), round(fp,1), round(fc2,1), round(ff,1))

    if best is None: return plan
    r_row, port, fc, fp, fc2, ff = best

    filler_r = {
        "name":r_row["name"], "portion":port,
        "calories_shown":fc, "protein_shown":fp,
        "carb_shown":fc2, "fat_shown":ff,
        "calories":float(r_row["calories"]),
        "protein":float(r_row["protein"]),
        "carbohydrate":float(r_row["carbohydrate"]),
        "fat":float(r_row["fat"]),
        "role":GAP_FILLER_ROLE, "is_gap_filler":True,
    }

    target_slot = plan["slots"][-1]["type"]
    updated = []
    for slot in plan["slots"]:
        if slot["type"]==target_slot:
            updated.append({**slot,
                "recipes":  slot["recipes"]+[filler_r],
                "total_cal":slot["total_cal"]+fc,
                "n_recipes":slot["n_recipes"]+1,
            })
        else:
            updated.append(slot)

    nc=round(plan["total_cal"]+fc); np2=round(plan["protein_g"]+fp,1)
    nc2=round(plan["carb_g"]+fc2,1); nf=round(plan["fat_g"]+ff,1)
    mc=max(np2*4+nc2*4+nf*9,1)

    return {**plan, "slots":updated, "total_cal":nc,
            "protein_g":np2, "carb_g":nc2, "fat_g":nf,
            "prot_pct":round(np2*4/mc*100),
            "carb_pct":round(nc2*4/mc*100),
            "fat_pct": round(nf*9/mc*100),
            "macro_deviations":{
                "calories":round((nc-nt["cal_target"])/nt["cal_target"]*100,1),
                "protein": round((np2-nt["protein_g"])/nt["protein_g"]*100,1),
                "fat":     round((nf-nt["fat_g"])/nt["fat_g"]*100,1),
                "carbs":   round((nc2-nt["carb_g"])/nt["carb_g"]*100,1),
            },
            "gap_filler":{"name":r_row["name"],"portion":port,
                          "slot":target_slot,"dominant_macro":dominant,"cal":fc},
    }


# ── Scoring helpers ────────────────────────────────────────────────────────────
def _check_anchors(roles, s_type, nr):
    if s_type not in ("lunch","dinner"): return True
    if nr==1: return roles[0]==COMPLETE_MEAL_ROLE
    has_p = any(r in ANCHOR_PROTEIN_ROLES for r in roles)
    has_s = any(r in ANCHOR_STARCH_ROLES  for r in roles)
    has_c = any(r == COMPLETE_MEAL_ROLE   for r in roles)
    return has_c or (has_p and has_s)

def _anchor_bonus(roles, s_type):
    if s_type not in ("lunch","dinner"): return 0.0
    if (sum(1 for r in roles if r in ANCHOR_PROTEIN_ROLES)==1 and
        sum(1 for r in roles if r in ANCHOR_STARCH_ROLES)==1):
        return ANCHOR_PAIR_BONUS
    return 0.0

def _cuisine_pen(cuisines):
    valid=[c for c in cuisines if c!="unknown"]
    if len(valid)<2: return 0.0
    t=0.0
    for a,b in combinations(valid,2):
        fa=CUISINE_FAMILY.get(a,"other"); fb=CUISINE_FAMILY.get(b,"other")
        t += -CUISINE_MATCH_R if fa==fb else CUISINE_CLASH_P
    return t

def _portion_pen(portions, typicals):
    return sum(PORTION_DEV_K*((p-t)/t)**2 for p,t in zip(portions,typicals) if t>0)

def _hard_feasible(cal,pg,fg,cg,t):
    return ((cal>=t["cal_target"]*(1-t["cal_hard_pct"])) &
            (cal<=t["cal_target"]*(1+t["cal_hard_pct"])) &
            (pg>=t["protein_g"]*(1-t["protein_hard_lo"])) &
            (pg<=t["protein_g"]*(1+t.get("protein_hard_hi",0.10))) &
            (fg>=t["fat_g"]*(1-t["fat_hard_lo"])) &
            (fg<=t["fat_g"]*(1+t["fat_hard_hi"])) &
            (cg>=t["carb_g"]*(1-t["carb_hard_pct"])) &
            (cg<=t["carb_g"]*(1+t["carb_hard_pct"])))

def _scale_hard(t, mult):
    out=dict(t)
    for k in ["cal_hard_pct","protein_hard_lo","protein_hard_hi",
              "fat_hard_hi","fat_hard_lo","carb_hard_pct","fiber_hard_lo"]:
        out[k]=t.get(k,0.25)*mult
    return out

def _macro_pen(cal,pg,fg,cg,t):
    pen=np.zeros(len(cal)); kp=t.get("k_protein_under",2500)
    cal_dev=np.maximum(0,np.abs(cal-t["cal_target"])/t["cal_target"]-t.get("cal_soft_pct",0.08))
    pen+=t.get("k_cal",1000)*cal_dev**2
    pu=np.maximum(0,(t["protein_g"]*(1-t.get("protein_soft_lo",0.05))-pg)/t["protein_g"])
    po=np.maximum(0,(pg-t["protein_g"]*1.25)/t["protein_g"])
    pen+=kp*pu**2+(kp/4)*po**2
    fo=np.maximum(0,(fg-t["fat_g"]*(1+t.get("fat_soft_hi",0.10)))/t["fat_g"])
    fu=np.maximum(0,(t["fat_g"]*0.60-fg)/t["fat_g"])
    pen+=t.get("k_fat_over",1500)*fo**2+200*fu**2
    cd=np.maximum(0,np.abs(cg-t["carb_g"])/t["carb_g"]-t.get("carb_soft_pct",0.15))
    pen+=t.get("k_carb",400)*cd**2
    return pen


# ── Phase 1 ────────────────────────────────────────────────────────────────────
def _gen_slot_cands(df, s_type, s_target, nt):
    sp=SLOT_PARAMS[s_type]; min_n=sp["min_n"]; max_n=sp["max_n"]
    has_fg="food_group" in df.columns
    elig=df[df["meal_type"].str.contains(sp["kw"],case=False,na=False)].copy()
    ne=len(elig)
    if ne==0: return []

    cal_lo=s_target*(1-SLOT_WINDOW); cal_hi=s_target*(1+SLOT_WINDOW)
    all_c=[]

    # Single-recipe candidates
    for ii in range(ne):
        r=elig.iloc[ii]; role=str(r.get("role","side"))
        if s_type in ("lunch","dinner") and role!=COMPLETE_MEAL_ROLE and min_n>1:
            continue
        p_min=float(r.get("portion_min",0.5)); p_typ=float(r.get("portion_typical",1.0))
        p_max=float(r.get("portion_max",2.5)); cal=float(r["calories"])
        opts=np.unique(np.clip([p_min,p_typ,(p_typ+p_max)/2,p_max],p_min,p_max))
        bp=opts[np.argmin(np.abs(cal*opts-s_target))]; tc=cal*bp
        if tc<cal_lo or tc>cal_hi: continue
        all_c.append({
            "indices":    [int(elig.index[ii])],
            "portions":   [float(bp)], "n":1,
            "total_cal":  float(tc),
            "prot_cal":   float(r["protein"]      *bp*4),
            "carb_cal":   float(r["carbohydrate"] *bp*4),
            "fat_cal":    float(r["fat"]           *bp*9),
            "food_groups":[str(r.get("food_group","misc"))],
            "extra_pen":  0.0,
            "portion_pen":float(_portion_pen([bp],[p_typ])),
            "cuisine_pen":0.0,
            "anchor_bonus":float(_anchor_bonus([role],s_type)),
            "score":      float((tc-s_target)**2/max(s_target,1)),
        })

    # Multi-recipe candidates
    for nr in range(max(min_n,2), min(max_n,ne)+1):
        per_tgt=s_target/nr
        top_n=min({2:20,3:16,4:12}[min(nr,4)],ne)
        devs=np.abs(elig["calories"].values.astype(float)-per_tgt)
        top=np.argsort(devs)[:top_n]
        if top_n<nr: continue

        for cl in combinations(range(top_n),nr):
            ei=top[list(cl)]; rr=elig.iloc[ei]
            if "role" in rr.columns and (rr["role"]==GAP_FILLER_ROLE).any(): continue
            fgs=rr["food_group"].tolist() if has_fg else ["misc"]*nr
            if len(set(fgs))<nr: continue
            roles=rr["role"].tolist() if "role" in rr.columns else ["side"]*nr
            if not _check_anchors(roles,s_type,nr): continue

            pgrids=[]; typs=[]
            for il in ei:
                rx=elig.iloc[il]
                pmn=float(rx.get("portion_min",0.5)); pt=float(rx.get("portion_typical",1.0))
                pmx=float(rx.get("portion_max",2.5))
                pgrids.append(np.unique(np.clip([pmn,pt,(pt+pmx)/2,pmx],pmn,pmx)))
                typs.append(pt)

            pm=np.array(list(iproduct(*pgrids))); cals=rr["calories"].values.astype(float)
            tots=pm@cals; bgi=int(np.argmin(np.abs(tots-s_target)))
            bp=pm[bgi].tolist(); tc=float(tots[bgi])
            if tc<cal_lo or tc>cal_hi: continue

            ep=(nr-1)*EXTRA_PENALTY; pp=_portion_pen(bp,typs)
            cuis=rr["cuisine"].tolist() if "cuisine" in rr.columns else ["unknown"]*nr
            cp=_cuisine_pen(cuis); ab=_anchor_bonus(roles,s_type)
            all_c.append({
                "indices":   [int(elig.index[i]) for i in ei],
                "portions":  bp, "n":nr, "total_cal":tc,
                "prot_cal":  float(np.sum(rr["protein"].values     *bp)*4),
                "carb_cal":  float(np.sum(rr["carbohydrate"].values*bp)*4),
                "fat_cal":   float(np.sum(rr["fat"].values          *bp)*9),
                "food_groups":fgs, "extra_pen":float(ep),
                "portion_pen":float(pp), "cuisine_pen":float(cp),
                "anchor_bonus":float(ab),
                "score":float((tc-s_target)**2/max(s_target,1)+ep+pp+cp+ab),
            })

    all_c.sort(key=lambda c:c["score"])
    return all_c[:M_CANDS]


# ── Output ─────────────────────────────────────────────────────────────────────
def _format(selected, slot_seq, df, nt):
    plans=[]
    for score,combo,chosen in selected:
        slots=[]; tp=tc=tf=0.0
        for si,cand in enumerate(chosen):
            rs=[]
            for idx,port in zip(cand["indices"],cand["portions"]):
                r=df.iloc[idx].to_dict()
                r["portion"]=port
                r["calories_shown"]=round(r["calories"]    *port)
                r["protein_shown"] =round(r["protein"]     *port,1)
                r["carb_shown"]    =round(r["carbohydrate"]*port,1)
                r["fat_shown"]     =round(r["fat"]          *port,1)
                rs.append(r); tp+=r["protein_shown"]; tc+=r["carb_shown"]; tf+=r["fat_shown"]
            slots.append({"type":slot_seq[si],"recipes":rs,
                          "total_cal":sum(r["calories_shown"]for r in rs),
                          "n_recipes":len(rs)})
        total_c=round(sum(s["total_cal"]for s in slots)); mc=max(tp*4+tc*4+tf*9,1)
        plans.append({
            "slots":slots,"total_cal":total_c,
            "protein_g":round(tp,1),"carb_g":round(tc,1),"fat_g":round(tf,1),
            "score":round(score,1),
            "prot_pct":round(tp*4/mc*100),"carb_pct":round(tc*4/mc*100),"fat_pct":round(tf*9/mc*100),
            "macro_deviations":{
                "calories":round((total_c-nt["cal_target"])/nt["cal_target"]*100,1),
                "protein": round((tp-nt["protein_g"])/nt["protein_g"]*100,1),
                "fat":     round((tf-nt["fat_g"])/nt["fat_g"]*100,1),
                "carbs":   round((tc-nt["carb_g"])/nt["carb_g"]*100,1),
            },
            "gap_filler":None,
        })
    return plans
