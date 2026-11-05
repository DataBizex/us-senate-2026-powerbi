# US Senate 2026 — election data model and Power BI report

A validated data model of the **3 November 2026 United States Senate elections**, built so that incomplete, conflicting or unverified evidence cannot be mistaken for a final result.

The interesting part of this project is not the election. It is the handling of evidence that arrives in pieces, from sources of unequal authority, at different times, some of it wrong.

---

## What this contains

| | |
|---|---|
| **Races** | 35, including the Florida and Ohio special elections |
| **Model** | Star schema: 7 dimensions, 5 fact tables |
| **Candidate results** | 169 rows, one per candidate per race |
| **Observation history** | 159 append-only observations across 2 collection rounds |
| **Campaign finance** | 619 FEC filers, joined by candidate ID and committee ID |
| **Quality checks** | 51, each with severity, lineage and a recommended resolution |
| **Automated tests** | 238, re-running those checks against the CSV files |
| **Snapshot date** | 5 November 2026 — a dated research snapshot, not a live tracker |

---

## The problem this model solves

Election data in the days after a vote is a moving target. Different sources disagree, some publish partial counts without saying so, and nothing is certified for weeks. A dashboard built naively on that data will state a margin to two decimal places that is simply wrong.

Three mechanisms prevent that here.

**1. Evidence is tiered, and the tier is stored.** Every race carries four independent columns: a media projection, an aggregator count, an official state count, and a certification status. They are never merged into one "result" field. A `race-quality-flags` table then classifies each race, and `headline_eligible` gates every measure a reader might quote.

**2. Only complete official counts qualify for a margin.** Three of thirty-five races currently pass: Texas, Virginia and Wyoming. Everywhere else the margin measure returns **"Not reportable"** rather than a number. Montana is excluded from all headline figures regardless of completeness, because its official results page carries an unexplained `TEST` marker.

**3. Observations are append-only.** When an official count supersedes an earlier aggregator capture, both rows survive. The current-best row is selected by a written rule — source tier first, then completeness, then recency — so a newer but weaker source can never displace a stronger older one.

---

## What the data showed

- **Virginia's aggregator count was 0.65% of the real one.** The capture read 23,140 votes; the Commonwealth's own system reported 3,568,674 across 133 of 133 localities. Three more states remain in that condition and are flagged, not published.
- **A source defaulted to the wrong election.** Texas's older official results system opens on the 2024 general election. Its 11.3 million-vote Senate race would have passed silently as a 2026 figure. It was identified and rejected; the current system was used instead.
- **An incumbent identity was wrong at the source.** A race table built from a June snapshot named the wrong sitting senator for South Carolina after a mid-cycle death and appointment. Three independent sources resolved it; the original value is retained in a correction register rather than overwritten.
- **No race rating could be verified.** All 210 pre-election forecasts are quarantined — none could be confirmed at its publisher and three are contradicted by a later source. The forecast page exists but is deliberately empty.
- **All 33 projected winners were validated individually**, six against the state's own election system. Every one agrees with the published count on the winning party.

---

## Validating the model

The register in `data/quality/data-quality-checks.csv` documents the checks. The suite under `tests/` makes them executable, re-running them against the CSV files themselves. It reads `data/` and never writes to it.

```bash
pip install -r requirements-dev.txt
pytest
```

238 tests across six modules:

| Module | What it enforces |
|---|---|
| `test_referential_integrity.py` | every foreign key resolves, including multi-value and nullable keys |
| `test_vote_totals.py` | candidate votes sum exactly to the published race total |
| `test_eligibility.py` | `headline_eligible` is derived from the evidence, not taken on trust |
| `test_election_year.py` | no value from any election year other than 2026 |
| `test_text_ids.py` | FIPS and ID columns remain text, with leading zeros intact |
| `test_check_functions.py` | each check is shown to fail on synthetic broken data |

