import pytest

from tests.conftest import ROSTER


def test_health(client):
    res = client.get("/api/health")
    assert res.json == {"status": "ok", "version": "2.0.0"}


def test_build_teams(client):
    res = client.post("/api/teams", json={"roster": ROSTER, "composition": {"Dev": 3, "BA": 1, "DA": 1}})
    assert res.status_code == 200
    body = res.json
    assert body["team_count"] == 2
    assert body["leftover_count"] == 2
    assert body["teams"][0] == {"Dev": ["d1", "d2", "d3"], "BA": ["b1"], "DA": ["a1"]}
    assert body["warnings"] == []


def test_build_teams_with_options(client):
    payload = {
        "roster": ROSTER,
        "composition": {"Dev": 3, "BA": 1, "DA": 1},
        "shuffle": True,
        "seed": 5,
        "distribute_leftovers": True,
    }
    first = client.post("/api/teams", json=payload).json
    assert first == client.post("/api/teams", json=payload).json
    assert first["leftover_count"] == 0


def test_reports_roster_warnings(client):
    res = client.post("/api/teams", json={"roster": {"Dev": ["a", "A", "b"]}, "composition": {"Dev": 1}})
    assert res.json["warnings"] == ["Removed duplicate 'A' from Dev."]


@pytest.mark.parametrize(
    ("payload", "status", "message"),
    [
        (None, 400, "Send a JSON object"),
        ([], 400, "Send a JSON object"),
        ({"roster": ROSTER, "composition": {"Dev": 1}, "seed": "x"}, 400, "'seed' must be"),
        ({"roster": ROSTER, "composition": {"Dev": 1}, "seed": True}, 400, "'seed' must be"),
        ({"roster": ROSTER, "composition": {"Dev": 1}, "shuffle": "yes"}, 400, "must be booleans"),
        ({"roster": "nope", "composition": {"Dev": 1}}, 422, "must map role names"),
        ({"roster": ROSTER, "composition": {"PM": 1}}, 422, "Unknown role"),
        ({"roster": ROSTER, "composition": {"BA": 3}}, 422, "Not enough people"),
    ],
)
def test_rejects_bad_requests(client, payload, status, message):
    res = (
        client.post("/api/teams", json=payload)
        if payload is not None
        else client.post("/api/teams", data="not json", content_type="application/json")
    )
    assert res.status_code == status
    assert message in res.json["error"]


def test_unknown_api_routes_are_json_404s(client):
    res = client.get("/api/nope")
    assert res.status_code == 404
    assert res.json == {"error": "Not found."}
