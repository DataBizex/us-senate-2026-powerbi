"""Headline eligibility (R02, R03, Q51) and the rating quarantine (Q33).

A race may be headline-eligible only when all of the following hold. Each
condition is proven from a different table where possible, so a mislabelled
flag in race-quality-flags cannot vouch for itself:

* official source - race-quality-flags names the official state election
  authority as the count source, the race table says the official count was
  published, and every candidate row in that race cites a source whose
  dim-source type is the official state election authority;
* complete reporting units - the completeness label says complete on the
  race and candidate rows, and every "N of M" fraction in the published
  reporting-units text has N equal to M;
* no integrity flag - source_integrity_flag is "N".
"""

from __future__ import annotations

import re
from typing import Any

import pandas as pd

from ..tables import TableStore
from ._util import truncate

_FRACTION = re.compile(r"(\d[\d,]*)\s*(?:of|/)\s*(\d[\d,]*)")


def reporting_units_complete(text: str) -> bool:
    """True when the text contains at least one "N of M" and every N equals M."""
    fractions = _FRACTION.findall(text)
    if not fractions:
        return False
    return all(int(a.replace(",", "")) == int(b.replace(",", "")) for a, b in fractions)


def unmet_headline_conditions(store: TableStore, settings: dict[str, Any]) -> dict[str, list[str]]:
    """Map race_id -> conditions that race fails. An empty list means eligible."""
    flags = store.frame(settings["flags_table"])
    races = store.frame("fact_race_result").set_index("race_id")
    candidates = store.frame("fact_candidate_result")
    source_types = dict(zip(store.frame("dim_source")["source_id"], store.frame("dim_source")["source_type"]))

    official = settings["official_tier"]
    complete = settings["complete_label"]
    completeness = settings["completeness_column"]

    result: dict[str, list[str]] = {}
    for _, flag in flags.iterrows():
        race_id = flag["race_id"]
        unmet: list[str] = []

        if flag[settings["source_tier_column"]] != official:
            unmet.append(f"count source is {flag[settings['source_tier_column']]!r}")
        if flag[settings["integrity_column"]] != "N":
            unmet.append(f"source integrity flag is {flag[settings['integrity_column']]!r}")

        if race_id not in races.index:
            unmet.append("no row in fact_race_result")
        else:
            race = races.loc[race_id]
            if race[settings["official_status_column"]] != settings["official_status"]:
                unmet.append(f"official count status is {race[settings['official_status_column']]!r}")
            if race[completeness] != complete:
                unmet.append(f"race completeness is {race[completeness]!r}")
            units = race[settings["reporting_units_column"]]
            if not reporting_units_complete(units):
                unmet.append(f"reporting units not all in: {units or 'not published'!r}")

        rows = candidates[candidates["race_id"] == race_id]
        if rows.empty:
            unmet.append("no candidate rows")
        else:
            not_official = sorted({s for s in rows["source_id"] if source_types.get(s) != official})
            if not_official:
                unmet.append(f"candidate rows cite non-official source(s) {not_official}")
            incomplete = sorted(set(rows[completeness]) - {complete})
            if incomplete:
                unmet.append(f"candidate rows completeness {incomplete}")

        result[race_id] = unmet
    return result


def headline_violations(store: TableStore, settings: dict[str, Any]) -> list[str]:
    """headline_eligible = Y on a race that fails any condition."""
    flags = store.frame(settings["flags_table"]).set_index("race_id")
    unmet = unmet_headline_conditions(store, settings)
    return truncate(
        f"{race_id}: headline_eligible is Y but {'; '.join(reasons)}"
        for race_id, reasons in unmet.items()
        if flags.loc[race_id, settings["eligible_column"]] == "Y" and reasons
    )


def headline_omissions(store: TableStore, settings: dict[str, Any]) -> list[str]:
    """A race meeting every condition but left out of headline figures."""
    flags = store.frame(settings["flags_table"]).set_index("race_id")
    unmet = unmet_headline_conditions(store, settings)
    return truncate(
        f"{race_id}: meets every headline condition but headline_eligible is {flags.loc[race_id, settings['eligible_column']]!r}"
        for race_id, reasons in unmet.items()
        if not reasons and flags.loc[race_id, settings["eligible_column"]] != "Y"
    )


def expected_set_violations(store: TableStore, settings: dict[str, Any]) -> list[str]:
    flags = store.frame(settings["flags_table"])
    actual = set(flags.loc[flags[settings["eligible_column"]] == "Y", "race_id"])
    expected = set(settings["expected_eligible"])
    violations = []
    if actual - expected:
        violations.append(f"eligible but not expected: {sorted(actual - expected)}")
    if expected - actual:
        violations.append(f"expected but not eligible: {sorted(expected - actual)}")
    return violations


def yes_no_violations(frame: pd.DataFrame, column: str) -> list[str]:
    bad = frame[~frame[column].isin(["Y", "N"])]
    return truncate(f"CSV line {i + 2}: {column} is {v!r}, expected 'Y' or 'N'" for i, v in bad[column].items())


def required_value_violations(frame: pd.DataFrame, column: str, required: str) -> list[str]:
    bad = frame[frame[column] != required]
    key = frame.columns[0]
    return truncate(
        f"CSV line {i + 2} ({row[key]}): {column} is {row[column]!r}, must be {required!r}"
        for i, row in bad.iterrows()
    )
