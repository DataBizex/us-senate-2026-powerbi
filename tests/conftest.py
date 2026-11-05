"""Shared fixtures and the register marker.

Tests are tagged with ``@pytest.mark.register("Q18")`` naming the check in
data/quality/data-quality-checks.csv (or rule in model-rules.csv) that they
re-run. Collection fails if a tag names an ID that is not in either register,
so the link between the documentation and the executable check stays true.
"""

from __future__ import annotations

import pytest

from senate_validation import TableStore, load_config


@pytest.fixture(scope="session")
def config():
    return load_config()


@pytest.fixture(scope="session")
def store(config):
    return TableStore(config)


def pytest_collection_modifyitems(config, items):
    cfg = load_config()
    store = TableStore(cfg)
    known = set(store.frame("data_quality_checks")["check_id"]) | set(store.frame("model_rules")["rule_id"])
    unknown = sorted(
        {
            f"{item.nodeid}: {ref}"
            for item in items
            for marker in item.iter_markers("register")
            for ref in marker.args
            if ref not in known
        }
    )
    if unknown:
        raise pytest.UsageError("register marker names unknown check or rule IDs:\n" + "\n".join(unknown))
