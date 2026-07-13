# -*- coding: utf-8 -*-
"""Turkiye vs Ispanya karsilastirmasi: ayni fikir, farkli infaz (TR + EN)."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "output"

INK = "#1a1d21"; MUTED = "#6b7280"; GRID = "#e5e7eb"; SURFACE = "#ffffff"
C_RED = "#dc2626"; C_GOLD = "#d97706"; C_GRAY = "#9ca3af"
plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "font.family": "DejaVu Sans", "text.color": INK,
    "axes.edgecolor": GRID, "axes.labelcolor": MUTED,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.spines.left": False, "axes.spines.bottom": False,
})

tm = pd.read_csv(DATA / "team_match_tactics.csv")
lb = pd.read_csv(DATA / "team_line_break_profile.csv")

tur = tm[tm["team"].str.contains("rkiye")]
esp = tm[tm["team"] == "Spain"]
stats = {}
for key, d in [("tur", tur), ("esp", esp)]:
    stats[key] = dict(
        conv=100 * d["goals"].sum() / d["attempts"].sum(),
        xg_shot=d["xg"].sum() / d["attempts"].sum(),
        shots=int(d["attempts"].sum()), goals=int(d["goals"].sum()),
        n=len(d))
avg_conv = 100 * tm["goals"].sum() / tm["attempts"].sum()
lb_tur = 100 * lb.loc[lb["team"].str.contains("rkiye"), "lb_success"].iloc[0]
lb_esp = 100 * lb.loc[lb["team"] == "Spain", "lb_success"].iloc[0]
lb_avg = 100 * lb["lb_success"].mean()

TXT = {
    "tr": dict(
        title="İspanya da aynı futbolu oynadı — farkı isabet yarattı",
        sub=f"Türkiye {stats['tur']['n']} maçta {stats['tur']['shots']} şut / {stats['tur']['goals']} gol, "
            f"İspanya {stats['esp']['n']} maçta {stats['esp']['shots']} şut / {stats['esp']['goals']} gol "
            "— iki baskılı takımın hücum kalitesi yan yana",
        panels=["Şut dönüşümü (%)", "Şut başına şans kalitesi (xG)", "Hat kırma isabeti (%)"],
        ptitles=["Golü bulmak", "Doğru pozisyonu seçmek", "Bloğu temiz aşmak"],
        teams=["Türkiye", "İspanya"], avg="turnuva ort.",
        foot="Veri: FIFA Training Centre maç raporları. Dönüşüm = gol/şut; xG/şut = üretilen pozisyonların ortalama kalitesi; "
             "hat kırma isabeti = başarılı deneme payı. Türkiye 3 maç (küçük örneklem).",
        file="turkiye_vs_ispanya.png"),
    "en": dict(
        title="Spain played the same football — accuracy made the difference",
        sub=f"Türkiye: {stats['tur']['shots']} shots / {stats['tur']['goals']} goals in {stats['tur']['n']} matches; "
            f"Spain: {stats['esp']['shots']} shots / {stats['esp']['goals']} goals in {stats['esp']['n']} "
            "— two pressing sides, attack quality side by side",
        panels=["Shot conversion (%)", "Chance quality per shot (xG)", "Line-break completion (%)"],
        ptitles=["Finding the goal", "Picking the right shot", "Beating the block cleanly"],
        teams=["Türkiye", "Spain"], avg="tournament avg",
        foot="Data: FIFA Training Centre match reports. Conversion = goals/shots; xG per shot = average quality of chances created; "
             "line-break completion = share of successful attempts. Türkiye: 3 matches (small sample).",
        file="turkiye_vs_ispanya_en.png"),
}

for lang, T in TXT.items():
    fig, axes = plt.subplots(1, 3, figsize=(12.5, 6.75))
    fig.subplots_adjust(top=0.76, bottom=0.10, left=0.06, right=0.97, wspace=0.35)
    data = [
        ([stats["tur"]["conv"], stats["esp"]["conv"]], avg_conv, "{:.1f}%" if lang == "en" else "%{:.1f}"),
        ([stats["tur"]["xg_shot"], stats["esp"]["xg_shot"]], None, "{:.3f}"),
        ([lb_tur, lb_esp], lb_avg, "{:.0f}%" if lang == "en" else "%{:.0f}"),
    ]
    for ax, ptitle, ylab, (vals, avg, fmt) in zip(axes, T["ptitles"], T["panels"], data):
        bars = ax.bar(T["teams"], vals, width=0.55, color=[C_RED, C_GOLD], zorder=3)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v * 1.02, fmt.format(v),
                    ha="center", fontsize=13, fontweight="bold", color=INK)
        if avg is not None:
            ax.axhline(avg, color=MUTED, linewidth=1.4, linestyle="--", zorder=2)
            ax.text(1.72, avg + max(vals) * 0.015, T["avg"], fontsize=8.5,
                    color=MUTED, va="bottom", ha="right")
        ax.set_ylim(0, max(vals) * 1.22)
        ax.set_xlim(-0.6, 1.75)
        ax.set_ylabel(ylab, fontsize=10)
        ax.grid(axis="x", visible=False); ax.tick_params(length=0)
        ax.tick_params(axis="x", labelsize=11)
        ax.set_title(ptitle, fontsize=12, color=INK, fontweight="bold", pad=12)
    fig.text(0.06, 0.94, T["title"], fontsize=15.5, fontweight="bold", color=INK)
    fig.text(0.06, 0.885, T["sub"], fontsize=10.5, color=MUTED)
    fig.text(0.06, 0.02, T["foot"], fontsize=7.5, color=MUTED)
    fig.savefig(OUT / T["file"], dpi=150)
    plt.close(fig)
    print("Yazildi:", T["file"])
