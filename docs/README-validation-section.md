## Validating the data model

The quality register in `data/quality/data-quality-checks.csv` documents the checks; the suite under `tests/` re-runs them against the CSV files on every invocation. It reads `data/` and never writes to it.

### Run it

Requires Python 3.11 or later, pandas and pytest.

```bash
make install    # pip install -r requirements-dev.txt
make validate   # run every check
make validate-verbose   # list each check as it runs
```

Without `make` (for example on Windows), run the same commands directly:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
```

A clean run ends with `N passed` and nothing failed. A failing check prints each offending row with its CSV line number and the value that broke the rule.

### What it checks

| Rule | Test file | Register |
|---|---|---|
| Every foreign key resolves: `race_id`, `fec_cand_id`, `state_fips`, `source_id`, `rater`; primary keys are unique and the row counts match the grain in `docs/METHODOLOGY.md` | `test_referential_integrity.py` | Q01–Q04, Q06 |
| Candidate votes sum exactly to `race_total_votes` in every counted race, in both the current-best table and every snapshot in the observation log; race and candidate totals agree; overvotes and undervotes are never vote rows | `test_vote_totals.py` | Q18, Q23, Q45, R04 |
| `headline_eligible` is `Y` only where the count is from an official state source, reporting units are complete and `source_integrity_flag` is `N` — and every race meeting those conditions is `Y`. The result must be Texas, Virginia and Wyoming | `test_eligibility.py` | R02, R03, Q51 |
| `analysis_eligible` is `N` on every row of `fact-race-rating.csv` | `test_eligibility.py` | Q33 |
| No file contains a value from an election year other than 2026 | `test_election_year.py` | Q49 |
| `state_fips` and every ID column are text with leading zeros intact, in the file and as loaded; FIPS codes match the Census codes | `test_text_ids.py` | Q05 |

Headline eligibility is proven from evidence outside `race-quality-flags.csv`: the source type in `dim-source.csv` of every candidate row, the official count status, and the published reporting-units text (every "N of M" must have N = M). A mislabelled flag cannot vouch for itself.

`test_check_functions.py` runs each check on small synthetic tables containing a deliberate breach, to prove the checks can fail.

Tests carry a `register` marker naming the check or rule they re-run. Collection stops with an error if a marker names an ID that is not in `data-quality-checks.csv` or `model-rules.csv`.

### Configuration

Paths, key relationships and expected values live in `config/validation.toml`, not in test code. Set `SENATE_VALIDATION_CONFIG` to run the suite against another copy of the model.

The suite fails if a CSV is added under `data/` without a `[tables]` entry, or if a column whose name contains an `id`, `ids` or `fips` token has no format under `[text_ids.formats]`, so new files and keys cannot slip past unchecked.

### The election-year rule

Every cell is scanned for four-digit years and `m/d/yy` dates. An even year other than 2026 fails; odd years are not election years, so 2025 activity in the 2026 FEC cycle passes. Numeric measures such as vote counts and dollar amounts are not read as years.

Some columns legitimately hold other years, and each is exempted in the config with a reason: incumbents' first-elected year, original values kept in the correction register, ACS 2020–2024 and Census 2020 reference vintages, an FEC committee name, and notes recording that older-election content was seen and rejected.

Five finance rows are listed as known exceptions: their FEC 2026-cycle reporting period opens in October–December 2024, because the FEC starts a committee's first report of a cycle the day after its previous report closed. Each exception is pinned to a filer ID, and the suite fails if an exception stops matching, so the list cannot go stale. Delete the entry to make the rule strict.

### Layout

```
config/validation.toml          paths, keys and expected values
src/senate_validation/
    config.py                   loads the config and resolves paths
    tables.py                   read-only CSV access, every cell as text
    checks/keys.py              primary keys, grain, foreign keys
    checks/votes.py             vote reconciliation
    checks/eligibility.py       headline eligibility, rating quarantine
    checks/election_year.py     election-year scan
    checks/text_ids.py          text IDs and leading zeros
tests/                          one pytest module per rule family
Makefile                        install, validate, validate-verbose
```

Each check function returns a list of violations, so the checks can also be called from a notebook or script without pytest.
