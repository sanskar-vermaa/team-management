import io
import json

import pandas as pd
import pytest

from team_builder.app import create_app


@pytest.fixture
def app():
    return create_app({"TESTING": True, "WTF_CSRF_ENABLED": False, "SECRET_KEY": "test"})


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def roster_xlsx():
    def make(data=None):
        data = data or {
            "Dev": ["d1", "d2", "d3", "d4", "d5", "d6", "d7"],
            "BA": ["b1", "b2", None, None, None, None, None],
            "DA": ["a1", "a2", "a3", None, None, None, None],
        }
        buf = io.BytesIO()
        pd.DataFrame(data).to_excel(buf, index=False)
        buf.seek(0)
        return buf

    return make


ROSTER = {"Dev": ["d1", "d2", "d3", "d4", "d5", "d6", "d7"], "BA": ["b1", "b2"], "DA": ["a1", "a2", "a3"]}


@pytest.fixture
def roster_json():
    return json.dumps(ROSTER)
