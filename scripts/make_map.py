# -*- coding: utf-8 -*-
"""2026'nin taktik haritasi: PCA duzleminde 48 takim, 4 stil ailesi."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)

INK = "#1a1d21"; MUTED = "#6b7280"; GRID = "#e5e7eb"; SURFACE = "#ffffff"
CLUSTER_STYLE = {
    0: ("#0ea5e9", "Kontrolcü baskıcılar"),
    3: ("#059669", "Dengeli pragmatikler"),
    2: ("#f97316", "Dikey avcılar (yüksek direkt pres)"),
    1: ("#7c3aed", "Derin blok reaktifler"),
}
plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "font.family": "DejaVu Sans", "text.color": INK,
    "axes.edgecolor": GRID, "axes.labelcolor": MUTED,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.spines.left": False, "axes.spines.bottom": False,
})

TR = {"Spain": "İspanya", "France": "Fransa", "England": "İngiltere",
      "Argentina": "Arjantin", "Türkiye": "Türkiye", "Germany": "Almanya",
      "Brazil": "Brezilya", "Portugal": "Portekiz", "Morocco": "Fas",
      "Netherlands": "Hollanda", "USA": "ABD", "Mexico": "Meksika",
      "Japan": "Japonya", "Canada": "Kanada", "Uruguay": "Uruguay",
      "Switzerland": "İsviçre", "Belgium": "Belçika", "Croatia": "Hırvatistan"}

SEMIS = {"France", "Spain", "England", "Argentina"}

df = pd.read_csv(DATA / "team_clusters.csv")

fig, ax = plt.subplots(figsize=(12.5, 8.5))
fig.subplots_adjust(top=0.86, bottom=0.12, left=0.05, right=0.97)

for c, (color, label) in CLUSTER_STYLE.items():
    sub = df[df["cluster"] == c]
    ax.scatter(sub["pc1"], sub["pc2"], s=90, color=color, alpha=0.85,
               edgecolor=SURFACE, linewidth=1.5, zorder=3, label=label)

for _, r in df.iterrows():
    name = TR.get(r["team"], r["team"])
    bold = r["team"] in SEMIS
    ax.annotate(name, (r["pc1"], r["pc2"]), xytext=(0, 8),
                textcoords="offset points", ha="center",
                fontsize=8.5 if bold else 7.5,
                fontweight="bold" if bold else "normal",
                color=INK if bold else MUTED, zorder=4)

ax.tick_params(length=0, labelleft=False, labelbottom=False)
ax.set_xlabel("← reaktif / uzun geri kazanım        top ve saha kontrolü →",
              fontsize=10.5)
ax.set_ylabel("← sabırlı hücum        direkt & dikey hücum →", fontsize=10.5)
ax.legend(frameon=False, fontsize=9.5, loc="lower right")

fig.text(0.05, 0.955, "2026 Dünya Kupası'nın Taktik Haritası",
         fontsize=17, fontweight="bold", color=INK)
fig.text(0.05, 0.905,
         "FIFA'nın resmî taktik verisiyle 48 takım, 10 stil metriği, 4 aile — kalın yazılanlar yarı finalist (4/4 mavi ailede)",
         fontsize=10.5, color=MUTED)
fig.text(0.05, 0.02,
         "Veri: FIFA Training Centre maç raporları (100 maç, takım başına ort. 4+ maç ortalaması). Metrikler: topa sahiplik, pas isabeti, line-break/pas,\n"
         "son üçlü bölge alışları, orta eğilimi, PPDA benzeri pres yoğunluğu, direkt pres payı, pres süresi, top geri kazanma süresi, pres yönü. PCA + k-means.",
         fontsize=7.5, color=MUTED)
fig.savefig(OUT / "tactical_map_2026.png", dpi=150)
print("Yazildi:", OUT / "tactical_map_2026.png")
