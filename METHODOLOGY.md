# Methodology

## 1. Source and extraction

**Source:** FIFA Training Centre post-match summary reports (100 PDFs,
group + knockout hubs), the same corpus as the companion
[climate project](https://github.com/CeyhunOzcorapsiz/wc2026-climate-analysis).

Numeric glyphs in these PDFs use a Private-Use-Area font mapping
(U+E071…U+E07A = digits 0–9, U+E094 = decimal point) and are invisible to
standard text extraction. All parsers decode this mapping and validate
every extracted row.

**Pages parsed:**
- *Match Summary – Key Statistics*: possession (incl. contested), xG,
  attempts, passes and completion, completed/defensive line breaks,
  final-third receptions, crosses, ball progressions, defensive pressures
  (direct), forced turnovers, second balls, distance.
- *Defensive Pressure*: average pressure duration, ball-recovery time,
  pushing-on counts, pressing direction (inside/outside).
- *Line Breaks (per player)*: attempts, completions, direction
  (through/around/over), vehicle (pass/cross/carry).
- *Attempts at Goal (per shot)*: minute, player, outcome, body part,
  delivery type (pass/cross/corner/freekick/penalty/loose ball/other).

**Validation:** direction sums ≡ attempts for 100% of 3,159 player-match
rows; parsed goals ≡ official scores for 100/100 matches; match identity
established by report-header date + team pair (FIFA match numbers do NOT
equal third-party dataset ids). Goalkeeper identification uses FIFA's
row ordering (keeper listed first), spot-checked against known keepers.

## 2. Style features and clustering

Ten features chosen to measure *how* a team plays rather than how well:
possession %, pass completion %, directness (line breaks / pass),
verticality (final-third receptions / pass), cross share, PPDA-like
pressing intensity (opponent passes / pressures), direct-press share,
press duration, recovery time, press-inside share. Team = mean over its
matches (4–7 per team); z-standardised; k-means with silhouette scan.

Silhouette favours **k = 2**, a control-vs-reactive macro axis (the
control side averaged ~1.5 rounds deeper). **k = 4** is reported for
interpretability; both labelings are in `data/team_clusters.csv`.

## 3. Statistical notes and exclusions

- **Game-state confounding:** full-match aggregates mean leading teams
  concede possession; associations between pressing/possession
  differentials and winning are reported as descriptive, not causal.
- **Opponent-quality confounding:** the group-vs-knockout comparison uses
  within-team paired tests, but knockout opponents are systematically
  stronger; interpreted as "knockout matches are more transitional",
  not "teams choose caution".
- **Excluded for insufficient data** (by design, not omission):
  family-vs-family match-up cells with <10 matches (the 5-team vertical
  hunters family has only 2 intra-family matches), and the style-volatility
  analysis (null result with n = 48 and high estimator variance).
- Multiple comparisons: findings are screened at p < 0.05 but presented
  with exact p-values and sample sizes; treat borderline results as
  suggestive.

## 4. Known limitations

Aggregates hide within-match dynamics; no event-level timestamps; block
height diagrams (meters) not parsed (layout too ambiguous); goalkeeper
distribution pages not parsed for the same reason. 48 teams is a small
cross-section for team-level correlations; effect sizes are reported with
confidence context rather than headline certainty.
