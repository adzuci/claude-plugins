---
name: sec-python
description: >-
  Python backend security — FastAPI, Flask, Django: auth, IDOR/scoping,
  Pydantic validation, SQL injection, pickle/deserialization, command injection,
  SSRF, CORS, and AI anti-patterns. Use when writing or reviewing Python APIs,
  scripts, workers, or server-side automation.
---

# Python Backend Security

This skill covers server-side Python — APIs (FastAPI, Flask, Django), workers,
and scripts that handle untrusted input. **Apollo's baseline security rules
always apply**; this is the Python depth behind them.

**Related skills:** browser/client code → `sec-js`. Ruby/Rails → `sec-rails`.

**Questions?** App-security help, platform changes, and policy exceptions →
**#security-requests**.

## The one rule (plain language)

Every request body, query param, header, uploaded file, and job message is
**untrusted**. FastAPI's type hints and Pydantic models help, but they are not
authorization — you still must verify **who** the caller is and **what** they
are allowed to access on every protected endpoint.

## Top 10 easy wins

Apply these automatically, in priority order:

1. **Authenticate every protected route** — dependency/middleware/decorator on
   each handler, not only on the router mount.
1. **Authorize + scope data** — filter queries by tenant/user; never
   `db.get(Model, id=request_id)` without ownership check (IDOR).
1. **Validate at the boundary** — use what the project already has (Pydantic,
   Django/DRF serializers, dataclasses, argparse); don't add Pydantic just for
   validation. Reject bad input; don't pass raw `dict` from `request.json()`
   deeper into the app.
1. **ORM parameterized queries only** — SQLAlchemy/Django ORM bindings. No
   f-strings or `%` formatting in SQL.
1. **No secrets in code** — `os.environ`, `.env` in `.gitignore`, GCP Secret
   Manager in production. Never commit keys.
1. **Never `pickle.loads` on untrusted data** — RCE risk. Use JSON, msgpack with
   schema validation, or signed tokens.
1. **No shell with user input** — avoid `os.system`, `subprocess` with
   `shell=True` on request data.
1. **SSRF guard on outbound HTTP** — allowlist hosts when URL comes from users;
   block localhost and cloud metadata IPs.
1. **Lock down CORS** — allowlist origins; never `*` with credentials.
1. **Pin dependencies** — commit `requirements.txt`, `poetry.lock`, or
   `uv.lock`. Flag unfamiliar packages before adding.

## What AI must NOT do

Stop, explain the risk, and ask before generating any of these. This applies to
code you write or change; flag existing occurrences, don't stop on them.

| Never | Instead |
|----------|------------|
| `db.execute(f"SELECT ... {user_input}")` | SQLAlchemy `text()` with bound params or ORM filters |
| `pickle.loads(request.body)` or untrusted cache blobs | JSON + Pydantic; signed serialization |
| `eval()`, `exec()`, or `__import__()` on user strings | Parse with schema; allowlist operations |
| `os.system(user_input)` or `subprocess.run(..., shell=True)` | Argument list without shell; allowlist |
| `httpx.get(url_from_user)` without validation | Host allowlist; block private IP ranges |
| Hardcoded `API_KEY = "..."` in source | `os.environ["API_KEY"]`, sourced from GCP Secret Manager in production |
| `CORSMiddleware(allow_origins=["*"], allow_credentials=True)` | Explicit origin allowlist |
| `app.run(host="0.0.0.0")` in committed prod config without intent | Bind appropriately; confirm exposure |
| Trust JWT claims without signature verification | Verify with issuer secret/key; check `exp` |
| `DEBUG = True` or `app.debug = True` in production settings | Environment-based config; generic errors in prod |

## Stack cheat sheet

**FastAPI**

- Dependencies for auth: `Depends(get_current_user)` on every protected route.
- Pydantic models for request/response — `response_model` to avoid over-exposing
  ORM fields.
- Background tasks and `BackgroundTasks` still need authorization context passed
  explicitly.

**Flask**

- `@login_required` (Flask-Login) or custom decorator on every sensitive view.
- `request.args` / `request.form` validated before use; use WTForms or Marshmallow.
- Don't disable `WTF_CSRF` on session-backed forms without alternative.

**Django**

