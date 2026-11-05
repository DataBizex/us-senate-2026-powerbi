"""Candidate votes reconcile exactly to race_total_votes.

Totals are compared as exact integers parsed from the CSV text, never as
floats, so a one-vote difference cannot be rounded away.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

import pandas as pd

from ._util import truncate

_INTEGER = re.compile(r"^[0-9]+$")


def _parse_int(value: str, where: str, violations: list[str]) -> int | None:
    if value == "":
        return None
    if not _INTEGER.match(value):
        violations.append(f"{where}: {value!r} is not a whole number of votes")
        return None
    return int(value)


def _single_total(group: pd.DataFrame, label: str, violations: list[str]) -> tuple[bool, int | None]:
    """Return (has_count, total) for a group that should share one race total."""
    totals = set(group["race_total_votes"]) - {""}
    if not totals:
        return False, None
    if len(totals) > 1:
        violations.append(f"{label}: race_total_votes differs between rows: {sorted(totals)}")
        return True, None
    blanks = group[group["race_total_votes"] == ""]
    if not blanks.empty:
        lines = [i + 2 for i in blanks.index]
        violations.append(f"{label}: race_total_votes blank on CSV lines {lines} but set elsewhere in the race")
    return True, _parse_int(totals.pop(), label, violations)


def counted_races(race_frame: pd.DataFrame) -> set[str]:
    """Races whose race-level row carries a published total."""
    return set(race_frame.loc[race_frame["race_total_votes"] != "", "race_id"])


def candidate_sum_violations(
    candidates: pd.DataFrame, blank_votes_allowed_row_types: Sequence[str]
) -> list[str]:
    """In each race with a total, candidate_votes must sum exactly to it."""
    violations: list[str] = []
    allowed = set(blank_votes_allowed_row_types)

    for race_id, group in candidates.groupby("race_id", sort=True):
        has_count, total = _single_total(group, race_id, violations)
        if not has_count:
            stray = group[group["candidate_votes"] != ""]
            if not stray.empty:
                violations.append(f"{race_id}: candidate votes present but no race_total_votes")
            continue

        votes = 0
        for index, row in group.iterrows():
            where = f"{race_id} CSV line {index + 2}"
            if row["candidate_votes"] == "":
                if row["row_type"] not in allowed:
                    violations.append(f"{where}: blank candidate_votes on a {row['row_type']!r} row in a counted race")
                continue
            value = _parse_int(row["candidate_votes"], where, violations)
            votes += value or 0

        if total is not None and votes != total:
            violations.append(f"{race_id}: candidate votes sum to {votes:,}, race_total_votes is {total:,} (diff {votes - total:+,})")
    return truncate(violations)


def race_total_agreement_violations(candidates: pd.DataFrame, races: pd.DataFrame) -> list[str]:
    """The race-level total must equal the total on that race's candidate rows."""
    violations: list[str] = []
    candidate_totals = {
        race_id: (set(group["race_total_votes"]) - {""})
        for race_id, group in candidates.groupby("race_id", sort=True)
    }
    for _, row in races.iterrows():
        race_id = row["race_id"]
        race_total = row["race_total_votes"]
        from_candidates = candidate_totals.get(race_id, set())
        if race_total == "" and not from_candidates:
            continue
        if {race_total} != from_candidates:
            violations.append(
                f"{race_id}: race table total {race_total or 'blank'!s} vs candidate table {sorted(from_candidates) or 'blank'}"
            )
    return truncate(violations)


def leading_votes_violations(candidates: pd.DataFrame, races: pd.DataFrame) -> list[str]:
    """leading_votes is one candidate's votes, the largest in the race (R04)."""
    violations: list[str] = []
    for _, row in races.iterrows():
        if row["race_total_votes"] == "":
            continue
        race_id = row["race_id"]
        group = candidates[(candidates["race_id"] == race_id) & (candidates["candidate_votes"] != "")]
        if group.empty:
            continue
        top = max(int(v) for v in group["candidate_votes"] if v.isdigit())
        if row["leading_votes"] != str(top):
            violations.append(f"{race_id}: leading_votes {row['leading_votes'] or 'blank'} but the largest candidate count is {top}")
    return truncate(violations)


def observation_sum_violations(observations: pd.DataFrame, snapshot: Sequence[str]) -> list[str]:
    """Every published snapshot in the append-only log must also reconcile."""
    violations: list[str] = []
    for key, group in observations.groupby(list(snapshot), sort=True):
        label = " / ".join(key)
        has_count, total = _single_total(group, label, violations)
        if not has_count:
            continue
        votes = 0
        for index, value in group["candidate_votes"].items():
            votes += _parse_int(value, f"{label} CSV line {index + 2}", violations) or 0
        if total is not None and votes != total:
            violations.append(f"{label}: candidate votes sum to {votes:,}, race_total_votes is {total:,} (diff {votes - total:+,})")
    return truncate(violations)


def ballot_handling_violations(frame: pd.DataFrame, name_column: str, terms: Sequence[str]) -> list[str]:
    """Overvotes and undervotes are never counted as votes."""
    pattern = re.compile("|".join(re.escape(t) for t in terms), re.IGNORECASE)
    hits = frame[frame[name_column].str.contains(pattern)]
    return truncate(
        f"CSV line {i + 2}: {row['race_id']} has a vote row named {row[name_column]!r}"
        for i, row in hits.iterrows()
    )
