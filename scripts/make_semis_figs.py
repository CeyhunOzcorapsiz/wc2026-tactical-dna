# -*- coding: utf-8 -*-
"""Yari finalist DNA radarlari + Turkiye vs yari finalistler (TR + EN).

Her metrik 48 takim icindeki yuzdelik dilim (0-100) olarak cizilir;
recovery_time ve ppda_like ters cevrilir (yuksek = daha iyi/agresif).
"""
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
SEMI_COLORS = {"Spain": "#d97706", "France": "#0ea5e9",
               "England": "#7c3aed", "Argentina": "#059669"}
C_RED = "#dc2626"
SEMIS = ["Spain", "France", "England", "Argentina"]

# ---------- metrikler ----------
cl = pd.read_csv(DATA / "team_clusters.csv")
lb = pd.read_csv(DATA / "team_line_break_profile.csv")[["team", "lb_success"]]
tm = pd.read_csv(DATA / "team_match_tactics.csv")
conv = tm.groupby("team").apply(
    lambda d: 100 * d["goals"].sum() / d["attempts"].sum(),
    include_groups=False).rename("conversion").reset_index()

df = cl.merge(lb, on="team").merge(conv, on="team")
# ters cevrilenler: dusuk deger = daha iyi
df["press_intensity"] = -df["ppda_like"]
df["recovery_speed"] = -df["recovery_time_s"]

METRICS = ["possession_pct", "pass_completion_pct", "lb_success",
           "conversion", "press_intensity", "recovery_speed"]
for m in METRICS:
    df[m + "_pct"] = 100 * stats.rankdata(df[m]) / len(df)

LABELS = {
    "tr": ["Topla\noynama", "Pas\nisabeti", "Hat kırma\nisabeti",
           "Şut\ndönüşümü", "Pres\nyoğunluğu", "Top geri\nkazanma hızı"],
    "en": ["Possession", "Pass\ncompletion", "Line-break\ncompletion",
           "Shot\nconversion", "Press\nintensity", "Recovery\nspeed"],
}
TEAM_TR = {"Spain": "İspanya", "France": "Fransa", "England": "İngiltere",
           "Argentina": "Arjantin"}

def radar_axes(ax, labels):
    n = len(labels)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_xticks(angles)
    ax.set_xticklabels(labels, fontsize=8.5, color=MUTED)
    ax.set_ylim(0, 100)
    ax.set_yticks([25, 50, 75, 100])
    ax.set_yticklabels(["", "50", "", "100"], fontsize=7, color=MUTED)
    ax.grid(color=GRID, linewidth=0.8)
    ax.spines["polar"].set_color(GRID)
    ax.set_facecolor(SURFACE)
    return angles

def poly(vals):
    return np.concatenate([vals, vals[:1]])

def team_vals(team_filter):
    r = df[team_filter].iloc[0]
    return np.array([r[m + "_pct"] for m in METRICS])

# ============ Figur 1: yari finalist DNA'lari (2x2 radar) ============
for lang in ("tr", "en"):
    labels = LABELS[lang]
    fig, axes = plt.subplots(2, 2, figsize=(11.5, 10.5),
                             subplot_kw=dict(polar=True))
    fig.patch.set_facecolor(SURFACE)
    fig.subplots_adjust(top=0.84, bottom=0.06, left=0.07, right=0.93,
                        hspace=0.42, wspace=0.38)
    for ax, team in zip(axes.flat, SEMIS):
        angles = radar_axes(ax, labels)
        vals = team_vals(df["team"] == team)
        c = SEMI_COLORS[team]
        ax.plot(poly(angles), poly(vals), color=c, linewidth=2.2, zorder=3)
        ax.fill(poly(angles), poly(vals), color=c, alpha=0.18, zorder=2)
        name = TEAM_TR[team] if lang == "tr" else team
        ax.set_title(name, fontsize=14, fontweight="bold", color=c, pad=18)
    if lang == "tr":
        fig.text(0.07, 0.955, "Yarı finalistlerin taktik DNA'sı",
                 fontsize=18, fontweight="bold", color=INK)
        fig.text(0.07, 0.915,
                 "Her eksen: 48 takım içindeki yüzdelik dilim (100 = turnuvanın en iyisi) — dördü de aynı kalıp:\n"
                 "topa hükmet, hatları isabetle kır, topu hızlı geri kazan",
                 fontsize=10.5, color=MUTED)
        fig.text(0.07, 0.015,
                 "Veri: FIFA Training Centre maç raporları (100 maç). Pres yoğunluğu ve top geri kazanma hızı ters ölçek (yüksek = daha agresif/hızlı).",
                 fontsize=7.5, color=MUTED)
        out = "semifinal_dna.png"
    else:
        fig.text(0.07, 0.955, "The tactical DNA of the semi-finalists",
                 fontsize=18, fontweight="bold", color=INK)
        fig.text(0.07, 0.915,
                 "Each axis: percentile rank among all 48 teams (100 = tournament best) — four teams, one blueprint:\n"
                 "dominate the ball, break lines accurately, win it back fast",
                 fontsize=10.5, color=MUTED)
        fig.text(0.07, 0.015,
                 "Data: FIFA Training Centre match reports (100 matches). Press intensity and recovery speed are inverted scales (higher = more aggressive/faster).",
                 fontsize=7.5, color=MUTED)
        out = "semifinal_dna_en.png"
    fig.savefig(OUT / out, dpi=150)
    plt.close(fig)
    print("Yazildi:", out)

