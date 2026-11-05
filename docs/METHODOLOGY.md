# Methodology

## Grain

| Table | One row is |
|---|---|
| `dim-state` | one US state |
| `dim-race` | one Senate seat contested in 2026 (35) |
| `dim-candidate` | one person who filed with the FEC for a 2026 Senate race (619) |
| `race-quality-flags` | one race, with its evidence classification (35) |
| `fact-race-result` | one race, with four evidence tiers side by side (35) |
| `fact-candidate-result` | one candidate's result in one race, current best evidence (169) |
| `fact-result-observation` | one candidate's votes, from one source, at one time (159, append-only) |
| `fact-candidate-finance` | one FEC candidate ID's money for its reporting period (619) |
| `fact-race-rating` | one publisher's rating of one race (210, all quarantined) |

## Source hierarchy

Strongest evidence first. A lower tier is never used when a higher one exists for the same race, and the superseded observation is always kept.

1. **Certified state result** — none exists yet.
2. **Official state election authority, unofficial count** — 6 races.
3. **Media aggregator count** — 27 races.
4. **Media projection only** — 0 races now rest on this alone.
5. **Pending** — 2 races, still uncalled.

## Current-best selection rule

When more than one observation exists for a race, the current-best row is chosen by:

1. **Source tier** — official state election authority outranks media aggregator.
2. **Completeness** — more reporting units outranks fewer.
3. **Recency** — only as a tie-breaker.

A later timestamp alone never promotes a record. A newer aggregator capture does not displace an older official count.

## Calculation rules

- **Headline eligibility.** A race enters headline and margin figures only when it carries a complete count from the state election authority *and* no source integrity flag. Three races qualify: Texas, Virginia, Wyoming.
- **Integrity flags override completeness.** Montana's results page carries an unexplained `TEST` marker. It is excluded from every headline figure regardless of how complete its count is, because completeness says nothing about whether a source is a production system.
- **Vote share** is candidate votes divided by the published race total, and reconciles to each source's own published percentages within 0.15 points on every row that has both.
- **Overvotes and undervotes are never counted as votes.** Wyoming publishes 70 and 3,325 respectively; both are excluded from the race total.
- **Seat totals** add 34 Democratic-caucus seats not contested in 2026 (45 D + 2 I − 13 D seats up). This is a constant with a single source and is documented wherever it appears.
- **Leading votes and race total are distinct quantities.** `leading_votes` is one candidate's votes; `race_total_votes` is every candidate added together. They are never alternatives for the same figure.

## Reporting-period limits

FEC candidate totals cover different periods by candidate. Only **108 of 619** filers report through 14 October 2026, and 286 state no period at all. Money is comparable only within one `comparability_cohort`.

Finance covers to 14 October at the latest; results are from 3–4 November. The two are separate facts and are never summed or presented as one period. Any relationship between money and outcome is association, not causation.

FEC candidate totals already aggregate a candidate's authorized committees, so summing by candidate cannot double-count. Rebuilding those totals from committee-level files without removing internal transfers would — 79 filers report such transfers, $200.4M in total.

**Excluded from candidate money by design:** leadership PACs, party committees and independent expenditures. None of it is received by the candidate.

## Known exceptions

| Race | Exception |
|---|---|
| South Carolina | Senator Lindsey Graham died 11 July 2026; his sister Darline Graham was appointed and won the nomination. The race table is corrected; original values retained. |
| Maine | Ranked-choice voting. Figures are round-one counts; the winner cleared 50% in round one. |
| Nebraska | Dan Osborn ran by petition, not as a party nominee. |
| Ohio | The FEC reports Sherrod Brown's 2025–26 activity under a PAC that is not an authorized committee, so his candidate total may understate. |
| Wyoming | Overvotes and undervotes are published separately and excluded here. |
| Texas | The state's older results system defaults to the 2024 election; its figures were rejected. |
| Idaho | The FEC lists the incumbent's party as `UNK`. The ballot party is used for display. |
| Oregon | Fusion ballot labels (two parties for one candidate). Group on `party_group`, not the published label. |

## What blank means

Blank means the source published no value. Nothing in this model is estimated, interpolated, or carried over from another election year. A blank reporting period in the finance table means no activity was reported — it does not mean zero raised.
