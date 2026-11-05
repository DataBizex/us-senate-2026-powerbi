"""Each check detects the breach it exists for.

These run on small synthetic tables, never on the files in data/, and prove
that a passing data test means the rule holds rather than that the check
cannot fail.
"""

import io

import pandas as pd
import pytest

from senate_validation.checks import election_year as ey
from senate_validation.checks import eligibility, keys, text_ids, votes
from senate_validation.config import ColumnRef


def _frame(text: str) -> pd.DataFrame:
    return pd.read_csv(io.StringIO(text), dtype=str, keep_default_na=False, na_filter=False)


class _Store:
    def __init__(self, **frames):
        self.frames = frames

    def frame(self, name):
        return self.frames[name]

    def column(self, ref):
        ref = ColumnRef.parse(ref) if isinstance(ref, str) else ref
        return self.frames[ref.table][ref.column]


# --- keys -------------------------------------------------------------------


def test_duplicate_and_blank_primary_keys_are_reported():
    frame = _frame("race_id,name\nA,x\nA,y\n,z\n")
    violations = keys.primary_key_violations(frame, ["race_id"])
    assert any("duplicate" in v for v in violations)
    assert any("blank" in v for v in violations)


def test_orphan_blank_and_uncovered_foreign_keys_are_reported():
    store = _Store(parent=_frame("id\nS01\nS02\nS03\n"), child=_frame('ref,n\n"S01; S99",1\n,2\n'))
    fk = keys.ForeignKey("source_id", ColumnRef("child", "ref"), ColumnRef("parent", "id"),
                         separator=";", covers_parent=True)
    violations = keys.foreign_key_violations(store, fk)
    assert any("'S99' not found" in v for v in violations)
    assert any("blank ref" in v for v in violations)
    assert any("'S02' has no row" in v for v in violations)


def test_nullable_foreign_key_accepts_blank():
    store = _Store(parent=_frame("id\nX\n"), child=_frame("ref,n\nX,1\n,2\n"))
    fk = keys.ForeignKey("fec_cand_id", ColumnRef("child", "ref"), ColumnRef("parent", "id"), nullable=True)
    assert keys.foreign_key_violations(store, fk) == []


# --- votes ------------------------------------------------------------------

CANDIDATES = """race_id,candidate_name,row_type,candidate_votes,race_total_votes
R1,A,Candidate,600,1000
R1,B,Candidate,400,1000
R1,C,Withdrawn candidate,,1000
R2,D,Candidate,,
"""


def test_reconciled_race_passes():
    assert votes.candidate_sum_violations(_frame(CANDIDATES), ["Withdrawn candidate"]) == []


def test_off_by_one_total_is_reported():
    frame = _frame(CANDIDATES.replace("400,1000", "401,1000"))
    violations = votes.candidate_sum_violations(frame, ["Withdrawn candidate"])
    assert violations == ["R1: candidate votes sum to 1,001, race_total_votes is 1,000 (diff +1)"]


def test_missing_candidate_votes_in_counted_race_is_reported():
    frame = _frame(CANDIDATES.replace("B,Candidate,400", "B,Candidate,"))
    violations = votes.candidate_sum_violations(frame, ["Withdrawn candidate"])
    assert any("blank candidate_votes" in v for v in violations)


def test_non_integer_votes_are_reported():
    frame = _frame(CANDIDATES.replace("600,1000", "600.0,1000"))
    violations = votes.candidate_sum_violations(frame, ["Withdrawn candidate"])
    assert any("not a whole number" in v for v in violations)


def test_race_and_candidate_totals_must_agree():
    races = _frame("race_id,race_total_votes\nR1,999\nR2,\n")
    violations = votes.race_total_agreement_violations(_frame(CANDIDATES), races)
    assert violations and violations[0].startswith("R1:")


def test_overvote_row_is_reported():
    frame = _frame("race_id,candidate_name\nWY,Overvotes\nWY,Jane Doe\n")
    assert len(votes.ballot_handling_violations(frame, "candidate_name", ["overvote"])) == 1


# --- headline eligibility and ratings ---------------------------------------


@pytest.mark.parametrize(
    "text, complete",
    [
        ("23 of 23 counties reporting", True),
        ("133/133 localities reporting", True),
        ("254 of 254 counties (100%), 5303 of 5303 polling locations (100%)", True),
        ("254 of 254 counties, 5302 of 5303 polling locations", False),
        ("623 of 728 precincts fully reporting, 105 partially", False),
        ("Not published", False),
        ("", False),
    ],
)
def test_reporting_units_parser(text, complete):
    assert eligibility.reporting_units_complete(text) is complete


HEADLINE = {
    "flags_table": "flags",
    "eligible_column": "headline_eligible",
    "integrity_column": "source_integrity_flag",
    "source_tier_column": "count_source_tier",
    "official_tier": "Official state election authority",
    "completeness_column": "count_completeness",
    "complete_label": "Complete reporting units",
    "official_status_column": "official_count_status",
    "official_status": "Published",
    "reporting_units_column": "official_reporting_units",
    "expected_eligible": ["OK"],
}


