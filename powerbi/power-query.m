// ============================================================
// US Senate 2026 - Power BI data load
// Paste each named block into its own blank query
// (Home > Transform data > New Source > Blank Query > Advanced Editor).
// Create the SourceFolder parameter FIRST.
// ============================================================

// ---- 1. PARAMETER: SourceFolder --------------------------------
// Home > Manage Parameters > New Parameter
//   Name: SourceFolder   Type: Text
//   Current Value: D:\portfolio\us-senate-2026-powerbi\data
//   (the repo's data folder; queries address files as "dimensions/..." and "facts/...")
// Every query below reads from it, so the whole model repoints by editing one value.

// ---- 2. QUERY: fnLoad (function) -------------------------------
// Name this query exactly: fnLoad
let
    fnLoad = (FileName as text) as table =>
        let
            Path   = SourceFolder & "\" & Text.Replace(FileName, "/", "\"),
            Source = Csv.Document(
                         File.Contents(Path),
                         [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
                     ),
            Headers = Table.PromoteHeaders(Source, [PromoteAllScalars = true])
        in
            Headers
in
    fnLoad

// ---- 3. QUERY: DimState ----------------------------------------
let
    T = fnLoad("dimensions/dim-state.csv"),
    // state_fips stays TEXT: typing it as a number destroys the leading zero on 01-09
    Typed = Table.TransformColumnTypes(T, {
        {"state_fips", type text}, {"state_postal", type text},
        {"state_name", type text}, {"has_2026_senate_race", type text}})
in
    Typed

// ---- 4. QUERY: DimRace -----------------------------------------
let
    T = fnLoad("dimensions/dim-race.csv"),
    Typed = Table.TransformColumnTypes(T, {
        {"race_id", type text}, {"state_fips", type text}, {"state_postal", type text},
        {"state_name", type text}, {"senate_class", Int64.Type},
        {"is_special_election", type text}, {"election_date", type date},
        {"incumbent_name", type text}, {"incumbent_party", type text},
        {"incumbent_fec_cand_id", type text}, {"incumbent_running", type text},
        {"pvi_numeric_dem_positive", type number}, {"seat_party_before", type text}})
in
    Typed

// ---- 5. QUERY: DimCandidate ------------------------------------
let
    T = fnLoad("dimensions/dim-candidate.csv"),
    Typed = Table.TransformColumnTypes(T, {
        {"fec_cand_id", type text}, {"race_id", type text},
        {"candidate_name_fec", type text}, {"party_fec", type text},
        {"party_group", type text}, {"ico_status_fec", type text},
        {"state_postal", type text}, {"office", type text},
        {"receipts_rank_in_race", Int64.Type}})
in
    Typed

// ---- 6. QUERY: RaceQualityFlags --------------------------------
let
    T = fnLoad("dimensions/race-quality-flags.csv"),
    Typed = Table.TransformColumnTypes(T, {
        {"race_id", type text}, {"state_postal", type text}, {"state_name", type text},
        {"quality_tier", type text}, {"quality_rank", Int64.Type},
        {"quality_color", type text}, {"headline_eligible", type text},
        {"margin_eligible", type text}, {"source_integrity_flag", type text},
        {"count_source_tier", type text}, {"exclusion_reason", type text},
        {"last_updated_display", type text}, {"status_label_display", type text},
        {"evidence_status", type text}, {"certified", type text}})
in
    Typed

// ---- 7. QUERY: FactRaceResult ----------------------------------
let
    T = fnLoad("facts/fact-race-result.csv"),
    Typed = Table.TransformColumnTypes(T, {
        {"race_id", type text}, {"state_postal", type text}, {"state_fips", type text},
        {"state_name", type text}, {"projection_status", type text},
        {"projected_winner_name", type text}, {"projected_winner_party", type text},
        {"projected_winner_fec_cand_id", type text}, {"projection_called_by", type text},
        {"official_count_status", type text}, {"official_status_label", type text},
        {"official_last_updated", type text}, {"certification_status", type text},
        {"best_evidence_tier", type text}, {"leading_candidate_name", type text},
        {"leading_candidate_party", type text}, {"leading_candidate_fec_cand_id", type text},
        {"race_total_votes", Int64.Type}, {"leading_votes", Int64.Type},
        {"margin_votes", Int64.Type}, {"margin_pct", type number},
        {"margin_safe_to_use", type text}, {"count_completeness", type text},
        {"sources_agree", type text}, {"seat_party_before", type text},
        {"flip_flag", type text}, {"is_special_election", type text}})
in
    Typed

// ---- 8. QUERY: FactCandidateResult -----------------------------
let
    T = fnLoad("facts/fact-candidate-result.csv"),
    Typed = Table.TransformColumnTypes(T, {
        {"candidate_result_id", type text}, {"race_id", type text},
        {"state_postal", type text}, {"state_fips", type text},
        {"candidate_name", type text}, {"party_as_published", type text},
        {"party_group", type text}, {"row_type", type text},
        {"fec_cand_id", type text}, {"candidate_votes", Int64.Type},
        {"race_total_votes", Int64.Type}, {"vote_share", type number},
        {"vote_share_pct", type number}, {"published_percent", type number},
        {"is_leading_candidate", type text}, {"result_status", type text},
        {"result_tier", type text}, {"count_completeness", type text},
        {"reporting_units", type text}, {"certified", type text},
        {"source_id", type text}, {"source_observed_at", type text}})
in
    Typed

// ---- 9. QUERY: FactResultObservation ---------------------------
// The append-only history. Never edited, only added to.
let
    T = fnLoad("facts/fact-result-observation.csv"),
    Typed = Table.TransformColumnTypes(T, {
        {"observation_id", type text}, {"race_id", type text}, {"state_postal", type text},
        {"candidate_name_as_published", type text}, {"party_as_published", type text},
        {"candidate_votes", Int64.Type}, {"published_percent", type number},
        {"race_total_votes", Int64.Type}, {"source_id", type text},
        {"observed_at", type text}, {"status_label_as_published", type text},
        {"reporting_units_as_published", type text}, {"source_tier", type text},
        {"fec_cand_id", type text}})
in
    Typed

// ---- 10. QUERY: FactCandidateFinance ---------------------------
let
    T = fnLoad("facts/fact-candidate-finance.csv"),
    Typed = Table.TransformColumnTypes(T, {
        {"fec_cand_id", type text}, {"coverage_start_date", type date},
        {"coverage_end_date", type date}, {"total_receipts", type number},
        {"total_disbursements", type number}, {"cash_on_hand_end", type number},
        {"individual_contributions", type number},
        {"other_committee_contributions", type number},
        {"party_committee_contributions", type number},
        {"candidate_self_contributions", type number}, {"candidate_loans", type number},
        {"operating_expenditures", type number},
        {"transfers_from_own_auth_committees", type number},
        {"receipts_excl_internal_transfers", type number},
        {"internal_transfer_share", type number},
        {"fec_committee_id", type text}, {"fec_committee_name", type text},
        {"other_authorized_committee_ids", type text},
        {"comparability_cohort", type text}, {"period_comparable_flag", type text}})
in
    Typed

// ---- 11. QUERY: FactRaceRating ---------------------------------
// Loaded so the rows stay visible, but every row has analysis_eligible = "N".
let
    T = fnLoad("facts/fact-race-rating.csv"),
    Typed = Table.TransformColumnTypes(T, {
        {"rating_id", type text}, {"race_id", type text}, {"rater", type text},
        {"rating", type text}, {"rating_score_dem_positive", type number},
        {"rating_as_of_date", type date}, {"verification_status", type text},
        {"analysis_eligible", type text}, {"quarantine_reason", type text},
        {"release_condition", type text}})
in
    Typed

// ---- 11b. QUERY: ModelRules ------------------------------------
let T = fnLoad("quality/model-rules.csv") in T

// ---- 12. SMALL REFERENCE TABLES --------------------------------
// Load each with all columns as text; none needs numeric typing.
//   DimSource            -> "dimensions/dim-source.csv"
//   DimRater             -> "dimensions/dim-rater.csv"
//   DimResultStatus      -> "dimensions/dim-result-status.csv"
//   DataQualityChecks    -> "quality/data-quality-checks.csv"
//   UnresolvedIssues     -> "quality/unresolved-issues.csv"
//   CorrectionRegister   -> "quality/correction-register.csv"
//   WinnerValidation     -> "quality/winner-validation.csv"
//   DataDictionary       -> "../docs/data-dictionary.csv"
// Pattern:
//   let T = fnLoad("dimensions/dim-source.csv") in T

// ---- 13. QUERY: _Measures (empty table to hold measures) -------
let
    Source = Table.FromRows({}, type table [Placeholder = text])
in
    Source
// After loading: Model view > select _Measures > hide the Placeholder column.
