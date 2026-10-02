import io

import pandas as pd
import pytest

from team_builder.roster import MAX_PEOPLE, RosterError, read_roster, roster_from_mapping


def xlsx(data: dict) -> io.BytesIO:
    buf = io.BytesIO()
    pd.DataFrame({k: pd.Series(v, dtype=object) for k, v in data.items()}).to_excel(buf, index=False)
    buf.seek(0)
    return buf


def test_reads_xlsx_columns_as_roles_in_order():
    roster = read_roster(xlsx({"Dev": ["Asha", "Ben", "Chen"], "QA": ["Dina", None, None]}), "team.xlsx")
    assert list(roster.roles) == ["Dev", "QA"]
    assert roster.roles == {"Dev": ["Asha", "Ben", "Chen"], "QA": ["Dina"]}
    assert roster.total_people == 4


def test_reads_csv():
    data = io.BytesIO("Dev,BA\nAsha,Ravi\nBen,\n".encode())
    assert read_roster(data, "roster.CSV").roles == {"Dev": ["Asha", "Ben"], "BA": ["Ravi"]}


def test_csv_keeps_unicode_names():
    data = io.BytesIO("Dev\nAnanyā\nसंस्कार\n".encode())
    assert read_roster(data, "r.csv").roles["Dev"] == ["Ananyā", "संस्कार"]


def test_trims_names_and_drops_blanks():
    roster = roster_from_mapping({" Dev ": ["  Asha ", "", "   ", None, float("nan")]})
    assert roster.roles == {"Dev": ["Asha"]}


def test_numeric_ids_lose_the_float_suffix():
    assert roster_from_mapping({"Dev": [1042.0, "1043.0", 7]}).roles["Dev"] == ["1042", "1043", "7"]


def test_removes_duplicates_case_insensitively_with_a_warning():
    roster = roster_from_mapping({"Dev": ["Asha", "asha", "Ben"]})
    assert roster.roles["Dev"] == ["Asha", "Ben"]
    assert roster.warnings == ["Removed duplicate 'asha' from Dev."]


def test_skips_unnamed_filler_columns():
    roster = read_roster(xlsx({"Dev": ["Asha"], "Unnamed: 1": ["x"]}), "t.xlsx")
    assert list(roster.roles) == ["Dev"]


def test_warns_about_empty_roles():
    roster = roster_from_mapping({"Dev": ["Asha"], "QA": []})
    assert roster.warnings == ["Role 'QA' has no people."]


@pytest.mark.parametrize("name", ["team.pdf", "team.txt", "team", ""])
def test_rejects_unsupported_files(name):
    with pytest.raises(RosterError, match="Unsupported file type"):
        read_roster(io.BytesIO(b"x"), name)


def test_rejects_corrupt_spreadsheets():
    with pytest.raises(RosterError, match="Could not read"):
        read_roster(io.BytesIO(b"definitely not a zip"), "team.xlsx")


@pytest.mark.parametrize(
    ("mapping", "message"),
    [
        ([], "must map role names"),
        ({}, "No roles found"),
        ({"Unnamed: 0": ["a"]}, "No roles found"),
        ({"Dev": [], "BA": []}, "no people"),
        ({"Dev": "Asha"}, "must be a list"),
        ({"Dev": ["Asha"], " Dev": ["Ben"]}, "appears more than once"),
        ({"D" * 101: ["a"]}, "Role name is too long"),
        ({"Dev": ["x" * 101]}, "Name is too long"),
        ({f"R{i}": ["a"] for i in range(21)}, "Too many roles"),
        ({"Dev": [f"p{i}" for i in range(MAX_PEOPLE + 1)]}, "Too many people"),
    ],
)
def test_rejects_invalid_rosters(mapping, message):
    with pytest.raises(RosterError, match=message):
        roster_from_mapping(mapping)
