"""JSON API for integrations: POST a roster and composition, get teams back."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from team_builder import __version__
from team_builder.roster import RosterError, roster_from_mapping
from team_builder.teams import CompositionError, build_teams

bp = Blueprint("api", __name__, url_prefix="/api")


def error(message: str, status: int = 400):
    return jsonify({"error": message}), status


@bp.get("/health")
def health():
    return jsonify({"status": "ok", "version": __version__})


@bp.post("/teams")
def teams():
    """Build teams.

    Body: {"roster": {"Dev": ["Asha", ...], ...},
           "composition": {"Dev": 3, "BA": 1},
           "shuffle": false, "seed": null, "distribute_leftovers": false}
    """
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return error("Send a JSON object with 'roster' and 'composition'.")

    seed = body.get("seed")
    if seed is not None and (isinstance(seed, bool) or not isinstance(seed, int)):
        return error("'seed' must be an integer or null.")
    flags = {k: body.get(k, False) for k in ("shuffle", "distribute_leftovers")}
    if not all(isinstance(v, bool) for v in flags.values()):
        return error("'shuffle' and 'distribute_leftovers' must be booleans.")

    try:
        roster = roster_from_mapping(body.get("roster"))
        plan = build_teams(roster.roles, body.get("composition"), seed=seed, **flags)
    except (RosterError, CompositionError) as exc:
        return error(str(exc), 422)

    return jsonify(
        {
            **plan.to_dict(),
            "team_count": len(plan.teams),
            "leftover_count": plan.leftover_count,
            "warnings": roster.warnings,
        }
    )