- `@login_required` / `PermissionRequiredMixin` on class views.
- ORM only: `.filter()`, `.get()` — never `.extra()` or raw SQL with interpolation.
- `DEBUG = False` in production; `ALLOWED_HOSTS` set explicitly.
- Admin at `/admin/` is a privileged surface — keep it behind strong auth and
  admin permissions, not Django's local password auth. Don't expose it on the
  public internet without extra controls.

**Async workers (Celery, RQ, ARQ)**

- Treat task arguments like HTTP params — re-validate and re-authorize in the
  task body.
- Don't pass pickled arbitrary objects from untrusted producers.

**Scripts & notebooks**

- Same rules apply when a script accepts CLI args or reads webhook files.
- Notebooks with production credentials are a leak risk — use env vars.

## Attack surfaces AI often misses

- **IDOR** — incrementing `?id=123` to access another user's row. Scope every
  read/update/delete.
- **Mass assignment** — Pydantic `model_config` or SQLAlchemy merging unchecked
  dicts into models (`**request.json()`).
- **Path traversal** — `open(os.path.join(UPLOAD_DIR, user_filename))` without
  `basename` / canonical path check.
- **Template injection** — Jinja2 `|safe` or `Environment(autoescape=False)`
  with user content → SSTI/XSS in HTML responses.
- **Open redirects** — `RedirectResponse(url=request.query_params["next"])`.
- **Over-sharing in OpenAPI** — auto-generated docs listing internal admin routes
  on public deployments.
- **Dependency confusion** — `pip install` of mistyped or typosquat package names
  suggested by AI.
- **LLM/agent tools** — Python glue that runs shell/SQL/file ops from model
  output needs the same sandboxing as user HTTP input.

## Injection & deserialization

- SQL: SQLAlchemy/Django ORM or `execute(text("..."), {"id": id})` with binds.
- NoSQL (Motor, pymongo): no string-built query documents from raw user input.
- Command: `subprocess.run([prog, arg], shell=False)` with validated `arg`.
- Deserialization: JSON/YAML (`safe_load` only) — never pickle/yaml.load on
  untrusted bytes.
- XML: defuse stdlib XML; beware billion-laughs and external entities.

## Auth, sessions & API keys

- Re-verify permissions per endpoint — global middleware is not enough if
  routes are added later without it.
- **Auth providers** — extend the app's existing auth stack. Adding or replacing
  an auth provider or auth library is a platform decision: route it to
  **#security-requests**.
- Never hand-roll password hashing, session, or token logic — no bare
  `hashlib`, no custom session tables.
- API keys in headers: constant-time comparison (`secrets.compare_digest`).
- OAuth: validate `state`; allowlist redirect URIs.
- Sessions: secure cookie flags behind HTTPS; don't store tokens in localStorage
  from Python-served templates without understanding XSS risk (see `sec-js`).

## Dependencies & deployment

- Commit lockfiles (`poetry.lock`, `uv.lock`, pinned `requirements.txt`).
- Review new PyPI packages — typosquatting and install-time code execution are
  real risks.
- Don't run containers as root; non-root user in Dockerfile.
- `uvicorn`/`gunicorn` binding — confirm `0.0.0.0` exposure is intended.

## Transport, logging & errors

- HTTPS/TLS only; never `verify=False` on `httpx`/`requests` to "fix" certs.
- FastAPI `HTTPException(detail=...)` — generic messages to clients; log trace
  server-side only.
- Structured logging without passwords, tokens, or full request bodies.

## Review checklist

When reviewing code or before shipping, verify:

```
- [ ] Every protected route has authentication
- [ ] Database access scoped by user/tenant (no IDOR)
- [ ] Boundary validation (project's existing tooling) on all external input
- [ ] No f-string or % SQL; ORM or bound parameters only
- [ ] No pickle/eval/exec on untrusted data
- [ ] No shell invocation with user-controlled strings
- [ ] CORS allowlist; not wildcard + credentials
- [ ] Secrets in env / GCP Secret Manager only; .env gitignored
- [ ] Lockfile committed; new deps reviewed
- [ ] Outbound HTTP from user URLs has SSRF protections
- [ ] DEBUG off in production; errors don't leak internals
```

Format review feedback as: CRITICAL (must fix) / FIX (should fix) /
NOTE (optional).

## When in doubt

Stop, explain the risk in one or two sentences, and point the user to
**#security-requests** for Python and application-security questions (auth, IDOR,
injection, SSRF, dependencies). Do not guess on security tradeoffs.

Platform or stack changes (new framework, database, hosting) → **#security-requests**.
