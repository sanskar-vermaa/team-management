import pytest

from team_builder.teams import CompositionError, TeamPlan, build_teams, plan_from_dict

ROSTER = {
    "Dev": ["d1", "d2", "d3", "d4", "d5", "d6", "d7"],
    "BA": ["b1", "b2"],
    "DA": ["a1", "a2", "a3"],
}
CLASSIC = {"Dev": 3, "BA": 1, "DA": 1}


def everyone(plan: TeamPlan) -> list[str]:
    names = [n for team in plan.teams for members in team.values() for n in members]
    names += [n for members in plan.leftovers.values() for n in members]
    return sorted(names)


def test_team_count_is_limited_by_the_scarcest_role():
    plan = build_teams(ROSTER, CLASSIC)
    assert len(plan.teams) == 2
    assert plan.teams[0] == {"Dev": ["d1", "d2", "d3"], "BA": ["b1"], "DA": ["a1"]}
    assert plan.leftovers == {"Dev": ["d7"], "DA": ["a3"]}
    assert plan.leftover_count == 2


def test_nobody_is_lost_or_duplicated():
    for distribute in (False, True):
        plan = build_teams(ROSTER, CLASSIC, shuffle=True, seed=7, distribute_leftovers=distribute)
        assert everyone(plan) == sorted(n for names in ROSTER.values() for n in names)


def test_distributing_leftovers_spreads_them_round_robin():
    plan = build_teams(ROSTER, CLASSIC, distribute_leftovers=True)
    assert plan.leftovers == {}
    assert plan.teams[0]["Dev"] == ["d1", "d2", "d3", "d7"]
    assert plan.teams[0]["DA"] == ["a1", "a3"]
    assert plan.teams[1]["DA"] == ["a2"]


def test_shuffle_is_reproducible_with_a_seed():
    a = build_teams(ROSTER, CLASSIC, shuffle=True, seed=42)
    b = build_teams(ROSTER, CLASSIC, shuffle=True, seed=42)
    c = build_teams(ROSTER, CLASSIC, shuffle=True, seed=43)
    assert a == b
    assert a != c


def test_shuffle_does_not_modify_the_input():
    roster = {k: list(v) for k, v in ROSTER.items()}
    build_teams(roster, CLASSIC, shuffle=True, seed=1)
    assert roster == ROSTER


def test_roles_with_zero_count_are_leftovers_or_spread():
    plan = build_teams(ROSTER, {"Dev": 2, "BA": 0, "DA": 0})
    assert len(plan.teams) == 3
    assert plan.leftovers == {"Dev": ["d7"], "BA": ["b1", "b2"], "DA": ["a1", "a2", "a3"]}
    assert all(set(team) == {"Dev"} for team in plan.teams)

    spread = build_teams(ROSTER, {"Dev": 2, "BA": 0, "DA": 0}, distribute_leftovers=True)
    assert spread.teams[0]["BA"] == ["b1"]
    assert "BA" not in spread.teams[2]


def test_roles_left_out_of_the_composition_count_as_zero():
    plan = build_teams(ROSTER, {"Dev": 7})
    assert len(plan.teams) == 1
    assert plan.leftovers["BA"] == ["b1", "b2"]


def test_explains_which_roles_are_short():
    with pytest.raises(CompositionError, match=r"BA \(need 3, have 2\)"):
        build_teams(ROSTER, {"Dev": 1, "BA": 3})


@pytest.mark.parametrize(
    ("composition", "message"),
    [
        ({}, "Choose how many"),
        ([], "Choose how many"),
        ({"PM": 1}, "Unknown role 'PM'"),
        ({"Dev": "3"}, "whole number"),
        ({"Dev": 2.5}, "whole number"),
        ({"Dev": True}, "whole number"),
        ({"Dev": -1}, "between 0 and 50"),
        ({"Dev": 51}, "between 0 and 50"),
        ({"Dev": 0, "BA": 0}, "above zero"),
    ],
)
def test_rejects_invalid_compositions(composition, message):
    with pytest.raises(CompositionError, match=message):
        build_teams(ROSTER, composition)


def test_plan_round_trips_through_dict():
    plan = build_teams(ROSTER, CLASSIC)
    assert plan_from_dict(plan.to_dict()) == plan


@pytest.mark.parametrize(
    "data",
    [
        None,
        [],
        {"teams": "x"},
        {"teams": []},
        {"teams": [["Dev"]]},
        {"teams": [{"Dev": "d1"}]},
        {"teams": [{"Dev": [1, 2]}]},
        {"teams": [{1: ["d1"]}]},
        {"teams": [{"Dev": ["d1"]}], "leftovers": ["x"]},
    ],
)
def test_plan_from_dict_rejects_tampered_data(data):
    with pytest.raises(CompositionError):
        plan_from_dict(data)
