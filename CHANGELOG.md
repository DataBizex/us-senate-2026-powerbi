# Changelog

All notable changes to this data model are recorded here.
The machine-readable version is `docs/model-changelog.csv`.

## [3.1] — 2026-11-05

### Added
- Quality-check register rebuilt as additive: 51 checks, each carrying `origin_check` and a `lineage` value (Retained, Restored, Consolidated into, Superseded by, Resolved and retired). Twelve checks that had been dropped without a record were restored and re-run.
- `data/quality/model-rules.csv` — eight written rules, including the current-best observation selection rule.
- `race-quality-flags` dimension: `headline_eligible`, `margin_eligible`, `source_integrity_flag`, quality tier and exclusion reason per race.

### Changed
- Leading-candidate votes and race total are now presented as explicitly separate columns. The previous labelling allowed the two to be read as conflicting snapshots of one figure; they are different quantities from the same reading and reconcile exactly in every race.
- The money-against-outcome visual is labelled exploratory, states its n, encodes count quality by transparency and carries no trend line or correlation statistic.
- Every report page carries the collection date.

## [3.0] — 2026-11-05

### Added
- Official counts retrieved from six state election authorities: Virginia, Montana, Nebraska, Texas, West Virginia and Wyoming. All six reconcile exactly to their published totals.
- `fact-result-observation` — append-only observation history, 159 rows across two collection rounds.
- `winner-validation` — all 33 projected winners validated individually across four evidence tiers.
- `correction-register` — corrections with the original value retained.

### Changed
- Virginia replaced with its official count: 3,568,674 votes across 133 of 133 localities, against 23,140 previously captured.
- South Carolina incumbent identity corrected following a mid-cycle death and appointment.
- All 210 race ratings quarantined: `analysis_eligible = N`, excluded from every forecast measure.

### Fixed
- Texas's older official results system defaults to the 2024 general election. Its figures were identified and rejected.

## [2.0] — 2026-11-05

### Added
- `fact-candidate-result` — candidate-level results, one row per candidate per race.
- Projection, published count and certification split into separate column groups.
- Vote-count completeness flag.
- Data dictionary and entity relationship diagram.

## [1.0] — 2026-11-05

Initial model: races, ratings, race results, candidates, campaign finance, source register and quality checks.
