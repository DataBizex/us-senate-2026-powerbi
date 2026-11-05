"""Read-only access to the model's CSV files.

Two views of each file are offered:

* ``frame`` - a pandas DataFrame where every cell is text and blanks stay as
  empty strings. Nothing is inferred, so "01" stays "01" and a blank is never
  turned into NaN or zero.
* ``raw`` - rows parsed with the standard-library csv module, used as the
  reference for what the file literally contains.

Files are only ever opened for reading.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd

from .config import ColumnRef, Config

ENCODING = "utf-8-sig"


def read_frame(path: Path) -> pd.DataFrame:
    return pd.read_csv(
        path,
        dtype=str,
        keep_default_na=False,
        na_filter=False,
        encoding=ENCODING,
    )


def read_raw(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding=ENCODING, newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        return list(reader.fieldnames or []), rows


class TableStore:
    """Caches each table so a test session reads every file once."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self._frames: dict[str, pd.DataFrame] = {}
        self._raw: dict[str, tuple[list[str], list[dict[str, str]]]] = {}

    def frame(self, name: str) -> pd.DataFrame:
        if name not in self._frames:
            self._frames[name] = read_frame(self.config.table_path(name))
        return self._frames[name]

    def raw(self, name: str) -> tuple[list[str], list[dict[str, str]]]:
        if name not in self._raw:
            self._raw[name] = read_raw(self.config.table_path(name))
        return self._raw[name]

    def column(self, ref: str | ColumnRef) -> pd.Series:
        ref = ColumnRef.parse(ref) if isinstance(ref, str) else ref
        frame = self.frame(ref.table)
        if ref.column not in frame.columns:
            raise KeyError(f"Column {ref} does not exist")
        return frame[ref.column]

    def names(self) -> list[str]:
        return list(self.config.tables)