# ============ Figur 2: Turkiye vs yari finalist ortalamasi ============
semi_avg = np.mean([team_vals(df["team"] == t) for t in SEMIS], axis=0)
tur_vals = team_vals(df["team"].str.contains("rkiye"))

for lang in ("tr", "en"):
    labels = LABELS[lang]
    fig, ax = plt.subplots(figsize=(9.5, 9.5), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor(SURFACE)
    fig.subplots_adjust(top=0.78, bottom=0.08, left=0.10, right=0.90)
    angles = radar_axes(ax, labels)
    ax.tick_params(axis="x", labelsize=10.5)
    l_semi, = ax.plot(poly(angles), poly(semi_avg), color="#d97706",
                      linewidth=2.5, zorder=3)
    ax.fill(poly(angles), poly(semi_avg), color="#d97706", alpha=0.15, zorder=2)
    l_tur, = ax.plot(poly(angles), poly(tur_vals), color=C_RED,
                     linewidth=2.5, zorder=4)
    ax.fill(poly(angles), poly(tur_vals), color=C_RED, alpha=0.15, zorder=2)
    if lang == "tr":
        ax.legend([l_semi, l_tur], ["Yarı finalist ortalaması", "Türkiye"],
                  loc="upper right", bbox_to_anchor=(1.18, 1.12),
                  frameon=False, fontsize=10.5)
        fig.text(0.08, 0.945, "Türkiye'nin yarı finalistlerden farkı tek eksende",
                 fontsize=16.5, fontweight="bold", color=INK)
        fig.text(0.08, 0.87,
                 "48 takım içindeki yüzdelik dilimler — topla oynamada ve top geri kazanma hızında\n"
                 "yarı finalistlerin bile önündeyiz; makas pas isabetinde, hat kırmada ve özellikle şut dönüşümünde açılıyor",
                 fontsize=10.5, color=MUTED)
        fig.text(0.08, 0.02,
                 "Veri: FIFA Training Centre maç raporları. Türkiye 3 maç (küçük örneklem). Pres yoğunluğu ve geri kazanma hızı ters ölçek.",
                 fontsize=7.5, color=MUTED)
        out = "turkiye_vs_semifinal.png"
    else:
        ax.legend([l_semi, l_tur], ["Semi-finalist average", "Türkiye"],
                  loc="upper right", bbox_to_anchor=(1.18, 1.12),
                  frameon=False, fontsize=10.5)
        fig.text(0.08, 0.945, "Türkiye vs the semi-finalists, one axis at a time",
                 fontsize=16.5, fontweight="bold", color=INK)
        fig.text(0.08, 0.87,
                 "Percentile ranks among all 48 teams — Türkiye held more of the ball and recovered it faster\n"
                 "than even the semi-finalists; the gap opens at pass and line-break accuracy and, above all, shot conversion",
                 fontsize=10.5, color=MUTED)
        fig.text(0.08, 0.02,
                 "Data: FIFA Training Centre match reports. Türkiye: 3 matches (small sample). Press intensity and recovery speed are inverted scales.",
                 fontsize=7.5, color=MUTED)
        out = "turkiye_vs_semifinal_en.png"
    fig.savefig(OUT / out, dpi=150)
    plt.close(fig)
    print("Yazildi:", out)

# kontrol degerleri
print("\nyuzdelikler (Turkiye):", dict(zip(METRICS, tur_vals.round(0))))
print("yuzdelikler (SF ort):", dict(zip(METRICS, semi_avg.round(0))))
