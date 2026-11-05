"""state_fips and ID columns are text with leading zeros intact (Q05).

Checked against the raw file text (standard-library csv module) and against
the pandas load used by the other checks, so a type-inferring loader or a
file re-saved through a spreadsheet would both be caught.
"""

from __future__ import annotations

import re
from typing import Any

import pandas as pd
from pandas.api.types import is_string_dtype

from ._util import split_cell, truncate

_ID_TOKENS = {"id", "ids", "fips"}


def looks_like_id_column(name: str) -> bool:
    return bool(_ID_TOKENS & set(name.lower().split("_")))


def unclassified_id_columns(
    columns_by_table: dict[str, list[str]], formats: dict[str, Any], non_id_columns: list[str]
) -> list[str]:
    """ID-like columns with no configured format, so none slips through."""
    known = set(formats) | set(non_id_columns)
    return sorted(
        f"{table}.{column}"
        for table, columns in columns_by_table.items()
        for column in columns
        if looks_like_id_column(column) and column not in known
    )


def format_violations(rows: list[dict[str, str]], column: str, spec: dict[str, Any]) -> list[str]:
    pattern = re.compile(spec["pattern"])
    allow_blank = spec.get("allow_blank", True)
    separator = spec.get("separator")

    violations = []
    for line, row in enumerate(rows, start=2):
        cell = row[column]
        if cell == "":
            if not allow_blank:
                violations.append(f"CSV line {line}: blank {column}")
            continue
        if cell != cell.strip():
            violations.append(f"CSV line {line}: {column} {cell!r} has surrounding whitespace")
        for value in split_cell(cell, separator):
            if not pattern.match(value):
                violations.append(f"CSV line {line}: {column} {value!r} does not match {spec['pattern']}")
    return truncate(violations)


def loaded_as_text_violations(frame: pd.DataFrame, rows: list[dict[str, str]], column: str) -> list[str]:
    """The loaded column is a string dtype and identical to the raw text."""
    violations = []
    if not is_string_dtype(frame[column]):
        violations.append(f"{column} loaded as {frame[column].dtype}, expected text")
    raw = [row[column] for row in rows]
    loaded = frame[column].tolist()
    for line, (r, v) in enumerate(zip(raw, loaded), start=2):
        if r != v or not isinstance(v, str):
            violations.append(f"CSV line {line}: file has {r!r}, loader returned {v!r}")
    if len(raw) != len(loaded):
        violations.append(f"row count differs: file {len(raw)}, loader {len(loaded)}")
    return truncate(violations)


def fips_reference_violations(rows: list[dict[str, str]], reference: dict[str, str]) -> list[str]:
    """dim-state matches the Census FIPS code for every state."""
    violations = []
    actual = {row["state_postal"]: row["state_fips"] for row in rows}
    for postal, fips in sorted(reference.items()):
        if postal not in actual:
            violations.append(f"{postal} missing from dim-state")
        elif actual[postal] != fips:
            violations.append(f"{postal}: state_fips {actual[postal]!r}, Census code is {fips!r}")
    for postal in sorted(set(actual) - set(reference)):
        violations.append(f"{postal} in dim-state is not a known state code")
    return violations


def postal_fips_pairing_violations(
    table: str, rows: list[dict[str, str]], reference: dict[str, str]
) -> list[str]:
    """Wherever state_postal and state_fips sit side by side, they agree."""
    return truncate(
        f"{table} CSV line {line}: {row['state_postal']} paired with state_fips {row['state_fips']!r}, expected {reference.get(row['state_postal'])!r}"
        for line, row in enumerate(rows, start=2)
        if reference.get(row["state_postal"]) != row["state_fips"]
    )
