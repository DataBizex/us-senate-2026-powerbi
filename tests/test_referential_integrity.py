"""Primary keys, grain and every foreign key in the model."""

import pytest

from senate_validation import load_config
from senate_validation.checks import keys

CONFIG = load_config()
FOREIGN_KEYS = keys.foreign_keys(CONFIG)
REQUIRED_FAMILIES = {"race_id", "fec_cand_id", "state_fips", "source_id", "rater"}


def test_every_required_key_family_is_configured():
    configured = {fk.family for fk in FOREIGN_KEYS}
    assert REQUIRED_FAMILIES <= configured, f"missing: {sorted(REQUIRED_FAMILIES - configured)}"


@pytest.mark.register("Q01", "Q02", "Q03", "Q06")
@pytest.mark.parametrize("table", sorted(CONFIG.section("primary_keys")))
def test_primary_key_is_present_and_unique(store, config, table):
    violations = keys.primary_key_violations(store.frame(table), config.section("primary_keys")[table])
    assert not violations, "\n".join(violations)


@pytest.mark.register("Q01")
@pytest.mark.parametrize("table, expected", sorted(CONFIG.section("expected_rows").items()))
def test_grain_row_count(store, table, expected):
    violations = keys.row_count_violation(store.frame(table), expected)
    assert not violations, "\n".join(violations)


@pytest.mark.register("Q04")
@pytest.mark.parametrize("fk", FOREIGN_KEYS, ids=lambda fk: fk.label)
def test_foreign_key_resolves(store, fk):
    violations = keys.foreign_key_violations(store, fk)
    assert not violations, "\n".join(violations)
