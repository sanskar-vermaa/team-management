# Security policy

## Reporting

Please report vulnerabilities privately through GitHub's **Report a vulnerability** button on the Security tab rather than a public issue.

## Design notes

- Uploaded files are parsed in memory and never written to disk or stored.
- Form posts require a CSRF token; the stateless JSON API needs none because it uses no cookies.
- Responses send a strict Content-Security-Policy (no inline scripts or styles), `X-Frame-Options: DENY` and `nosniff`.
- Uploads are limited by `MAX_UPLOAD_MB`, roster size and name length.
- Exported CSV and Excel cells that start with `=`, `+`, `-` or `@` are prefixed so spreadsheet apps don't run them as formulas.
- With `APP_ENV=production` the app refuses to start without a `SECRET_KEY`.
