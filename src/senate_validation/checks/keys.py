"""Primary keys, grain row counts and referential integrity."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from ..config import ColumnRef, Config
from ..tables import TableStore
from ._util import split_cell, truncate


@dataclass(frozen=True)
class ForeignKey:
    family: str
    child: ColumnRef
    parent: ColumnRef
    nullable: bool = False
    separator: str | None = None
    covers_parent: bool = False

    @property
    def label(self) -> str:
        return f"{self.family}:{self.child}"


def foreign_keys(config: Config) -> list[ForeignKey]:
    result = []
    for family, spec in config.section("foreign_keys").items():
        parent = ColumnRef.parse(spec["parent"])
        for child in spec["children"]:
            result.append(
                ForeignKey(
                    family=family,
                    child=ColumnRef.parse(child["column"]),
                    parent=parent,
                    nullable=bool(child.get("nullable", False)),
                    separator=child.get("separator"),
                    covers_parent=bool(child.get("covers_parent", False)),
                )
            )
    return result


def primary_key_violations(frame: pd.DataFrame, columns: list[str]) -> list[str]:
    missing = [c for c in columns if c not in frame.columns]
    if missing:
        return [f"key column(s) missing: {missing}"]

    violations = []
    blank = frame[(frame[columns] == "").any(axis=1)]
    for index in blank.index:
        violations.append(f"row {index + 2}: blank key {frame.loc[index, columns].tolist()}")

    duplicated = frame[frame.duplicated(columns, keep=False)]
    for key, group in duplicated.groupby(columns, sort=True):
        rows = [i + 2 for i in group.index]
        violations.append(f"duplicate key {key!r} on CSV lines {rows}")
    return truncate(violations)


def row_count_violation(frame: pd.DataFrame, expected: int) -> list[str]:
    actual = len(frame)
    return [] if actual == expected else [f"expected {expected} rows, found {actual}"]


def foreign_key_violations(store: TableStore, fk: ForeignKey) -> list[str]:
    parent_keys = set(store.column(fk.parent))
    child = store.column(fk.child)

    violations = []
    seen: set[str] = set()
    for index, cell in child.items():
        keys = split_cell(cell, fk.separator)
        if not keys:
            if not fk.nullable:
                violations.append(f"CSV line {index + 2}: blank {fk.child.column} (column is not nullable)")
            continue
        for key in keys:
            seen.add(key)
            if key not in parent_keys:
                violations.append(f"CSV line {index + 2}: {key!r} not found in {fk.parent}")

    if fk.covers_parent:
        for key in sorted(parent_keys - seen):
            violations.append(f"{fk.parent} value {key!r} has no row in {fk.child.table}")
    return truncate(violations)
