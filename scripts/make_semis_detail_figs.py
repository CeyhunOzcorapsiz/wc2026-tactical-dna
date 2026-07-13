# -*- coding: utf-8 -*-
"""Yari finalist detay gorselleri (TR + EN):
A) hat kirma parmak izi  B) gol anatomisi  C) pres kimligi
"""
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
TC = {"Spain": "#d97706", "France": "#0ea5e9",
      "England": "#7c3aed", "Argentina": "#059669"}
SEMIS = ["Spain", "France", "England", "Argentina"]
NAME = {"tr": {"Spain": "İspanya", "France": "Fransa",
               "England": "İngiltere", "Argentina": "Arjantin"},
        "en": {t: t for t in SEMIS}}
plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "font.family": "DejaVu Sans", "text.color": INK,
    "axes.edgecolor": GRID, "axes.labelcolor": MUTED,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.spines.left": False, "axes.spines.bottom": False,
})
FOOT = dict(fontsize=7.5, color=MUTED)

lbp = pd.read_csv(DATA / "team_line_break_profile.csv")
sh = pd.read_csv(DATA / "shot_details.csv")
tmt = pd.read_csv(DATA / "team_match_tactics.csv")

# ================= A) hat kirma parmak izi =================
for lang in ("tr", "en"):
    T = NAME[lang]
    if lang == "tr":
        dir_labels = ["Hat arasına\nara pasıyla", "Kanattan\ndolaşarak", "Üstünden\nuzun topla"]
        veh_labels = ["Pas oyunuyla", "Top sürerek", "Ortalarla"]
        t1, t2 = "Savunma bloğunu nereden deliyorlar?", "Silah tercihi ne?"
        title = "Blok delme sanatı: dört yarı finalistin parmak izi"
        sub = "Kademeli savunmayı aşma tercihleri — aynı ekol, dört farklı el yazısı"
        foot = ("Veri: FIFA Training Centre maç raporları, oyuncu bazlı hat kırma kayıtları; yön toplamı = deneme sayısı sağlaması %100. "
                "Paylar takımın toplam hat kırma denemeleri içindeki orandır.")
        out = "semifinal_lb_fingerprint.png"
    else:
        dir_labels = ["Through the lines\n(needle passes)", "Around the block\n(wide circulation)", "Over the top\n(long balls)"]
        veh_labels = ["Through passing", "On the carry", "From crosses"]
        t1, t2 = "Where do they unlock the block?", "Weapon of choice?"
        title = "The art of unlocking a block: four semi-finalist fingerprints"
        sub = "How each side beats a set defence — one school, four different handwritings"
        foot = ("Data: FIFA Training Centre match reports, per-player line-break records; direction sums ≡ attempts for 100% of rows. "
                "Shares are of each team's total line-break attempts.")
        out = "semifinal_lb_fingerprint_en.png"

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 6.75))
    fig.subplots_adjust(top=0.76, bottom=0.16, left=0.07, right=0.97, wspace=0.25)
    x1 = np.arange(3); x2 = np.arange(3); w = 0.19
    for i, team in enumerate(SEMIS):
        r = lbp[lbp["team"] == team].iloc[0]
        dirs = 100 * np.array([r["through_share"], r["around_share"], r["over_share"]])
        vehs = 100 * np.array([r["via_pass_share"], r["via_carry_share"], r["via_cross_share"]])
        off = (i - 1.5) * w
        b1 = ax1.bar(x1 + off, dirs, w, color=TC[team], zorder=3, label=T[team])
        b2 = ax2.bar(x2 + off, vehs, w, color=TC[team], zorder=3)
        for b, v in zip(b1, dirs):
            ax1.text(b.get_x() + b.get_width() / 2, v + 0.7, f"{v:.0f}",
                     ha="center", fontsize=7.5, fontweight="bold", color=INK)
        for b, v in zip(b2, vehs):
            ax2.text(b.get_x() + b.get_width() / 2, v + 1.4, f"{v:.0f}",
                     ha="center", fontsize=7.5, fontweight="bold", color=INK)
    ax1.set_xticks(x1, dir_labels, fontsize=9.5)
    ax2.set_xticks(x2, veh_labels, fontsize=9.5)
    for ax, t in [(ax1, t1), (ax2, t2)]:
        ax.set_ylabel("%", fontsize=10)
        ax.grid(axis="x", visible=False); ax.tick_params(length=0)
        ax.set_title(t, fontsize=12, color=INK, fontweight="bold", pad=12)
    ax1.set_ylim(0, 60); ax2.set_ylim(0, 100)
    ax1.legend(frameon=False, fontsize=9.5, loc="upper right", ncol=2,
               columnspacing=1.0, handlelength=1.2)
    fig.text(0.06, 0.94, title, fontsize=15.5, fontweight="bold", color=INK)
    fig.text(0.06, 0.885, sub, fontsize=10.5, color=MUTED)
    fig.text(0.06, 0.03, foot, **FOOT)
    fig.savefig(OUT / out, dpi=150)
    plt.close(fig)
    print("Yazildi:", out)

