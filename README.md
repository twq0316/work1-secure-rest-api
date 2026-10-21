# Secure REST API for Work 1

This repository contains the Work 1 Flask API, automated tests, a GitHub
Actions security pipeline, and a documented CVE laboratory procedure.

## Requirements

- Python 3.11 or later
- Git
- Docker Desktop with Docker Compose
- Postman or curl
- A GitHub or GitLab account
- A Snyk account and repository secret named `SNYK_TOKEN`

Create and activate a virtual environment:

```powershell
cd work1
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

Set the environment variables before starting the application:

```powershell
$env:JWT_SECRET = "replace-with-a-long-random-secret"
$env:DEMO_USERNAME = "alice"
$env:DEMO_PASSWORD = "ChangeMe-OnlyForLocal-123!"
python -m flask --app run.py init-db
python run.py
```

The server listens on `http://127.0.0.1:5000`.

## API

### `POST /auth/login`

Request:

```json
{
  "username": "alice",
  "password": "ChangeMe-OnlyForLocal-123!"
}
```

Success response:

```json
{
  "access_token": "<jwt>",
  "scheme": "Bearer"
}
```

### `GET /api/data`

Requires `Authorization: Bearer <jwt>`. The endpoint returns only records owned
by the authenticated user. Returned user-controlled strings are HTML-escaped.

### `POST /api/items`

Requires `Authorization: Bearer <jwt>`. This third endpoint accepts:

```json
{
  "title": "Example title",
  "content": "Example content"
}
```

It inserts the item with a parameterized SQL statement and returns the escaped
values in the JSON response.

## Call the API

Log in and keep the token in a PowerShell variable:

```powershell
$loginBody = '{"username":"alice","password":"ChangeMe-OnlyForLocal-123!"}'
$login = Invoke-RestMethod `
  -Uri 'http://127.0.0.1:5000/auth/login' `
  -Method Post `
  -ContentType 'application/json' `
  -Body $loginBody
$headers = @{ Authorization = "Bearer $($login.access_token)" }
```

Call the protected endpoints:

```powershell
Invoke-RestMethod -Uri 'http://127.0.0.1:5000/api/data' -Headers $headers

$itemBody = '{"title":"Demo","content":"Authenticated content"}'
Invoke-RestMethod `
  -Uri 'http://127.0.0.1:5000/api/items' `
  -Method Post `
  -Headers $headers `
  -ContentType 'application/json' `
  -Body $itemBody
```

Use these requests for the required screenshots:

```powershell
# No authorization header: expected HTTP 401.
try {
  Invoke-WebRequest -Uri 'http://127.0.0.1:5000/api/data' -UseBasicParsing
} catch {
  $_.Exception.Response.StatusCode.value__
}

# SQL injection attempt: expected HTTP 401.
$sqliBody = '{"username":"alice'' OR ''1''=''1","password":"x"}'
try {
  Invoke-RestMethod `
    -Uri 'http://127.0.0.1:5000/auth/login' `
    -Method Post `
    -ContentType 'application/json' `
    -Body $sqliBody
} catch {
  $_.Exception.Response.StatusCode.value__
}

# XSS payload: expected escaped HTML entities in the response.
$xssBody = '{"title":"<script>alert(1)</script>","content":"<img src=x onerror=alert(1)>"}'
Invoke-RestMethod `
  -Uri 'http://127.0.0.1:5000/api/items' `
  -Method Post `
  -Headers $headers `
  -ContentType 'application/json' `
  -Body $xssBody
```

## Security implementation

SQL injection is prevented in `secure_api/db.py` and `secure_api/routes.py` by
using SQLite parameter placeholders (`?`). User input is never concatenated into
an SQL string.

Cross-site scripting protection is implemented at the response boundary in
`secure_api/routes.py`. MarkupSafe `escape()` encodes HTML-significant
characters before user-controlled values are returned by the API.

Authentication uses bcrypt password hashes with a configurable cost factor.
Successful login issues a signed JWT containing `sub`, `username`, `iat`, and
`exp`. The `auth_required` decorator verifies signature, algorithm, expiry, and
the user record before a protected handler runs.

## Tests and scans

```powershell
python -m pytest -q
bandit -r secure_api -f txt
```

The GitHub Actions workflow runs pytest, Bandit SAST, and Snyk SCA on every push
and pull request. Save a screenshot of the successful workflow under
`evidence/screenshots/`.

## CVE laboratory

The selected vulnerability and the exact reproduction/fix procedure are in
`cve/CVE-2019-14234/README.md`. CVE-2019-14234 is a SQL injection vulnerability
in Django JSONField/HStoreField lookups affecting versions before 2.2.4,
2.1.11, and 1.11.23. The `cve/CVE-2019-14234/fix/` directory contains the
patched Compose configuration to attach to the final submission.

