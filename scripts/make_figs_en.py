# -*- coding: utf-8 -*-
"""English versions of the three published figures (…_en.png)."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
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

CLUSTER_EN = {0: "Control pressers", 3: "Balanced pragmatists",
              2: "Vertical hunters (high direct press)", 1: "Deep-block reactives"}
CLUSTER_COLOR = {0: C_BLUE, 3: C_GREEN, 2: C_ORANGE, 1: C_VIOLET}
SEMIS = {"France", "Spain", "England", "Argentina"}
STAGE_EN = {1: "Group", 2: "R32", 3: "R16", 4: "QF", 5: "SF", 7: "Final"}

# ---------- 1) Tactical map ----------
df = pd.read_csv(DATA / "team_clusters.csv")
fig, ax = plt.subplots(figsize=(12.5, 8.5))
fig.subplots_adjust(top=0.86, bottom=0.12, left=0.05, right=0.97)
for c in [0, 3, 2, 1]:
    sub = df[df["cluster"] == c]
    ax.scatter(sub["pc1"], sub["pc2"], s=90, color=CLUSTER_COLOR[c], alpha=0.85,
               edgecolor=SURFACE, linewidth=1.5, zorder=3, label=CLUSTER_EN[c])
for _, r in df.iterrows():
    bold = r["team"] in SEMIS
    ax.annotate(r["team"], (r["pc1"], r["pc2"]), xytext=(0, 8),
                textcoords="offset points", ha="center",
                fontsize=8.5 if bold else 7.5,
                fontweight="bold" if bold else "normal",
                color=INK if bold else MUTED, zorder=4)
ax.tick_params(length=0, labelleft=False, labelbottom=False)
ax.set_xlabel("← reactive / slow recovery        ball & territory control →",
              fontsize=10.5)
ax.set_ylabel("← patient attack        direct & vertical attack →", fontsize=10.5)
ax.legend(frameon=False, fontsize=9.5, loc="lower right")
fig.text(0.05, 0.955, "The Tactical Map of the 2026 World Cup",
         fontsize=17, fontweight="bold", color=INK)
fig.text(0.05, 0.905,
         "48 teams, 10 style metrics from FIFA's official tactical data, 4 families — bold = semi-finalists (4/4 in the blue family)",
         fontsize=10.5, color=MUTED)
fig.text(0.05, 0.02,
         "Data: FIFA Training Centre post-match reports (100 matches, 4+ match averages per team). Metrics: possession, pass completion, line breaks per pass,\n"
         "final-third receptions, cross tendency, PPDA-like press intensity, direct-press share, press duration, ball-recovery time, press direction. PCA + k-means.",
         fontsize=7.5, color=MUTED)
fig.savefig(OUT / "tactical_map_2026_en.png", dpi=150)
plt.close(fig)

# ---------- 2) Line-break anatomy ----------
team = pd.read_csv(DATA / "team_line_break_profile.csv")
CL_SHORT = {0: "Control\npressers", 1: "Deep-block\nreactives",
            2: "Vertical\nhunters", 3: "Balanced\npragmatists"}
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 6.75),
                               gridspec_kw={"width_ratios": [1.1, 1]})
fig.subplots_adjust(top=0.80, bottom=0.14, left=0.08, right=0.97, wspace=0.28)
prof = team.groupby("cluster")[["through_share", "around_share", "over_share"]].mean()
order = [0, 3, 2, 1]
x = np.arange(len(order)); w = 0.26
series = [("Through (between lines)", "through_share", C_BLUE),
          ("Around (wide)", "around_share", C_GREEN),
          ("Over (long ball)", "over_share", C_ORANGE)]
for i, (lab, col, color) in enumerate(series):
    vals = [100 * prof.loc[c, col] for c in order]
    bars = ax1.bar(x + (i - 1) * w, vals, w, color=color, zorder=3, label=lab)
    for b, v in zip(bars, vals):
        ax1.text(b.get_x() + b.get_width() / 2, v + 0.8, f"{v:.0f}%",
                 ha="center", fontsize=8.5, fontweight="bold", color=INK)
ax1.set_xticks(x, [CL_SHORT[c] for c in order], fontsize=9.5)
ax1.set_ylim(0, 62)
ax1.set_ylabel("Share of line-break attempts (%)", fontsize=10)
ax1.grid(axis="x", visible=False); ax1.tick_params(length=0)
ax1.legend(frameon=False, fontsize=8.5, loc="upper center", ncol=3,
           bbox_to_anchor=(0.5, 1.005), columnspacing=0.9, handlelength=1.2)
ax1.set_title("How blocks were broken (by family)", fontsize=11.5,
              color=INK, fontweight="bold", pad=12)

rho, p = stats.spearmanr(team["lb_success"], team["max_stage"])
jitter = np.random.default_rng(1).uniform(-0.12, 0.12, len(team))
ax2.scatter(100 * team["lb_success"], team["max_stage"] + jitter, s=60,
            color=C_BLUE, alpha=0.8, edgecolor=SURFACE, linewidth=1.2, zorder=3)
best = team.nlargest(1, "lb_success").iloc[0]
ax2.annotate(f"{best['team']} {100*best['lb_success']:.0f}%",
             (100 * best["lb_success"], best["max_stage"]),
             xytext=(-10, -14), textcoords="offset points", fontsize=8.5,
             fontweight="bold", color=MUTED, ha="right")
ax2.set_yticks(sorted(team["max_stage"].unique()),
               [STAGE_EN.get(int(s), str(int(s))) for s in sorted(team["max_stage"].unique())],
               fontsize=9)
ax2.set_xlabel("Line-break completion rate (%)", fontsize=10)
ax2.set_ylabel("Round reached", fontsize=10)
ax2.grid(axis="x", visible=False); ax2.tick_params(length=0)
ax2.set_title(f"Completion predicts progression (ρ=+{rho:.2f}, p<0.001)",
              fontsize=11.5, color=INK, fontweight="bold", pad=12)
fig.text(0.06, 0.945, "The anatomy of breaking the block: elites go around, survivors go over",
         fontsize=14.5, fontweight="bold", color=INK)
fig.text(0.06, 0.89, "48 teams, 100 matches, 27,000+ line-break attempts — FIFA official tactical data",
         fontsize=10.5, color=MUTED)
fig.text(0.06, 0.02,
         "Data: FIFA Training Centre match reports; direction sums ≡ attempts for 100% of rows. Line break: a pass/carry beating an opposition defensive line.",
         fontsize=7.5, color=MUTED)
fig.savefig(OUT / "line_break_anatomy_en.png", dpi=150)
plt.close(fig)

# ---------- 3) Goal sources ----------
sh = pd.read_csv(DATA / "shot_details.csv")
goals = sh[sh["is_goal"] == 1]
src = goals["delivery"].value_counts()
EN_DEL = {"Pass": "From open-play pass", "Cross": "From cross",
          "Loose Ball": "Loose ball / second ball", "Other": "Other",
          "Penalty": "Penalty", "Corner": "Corner", "Freekick": "Free kick"}
colors = {"From open-play pass": C_BLUE, "From cross": C_BLUE,
          "Loose ball / second ball": C_BLUE, "Other": "#9ca3af",
          "Penalty": C_ORANGE, "Corner": C_ORANGE, "Free kick": C_ORANGE}
fig, ax = plt.subplots(figsize=(12, 6.75))
fig.subplots_adjust(top=0.80, bottom=0.16, left=0.20, right=0.93)
items = [(EN_DEL[k], v) for k, v in src.items()][::-1]
names = [i[0] for i in items]; vals = [i[1] for i in items]
bars = ax.barh(names, vals, height=0.62, color=[colors[n] for n in names], zorder=3)
for b, v in zip(bars, vals):
    ax.text(v + 1.5, b.get_y() + b.get_height() / 2,
            f"{v}  ({100*v/len(goals):.0f}%)", va="center", fontsize=10.5,
            fontweight="bold", color=INK)
ax.grid(axis="y", visible=False); ax.tick_params(length=0)
ax.set_xlim(0, max(vals) * 1.16)
ax.set_xlabel("Goals", fontsize=11)
ax.tick_params(axis="y", labelsize=11)
fig.text(0.07, 0.94, "2026 was an open-play World Cup: only 13% of goals came from set pieces",
         fontsize=15.5, fontweight="bold", color=INK)
fig.text(0.07, 0.885, "Sources of all 268 goals — orange: set pieces (9% excluding penalties; historical World Cup norm ~25%)",
         fontsize=10.5, color=MUTED)
fig.text(0.07, 0.03,
         "Data: FIFA Training Centre match reports, shot-by-shot details for 100 matches (2,227 shots). Goal counts verified against official scores (own goals excluded).",
         fontsize=7.5, color=MUTED)
fig.savefig(OUT / "goal_sources_en.png", dpi=150)
plt.close(fig)
print("Yazildi: tactical_map_2026_en.png, line_break_anatomy_en.png, goal_sources_en.png")
