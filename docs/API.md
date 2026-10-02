# API reference

All endpoints return JSON. No authentication or CSRF token is needed; the API holds no state.

## `GET /api/health`

```json
{"status": "ok", "version": "2.0.0"}
```

## `POST /api/teams`

Build teams from a roster.

### Request body

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `roster` | object | yes | `{ "Role": ["Name", ...], ... }`. Up to 20 roles and 5,000 people; names up to 100 characters |
| `composition` | object | yes | People per team for each role, `0`–`50`. Roles left out count as `0` |
| `shuffle` | boolean | no | Shuffle each role before splitting (default `false`) |
| `seed` | integer \| null | no | Makes a shuffle reproducible |
| `distribute_leftovers` | boolean | no | Spread people who don't fill a team across teams round-robin (default `false`) |

Names are trimmed and de-duplicated case-insensitively within a role; removed duplicates are reported in `warnings`.

### Response `200`

```json
{
  "teams": [{"Dev": ["Asha", "Ben"], "QA": ["Maya"]}],
  "leftovers": {"Dev": ["Chen"]},
  "team_count": 1,
  "leftover_count": 1,
  "warnings": []
}
```

The number of teams is set by the scarcest role: `min(len(roster[role]) // count)` over roles with a count above zero.

### Errors

| Status | When | Example `error` |
| --- | --- | --- |
| `400` | Body isn't a JSON object, or `seed`/flags have the wrong type | `'seed' must be an integer or null.` |
| `413` | Body larger than `MAX_UPLOAD_MB` | `Request is larger than 2 MB.` |
| `422` | Roster or composition can't be used | `Not enough people for even one team: QA (need 2, have 1).` |

## Example (Python)

```python
import requests

resp = requests.post(
    "https://your-host/api/teams",
    json={
        "roster": {"Dev": ["Asha", "Ben", "Chen", "Diego"], "QA": ["Maya", "Noah"]},
        "composition": {"Dev": 2, "QA": 1},
        "shuffle": True,
        "seed": 42,
    },
    timeout=10,
)
resp.raise_for_status()
for i, team in enumerate(resp.json()["teams"], 1):
    print(f"Team {i}:", team)
```
