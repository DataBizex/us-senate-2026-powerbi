"""Headline eligibility and the rating quarantine."""

import pytest

from senate_validation.checks import eligibility


@pytest.fixture(scope="module")
def headline(config):
    return config.section("headline")


@pytest.fixture(scope="module")
def flags(store, headline):
    return store.frame(headline["flags_table"])


@pytest.mark.parametrize("column_key", ["eligible_column", "integrity_column"])
def test_flags_are_y_or_n(flags, headline, column_key):
    violations = eligibility.yes_no_violations(flags, headline[column_key])
    assert not violations, "\n".join(violations)


@pytest.mark.register("R02", "R03", "Q51")
def test_headline_only_for_official_complete_unflagged_counts(store, headline):
    violations = eligibility.headline_violations(store, headline)
    assert not violations, "\n".join(violations)


@pytest.mark.register("R02")
def test_every_qualifying_race_is_headline(store, headline):
    violations = eligibility.headline_omissions(store, headline)
    assert not violations, "\n".join(violations)


@pytest.mark.register("R02")
def test_headline_races_are_the_ones_named_in_r02(store, headline):
    violations = eligibility.expected_set_violations(store, headline)
    assert not violations, "\n".join(violations)


@pytest.mark.register("R03", "Q51")
def test_integrity_flag_excludes_regardless_of_completeness(flags, headline):
    flagged = flags[flags[headline["integrity_column"]] == "Y"]
    included = flagged[flagged[headline["eligible_column"]] != "N"]
    assert included.empty, f"integrity-flagged races in headline figures: {included['race_id'].tolist()}"


@pytest.mark.register("Q33")
def test_every_rating_is_quarantined(store, config):
    ratings = config.section("ratings")
    violations = eligibility.required_value_violations(
        store.frame(ratings["table"]), ratings["column"], ratings["required"]
    )
    assert not violations, "\n".join(violations)