# ================= B) gol anatomisi =================
goals = sh[(sh["is_goal"] == 1) & (sh["team"].isin(SEMIS))].copy()
CAT = {"Pass": "open", "Cross": "open", "Loose Ball": "open", "Other": "open",
       "Penalty": "set", "Corner": "set", "Freekick": "set"}
goals["cat"] = goals["delivery"].map(CAT)

for lang in ("tr", "en"):
    T = NAME[lang]
    if lang == "tr":
        title = "Dört yarı finalistin gol anatomisi"
        sub = ("İspanya golünü tamamen akan oyundan buluyor; Arjantin maçları geç koparıyor — "
               "skoru kimin ne zaman ve nereden bulduğu tek bakışta")
        t1, t2 = "Goller nereden geldi?", "Skor anları: goller hangi dakikada?"
        leg1 = ["Akan oyun", "Duran top"]
        xlab2 = "Dakika"
        ht, ft = "İY", "90'"
        foot = ("Veri: FIFA Training Centre maç raporları, şut detayları (kendi kalesine goller hariç). "
                "Duran top: penaltı + korner + serbest vuruş. Dikey çizgiler: devre arası ve 90. dakika (sonrası uzatmalar).")
        out = "semifinal_goal_anatomy.png"
    else:
        title = "The goal anatomy of the four semi-finalists"
        sub = ("Spain score exclusively from open play; Argentina kill games late — "
               "who scores, when and from what, at a glance")
        t1, t2 = "Where the goals came from", "Match moments: when they struck"
        leg1 = ["Open play", "Set pieces"]
        xlab2 = "Minute"
        ht, ft = "HT", "90'"
        foot = ("Data: FIFA Training Centre match reports, shot-by-shot details (own goals excluded). "
                "Set pieces: penalties + corners + free kicks. Vertical lines: half-time and 90 minutes (extra time beyond).")
        out = "semifinal_goal_anatomy_en.png"

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 6.75),
                                   gridspec_kw={"width_ratios": [1, 1.35]})
    fig.subplots_adjust(top=0.76, bottom=0.14, left=0.10, right=0.97, wspace=0.30)
    ypos = np.arange(len(SEMIS))[::-1]
    for y, team in zip(ypos, SEMIS):
        g = goals[goals["team"] == team]
        n_open = (g["cat"] == "open").sum(); n_set = (g["cat"] == "set").sum()
        ax1.barh(y, n_open, height=0.55, color=TC[team], zorder=3)
        ax1.barh(y, n_set, left=n_open, height=0.55, color=TC[team],
                 alpha=0.35, zorder=3)
        ax1.text(n_open + n_set + 0.3, y, f"{n_open + n_set}", va="center",
                 fontsize=10.5, fontweight="bold", color=INK)
        if n_set:
            ax1.text(n_open + n_set / 2, y, str(n_set), va="center", ha="center",
                     fontsize=8.5, color=INK)
    ax1.set_yticks(ypos, [T[t] for t in SEMIS], fontsize=10.5)
    ax1.set_xlim(0, goals.groupby("team").size().max() * 1.18)
    ax1.set_xlabel(t1 if lang == "en" else "Gol sayısı", fontsize=10)
    ax1.grid(axis="y", visible=False); ax1.tick_params(length=0)
    ax1.set_title(t1, fontsize=12, color=INK, fontweight="bold", pad=12)
    from matplotlib.patches import Patch
    ax1.legend(handles=[Patch(color=MUTED), Patch(color=MUTED, alpha=0.35)],
               labels=leg1, frameon=False, fontsize=9, loc="upper center",
               bbox_to_anchor=(0.5, -0.10), ncol=2)

    rng = np.random.default_rng(4)
    for y, team in zip(ypos, SEMIS):
        g = goals[goals["team"] == team]
        mins = pd.to_numeric(g["minute"], errors="coerce").dropna()
        ax2.scatter(mins, np.full(len(mins), y) + rng.uniform(-0.14, 0.14, len(mins)),
                    s=55, color=TC[team], alpha=0.85, edgecolor=SURFACE,
                    linewidth=1.0, zorder=3)
    for xline, lab in [(45, ht), (90, ft)]:
        ax2.axvline(xline, color=MUTED, linewidth=1.2, linestyle="--", zorder=2)
        ax2.text(xline, 3.62, lab, fontsize=8.5, color=MUTED, ha="center")
    ax2.set_yticks(ypos, ["" for _ in SEMIS])
    ax2.set_ylim(-0.55, 3.8)
    ax2.set_xlim(-3, 128)
    ax2.set_xlabel(xlab2, fontsize=10)
    ax2.grid(axis="y", visible=False); ax2.tick_params(length=0)
    ax2.set_title(t2, fontsize=12, color=INK, fontweight="bold", pad=12)
    fig.text(0.06, 0.94, title, fontsize=15.5, fontweight="bold", color=INK)
    fig.text(0.06, 0.885, sub, fontsize=10.5, color=MUTED)
    fig.text(0.06, 0.03, foot, **FOOT)
    fig.savefig(OUT / out, dpi=150)
    plt.close(fig)
    print("Yazildi:", out)