def _headline_store(integrity="N", units="10 of 10", source="S14", eligible="Y"):
    return _Store(
        flags=_frame(
            "race_id,headline_eligible,source_integrity_flag,count_source_tier\n"
            f"OK,{eligible},{integrity},Official state election authority\n"
        ),
        fact_race_result=_frame(
            "race_id,official_count_status,count_completeness,official_reporting_units\n"
            f"OK,Published,Complete reporting units,{units}\n"
        ),
        fact_candidate_result=_frame(f"race_id,source_id,count_completeness\nOK,{source},Complete reporting units\n"),
        dim_source=_frame(
            "source_id,source_type\nS14,Official state election authority\nS10,Media aggregator\n"
        ),
    )


def test_qualifying_race_passes():
    assert eligibility.headline_violations(_headline_store(), HEADLINE) == []


@pytest.mark.parametrize(
    "override, reason",
    [
        ({"integrity": "Y"}, "integrity flag"),
        ({"units": "9 of 10"}, "reporting units"),
        ({"source": "S10"}, "non-official source"),
    ],
)
def test_headline_on_failing_race_is_reported(override, reason):
    violations = eligibility.headline_violations(_headline_store(**override), HEADLINE)
    assert len(violations) == 1 and reason in violations[0]


def test_qualifying_race_left_out_is_reported():
    assert eligibility.headline_omissions(_headline_store(eligible="N"), HEADLINE)


def test_released_rating_is_reported():
    frame = _frame("rating_id,analysis_eligible\nRAT0001,N\nRAT0002,Y\nRAT0003,\n")
    assert len(eligibility.required_value_violations(frame, "analysis_eligible", "N")) == 2


# --- election year ----------------------------------------------------------


@pytest.mark.parametrize(
    "value, found",
    [
        ("2026-11-03", []),
        ("2025-01-09", []),
        ("2024-10-01", [2024]),
        ("Last Updated: 11/3/24 23:54:49 MST", [2024]),
        ("Last Updated: 11/3/26 23:54:49 MST", []),
        ("https://www.fec.gov/data/candidate/S6FL00640/?cycle=2022", [2022]),
        ("S6FL00640", []),
        ("C00264697", []),
    ],
)
def test_other_election_years(value, found):
    assert ey.other_election_years(value, 2026) == found


def test_numeric_measures_are_not_read_as_years():
    assert ey.is_measure_column(pd.Series(["2046", "917347", ""]))
    assert ey.is_measure_column(pd.Series(["2024.5"]))
    assert not ey.is_measure_column(pd.Series(["2014", "2020", ""]))
    assert not ey.is_measure_column(pd.Series(["2026-11-03"]))


def test_scan_reports_unexempted_years_and_honours_exceptions():
    frame = _frame("id,date,note\nA,2024-11-05,saw 2024\nB,2024-01-01,\nC,2026-01-01,\n")
    exemptions = ey.Exemptions(
        columns=frozenset({ColumnRef("t", "note")}),
        cells=frozenset({("t", "B", "date"), ("t", "Z", "date")}),
    )
    violations, matched = ey.scan_table("t", frame, "id", 2026, exemptions)
    assert len(violations) == 1 and "id=A" in violations[0]
    assert matched == {("t", "B", "date")}
    assert len(ey.stale_exception_violations(exemptions, matched)) == 1


def test_exemption_without_reason_is_rejected():
    with pytest.raises(ValueError):
        ey.Exemptions.from_settings({"exempt_columns": [{"columns": ["t.c"]}]})


# --- text and leading zeros -------------------------------------------------

FIPS = {"pattern": "^[0-9]{2}$", "allow_blank": False}


def test_stripped_leading_zero_is_reported():
    rows = [{"state_fips": "01"}, {"state_fips": "1"}, {"state_fips": ""}]
    violations = text_ids.format_violations(rows, "state_fips", FIPS)
    assert len(violations) == 2


def test_numeric_load_is_reported():
    text = "state_fips\n01\n02\n"
    rows = [{"state_fips": "01"}, {"state_fips": "02"}]
    inferred = pd.read_csv(io.StringIO(text))
    assert text_ids.loaded_as_text_violations(inferred, rows, "state_fips")
    assert text_ids.loaded_as_text_violations(_frame(text), rows, "state_fips") == []


def test_wrong_fips_pairing_is_reported():
    rows = [{"state_postal": "AL", "state_fips": "01"}, {"state_postal": "AK", "state_fips": "01"}]
    assert len(text_ids.postal_fips_pairing_violations("t", rows, {"AL": "01", "AK": "02"})) == 1


def test_unformatted_id_column_is_reported():
    columns = {"t": ["race_id", "new_thing_id", "committee_id_status"]}
    assert text_ids.unclassified_id_columns(columns, {"race_id": {}}, ["committee_id_status"]) == ["t.new_thing_id"]
