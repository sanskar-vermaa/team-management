"""Reading a roster spreadsheet into ``{role: [names]}``.

Each column of the sheet is a role and each non-empty cell is a person. Column
order is preserved, blank cells and "Unnamed" filler columns are ignored, and
names are trimmed and de-duplicated within a role.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import BinaryIO

import pandas as pd

SUPPORTED_EXTENSIONS = (".xlsx", ".xls", ".csv")
MAX_ROLES = 20
MAX_PEOPLE = 5000
MAX_NAME_LENGTH = 100


class RosterError(ValueError):
    """The uploaded file can't be turned into a roster."""


@dataclass
class Roster:
    roles: dict[str, list[str]]
    warnings: list[str] = field(default_factory=list)

    @property
    def total_people(self) -> int:
        return sum(len(names) for names in self.roles.values())


def _clean_name(value: object) -> str:
    text = str(value).strip()
    # Spreadsheets store numeric ids as floats: 1042 -> 1042.0
    if text.endswith(".0") and text[:-2].isdigit():
        text = text[:-2]
    return text


def roster_from_mapping(mapping: dict[str, list[object]]) -> Roster:
    """Validate and clean an already-parsed ``{role: names}`` mapping."""
    if not isinstance(mapping, dict):
        raise RosterError("Roster must map role names to lists of people.")

    roles: dict[str, list[str]] = {}
    warnings: list[str] = []
    for raw_role, raw_names in mapping.items():
        role = _clean_name(raw_role)
        if not role or role.lower().startswith("unnamed"):
            continue
        if len(role) > MAX_NAME_LENGTH:
            raise RosterError(f"Role name is too long: {role[:20]}…")
        if role in roles:
            raise RosterError(f"Role '{role}' appears more than once.")
        if not isinstance(raw_names, list):
            raise RosterError(f"People for role '{role}' must be a list.")

        names: list[str] = []
        seen: set[str] = set()
        for value in raw_names:
            if value is None or (not isinstance(value, (list, dict)) and pd.isna(value)):
                continue
            name = _clean_name(value)
            if not name:
                continue
            if len(name) > MAX_NAME_LENGTH:
                raise RosterError(f"Name is too long in role '{role}': {name[:20]}…")
            if name.casefold() in seen:
                warnings.append(f"Removed duplicate '{name}' from {role}.")
                continue
            seen.add(name.casefold())
            names.append(name)
        roles[role] = names

    if not roles:
        raise RosterError("No roles found. Put each role in its own column with a header.")
    if len(roles) > MAX_ROLES:
        raise RosterError(f"Too many roles ({len(roles)}); the limit is {MAX_ROLES}.")
    total = sum(len(n) for n in roles.values())
    if total == 0:
        raise RosterError("The roster has role columns but no people in them.")
    if total > MAX_PEOPLE:
        raise RosterError(f"Too many people ({total}); the limit is {MAX_PEOPLE}.")

    for role, names in roles.items():
        if not names:
            warnings.append(f"Role '{role}' has no people.")
    return Roster(roles=roles, warnings=warnings)


def read_roster(stream: BinaryIO, filename: str) -> Roster:
    """Parse an uploaded .xlsx, .xls or .csv file."""
    ext = os.path.splitext(filename or "")[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise RosterError("Unsupported file type. Upload a .xlsx, .xls or .csv file.")

    try:
        if ext == ".csv":
            frame = pd.read_csv(stream, dtype=str, skip_blank_lines=True)
        else:
            frame = pd.read_excel(stream, dtype=str)
    except Exception as exc:  # pandas raises many different parser errors
        raise RosterError("Could not read that file. Make sure it is a valid spreadsheet.") from exc

    mapping = {str(col): frame[col].tolist() for col in frame.columns}
    return roster_from_mapping(mapping)
