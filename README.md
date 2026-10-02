# Team Builder

Split a roster spreadsheet into balanced teams in seconds. Upload an Excel or CSV file with one column per role, choose how many people of each role go into a team, and download the result as PDF, Excel or CSV. A JSON API exposes the same engine for integrations.

**Stack:** Python 3.11+ · Flask 3 · pandas · openpyxl · ReportLab · Flask-WTF · gunicorn · pytest · Docker · GitHub Actions

## Features

- **Any roles.** Every column header is a role (Dev, BA, DA, QA, Designer…); no fixed schema
- **Custom compositions.** e.g. 3 Dev + 1 BA + 1 DA per team; set a role to 0 to keep it out of the core team
- **Fair splits.** Optional shuffling with a displayed seed so any split can be reproduced; leftovers listed or spread round-robin
- **Clear errors.** "Not enough people for even one team: BA (need 3, have 2)"
- **Clean input.** Trims names, removes duplicates (with a warning), fixes `1042.0`-style ids, skips blank and filler columns
- **Exports.** Styled PDF, Excel workbook (summary plus one sheet per team) and Excel-friendly UTF-8 CSV with formula-injection protection
- **JSON API.** `POST /api/teams` for scripts and other apps ([docs](docs/API.md))
- **Secure by default.** CSRF tokens, strict Content-Security-Policy, upload size limits, production secret-key check
- **Quality.** 99 tests at 100% coverage, ruff lint and format, CI on Python 3.11 to 3.13 with a Docker smoke test

## Quick start

### Docker

```bash
docker compose up --build
```

Open <http://localhost:8000> and upload [`examples/roster.csv`](examples/roster.csv) or download the sample from the app.

### Local

```bash
python -m venv .venv && source .venv/bin/activate
make install
make dev           # http://127.0.0.1:5000
```

## Roster format

The first row holds role names; each cell below is a person. Columns can have different lengths.

| Dev | BA | DA |
| --- | --- | --- |
| Asha Rao | Hiro Tanaka | Jonas Berg |
| Ben Clarke | Isha Verma | Kavya Nair |
| Chen Wei | | Liam O'Brien |

Supported files: `.xlsx`, `.xls`, `.csv` (up to 20 roles, 5,000 people, 2 MB by default).

## API example

```bash
curl -X POST http://localhost:8000/api/teams \
  -H 'Content-Type: application/json' \
  -d '{"roster": {"Dev": ["Asha", "Ben", "Chen", "Diego"], "QA": ["Maya", "Noah"]},
       "composition": {"Dev": 2, "QA": 1},
       "shuffle": true, "seed": 42}'
```

```json
{
  "team_count": 2,
  "teams": [{"Dev": ["Chen", "Ben"], "QA": ["Noah"]}, {"Dev": ["Diego", "Asha"], "QA": ["Maya"]}],
  "leftovers": {},
  "leftover_count": 0,
  "warnings": []
}
```

Full reference: [docs/API.md](docs/API.md).

## Configuration

| Variable | Default | Description |
| --- | --- | --- |
| `SECRET_KEY` | dev key | Signs sessions and CSRF tokens. **Required when `APP_ENV=production`** |
| `APP_ENV` | `development` | `production` enables the secret-key check and secure cookies |
| `MAX_UPLOAD_MB` | `2` | Largest accepted upload |
| `PORT` | `8000` | Port in the Docker image |
| `WEB_CONCURRENCY` | `2` | gunicorn workers in the Docker image |

## Deployment

- **Vercel:** import the repository; Vercel serves the Flask app from `app.py`. Set `SECRET_KEY` and `APP_ENV=production` in the project's environment variables.
- **Render:** New → Blueprint uses [`render.yaml`](render.yaml) and generates `SECRET_KEY`.
- **Any Docker host:** `docker run -p 8000:8000 -e SECRET_KEY=... ghcr.io/you/team-builder` (build with `docker build -t team-builder .`).

The app is stateless (rosters and plans travel with the form), so it scales horizontally without shared storage.

## Development

```bash
make test     # pytest with coverage
make lint     # ruff check + format check
make format   # apply fixes
```

```
app.py                  entry point (flask, gunicorn, Vercel)
team_builder/
  roster.py             spreadsheet -> {role: [names]} with cleaning and limits
  teams.py              composition validation, shuffling, leftovers
  exporters.py          PDF, Excel and CSV output
  web.py                upload -> compose -> results -> export pages
  api.py                JSON API
  app.py                app factory, CSRF, security headers, error pages
  templates/, static/   UI
tests/                  pytest suite
```

## License

[MIT](LICENSE)
