# -*- coding: utf-8 -*-
"""Taktik DNA ek bulgular (1-7): stil ve sonuc iliskileri.

1 Kazanma formulu (rakip farki uzerinden lojistik regresyon)
2 Aileler arasi catisma matrisi (mac basi puan)
3 Underdog recetesi (dusuk Elo'nun surpriz maclarindaki stil)
4 Eleme turu kabuk degistirmesi (takim ici grup vs eleme farki)
5 Turnuva yorgunlugu (mac sirasi vs pres metrikleri, takim ici)
6 Stil istikrari (mactan maca varyans vs basari)
7 Sicaklik x pres (iklim projesi hava verisiyle kopru)
"""
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
FOOTBALL = ROOT.parent
DATA = ROOT / "data"

tm = pd.read_csv(DATA / "team_style_features.csv")  # cluster_teams ciktisi (turetilmis ozelliklerle)
cl = pd.read_csv(DATA / "team_clusters.csv")[["team", "cluster", "max_stage"]]
teams_ref = pd.read_csv(FOOTBALL / "wc2026_dataset" / "teams.csv")
elo = teams_ref.set_index("team_name")["elo_rating"]

# --- mac eslemesi (header tarihi + takim cifti -> wc match_id) ---
wc = pd.read_csv(FOOTBALL / "wc2026_dataset" / "matches.csv")
names = teams_ref.set_index("team_id")["team_name"]
wc["home"] = wc["home_team_id"].map(names)
wc["away"] = wc["away_team_id"].map(names)
wc["pair"] = wc.apply(lambda r: frozenset([r["home"], r["away"]]), axis=1)
wc["wc_date"] = pd.to_datetime(wc["date"])

tm["pdf_date"] = pd.to_datetime(
    tm["header"].str.extract(r"^(\d{1,2} \w+ \d{4})")[0], format="%d %B %Y")
tm["pair"] = tm.apply(lambda r: frozenset([r["team"], r["opponent"]]), axis=1)
cand = tm[["match_number", "pdf_date", "pair"]].drop_duplicates("match_number")
cand = cand.merge(wc[["match_id", "pair", "wc_date", "stage_id"]], on="pair")
cand["dd"] = (cand["wc_date"] - cand["pdf_date"]).dt.days.abs()
cand = cand[cand["dd"] <= 1].sort_values("dd").drop_duplicates("match_number")
tm = tm.merge(cand[["match_number", "match_id", "stage_id"]], on="match_number")
print(f"mac eslesme: {tm['match_id'].nunique()} / {tm['match_number'].nunique()}")

tm["is_knockout"] = (tm["stage_id"] > 1).astype(int)
tm["elo"] = tm["team"].map(elo)
tm["opp_elo"] = tm["opponent"].map(elo)
tm = tm.merge(cl.rename(columns={"cluster": "cluster_team"}), on="team")
tm = tm.merge(cl[["team", "cluster"]].rename(
    columns={"team": "opponent", "cluster": "cluster_opp"}), on="opponent")

opp_g = tm[["match_id", "team", "goals"]].rename(
    columns={"team": "opponent", "goals": "opp_goals"})
tm = tm.merge(opp_g, on=["match_id", "opponent"])
tm["win"] = (tm["goals"] > tm["opp_goals"]).astype(int)
tm["points"] = np.select([tm["goals"] > tm["opp_goals"],
                          tm["goals"] == tm["opp_goals"]], [3, 1], 0)

STYLE = ["possession_pct", "pass_completion_pct", "directness", "verticality",
         "cross_share", "ppda_like", "direct_press_share", "press_duration_s",
         "recovery_time_s", "press_inside_share"]

CLUSTER_NAMES = {0: "Kontrolcu baskicilar", 1: "Derin blok reaktifler",
                 2: "Dikey avcilar", 3: "Dengeli pragmatikler"}

# ---------------- 1: Kazanma formulu ----------------
print("\n" + "=" * 60)
print("1) KAZANMA FORMULU — rakip farki, beraberlikler haric")
opp_style = tm[["match_id", "team"] + STYLE].rename(
    columns={"team": "opponent", **{s: s + "_opp" for s in STYLE}})
d = tm.merge(opp_style, on=["match_id", "opponent"])
d = d[d["goals"] != d["opp_goals"]].copy()
d["elo_diff"] = d["elo"] - d["opp_elo"]
for s in STYLE:
    d[s + "_diff"] = d[s] - d[s + "_opp"]
    d[s + "_diff"] = (d[s + "_diff"] - d[s + "_diff"].mean()) / d[s + "_diff"].std()
print(f"n={len(d)} takim-mac (galibiyet/maglubiyet)")
for s in STYLE:
    r = smf.logit(f"win ~ {s}_diff + elo_diff", data=d).fit(disp=0)
    b, p = r.params[f"{s}_diff"], r.pvalues[f"{s}_diff"]
    star = " *" if p < 0.05 else ("  ." if p < 0.10 else "")
    print(f"  {s:20s} OR(1sd)={np.exp(b):.2f}  p={p:.3f}{star}")

# ---------------- 2: Catisma matrisi ----------------
print("\n" + "=" * 60)
print("2) AILELER ARASI CATISMA — satirdaki ailenin mac basi puani")
mat = tm.pivot_table(index="cluster_team", columns="cluster_opp",
                     values="points", aggfunc="mean").round(2)
