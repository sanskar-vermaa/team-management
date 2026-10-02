"""Splitting a roster into teams.

A *composition* says how many people of each role go into one team, e.g.
``{"Dev": 3, "BA": 1, "DA": 1}``. The number of teams is limited by the role
that runs out first. People who don't fit are either reported as leftovers
or spread across the existing teams round-robin.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

MAX_PER_ROLE = 50


class CompositionError(ValueError):
    """The requested team composition can't be applied to the roster."""


@dataclass
class TeamPlan:
    teams: list[dict[str, list[str]]]
    leftovers: dict[str, list[str]] = field(default_factory=dict)

    @property
    def leftover_count(self) -> int:
        return sum(len(v) for v in self.leftovers.values())

    def to_dict(self) -> dict:
        return {"teams": self.teams, "leftovers": self.leftovers}


def validate_composition(roles: dict[str, list[str]], composition: dict[str, int]) -> dict[str, int]:
    if not isinstance(composition, dict) or not composition:
        raise CompositionError("Choose how many people of each role go into a team.")

    clean: dict[str, int] = {}
    for role, count in composition.items():
        if role not in roles:
            raise CompositionError(f"Unknown role '{role}'.")
        if isinstance(count, bool) or not isinstance(count, int):
            raise CompositionError(f"Count for '{role}' must be a whole number.")
        if count < 0 or count > MAX_PER_ROLE:
            raise CompositionError(f"Count for '{role}' must be between 0 and {MAX_PER_ROLE}.")
        clean[role] = count

    if not any(clean.values()):
        raise CompositionError("At least one role needs a count above zero.")
    return clean


def build_teams(
    roles: dict[str, list[str]],
    composition: dict[str, int],
    *,
    shuffle: bool = False,
    seed: int | None = None,
    distribute_leftovers: bool = False,
) -> TeamPlan:
    """Return teams built from ``roles`` following ``composition``.

    Roles missing from the composition are treated as count 0. ``seed`` makes
    a shuffled split reproducible.
    """
    composition = validate_composition(roles, composition)
    pools = {role: list(names) for role, names in roles.items()}
    if shuffle:
        rng = random.Random(seed)  # noqa: S311 - reproducible shuffles, not security
        for names in pools.values():
            rng.shuffle(names)

    needed = {role: composition.get(role, 0) for role in pools}
    team_count = min(len(pools[role]) // count for role, count in needed.items() if count > 0)
    if team_count == 0:
        short = [
            f"{role} (need {count}, have {len(pools[role])})"
            for role, count in needed.items()
            if count > len(pools[role])
        ]
        raise CompositionError("Not enough people for even one team: " + ", ".join(short) + ".")

    teams: list[dict[str, list[str]]] = [{} for _ in range(team_count)]
    leftovers: dict[str, list[str]] = {}
    for role, names in pools.items():
        count = needed[role]
        for i, team in enumerate(teams):
            team[role] = names[i * count : (i + 1) * count]
        rest = names[team_count * count :]
        if not rest:
            continue
        if distribute_leftovers:
            for i, name in enumerate(rest):
                teams[i % team_count][role].append(name)
        else:
            leftovers[role] = rest

    # Drop empty role lists so output only shows roles each team actually has.
    teams = [{role: names for role, names in team.items() if names} for team in teams]
    return TeamPlan(teams=teams, leftovers=leftovers)


def plan_from_dict(data: object) -> TeamPlan:
    """Rebuild a plan that came back from the browser (e.g. for export)."""
    if not isinstance(data, dict) or not isinstance(data.get("teams"), list):
        raise CompositionError("Invalid team data.")

    def names_map(obj: object) -> dict[str, list[str]]:
        if not isinstance(obj, dict):
            raise CompositionError("Invalid team data.")
        out: dict[str, list[str]] = {}
        for role, names in obj.items():
            if not isinstance(role, str) or not isinstance(names, list):
                raise CompositionError("Invalid team data.")
            if not all(isinstance(n, str) for n in names):
                raise CompositionError("Invalid team data.")
            out[role] = names
        return out

    teams = [names_map(team) for team in data["teams"]]
    if not teams:
        raise CompositionError("There are no teams to export.")
    return TeamPlan(teams=teams, leftovers=names_map(data.get("leftovers") or {}))
