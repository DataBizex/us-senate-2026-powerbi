"""Load config/validation.toml and resolve its paths."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

CONFIG_ENV_VAR = "SENATE_VALIDATION_CONFIG"
DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "config" / "validation.toml"


@dataclass(frozen=True)
class ColumnRef:
    """A "table.column" reference from the config."""

    table: str
    column: str

    @classmethod
    def parse(cls, ref: str) -> "ColumnRef":
        table, sep, column = ref.partition(".")
        if not sep or not table or not column:
            raise ValueError(f"Expected 'table.column', got {ref!r}")
        return cls(table, column)

    def __str__(self) -> str:
        return f"{self.table}.{self.column}"


@dataclass(frozen=True)
class Config:
    path: Path
    root: Path
    data_dir: Path
    tables: dict[str, Path]
    settings: dict[str, Any]

    def table_path(self, name: str) -> Path:
        try:
            return self.tables[name]
        except KeyError:
            raise KeyError(f"Table {name!r} is not listed under [tables] in {self.path}") from None

    def section(self, name: str) -> dict[str, Any]:
        try:
            return self.settings[name]
        except KeyError:
            raise KeyError(f"Section [{name}] is missing from {self.path}") from None


def _resolve_config_path(path: str | os.PathLike[str] | None) -> Path:
    if path is not None:
        return Path(path).resolve()
    from_env = os.environ.get(CONFIG_ENV_VAR)
    if from_env:
        return Path(from_env).resolve()
    return DEFAULT_CONFIG


@lru_cache(maxsize=None)
def _load(path: Path) -> Config:
    with path.open("rb") as handle:
        settings = tomllib.load(handle)

    paths = settings.get("paths", {})
    root = (path.parent / paths.get("root", ".")).resolve()
    data_dir = (root / paths.get("data_dir", "data")).resolve()
    tables = {name: data_dir / rel for name, rel in settings.get("tables", {}).items()}
    return Config(path=path, root=root, data_dir=data_dir, tables=tables, settings=settings)


def load_config(path: str | os.PathLike[str] | None = None) -> Config:
    """Load the validation config.

    Resolution order: explicit ``path``, the SENATE_VALIDATION_CONFIG
    environment variable, then config/validation.toml at the repository root.
    """
    return _load(_resolve_config_path(path))