cnt = tm.pivot_table(index="cluster_team", columns="cluster_opp",
                     values="points", aggfunc="count")
mat.index = [CLUSTER_NAMES[i] for i in mat.index]
mat.columns = [CLUSTER_NAMES[c] for c in mat.columns]
print(mat.to_string())
print("\nmac sayilari:")
cnt.index = [CLUSTER_NAMES[i] for i in cnt.index]
cnt.columns = [CLUSTER_NAMES[c] for c in cnt.columns]
print(cnt.to_string())

# ---------------- 3: Underdog recetesi ----------------
print("\n" + "=" * 60)
print("3) UNDERDOG RECETESI — Elo'su >=50 dusuk takimlarin maclari")
ud = tm[tm["elo"] <= tm["opp_elo"] - 50].copy()
ud["upset"] = (ud["points"] >= 1).astype(int)  # puan almak = basari
print(f"underdog maci: {len(ud)}, puan alinan: {ud['upset'].sum()}")
for s in STYLE:
    a = ud.loc[ud["upset"] == 1, s].dropna()
    b = ud.loc[ud["upset"] == 0, s].dropna()
    t, p = stats.mannwhitneyu(a, b)
    star = " *" if p < 0.05 else ("  ." if p < 0.10 else "")
    print(f"  {s:20s} puanli={a.mean():.3f} puansiz={b.mean():.3f}  p={p:.3f}{star}")

# ---------------- 4: Eleme turu kabuk degistirmesi ----------------
print("\n" + "=" * 60)
print("4) ELEME TURUNDA STIL DEGISIMI — ayni takim, grup vs eleme (esli test)")
both = tm.groupby("team")["is_knockout"].nunique()
teams_both = both[both == 2].index
sub = tm[tm["team"].isin(teams_both)]
g = sub.groupby(["team", "is_knockout"])[STYLE + ["pressures", "goals"]].mean()
for s in STYLE + ["pressures"]:
    w = g[s].unstack()
    t, p = stats.wilcoxon(w[0], w[1])
    diff = (w[1] - w[0]).mean()
    star = " *" if p < 0.05 else ("  ." if p < 0.10 else "")
    print(f"  {s:20s} eleme-grup farki={diff:+.3f}  p={p:.3f}{star}  (n={len(w)} takim)")

# ---------------- 5: Turnuva yorgunlugu ----------------
print("\n" + "=" * 60)
print("5) TURNUVA YORGUNLUGU — mac sirasi etkisi (takim ici, demeaned)")
tm = tm.sort_values(["team", "pdf_date"])
tm["match_no"] = tm.groupby("team").cumcount() + 1
for s in ["pressures", "direct_pressures", "press_duration_s",
          "recovery_time_s", "distance_km"]:
    d5 = tm[[s, "match_no", "team"]].dropna().copy()
    d5["y"] = d5[s] - d5.groupby("team")[s].transform("mean")
    d5["x"] = d5["match_no"] - d5.groupby("team")["match_no"].transform("mean")
    r = smf.ols("y ~ x", data=d5).fit()
    star = " *" if r.pvalues["x"] < 0.05 else ""
    print(f"  {s:20s} mac basina egim={r.params['x']:+.3f}  p={r.pvalues['x']:.3f}{star}")

# ---------------- 6: Stil istikrari ----------------
print("\n" + "=" * 60)
print("6) STIL ISTIKRARI — stil varyansi dusuk olan daha mi ileri gitti?")
zt = tm.copy()
for s in STYLE:
    zt[s] = (zt[s] - zt[s].mean()) / zt[s].std()
cons = zt.groupby("team")[STYLE].std().mean(axis=1).rename("style_volatility")
cons = cons.reset_index().merge(cl, on="team")
cons = cons.merge(tm.groupby("team")["elo"].first(), on="team")
rho, p = stats.spearmanr(cons["style_volatility"], cons["max_stage"])
print(f"  ham korelasyon: rho={rho:+.2f} p={p:.3f}")
r = smf.ols("max_stage ~ style_volatility + elo", data=cons).fit()
print(f"  Elo kontrollu: katsayi={r.params['style_volatility']:+.2f} p={r.pvalues['style_volatility']:.3f}")

# ---------------- 7: Sicaklik x pres ----------------
print("\n" + "=" * 60)
print("7) SICAKLIK x PRES — iklim koprusu (acik hava)")
wx = pd.read_csv(FOOTBALL / "climate_analysis" / "data" / "match_weather.csv")
d7 = tm.merge(wx[["match_id", "apparent_temperature", "climate_controlled"]],
              on="match_id")
d7 = d7[d7["climate_controlled"] == 0].copy()
d7["heat10"] = d7["apparent_temperature"] / 10
print(f"n={len(d7)} takim-mac")
for s in ["pressures", "direct_pressures", "press_duration_s",
          "recovery_time_s", "ppda_like", "forced_turnovers"]:
    r = smf.ols(f"{s} ~ heat10 + is_knockout + elo + opp_elo", data=d7).fit()
    eff = 100 * r.params["heat10"] / d7[s].mean()
    star = " *" if r.pvalues["heat10"] < 0.05 else ("  ." if r.pvalues["heat10"] < 0.10 else "")
    print(f"  {s:20s} +10C: %{eff:+.1f}  p={r.pvalues['heat10']:.3f}{star}")
