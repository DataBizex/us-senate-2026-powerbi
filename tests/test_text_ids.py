"""state_fips and every ID column are text with leading zeros intact."""

import pytest

from senate_validation import TableStore, load_config
from senate_validation.checks import text_ids

CONFIG = load_config()
_STORE = TableStore(CONFIG)
FORMATS = CONFIG.section("text_ids")["formats"]
REFERENCE = CONFIG.section("text_ids")["state_fips_reference"]

ID_COLUMNS = [
    (table, column)
    for table in sorted(CONFIG.tables)
    for column in _STORE.raw(table)[0]
    if column in FORMATS
]
STATE_TABLES = [
    table for table in sorted(CONFIG.tables) if {"state_postal", "state_fips"} <= set(_STORE.raw(table)[0])
]


def test_every_id_column_has_a_format(store):
    columns = {t: store.raw(t)[0] for t in store.names()}
    unclassified = text_ids.unclassified_id_columns(columns, FORMATS, CONFIG.section("text_ids")["non_id_columns"])
    assert not unclassified, f"add these to [text_ids.formats] or non_id_columns: {unclassified}"


@pytest.mark.register("Q05")
@pytest.mark.parametrize("table, column", ID_COLUMNS, ids=[f"{t}.{c}" for t, c in ID_COLUMNS])
def test_id_text_format_in_file(store, table, column):
    _, rows = store.raw(table)
    violations = text_ids.format_violations(rows, column, FORMATS[column])
    assert not violations, "\n".join(violations)


@pytest.mark.register("Q05")
@pytest.mark.parametrize("table, column", ID_COLUMNS, ids=[f"{t}.{c}" for t, c in ID_COLUMNS])
def test_id_loaded_as_text(store, table, column):
    _, rows = store.raw(table)
    violations = text_ids.loaded_as_text_violations(store.frame(table), rows, column)
    assert not violations, "\n".join(violations)


@pytest.mark.register("Q05")
def test_dim_state_matches_census_fips(store):
    _, rows = store.raw("dim_state")
    violations = text_ids.fips_reference_violations(rows, REFERENCE)
    assert not violations, "\n".join(violations)


@pytest.mark.register("Q05")
@pytest.mark.parametrize("table", STATE_TABLES)
def test_state_postal_and_fips_agree(store, table):
    _, rows = store.raw(table)
    violations = text_ids.postal_fips_pairing_violations(table, rows, REFERENCE)
    assert not violations, "\n".join(violations)
