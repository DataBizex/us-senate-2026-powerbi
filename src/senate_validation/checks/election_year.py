"""No value from an election year other than 2026 (Q49).

Every cell of every table is scanned. A cell fails when it contains an even
(federal election) year other than the configured one, written either as a
four-digit year or as an m/d/yy date. Odd years are not election years.
Exemptions and known exceptions come from config and must each carry a reason.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import pandas as pd

from ..config import ColumnRef
from ._util import truncate

_FOUR_DIGIT_YEAR = re.compile(r"(?<!\d)((?:19|20)\d{2})(?!\d)")
_SHORT_DATE = re.compile(r"(?<!\d)\d{1,2}/\d{1,2}/(\d{2})(?!\d)")
_NUMBER = re.compile(r"^-?\d+(?:\.\d+)?$")


def years_in(value: str) -> set[int]:
    years = {int(y) for y in _FOUR_DIGIT_YEAR.findall(value)}
    years |= {2000 + int(y) for y in _SHORT_DATE.findall(value)}
    return years


def other_election_years(value: str, election_year: int) -> list[int]:
    return sorted(y for y in years_in(value) if y % 2 == 0 and y != election_year)


def is_measure_column(series: pd.Series) -> bool:
    """True for numeric measures (votes, dollars, shares) that are not years.

    A column is a measure when every non-blank value is a number and at least
    one of them could not be a year (a decimal, or outside 1900-2100).
    """
    values = [v for v in series if v != ""]
    if not values or not all(_NUMBER.match(v) for v in values):
        return False
    return any("." in v or not (1900 <= int(v) <= 2100) for v in values)


@dataclass(frozen=True)
class Exemptions:
    columns: frozenset[ColumnRef]
    cells: frozenset[tuple[str, str, str]]  # (table, key, column)

    @classmethod
    def from_settings(cls, settings: dict[str, Any]) -> "Exemptions":
        columns = set()
        for entry in settings.get("exempt_columns", []):
            if not entry.get("reason"):
                raise ValueError(f"exempt_columns entry without a reason: {entry}")
            columns.update(ColumnRef.parse(c) for c in entry["columns"])
        cells = set()
        for entry in settings.get("known_exceptions", []):
            if not entry.get("reason"):
                raise ValueError(f"known_exceptions entry without a reason: {entry}")
            for key in entry["keys"]:
                for column in entry["columns"]:
                    cells.add((entry["table"], key, column))
        return cls(frozenset(columns), frozenset(cells))


def scan_table(
    table: str,
    frame: pd.DataFrame,
    key_column: str,
    election_year: int,
    exemptions: Exemptions,
) -> tuple[list[str], set[tuple[str, str, str]]]:
    """Return (violations, known-exception cells that matched)."""
    violations: list[str] = []
    matched: set[tuple[str, str, str]] = set()

    for column in frame.columns:
        if ColumnRef(table, column) in exemptions.columns:
            continue
        series = frame[column]
        if is_measure_column(series):
            continue
        for index, value in series.items():
            found = other_election_years(value, election_year)
            if not found:
                continue
            key = frame.at[index, key_column]
            cell = (table, key, column)
            if cell in exemptions.cells:
                matched.add(cell)
                continue
            violations.append(f"{table}.{column} CSV line {index + 2} ({key_column}={key}): year {found} in {value[:80]!r}")
    return violations, matched


def stale_exception_violations(exemptions: Exemptions, matched: set[tuple[str, str, str]]) -> list[str]:
    return truncate(
        f"known exception {table}.{column} key {key!r} no longer matches any value; remove it from the config"
        for table, key, column in sorted(exemptions.cells - matched)
    )


def unknown_exemption_columns(exemptions: Exemptions, columns_by_table: dict[str, list[str]]) -> list[str]:
    """Exemptions naming a table or column that does not exist are typos."""
    violations = []
    for ref in sorted(exemptions.columns, key=str):
        if ref.column not in columns_by_table.get(ref.table, []):
            violations.append(f"exempt column {ref} does not exist")
    for table, _key, column in sorted(exemptions.cells):
        if column not in columns_by_table.get(table, []):
            violations.append(f"known exception column {table}.{column} does not exist")
    return violations


def election_date_violations(dates: pd.Series, expected: str) -> list[str]:
    return truncate(
        f"CSV line {i + 2}: election_date is {v!r}, expected {expected!r}"
        for i, v in dates.items()
        if v != expected
    )
