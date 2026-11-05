# Building the Power BI report

The report is eight pages. `build-sheet.html` draws every page at true pixel size (1280×720) with each object's exact X / Y / Width / Height, its Power BI visual type, and its field and measure bindings. Open it in a browser alongside Power BI Desktop and work through it page by page.

## Order of work

**1. Canvas.** New file. Page 1 → Format page → Canvas settings → Type **Custom**, Width **1280**, Height **720**. Custom pins the size; the default "16:9" rescales when the aspect ratio changes.

**2. Parameter.** Home → Manage Parameters → New. Name `SourceFolder`, type Text, value = this repository's `data` folder. One place repoints the whole model.

**3. Queries.** Create the queries in `powerbi/power-query.m`, starting with `fnLoad`. The script keeps `state_fips`, `county_fips` and every ID column as **text** — typing them as numbers destroys leading zeros on states 01–09.

**4. Relationships.** Build the list in `build-sheet.html`. One is load-bearing:

> `DimRace[race_id]` ↔ `RaceQualityFlags[race_id]` must filter **both** directions.

Without it the quality flags cannot reach the result facts, and every headline measure silently returns all 35 races instead of the 3 that qualify. This is the single setting that would break the safety model without any visible error.

**5. Measures.** Create a blank query named `_Measures`, load it, hide its placeholder column, then paste `powerbi/measures.dax` — 72 measures.

**6. Pages.** Build from the build sheet. Page 3 is a drillthrough page on `DimRace[race_id]`.

## Rules to hold while building

- **Never place `margin_pct` on a visual without the `margin_eligible` filter.** It is the one number a reader will quote, and only three races support it.
- **Rename two columns on any results table.** `leading_votes` → "Leader's votes", `race_total_votes` → "All candidates (race total)". Power BI's defaults put "Total votes" beside a leader's name, which reads as that leader's total.
- **Keep the reporting-period slicer set** on the finance page, with its default cohort. Removing it puts five different reporting windows on one chart.
- **Repeat the snapshot banner on all eight pages.**
- **Leave the forecast and demographics pages empty.** Their measures return blank by design, so the pages show their banners rather than a plausible wrong number.

## Pages

| # | Page | Purpose |
|---|---|---|
| 1 | National Overview | KPIs, quality strip, quality-coloured map, official counts |
| 2 | State Map | Map at full size, margin ranking restricted to eligible races, exclusions table |
| 3 | Race Profile | Drillthrough: status strip, candidate results, observation history |
| 4 | Candidate Finance | Reporting-period filter first, top filers, exploratory money-outcome view |
| 5 | Forecast Performance | Built, deliberately empty — ratings quarantined |
| 6 | Demographics | Built, deliberately empty — awaiting ACS data |
| 7 | Data Quality and Sources | Quality score, checks, unresolved issues, source register |
| 8 | Methodology | Grain, source hierarchy, calculation rules, exceptions |

## After the first build

Save the file as **`.pbip`** (Power BI Project), not only `.pbix`. The project format writes the model and report definition as text files, which version properly in git. `.pbix` is a binary and is gitignored here.