# ================= C) pres kimligi =================
sub_t = tmt[tmt["team"].isin(SEMIS)]
agg = sub_t.groupby("team").agg(
    press_duration=("press_duration_s", "mean"),
    recovery=("recovery_time_s", "mean"),
    pressures=("pressures", "sum"),
    direct=("direct_pressures", "sum"),
    inside=("press_inside", "sum"),
    outside=("press_outside", "sum"))
agg["direct_share"] = 100 * agg["direct"] / agg["pressures"]
agg["inside_share"] = 100 * agg["inside"] / (agg["inside"] + agg["outside"])
tour = dict(
    direct_share=100 * tmt["direct_pressures"].sum() / tmt["pressures"].sum(),
    press_duration=tmt["press_duration_s"].mean(),
    recovery=tmt["recovery_time_s"].mean(),
    inside_share=100 * tmt["press_inside"].sum() /
                 (tmt["press_inside"].sum() + tmt["press_outside"].sum()))

for lang in ("tr", "en"):
    T = NAME[lang]
    if lang == "tr":
        title = "Dört yüksek pres, dört farklı pres kimliği"
        sub = ("Adamına pres mi, alan daraltma mı? Gegenpressing'in dört yorumu — kesikli çizgi: 48 takım ortalaması")
        panels = [("direct_share", "Direkt pres payı (%)", "Topun adamını ne kadar boğuyor?", "%{:.0f}"),
                  ("press_duration", "Pres süresi (sn)", "Baskı dalgası kaç saniye sürüyor?", "{:.2f}"),
                  ("recovery", "Topu geri kazanma (sn)", "Kayıptan sonra top kaç saniyede geri?", "{:.1f}"),
                  ("inside_share", "Orta koridora yönlendirme (%)", "Rakibi hangi koridora hapsediyor?", "%{:.0f}")]
        avg_lab = "turnuva ort."
        foot = ("Veri: FIFA Training Centre maç raporları, savunma baskısı sayfaları (takım başına 6 maç). "
                "Direkt pres: topa oynayan oyuncuya uygulanan baskı; orta koridora yönlendirme: presin rakibi kalabalık merkeze itmesi.")
        out = "semifinal_press_identity.png"
    else:
        title = "Four high presses, four pressing identities"
        sub = ("Man-oriented or space-squeezing? Four readings of the counter-press — dashed line: 48-team tournament average")
        panels = [("direct_share", "Direct-press share (%)", "How hard do they hunt the ball-carrier?", "{:.0f}%"),
                  ("press_duration", "Press duration (s)", "How long does the pressing wave last?", "{:.2f}"),
                  ("recovery", "Ball recovery (s)", "Seconds to win it back after losing it", "{:.1f}"),
                  ("inside_share", "Central-channel steer (%)", "Which channel do they trap opponents in?", "{:.0f}%")]
        avg_lab = "tournament avg"
        foot = ("Data: FIFA Training Centre match reports, defensive-pressure pages (6 matches per team). "
                "Direct press: pressure on the player in possession; central steer: press funnelling opponents into congested central areas.")
        out = "semifinal_press_identity_en.png"

    fig, axes = plt.subplots(2, 2, figsize=(12, 8.5))
    fig.subplots_adjust(top=0.82, bottom=0.09, left=0.08, right=0.96,
                        hspace=0.55, wspace=0.30)
    for ax, (col, ylab, ptitle, fmt) in zip(axes.flat, panels):
        vals = [agg.loc[t, col] for t in SEMIS]
        bars = ax.bar([T[t] for t in SEMIS], vals, width=0.6,
                      color=[TC[t] for t in SEMIS], zorder=3)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v * 1.015, fmt.format(v),
                    ha="center", fontsize=10.5, fontweight="bold", color=INK)
        ax.axhline(tour[col], color=MUTED, linewidth=1.3, linestyle="--", zorder=2)
        ax.set_xlim(-1.15, 3.6)
        ax.text(-1.08, tour[col] + max(vals) * 0.015, avg_lab, fontsize=8,
                color=MUTED, ha="left", va="bottom")
        ax.set_ylim(0, max(max(vals), tour[col]) * 1.18)
        ax.set_ylabel(ylab, fontsize=9.5)
        ax.grid(axis="x", visible=False); ax.tick_params(length=0)
        ax.tick_params(axis="x", labelsize=10)
        ax.set_title(ptitle, fontsize=11.5, color=INK, fontweight="bold", pad=10)
    fig.text(0.06, 0.945, title, fontsize=16, fontweight="bold", color=INK)
    fig.text(0.06, 0.905, sub, fontsize=10.5, color=MUTED)
    fig.text(0.06, 0.02, foot, **FOOT)
    fig.savefig(OUT / out, dpi=150)
    plt.close(fig)
    print("Yazildi:", out)
