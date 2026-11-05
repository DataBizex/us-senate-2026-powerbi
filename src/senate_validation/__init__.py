"""Executable checks for the US Senate 2026 data model.

Each check function returns a list of human-readable violations; an empty
list means the check passed. The pytest suite under tests/ asserts that
every list is empty.
"""

from .config import Config, load_config
from .tables import TableStore

__all__ = ["Config", "TableStore", "load_config"]
