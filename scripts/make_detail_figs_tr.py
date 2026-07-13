# -*- coding: utf-8 -*-
"""Turkce detay gorselleri: kaleci paradoksu, underdog recetesi, eleme turu."""
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
STAGE_TR = {1: "Grup", 2: "Son 32", 3: "Son 16", 4: "Çeyrek", 5: "Yarı f.", 7: "Final"}
TEAM_TR = {"Paraguay": "Paraguay", "Norway": "Norveç", "Brazil": "Brezilya",
           "Portugal": "Portekiz", "Spain": "İspanya", "Argentina": "Arjantin"}
FOOT = dict(fontsize=7.5, color=MUTED)

# ---------- ortak mac tablosu (findings.py esleme mantigi) ----------
tm = pd.read_csv(DATA / "team_style_features.csv")
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

# ============ 1) Kaleci paradoksu ============
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
        ax.annotate(TEAM_TR[team], (r["gk_lb_per_match"], r["max_stage"] + jit[r.name]),
                    xytext=dxy, textcoords="offset points", fontsize=9,
                    fontweight="bold", color=INK)
ax.set_yticks(sorted(gk["max_stage"].unique()),
              [STAGE_TR.get(int(s), str(int(s))) for s in sorted(gk["max_stage"].unique())])
ax.set_xlabel("Kalecinin maç başına hat kırma denemesi", fontsize=10.5)
ax.set_ylabel("Ulaşılan tur", fontsize=10.5)
ax.grid(axis="x", visible=False); ax.tick_params(length=0)
fig.text(0.07, 0.94, "Kaleci paradoksu: kalecisi çok top oynayan, erken evine döndü",
         fontsize=15.5, fontweight="bold", color=INK)
fig.text(0.07, 0.885,
         f"Kalecisi hat kırmaya çok katılan takımlar daha erken elendi "
         f"(ρ = {rho:+.2f}, p = {p:.3f}, n = {len(gk)})",
         fontsize=10.5, color=MUTED)
fig.text(0.07, 0.03,
         "Yüksek kaleci katılımı çoğu zaman modern oyun kurma değil, baskı altında uzun top çaresizliği. "
         "Veri: FIFA Training Centre maç raporları, oyuncu bazlı hat kırma kayıtları (100 maç).", **FOOT)
fig.savefig(OUT / "gk_paradox.png", dpi=150)
plt.close(fig)
print(f"gk_paradox.png  rho={rho:+.2f} p={p:.3f}")

# ============ 2) Underdog recetesi ============
ud = tm[tm["elo"] <= tm["opp_elo"] - 50].copy()
ud["upset"] = (ud["points"] >= 1).astype(int)
n_up, n_dn = int(ud["upset"].sum()), int((1 - ud["upset"]).sum())
fig, axes = plt.subplots(1, 2, figsize=(12, 6.75))
fig.subplots_adjust(top=0.78, bottom=0.12, left=0.08, right=0.96, wspace=0.30)
panels = [("recovery_time_s", "Topu geri kazanma süresi (saniye)",
           "Topu daha hızlı geri kazanıyor", axes[0], "{:.1f} sn"),
          ("cross_share", "Orta eğilimi (servislerdeki pay, %)",
           "Ortaya daha az bel bağlıyor", axes[1], "%{:.1f}")]
for col, xlab, ptitle, ax, fmt in panels:
    a = ud.loc[ud["upset"] == 1, col].dropna()
    b = ud.loc[ud["upset"] == 0, col].dropna()
    _, pv = stats.mannwhitneyu(a, b)
    mult = 100 if col == "cross_share" else 1
    vals = [a.mean() * mult, b.mean() * mult]
    bars = ax.bar(["Puan alan\nunderdoglar", "Kaybeden\nunderdoglar"], vals,
                  width=0.55, color=[C_GREEN, "#9ca3af"], zorder=3)
    for bb, v in zip(bars, vals):
        ax.text(bb.get_x() + bb.get_width() / 2, v * 1.01, fmt.format(v),
                ha="center", fontsize=12, fontweight="bold", color=INK)
    ax.set_ylim(0, max(vals) * 1.18)
    ax.set_ylabel(xlab, fontsize=10)
    ax.grid(axis="x", visible=False); ax.tick_params(length=0)
    ax.set_title(f"{ptitle}  (p = {pv:.3f})", fontsize=11.5, color=INK,
                 fontweight="bold", pad=12)
fig.text(0.06, 0.94, "Sürprizin reçetesi: topu hızlı geri al, umutsuz ortalarla topu harcama",
         fontsize=15, fontweight="bold", color=INK)
fig.text(0.06, 0.885,
         f"Elo farkı ≥50 olan {len(ud)} maç — puan alan {n_up} underdog performansını "
         f"kaybeden {n_dn} performanstan ayıran iki şey",
         fontsize=10.5, color=MUTED)
fig.text(0.06, 0.03,
         "Maç bazlı stil metriklerinde Mann-Whitney U testleri. Elo: turnuva öncesi. "
         "Veri: FIFA Training Centre maç raporları (100 maç).", **FOOT)
fig.savefig(OUT / "underdog_recipe.png", dpi=150)
plt.close(fig)
print("underdog_recipe.png")

# ============ 3) Eleme turu degisimi ============
both = tm.groupby("team")["is_knockout"].nunique()
teams_both = both[both == 2].index
sub = tm[tm["team"].isin(teams_both)]
g = sub.groupby(["team", "is_knockout"])[
    ["possession_pct", "pressures", "recovery_time_s"]].mean()
fig, axes = plt.subplots(1, 3, figsize=(12.5, 6.75))
fig.subplots_adjust(top=0.78, bottom=0.12, left=0.06, right=0.97, wspace=0.35)
panels = [("possession_pct", "Topla oynama (%)", "Top daha az", axes[0]),
          ("pressures", "Maç başına pres", "Pres daha çok", axes[1]),
          ("recovery_time_s", "Topu geri kazanma (sn)", "Geri kazanım daha yavaş", axes[2])]
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
    ax.set_xticks([0, 1], ["Grup\naşaması", "Eleme\nturları"], fontsize=10)
    ax.set_xlim(-0.25, 1.25)
    ax.set_ylabel(ylab, fontsize=10)
    ax.grid(axis="x", visible=False); ax.tick_params(length=0)
    ax.set_title(f"{ptitle}  (p = {pv:.3f})", fontsize=11.5, color=INK,
                 fontweight="bold", pad=12)
fig.text(0.06, 0.94, "Eleme turu futbolu başka bir spor",
         fontsize=15.5, fontweight="bold", color=INK)
fig.text(0.06, 0.885,
         f"Aynı {len(teams_both)} takım, grup maçları vs eleme maçları — gri çizgiler: tek tek takımlar, "
         "turuncu: ortalama değişim (eşleştirilmiş Wilcoxon testleri)",
         fontsize=10.5, color=MUTED)
fig.text(0.06, 0.03,
         "Kısmen rakip kalitesi, kısmen geçiş futboluna gerçek bir kayış. "
         "Veri: FIFA Training Centre maç raporları (100 maç).", **FOOT)
fig.savefig(OUT / "knockout_shift.png", dpi=150)
plt.close(fig)
print("knockout_shift.png")
