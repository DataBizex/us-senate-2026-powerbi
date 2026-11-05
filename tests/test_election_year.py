"""No file contains a value from an election year other than 2026."""

import pytest

from senate_validation import load_config
from senate_validation.checks import election_year as ey

CONFIG = load_config()
TABLES = sorted(CONFIG.tables)


@pytest.fixture(scope="module")
def settings(config):
    return config.section("election_year")


@pytest.fixture(scope="module")
def exemptions(settings):
    return ey.Exemptions.from_settings(settings)


def _key_column(config, store, table):
    keys = config.section("primary_keys").get(table)
    return keys[0] if keys else store.frame(table).columns[0]


def test_every_data_file_is_registered(config):
    on_disk = {p.resolve() for p in config.data_dir.rglob("*.csv")}
    registered = {p.resolve() for p in config.tables.values()}
    assert not (on_disk - registered), f"CSV files not listed under [tables]: {sorted(map(str, on_disk - registered))}"
    assert not (registered - on_disk), f"[tables] entries with no file: {sorted(map(str, registered - on_disk))}"


def test_exemptions_name_real_columns(store, exemptions):
    columns = {t: list(store.frame(t).columns) for t in store.names()}
    violations = ey.unknown_exemption_columns(exemptions, columns)
    assert not violations, "\n".join(violations)


@pytest.mark.register("Q49")
@pytest.mark.parametrize("table", TABLES)
def test_no_value_from_another_election_year(config, store, settings, exemptions, table):
    violations, _ = ey.scan_table(
        table, store.frame(table), _key_column(config, store, table), settings["year"], exemptions
    )
    assert not violations, "\n".join(violations[:20])


def test_known_exceptions_still_apply(config, store, settings, exemptions):
    matched = set()
    for table in TABLES:
        _, hits = ey.scan_table(
            table, store.frame(table), _key_column(config, store, table), settings["year"], exemptions
        )
        matched |= hits
    violations = ey.stale_exception_violations(exemptions, matched)
    assert not violations, "\n".join(violations)


@pytest.mark.register("Q49")
def test_election_date(store, settings):
    violations = ey.election_date_violations(store.column(settings["date_column"]), settings["election_date"])
    assert not violations, "\n".join(violations)
