"""HTML pages: upload a roster, choose a composition, review and export."""

from __future__ import annotations

import io
import json
import secrets

import pandas as pd
from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)

from team_builder.exporters import EXPORTERS
from team_builder.roster import SUPPORTED_EXTENSIONS, RosterError, read_roster, roster_from_mapping
from team_builder.teams import MAX_PER_ROLE, CompositionError, build_teams, plan_from_dict

bp = Blueprint("web", __name__)

# Sensible starting counts for the classic Dev/BA/DA roster.
DEFAULT_COUNTS = {"dev": 3, "developer": 3, "developers": 3}


def _load_json(field: str):
    try:
        return json.loads(request.form.get(field, ""))
    except (TypeError, ValueError):
        return None


def _int_field(name: str, default: int | None = None) -> int | None:
    raw = (request.form.get(name) or "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return None


@bp.get("/")
def index():
    return render_template("index.html", extensions=", ".join(SUPPORTED_EXTENSIONS))


@bp.post("/upload")
def upload():
    file = request.files.get("file")
    if not file or not file.filename:
        flash("Please choose a roster file to upload.", "error")
        return redirect(url_for("web.index"))
    try:
        roster = read_roster(file.stream, file.filename)
    except RosterError as exc:
        flash(str(exc), "error")
        return redirect(url_for("web.index"))

    for warning in roster.warnings:
        flash(warning, "warning")
    counts = {role: DEFAULT_COUNTS.get(role.lower(), 1) for role in roster.roles}
    return render_template(
        "configure.html",
        roster=roster.roles,
        roster_json=json.dumps(roster.roles),
        counts=counts,
        max_per_role=MAX_PER_ROLE,
        filename=file.filename,
    )


@bp.post("/teams")
def teams():
    try:
        roster = roster_from_mapping(_load_json("roster_json"))
    except RosterError:
        flash("Your roster expired or was changed. Please upload it again.", "error")
        return redirect(url_for("web.index"))

    composition = {}
    for i, role in enumerate(roster.roles):
        value = _int_field(f"count_{i}", 0)
        if value is None:
            flash(f"Count for {role} must be a whole number.", "error")
            return redirect(url_for("web.index"))
        composition[role] = value

    shuffle = request.form.get("shuffle") == "on"
    distribute = request.form.get("distribute") == "on"
    seed = _int_field("seed")
    if shuffle and seed is None:
        # Pick a seed so the user can reproduce (or share) this exact split.
        seed = secrets.randbelow(900_000) + 100_000
    try:
        plan = build_teams(
            roster.roles,
            composition,
            shuffle=shuffle,
            seed=seed,
            distribute_leftovers=distribute,
        )
    except CompositionError as exc:
        flash(str(exc), "error")
        return render_template(
            "configure.html",
            roster=roster.roles,
            roster_json=json.dumps(roster.roles),
            counts=composition,
            max_per_role=MAX_PER_ROLE,
            shuffle=shuffle,
            distribute=distribute,
        ), 422

    return render_template(
        "results.html",
        plan=plan,
        plan_json=json.dumps(plan.to_dict()),
        roster_json=json.dumps(roster.roles),
        composition=composition,
        shuffle=shuffle,
        seed=seed if shuffle else None,
        distribute=distribute,
    )


@bp.post("/export/<fmt>")
def export(fmt: str):
    if fmt not in EXPORTERS:
        abort(404)
    try:
        plan = plan_from_dict(_load_json("plan_json"))
    except CompositionError:
        flash("Nothing to export. Generate teams first.", "error")
        return redirect(url_for("web.index"))
    render, mimetype = EXPORTERS[fmt]
    return send_file(render(plan), mimetype=mimetype, as_attachment=True, download_name=f"teams.{fmt}")


@bp.get("/sample-roster.xlsx")
def sample_roster():
    frame = pd.DataFrame(
        {
            "Dev": [
                "Asha Rao",
                "Ben Clarke",
                "Chen Wei",
                "Diego Lopez",
                "Elena Petrova",
                "Farhan Ali",
                "Grace Kim",
            ],
            "BA": ["Hiro Tanaka", "Isha Verma", None, None, None, None, None],
            "DA": ["Jonas Berg", "Kavya Nair", "Liam O'Brien", None, None, None, None],
        }
    )
    out = io.BytesIO()
    frame.to_excel(out, index=False)
    out.seek(0)
    return send_file(
        out,
        mimetype=EXPORTERS["xlsx"][1],
        as_attachment=True,
        download_name="sample-roster.xlsx",
    )
