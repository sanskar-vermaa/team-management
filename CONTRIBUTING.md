# Contributing

```bash
python -m venv .venv && source .venv/bin/activate
make install
make test lint
```

- Keep `roster.py` and `teams.py` free of Flask imports; they are the engine behind both the web pages and the API.
- Every bug fix comes with a test. Coverage is enforced at 95% in CI.
- Run `make format` before committing.
- Update `docs/API.md` and `CHANGELOG.md` when behaviour changes.
