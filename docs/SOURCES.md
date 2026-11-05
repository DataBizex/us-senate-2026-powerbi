# Sources and licensing

Every fact row in this model carries a `source_id` that resolves to `data/dimensions/dim-source.csv`.
This file explains what each source contributed and, importantly, **what you may do with it**.

---

## Read this before publishing or redistributing

The sources in this model do not share one licence. Three groups behave differently.

### 1. United States government works — free to use

| Source | Used for |
|---|---|
| Federal Election Commission, candidate summary and candidate pages | Campaign finance, candidate IDs, committee IDs |
| State election authorities (VA, MT, NE, TX, WV, WY) | Official vote counts |
| US Census Bureau (county FIPS reference; ACS when loaded) | Geography keys, demographics |

Works of the US federal government are not subject to copyright in the United States. State election results are public records. These are the backbone of the model and are the parts you can redistribute most freely.

### 2. Wikipedia-derived — CC BY-SA 4.0, share-alike applies

`data/facts/fact-race-rating.csv` and parts of `data/dimensions/dim-race.csv` (race list, Senate class, PVI, incumbents) originate from the Wikipedia article on the 2026 United States Senate elections.

Wikipedia text is licensed **CC BY-SA 4.0**. That means attribution is required and derivative works carry the same licence. This repository attributes the source in `dim-source.csv` (`S02`) and in this file.

**Practical note:** the ratings table is also the weakest part of the model — all 210 rows are quarantined and unusable. If licensing complexity is unwelcome, dropping the ratings fact entirely costs you nothing analytically.

### 3. Media aggregator and news — verify before redistributing

| Source | Used for | Position |
|---|---|---|
| Ballotpedia, per-state election pages | Candidate-level counts for 27 races | **Check their reuse terms before redistributing these rows.** Facts such as vote totals are not themselves copyrightable, but a substantial extraction of a compiled database can raise separate issues. |
| CBS News results coverage | Projection times and projected winners | Only the underlying facts are used — who was projected and when. No text is reproduced. Attributed in `dim-source.csv` (`S03`). |
| Associated Press report | The South Carolina death, appointment and runoff result | Facts only, attributed in the correction register. |

**Recommended position.** Aggregator-derived counts are segregated in the observation table under `source_id = S10` and are already excluded from every headline figure. If you would rather publish without them, filter the observation table to `source_tier = "Official state election authority"` and the FEC data, and the repository remains coherent — you lose 27 unofficial counts and keep everything the model actually relies on.

---

## Source register

| ID | Source | Type | Contributed |
|---|---|---|---|
| S01 | FEC candidate summary 2025–2026 | Official | Candidate finance, FEC candidate IDs |
| S02 | Wikipedia, 2026 US Senate elections | Secondary, CC BY-SA 4.0 | Race list, class, PVI, incumbents, ratings |
| S03 | CBS News Senate results coverage | Media projection | Projected winners and call times |
| S04 | Ballotpedia, elections overview | Secondary | Superseded by S10 and S14 |
| S05 | Compiled national finance summary | Context | Not joined to any table |
| S06 | Census ACS 5-Year 2020–2024 | Official | Not retrieved — needs an API key |
| S07 | FEC bulk candidate and committee master | Official | Superseded for the ballot set by S13 |
| S08 | State election offices, certification | Official | Not available — no state had certified |
| S09 | Rating publishers (six) | Secondary | None reachable; all ratings unverified |
| S10 | Ballotpedia per-state Senate pages | Media aggregator | Candidate counts for 27 races |
| S11 | Census county FIPS reference file | Official | County geography keys |
| S12 | Associated Press report, 26 Aug 2026 | News | Basis of correction C01 |
| S13 | FEC candidate pages | Official | Principal and authorized committee IDs |
| S14 | State election authority results systems | **Official** | Official counts for six races |

---

## A note on provenance discipline

Two source behaviours in this project are worth knowing about if you reuse this material.

**A source can serve the wrong year by default.** Texas's older official results system opens on the 2024 general election. Nothing on the page warns you. Always confirm the election name shown on screen before reading figures.

**A source can publish a partial count without labelling it partial.** None of the aggregator pages published a percent-reporting figure. Virginia's capture held 0.65% of the eventual count and looked entirely normal. Internal consistency — candidate votes summing to the stated total — is not evidence of completeness.