That last module matters most. A validation suite that has never been observed failing proves nothing, so each check is exercised against data designed to break it, and the whole suite was run against a deliberately corrupted copy of `data/` — a dropped leading zero on a FIPS code, an added vote, a flipped eligibility flag, a rating marked analysis-eligible, a misspelled rater, an observation re-dated to 2024. Every break was caught and reported with its CSV line number.

Each test is tagged with the check or rule ID it re-runs (`Q18`, `R02` and so on), and an unrecognized ID fails the run, so the tests and the register cannot drift apart. `config/validation.toml` holds every path, key and expected value; a new CSV or ID column that is not registered there fails the suite rather than being silently ignored.

**Documented exceptions.** Five filers carry 2026-cycle reporting periods that open in October–December 2024, which is how the FEC numbers its cycles. They are allowed through by filer ID, and the suite fails if one stops matching. Odd calendar years pass, since the 2026 FEC cycle opens in January 2025; even years other than 2026 fail. Columns legitimately holding earlier years — incumbents' first-elected year, the correction register's original values, ACS 2020–2024 and Census 2020 references, and notes recording older data being rejected — are exempted individually with a written reason.

---

## Repository layout

```
data/
  dimensions/        state, race, candidate, rater, source, result status, quality flags
  facts/             race result, candidate result, observation history, finance, ratings
  quality/           51 checks, model rules, corrections, validations, unresolved issues
  us-senate-2026-model.xlsx    all tables in one workbook
docs/
  build-sheet.html         pixel-level layout for all 8 report pages
  data-model-diagram.html  entity relationship diagram
  report-preview.html      visual preview of the finished report
  data-dictionary.csv      264 fields: grain, type, unit, meaning
  METHODOLOGY.md           grain, source hierarchy, calculation rules, exceptions
  SOURCES.md               full source register and licensing
  DATA-QUALITY.md          what passes, what fails, what is unresolved
  BUILD-GUIDE.md           how to build the Power BI report from this model
powerbi/
  power-query.m            typed load script for every table
  measures.dax             72 measures, including the exclusion rules
src/senate_validation/     one module per group of checks, callable without pytest
tests/                     238 tests, each tagged with the check ID it re-runs
config/validation.toml     paths, keys, expected values and documented exceptions
scripts/
  refresh_acs_and_fec.py   fills the two layers that need an API key
```

---

## Reproducing the report

1. Clone the repository.
2. Open Power BI Desktop and create a text parameter `SourceFolder` pointing at this repo's `data` folder.
3. Create the queries in `powerbi/power-query.m`, beginning with `fnLoad`.
4. Build the relationships listed in `docs/build-sheet.html`. Set `DimRace` ↔ `RaceQualityFlags` to filter **both** directions — without it the quality flags cannot reach the result facts and every headline measure silently returns all 35 races.
5. Paste the measures from `powerbi/measures.dax` into a `_Measures` table.
6. Build the eight pages from `docs/build-sheet.html`, which gives every object's exact position, visual type and field bindings.

---

## Known limitations

This model is deliberately explicit about what it cannot support.

- Only 3 of 35 races carry a count complete enough for a margin figure.
- Massachusetts, Illinois and Rhode Island rest on partial counts; their official sources were unreachable or had not published.
- Alaska and Mississippi were still uncalled at collection.
- No race is certified. Certification follows each state's canvass.
- The demographic layer is not loaded; it needs a free Census API key.
- Campaign finance covers to 14 October 2026 while results are from 3 November. The relationship between money and outcome is **association at best**, and the comparable reporting cohort is 108 of 619 filers.

Twelve open issues are tracked in `data/quality/unresolved-issues.csv` with their cause and the action that would close each one.

---

## License

Code, model definitions and documentation: **MIT** (see `LICENSE`).

Data files carry the terms of their upstream sources. See `docs/SOURCES.md` for the per-source position before redistributing.

---

## Author

**Ali Soltanhosseini** — Data Analyst
[databizex.com](https://databizex.com) · [LinkedIn](https://linkedin.com/in/ali-soltanhosseini-aut) · [GitHub](https://github.com/DataBizex) · a.soltanhosseini@gmail.com
