# Data quality

The machine-readable register is `data/quality/data-quality-checks.csv` — 51 checks, each with a category, severity, lineage and recommended resolution.

## Summary

| Result | Count |
|---|---|
| PASS | 33 |
| WARN | 12 |
| FAIL | 6 |

| Severity | Count |
|---|---|
| Info (passing) | 33 |
| Low | 4 |
| Medium | 8 |
| High | 6 |

## Check lineage

Checks are never silently dropped between versions. Every check carries an `origin_check` and a `lineage` value:

| Lineage | Count | Meaning |
|---|---|---|
| Retained | 12 | Carried forward unchanged |
| **Restored in v3.1** | 15 | Dropped from an earlier register without a record; restored and re-run |
| New in v3 | 12 | Added with the official-source retrieval |
| New in v3.1 | 2 | Added with the written model rules |
| Consolidated into… | 4 | Merged into a named successor check |
| Superseded by… | 3 | Replaced by a register or dictionary entry |
| Resolved and retired | 1 | The condition no longer exists |

Restoring the dropped checks surfaced two findings the register had stopped reporting: Idaho's unknown FEC party, and the absence of filing dates on all finance rows.

## What passes

- Candidate votes sum to the published race total in **every** counted race, including all six official-source states.
- All 33 projected winners validated; every one agrees with the published count on the winning party.
- Each projected winner's FEC record is a Senate filing in the same state as the race.
- No historical result is used as a 2026 value.
- Every fact row carries a source and an observation time.
- Earlier observations preserved rather than overwritten.

## What fails, and why

| Check | Severity | Why |
|---|---|---|
| Official sources for all priority races | High | 6 of 9 obtained. Massachusetts, Illinois and Rhode Island unreachable or unpublished. |
| No race on a clearly partial count | High | 3 remain: MA, IL, RI. |
| Any rating verified at its publisher | High | 0 of 210. All six publishers unreachable. |
| Ratings excluded from forecast measures | High | Enforced — this "failure" is the safeguard working. |
| One reporting period across all filers | High | 108 of 619. A property of the FEC source, not an error. |
| ACS demographic layer loaded | High | Needs a free Census API key. |

## Unresolved issues

Twelve issues are tracked in `data/quality/unresolved-issues.csv`, each with its cause and the action that would close it. The ones that matter most:

1. **MA, IL and RI counts are partial.** Excluded from every headline figure. Clears when the state sources publish.
2. **All 210 ratings unverified.** Quarantined. Clears when each value and its publication date are re-collected from the publisher.
3. **ACS layer not loaded.** Clears with a free Census API key and `scripts/refresh_acs_and_fec.py`.
4. **Montana carries a `TEST` marker.** Excluded from headline figures. Clears on confirmation from the Montana Secretary of State.
5. **No race certified.** Clears after each state's canvass.
