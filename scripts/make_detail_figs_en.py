# -*- coding: utf-8 -*-
"""English detail figures: GK paradox, underdog recipe, knockout shift."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
FOOTBALL = ROOT.parent
DATA = ROOT / "data"
OUT = ROOT / "output"

INK = "#1a1d21"; MUTED = "#6b7280"; GRID = "#e5e7eb"; SURFACE = "#ffffff"
C_BLUE = "#0ea5e9"; C_GREEN = "#059669"; C_ORANGE = "#f97316"; C_VIOLET = "#7c3aed"
plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "font.family": "DejaVu Sans", "text.color": INK,
    "axes.edgecolor": GRID, "axes.labelcolor": MUTED,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.spines.left": False, "axes.spines.bottom": False,
})
STAGE_EN = {1: "Group", 2: "R32", 3: "R16", 4: "QF", 5: "SF", 7: "Final"}
FOOT = dict(fontsize=7.5, color=MUTED)

# ---------- shared match-level table (findings.py join logic) ----------
tm = pd.read_csv(DATA / "team_style_features.csv")
cl = pd.read_csv(DATA / "team_clusters.csv")[["team", "cluster", "max_stage"]]
teams_ref = pd.read_csv(FOOTBALL / "wc2026_dataset" / "teams.csv")
elo = teams_ref.set_index("team_name")["elo_rating"]

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
tm["is_knockout"] = (tm["stage_id"] > 1).astype(int)
tm["elo"] = tm["team"].map(elo)
tm["opp_elo"] = tm["opponent"].map(elo)
opp_g = tm[["match_id", "team", "goals"]].rename(
    columns={"team": "opponent", "goals": "opp_goals"})
tm = tm.merge(opp_g, on=["match_id", "opponent"])
tm["points"] = np.select([tm["goals"] > tm["opp_goals"],
                          tm["goals"] == tm["opp_goals"]], [3, 1], 0)

# ============ 1) GK paradox ============
gk = pd.read_csv(DATA / "gk_buildup.csv")
rho, p = stats.spearmanr(gk["gk_lb_per_match"], gk["max_stage"])
fig, ax = plt.subplots(figsize=(12, 6.75))
fig.subplots_adjust(top=0.80, bottom=0.13, left=0.07, right=0.96)
jit = np.random.default_rng(2).uniform(-0.12, 0.12, len(gk))
ax.scatter(gk["gk_lb_per_match"], gk["max_stage"] + jit, s=70, color=C_VIOLET,
           alpha=0.8, edgecolor=SURFACE, linewidth=1.2, zorder=3)
for team, dxy in {"Paraguay": (8, -4), "Norway": (8, -4), "Brazil": (8, -14),
                  "Portugal": (8, 8), "Spain": (8, 4), "Argentina": (8, 4)}.items():
    r = gk[gk["team"] == team]
    if len(r):
        r = r.iloc[0]
        ax.annotate(team, (r["gk_lb_per_match"], r["max_stage"] + jit[r.name]),
                    xytext=dxy, textcoords="offset points", fontsize=9,
                    fontweight="bold", color=INK)
ax.set_yticks(sorted(gk["max_stage"].unique()),
              [STAGE_EN.get(int(s), str(int(s))) for s in sorted(gk["max_stage"].unique())])
ax.set_xlabel("Goalkeeper line-break attempts per match", fontsize=10.5)
ax.set_ylabel("Round reached", fontsize=10.5)
ax.grid(axis="x", visible=False); ax.tick_params(length=0)
fig.text(0.07, 0.94, "The goalkeeper paradox: busier keepers, earlier exits",
         fontsize=15.5, fontweight="bold", color=INK)
fig.text(0.07, 0.885,
         f"The more a team's goalkeeper attempted line breaks, the sooner the team went home "
         f"(ρ = {rho:+.2f}, p = {p:.3f}, n = {len(gk)})",
         fontsize=10.5, color=MUTED)
fig.text(0.07, 0.03,
         "High keeper involvement mostly reflects long clearances under pressure, not modern build-up play. "
         "Data: FIFA Training Centre match reports, per-player line-break records (100 matches).", **FOOT)
fig.savefig(OUT / "gk_paradox_en.png", dpi=150)
plt.close(fig)
print(f"gk_paradox_en.png  rho={rho:+.2f} p={p:.3f}")

# ============ 2) Underdog recipe ============
ud = tm[tm["elo"] <= tm["opp_elo"] - 50].copy()
ud["upset"] = (ud["points"] >= 1).astype(int)
n_up, n_dn = int(ud["upset"].sum()), int((1 - ud["upset"]).sum())
fig, axes = plt.subplots(1, 2, figsize=(12, 6.75))
fig.subplots_adjust(top=0.78, bottom=0.12, left=0.08, right=0.96, wspace=0.30)
panels = [("recovery_time_s", "Ball-recovery time (seconds)",
           "Winning the ball back faster", axes[0], "{:.1f} s"),
          ("cross_share", "Cross tendency (share of deliveries, %)",
           "Wasting fewer balls on crosses", axes[1], "{:.1f}%")]
for col, xlab, ptitle, ax, fmt in panels:
    a = ud.loc[ud["upset"] == 1, col].dropna()
    b = ud.loc[ud["upset"] == 0, col].dropna()
    _, pv = stats.mannwhitneyu(a, b)
    mult = 100 if col == "cross_share" else 1
    vals = [a.mean() * mult, b.mean() * mult]
    bars = ax.bar(["Underdogs who\ntook points", "Underdogs who\nlost"], vals,
                  width=0.55, color=[C_GREEN, "#9ca3af"], zorder=3)
    for bb, v in zip(bars, vals):
        ax.text(bb.get_x() + bb.get_width() / 2, v * 1.01, fmt.format(v),
                ha="center", fontsize=12, fontweight="bold", color=INK)
    ax.set_ylim(0, max(vals) * 1.18)
    ax.set_ylabel(xlab, fontsize=10)
    ax.grid(axis="x", visible=False); ax.tick_params(length=0)
    ax.set_title(f"{ptitle}  (p = {pv:.3f})", fontsize=11.5, color=INK,
                 fontweight="bold", pad=12)
    print(f"underdog {col}: {vals[0]:.2f} vs {vals[1]:.2f}  p={pv:.3f}")
fig.text(0.06, 0.94, "The underdog recipe: press the reset button fast, don't hope on crosses",
         fontsize=15, fontweight="bold", color=INK)
fig.text(0.06, 0.885,
         f"All {len(ud)} matches with a ≥50 Elo gap — what separated the {n_up} underdog performances "
         f"that took points from the {n_dn} that didn't",
         fontsize=10.5, color=MUTED)
fig.text(0.06, 0.03,
         "Mann-Whitney U tests on per-match style metrics. Elo ratings: pre-tournament. "
         "Data: FIFA Training Centre match reports (100 matches).", **FOOT)
fig.savefig(OUT / "underdog_recipe_en.png", dpi=150)
plt.close(fig)

# ============ 3) Knockout shift ============
both = tm.groupby("team")["is_knockout"].nunique()
teams_both = both[both == 2].index
sub = tm[tm["team"].isin(teams_both)]
g = sub.groupby(["team", "is_knockout"])[
    ["possession_pct", "pressures", "recovery_time_s"]].mean()
fig, axes = plt.subplots(1, 3, figsize=(12.5, 6.75))
fig.subplots_adjust(top=0.78, bottom=0.12, left=0.06, right=0.97, wspace=0.35)
panels = [("possession_pct", "Possession (%)", "Less of the ball", axes[0]),
          ("pressures", "Pressures per match", "More pressing", axes[1]),
          ("recovery_time_s", "Ball-recovery time (s)", "Slower regains", axes[2])]
for col, ylab, ptitle, ax in panels:
    w = g[col].unstack()
    _, pv = stats.wilcoxon(w[0], w[1])
    for _, row in w.iterrows():
        ax.plot([0, 1], [row[0], row[1]], color=GRID, linewidth=1.2, zorder=2)
    m0, m1 = w[0].mean(), w[1].mean()
    ax.plot([0, 1], [m0, m1], color=C_ORANGE, linewidth=3.5, zorder=4,
            marker="o", markersize=8)
    diff = m1 - m0
    sign = "+" if diff >= 0 else "−"
    ax.text(0.5, max(m0, m1) + (w.values.max() - w.values.min()) * 0.06,
            f"{sign}{abs(diff):.1f}", ha="center", fontsize=13,
            fontweight="bold", color=C_ORANGE)
    ax.set_xticks([0, 1], ["Group\nstage", "Knockout\nrounds"], fontsize=10)
    ax.set_xlim(-0.25, 1.25)
    ax.set_ylabel(ylab, fontsize=10)
    ax.grid(axis="x", visible=False); ax.tick_params(length=0)
    ax.set_title(f"{ptitle}  (p = {pv:.3f})", fontsize=11.5, color=INK,
                 fontweight="bold", pad=12)
    print(f"knockout {col}: {m0:.1f} -> {m1:.1f}  p={pv:.3f}")
fig.text(0.06, 0.94, "Knockout football is a different sport",
         fontsize=15.5, fontweight="bold", color=INK)
fig.text(0.06, 0.885,
         f"The same {len(teams_both)} teams, group games vs knockout games — grey lines: individual teams, "
         "orange: the average shift (paired Wilcoxon tests)",
         fontsize=10.5, color=MUTED)
fig.text(0.06, 0.03,
         "Partly tougher opponents, partly a real shift toward transition football. "
         "Data: FIFA Training Centre match reports (100 matches).", **FOOT)
fig.savefig(OUT / "knockout_shift_en.png", dpi=150)
plt.close(fig)
print("done")
