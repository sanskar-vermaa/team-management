# Changelog

## 2.0.0

Rebuilt as a package with a test suite and production setup.

### Added
- Any number of roles read from the column headers, with per-role team counts
- Reproducible shuffling (seed shown on the results page) and a "Shuffle again" button
- Option to spread leftovers across teams instead of listing them
- Excel and CSV exports alongside an improved PDF; sample roster download
- CSV input and `.xls` support
- JSON API (`POST /api/teams`, `GET /api/health`)
- CSRF protection, Content-Security-Policy and other security headers, upload size limit
- Dark mode and a responsive layout
- 99 pytest tests at 100% coverage, ruff, GitHub Actions CI, Docker image, docker-compose, Vercel and Render configs

### Fixed
- `.xls` uploads always failed because `xlrd` was not installed
- The PDF route returned a 500 for malformed team data
- Pinned dependencies (pandas 2.2.2) could not be installed on Python 3.13
- The app started with `debug=True` when run directly
- Names stored as numbers showed up as `1042.0`
- Spreadsheet formulas in names were exported unescaped

## 1.1.0

- Validation, results preview, configurable developer count and styled PDF export

## 1.0.0

- First version: Dev/BA/DA team split from an Excel file with PDF download
