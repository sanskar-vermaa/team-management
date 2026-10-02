import io
import logging

import pytest

from team_builder.app import create_app
from team_builder.config import DEV_SECRET_KEY, check_config


def test_security_headers(client):
    res = client.get("/")
    assert "default-src 'self'" in res.headers["Content-Security-Policy"]
    assert res.headers["X-Frame-Options"] == "DENY"
    assert res.headers["X-Content-Type-Options"] == "nosniff"


def test_unknown_pages_redirect_home(client):
    res = client.get("/missing")
    assert res.status_code == 302
    assert res.headers["Location"] == "/"


def test_large_uploads_are_rejected_politely():
    app = create_app(
        {"TESTING": True, "WTF_CSRF_ENABLED": False, "SECRET_KEY": "t", "MAX_CONTENT_LENGTH": 1024}
    )
    client = app.test_client()
    res = client.post("/upload", data={"file": (io.BytesIO(b"x" * 4096), "big.csv")}, follow_redirects=True)
    assert b"larger than" in res.data

    api = client.post("/api/teams", data=b"x" * 4096, content_type="application/json")
    assert api.status_code == 413
    assert "larger than" in api.json["error"]


def test_forms_require_a_csrf_token():
    app = create_app({"TESTING": True, "SECRET_KEY": "t"})
    client = app.test_client()
    res = client.post("/upload", data={}, follow_redirects=True)
    assert b"Your session expired" in res.data


def test_the_json_api_does_not_need_csrf():
    app = create_app({"TESTING": True, "SECRET_KEY": "t"})
    res = app.test_client().post("/api/teams", json={"roster": {"Dev": ["a"]}, "composition": {"Dev": 1}})
    assert res.status_code == 200


def test_production_requires_a_secret_key():
    with pytest.raises(RuntimeError, match="SECRET_KEY must be set"):
        check_config({"SECRET_KEY": DEV_SECRET_KEY, "APP_ENV": "production"})


def test_development_warns_about_the_default_key(caplog):
    with caplog.at_level(logging.WARNING):
        check_config({"SECRET_KEY": DEV_SECRET_KEY, "APP_ENV": "development"})
    assert "SECRET_KEY is not set" in caplog.text


def test_a_real_key_passes():
    check_config({"SECRET_KEY": "x" * 40, "APP_ENV": "production"})


def test_entry_point_exposes_the_app():
    import app as entry

    assert entry.app.name == "team_builder.app"
