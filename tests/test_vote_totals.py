"""Candidate votes reconcile exactly to race_total_votes."""

import pytest

from senate_validation.checks import votes


@pytest.fixture(scope="module")
def settings(config):
    return config.section("votes")


@pytest.fixture(scope="module")
def candidates(store, settings):
    return store.frame(settings["candidate_table"])


@pytest.fixture(scope="module")
def races(store, settings):
    return store.frame(settings["race_table"])


@pytest.mark.register("Q18")
def test_candidate_votes_sum_to_race_total(candidates, settings):
    violations = votes.candidate_sum_violations(candidates, settings["blank_votes_allowed_row_types"])
    assert not violations, "\n".join(violations)


@pytest.mark.register("Q18")
def test_race_table_total_matches_candidate_rows(candidates, races):
    violations = votes.race_total_agreement_violations(candidates, races)
    assert not violations, "\n".join(violations)


@pytest.mark.register("Q18", "Q45")
def test_every_logged_snapshot_reconciles(store, settings):
    observations = store.frame(settings["observation_table"])
    violations = votes.observation_sum_violations(observations, settings["observation_snapshot"])
    assert not violations, "\n".join(violations)


@pytest.mark.register("Q18", "Q22")
def test_number_of_counted_races(races, settings):
    assert len(votes.counted_races(races)) == settings["expected_counted_races"]


@pytest.mark.register("R04")
def test_leading_votes_is_the_top_candidates_votes(candidates, races):
    violations = votes.leading_votes_violations(candidates, races)
    assert not violations, "\n".join(violations)


@pytest.mark.register("Q23")
@pytest.mark.parametrize(
    "table_key, name_column",
    [("candidate_table", "candidate_name"), ("observation_table", "candidate_name_as_published")],
)
def test_overvotes_and_undervotes_are_not_vote_rows(store, settings, table_key, name_column):
    frame = store.frame(settings[table_key])
    violations = votes.ballot_handling_violations(frame, name_column, settings["ballot_handling_terms"])
    assert not violations, "\n".join(violations)
