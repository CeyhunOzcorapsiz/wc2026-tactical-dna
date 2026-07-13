# -*- coding: utf-8 -*-
"""Taktik DNA: takim stillerini kumeler (2026 Dunya Kupasi).

Ozellikler kalite degil STIL olcer (iyi/kotu degil, nasil oynadigi):
 - topa sahip olma ve tempo, pas guvenligi, dikeylik, orta egilimi,
 - pres yogunlugu (PPDA benzeri), pres suresi/yonu, top geri kazanma.
Yontem: z-standardizasyon -> PCA (gorsellestirme) -> k-means (silhouette ile k).
Cikti: data/team_style_features.csv, data/team_clusters.csv + stdout ozet.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
FOOTBALL = ROOT.parent
DATA = ROOT / "data"

tm = pd.read_csv(DATA / "team_match_tactics.csv")

# rakip pas sayisini ekle (PPDA benzeri pres yogunlugu icin)
opp = tm[["match_number", "team", "passes"]].rename(
    columns={"team": "opponent", "passes": "opp_passes"})
tm = tm.merge(opp, on=["match_number", "opponent"], how="left")

# stil ozellikleri (mac duzeyinde), sonra takim ortalamasi
tm["directness"] = tm["line_breaks"] / tm["passes"]
tm["verticality"] = tm["final_third_receptions"] / tm["passes"]
tm["cross_share"] = tm["crosses"] / tm["final_third_receptions"]
tm["ppda_like"] = tm["opp_passes"] / tm["pressures"]  # dusuk = yogun pres
tm["direct_press_share"] = tm["direct_pressures"] / tm["pressures"]
tm["press_inside_share"] = tm["press_inside"] / (tm["press_inside"] + tm["press_outside"])

FEATURES = ["possession_pct", "pass_completion_pct", "directness",
            "verticality", "cross_share", "ppda_like", "direct_press_share",
            "press_duration_s", "recovery_time_s", "press_inside_share"]

team = tm.groupby("team").agg(
    n_matches=("match_number", "count"),
    **{f: (f, "mean") for f in FEATURES}).reset_index()
print(f"{len(team)} takim, ozellik eksigi olan takim: "
      f"{team[FEATURES].isna().any(axis=1).sum()}")
team = team.dropna(subset=FEATURES)

X = StandardScaler().fit_transform(team[FEATURES])

print("\nsilhouette skorlari:")
best_k, best_s = 2, -1
for k in range(2, 8):
    km = KMeans(n_clusters=k, n_init=25, random_state=42).fit(X)
    s = silhouette_score(X, km.labels_)
    print(f"  k={k}: {s:.3f}")
    if s > best_s:
        best_k, best_s = k, s
print(f"silhouette maksimumu k={best_k}")

# k=2 'kontrol vs reaktif' ana eksenini veriyor (bulgu olarak raporlanir);
# taktik AILELER icin k=4 kullanilir - silhouette farki kucuk,
# yorumlanabilirlik tercihi (metodolojide gerekcelendirildi).
FINAL_K = 4
km2 = KMeans(n_clusters=2, n_init=50, random_state=42).fit(X)
team["macro_cluster"] = km2.labels_
km = KMeans(n_clusters=FINAL_K, n_init=50, random_state=42).fit(X)
team["cluster"] = km.labels_

pca = PCA(n_components=2, random_state=42)
xy = pca.fit_transform(X)
team["pc1"], team["pc2"] = xy[:, 0], xy[:, 1]
print(f"\nPCA aciklanan varyans: {pca.explained_variance_ratio_.round(2)}")
print("PC1 yukleri:", dict(zip(FEATURES, pca.components_[0].round(2))))
print("PC2 yukleri:", dict(zip(FEATURES, pca.components_[1].round(2))))

# basari: elde edilen en ileri asama
wc = pd.read_csv(FOOTBALL / "wc2026_dataset" / "matches.csv")
teams_ref = pd.read_csv(FOOTBALL / "wc2026_dataset" / "teams.csv")
names = teams_ref.set_index("team_id")["team_name"]
wc["home"] = wc["home_team_id"].map(names)
wc["away"] = wc["away_team_id"].map(names)
long = pd.concat([wc[["stage_id", "home"]].rename(columns={"home": "team"}),
                  wc[["stage_id", "away"]].rename(columns={"away": "team"})])
team = team.merge(long.groupby("team")["stage_id"].max()
                  .rename("max_stage"), on="team", how="left")

print("\n=== Kumeler ===")
for c in sorted(team["cluster"].unique()):
    sub = team[team["cluster"] == c]
    print(f"\nKume {c} (n={len(sub)}), ort. asama={sub['max_stage'].mean():.1f}")
    print("  takimlar:", ", ".join(sorted(sub["team"])))
    prof = sub[FEATURES].mean() - team[FEATURES].mean()
    z = prof / team[FEATURES].std()
    top = z.abs().sort_values(ascending=False).head(4)
    for f in top.index:
        print(f"  {f}: {'+' if z[f] > 0 else ''}{z[f]:.1f} sd")

team.to_csv(DATA / "team_clusters.csv", index=False)
tm.to_csv(DATA / "team_style_features.csv", index=False)
print(f"\nYazildi: {DATA / 'team_clusters.csv'}")
