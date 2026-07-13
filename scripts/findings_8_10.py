# -*- coding: utf-8 -*-
"""Bulgular 8-10: kaleci oyun kurma, duran top payi, line-break anatomisi."""
from pathlib import Path
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

ALIAS = {"Korea Republic": "South Korea", "United States": "USA",
         "Czech Republic": "Czechia",
         "Bosnia-Herzegovina": "Bosnia and Herzegovina"}
CLUSTER_NAMES = {0: "Kontrolcu baskicilar", 1: "Derin blok reaktifler",
                 2: "Dikey avcilar", 3: "Dengeli pragmatikler"}

lb = pd.read_csv(DATA / "player_line_breaks.csv")
sh = pd.read_csv(DATA / "shot_details.csv")
cl = pd.read_csv(DATA / "team_clusters.csv")[["team", "cluster", "max_stage"]]
for df in (lb, sh):
    df["team"] = df["team"].replace(ALIAS)

# ---------------- 8: Kaleci oyun kurma ----------------
print("=" * 60)
print("8) KALECI OYUN KURMA — tablodaki ilk satir = kaleci (FIFA siralamasi)")
gk = lb.groupby(["match_number", "team"]).first().reset_index()
print("ornek kaleciler (dogrulama):",
      ", ".join(gk["player"].head(6)))
gk_team = gk.groupby("team").agg(
    gk_lb_per_match=("lb_attempted", "mean"),
    gk_completion=("lb_completed", "sum"),
    gk_attempts=("lb_attempted", "sum")).reset_index()
gk_team["gk_completion_pct"] = 100 * gk_team["gk_completion"] / gk_team["gk_attempts"]
gk_team = gk_team.merge(cl, on="team")
print("\nkume basina kaleci line-break denemesi / mac:")
g = gk_team.groupby("cluster")["gk_lb_per_match"].mean()
for c, v in g.items():
    print(f"  {CLUSTER_NAMES[c]:24s} {v:.1f}")
rho, p = stats.spearmanr(gk_team["gk_lb_per_match"], gk_team["max_stage"])
print(f"kaleci katilimi vs ulasilan asama: rho={rho:+.2f} p={p:.3f}")
top = gk_team.nlargest(5, "gk_lb_per_match")[["team", "gk_lb_per_match"]]
bot = gk_team.nsmallest(5, "gk_lb_per_match")[["team", "gk_lb_per_match"]]
print("en oyun kurucu GK'ler:", ", ".join(f"{r.team} {r.gk_lb_per_match:.1f}" for r in top.itertuples()))
print("en az katilanlar:", ", ".join(f"{r.team} {r.gk_lb_per_match:.1f}" for r in bot.itertuples()))

# ---------------- 9: Duran top payi ----------------
print("\n" + "=" * 60)
print("9) DURAN TOP — gol kaynaklari")
sh["set_piece"] = sh["delivery"].isin(["Corner", "Freekick", "Penalty"])
goals = sh[sh["is_goal"] == 1]
print(f"toplam gol (sut sayfalarindan): {len(goals)}")
print(goals["delivery"].value_counts().to_string())
sp_share = goals["set_piece"].mean()
print(f"duran top payi (penalti dahil): %{100*sp_share:.1f}")
print(f"penalti haric: %{100*goals[goals['delivery']!='Penalty']['set_piece'].mean():.1f}")
tg = goals.merge(cl, on="team")
print("\nkume basina duran top gol payi:")
for c, grp in tg.groupby("cluster"):
    print(f"  {CLUSTER_NAMES[c]:24s} %{100*grp['set_piece'].mean():.0f}  ({grp['set_piece'].sum():.0f}/{len(grp)})")
tt = goals.groupby("team")["set_piece"].agg(["mean", "sum", "count"])
dep = tt[tt["count"] >= 4].nlargest(5, "mean")
print("duran topa en bagimli takimlar (>=4 gol):",
      ", ".join(f"{t} %{100*r['mean']:.0f}" for t, r in dep.iterrows()))
# korner verimi
corners_shots = sh[sh["delivery"] == "Corner"]
print(f"\nkorner kaynakli sut: {len(corners_shots)}, gol: {corners_shots['is_goal'].sum()} "
      f"(donusum %{100*corners_shots['is_goal'].mean():.1f})")

# ---------------- 10: Line-break anatomisi ----------------
print("\n" + "=" * 60)
print("10) LINE-BREAK ANATOMISI — bloklar nasil kirildi?")
tm = lb.groupby(["match_number", "team"])[
    ["lb_attempted", "lb_completed", "through", "around", "over",
     "via_pass", "via_cross", "via_carry"]].sum().reset_index()
team = tm.groupby("team").mean(numeric_only=True).reset_index().merge(cl, on="team")
for col in ["through", "around", "over"]:
    team[col + "_share"] = team[col] / team["lb_attempted"]
for col in ["via_pass", "via_cross", "via_carry"]:
    team[col + "_share"] = team[col] / team["lb_attempted"]
team["lb_success"] = team["lb_completed"] / team["lb_attempted"]
print("turnuva geneli: aradan %{:.0f}, etrafindan %{:.0f}, ustunden %{:.0f}".format(
    100 * team["through_share"].mean(), 100 * team["around_share"].mean(),
    100 * team["over_share"].mean()))
print("arac: pas %{:.0f}, orta %{:.0f}, tasima %{:.0f}".format(
    100 * team["via_pass_share"].mean(), 100 * team["via_cross_share"].mean(),
    100 * team["via_carry_share"].mean()))
print("\nkume profilleri (pay %):")
cols = ["through_share", "around_share", "over_share", "via_carry_share", "lb_success"]
prof = team.groupby("cluster")[cols].mean()
prof.index = [CLUSTER_NAMES[c] for c in prof.index]
print((100 * prof).round(0).to_string())
rho, p = stats.spearmanr(team["through_share"], team["max_stage"])
print(f"\n'aradan kirma' payi vs asama: rho={rho:+.2f} p={p:.3f}")
rho, p = stats.spearmanr(team["lb_success"], team["max_stage"])
print(f"line-break isabeti vs asama: rho={rho:+.2f} p={p:.3f}")

team.to_csv(DATA / "team_line_break_profile.csv", index=False)
gk_team.to_csv(DATA / "gk_buildup.csv", index=False)
print("\nYazildi: team_line_break_profile.csv, gk_buildup.csv")
