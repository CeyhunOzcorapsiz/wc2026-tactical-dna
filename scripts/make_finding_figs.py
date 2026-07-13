# -*- coding: utf-8 -*-
"""Bulgu grafikleri: line-break anatomisi + gol kaynaklari (TR)."""
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
    "axes.spines.left": False,
})

CLUSTER_NAMES = {0: "Top hakimiyeti\n+ yüksek pres", 1: "Alçak blok\n+ kontra",
                 2: "Geçiş oyunu\n+ ön alan presi", 3: "Dengeli /\npragmatik"}
STAGE_NAMES = {1: "Grup", 2: "Son 32", 3: "Son 16", 4: "Çeyrek", 5: "Yarı f.", 7: "Final"}

# ============ Figur A: line-break anatomisi ============
team = pd.read_csv(DATA / "team_line_break_profile.csv")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 6.75),
                               gridspec_kw={"width_ratios": [1.1, 1]})
fig.subplots_adjust(top=0.80, bottom=0.14, left=0.08, right=0.97, wspace=0.28)

# sol: aile basina yon paylari (gruplu bar)
prof = team.groupby("cluster")[["through_share", "around_share", "over_share"]].mean()
order = [0, 3, 2, 1]
labels = [CLUSTER_NAMES[c] for c in order]
x = np.arange(len(order)); w = 0.26
series = [("Ara pasıyla", "through_share", "#0ea5e9"),
          ("Kanattan dolaşarak", "around_share", "#059669"),
          ("Uzun topla", "over_share", "#f97316")]
for i, (lab, col, color) in enumerate(series):
    vals = [100 * prof.loc[c, col] for c in order]
    bars = ax1.bar(x + (i - 1) * w, vals, w, color=color, zorder=3, label=lab)
    for b, v in zip(bars, vals):
        ax1.text(b.get_x() + b.get_width() / 2, v + 0.8, f"%{v:.0f}",
                 ha="center", fontsize=8.5, fontweight="bold", color=INK)
ax1.set_xticks(x, labels, fontsize=9.5)
ax1.set_ylim(0, 62)
ax1.set_ylabel("Hat kırma denemelerindeki pay (%)", fontsize=10)
ax1.grid(axis="x", visible=False); ax1.tick_params(length=0)
ax1.legend(frameon=False, fontsize=8.5, loc="upper center", ncol=3,
           bbox_to_anchor=(0.5, 1.005), columnspacing=0.9, handlelength=1.2)
ax1.set_title("Savunma hatları nasıl aşıldı? (ekol başına)", fontsize=11.5,
              color=INK, fontweight="bold", pad=12)

# sag: lb isabeti vs asama
rho, p = stats.spearmanr(team["lb_success"], team["max_stage"])
jitter = np.random.default_rng(1).uniform(-0.12, 0.12, len(team))
ax2.scatter(100 * team["lb_success"], team["max_stage"] + jitter, s=60,
            color=C_BLUE, alpha=0.8, edgecolor=SURFACE, linewidth=1.2, zorder=3)
best = team.nlargest(1, "lb_success").iloc[0]
ax2.annotate(f"{best['team']} %{100*best['lb_success']:.0f}",
             (100 * best["lb_success"], best["max_stage"]),
             xytext=(-10, -14), textcoords="offset points", fontsize=8.5,
             fontweight="bold", color=MUTED, ha="right")
ax2.set_yticks(sorted(team["max_stage"].unique()),
               [STAGE_NAMES.get(int(s), str(int(s))) for s in sorted(team["max_stage"].unique())],
               fontsize=9)
ax2.set_xlabel("Hat kırma isabeti (%)", fontsize=10)
ax2.set_ylabel("Ulaşılan tur", fontsize=10)
ax2.grid(axis="x", visible=False); ax2.tick_params(length=0)
ax2.set_title(f"Hat kırma isabeti, tur atlamayı öngörüyor (ρ=+{rho:.2f})",
              fontsize=11.5, color=INK, fontweight="bold", pad=12)

fig.text(0.06, 0.945, "Kademeli savunmayı kırma sanatı: zirve takımlar kanattan dolaşıyor, zorlananlar uzun topa dönüyor",
         fontsize=14, fontweight="bold", color=INK)
fig.text(0.06, 0.89, "48 takım, 100 maç, 27.000+ hat kırma denemesi — FIFA resmî taktik verisi",
         fontsize=10.5, color=MUTED)
fig.text(0.06, 0.02,
         "Veri: FIFA Training Centre maç raporları; yön toplamı = deneme sayısı sağlaması %100. Hat kırma (line break): rakip savunma hattını aşan pas veya top taşıma.",
         fontsize=7.5, color=MUTED)
fig.savefig(OUT / "line_break_anatomy.png", dpi=150)
plt.close(fig)
print("Yazildi: line_break_anatomy.png")

# ============ Figur B: gol kaynaklari ============
sh = pd.read_csv(DATA / "shot_details.csv")
goals = sh[sh["is_goal"] == 1]
src = goals["delivery"].value_counts()
TR_DEL = {"Pass": "Açık oyun – pas organizasyonu", "Cross": "Orta / kanat servisi",
          "Loose Ball": "İkinci top", "Other": "Diğer", "Penalty": "Penaltı",
          "Corner": "Korner", "Freekick": "Serbest vuruş"}
colors = {"Açık oyun – pas organizasyonu": C_BLUE, "Orta / kanat servisi": C_BLUE,
          "İkinci top": C_BLUE, "Diğer": "#9ca3af", "Penaltı": C_ORANGE,
          "Korner": C_ORANGE, "Serbest vuruş": C_ORANGE}

fig, ax = plt.subplots(figsize=(12, 6.75))
fig.subplots_adjust(top=0.80, bottom=0.16, left=0.16, right=0.93)
items = [(TR_DEL[k], v) for k, v in src.items()][::-1]
names = [i[0] for i in items]; vals = [i[1] for i in items]
bars = ax.barh(names, vals, height=0.62,
               color=[colors[n] for n in names], zorder=3)
for b, v in zip(bars, vals):
    ax.text(v + 1.5, b.get_y() + b.get_height() / 2,
            f"{v}  (%{100*v/len(goals):.0f})", va="center", fontsize=10.5,
            fontweight="bold", color=INK)
ax.grid(axis="y", visible=False); ax.tick_params(length=0)
ax.set_xlim(0, max(vals) * 1.16)
ax.set_xlabel("Gol sayısı", fontsize=11)
ax.tick_params(axis="y", labelsize=11)

fig.text(0.07, 0.94, "2026 bir açık oyun kupasıydı: gollerin sadece %13'ü duran toptan",
         fontsize=16, fontweight="bold", color=INK)
fig.text(0.07, 0.885, "268 golün kaynağı — turuncu: duran top (penaltı hariç pay %9; tarihsel Dünya Kupası ortalaması ~%25)",
         fontsize=10.5, color=MUTED)
fig.text(0.07, 0.03,
         "Veri: FIFA Training Centre maç raporları, 100 maçın şut detayları (2.227 şut). Gol sayıları resmî skorlarla doğrulandı (kendi kalesine goller hariç).",
         fontsize=7.5, color=MUTED)
fig.savefig(OUT / "goal_sources.png", dpi=150)
plt.close(fig)
print("Yazildi: goal_sources.png")
