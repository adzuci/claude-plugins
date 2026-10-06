---
name: sec-rails
description: >-
  Ruby on Rails backend security — authentication, authorization, IDOR/team
  scoping, mass assignment, NoSQL injection, CSRF, background jobs, webhooks,
  SSRF, and AI anti-patterns. Use when writing or reviewing Rails controllers,
  models, workers, APIs, or Mongoid/ActiveRecord code.
---

# Ruby on Rails Backend Security

This skill covers server-side Ruby and Rails — APIs, controllers, models, jobs,
and webhooks. **Apollo's baseline security rules always apply**; this is the
Rails depth behind them.

**Related skills:** browser/client code → `sec-js`. Full per-endpoint IDOR
audit of controllers → `apollo-eng:security-review`.

**Questions?** App-security help, platform changes, and policy exceptions →
**#security-requests**.

## The one rule (plain language)

Every HTTP request, webhook, and background job argument is **untrusted**. The
caller can change IDs, team IDs, roles, and hidden fields. Your code must
**authenticate** who they are and **authorize** what they can access on every
protected path — finding a record by ID alone is never enough.

## Top 10 easy wins

Apply these automatically, in priority order:

1. **Authenticate every protected action** — usually inherited from
   `ApplicationController` (e.g. `before_action :require_login`). Don't
   redeclare it in subclasses; redeclaring (especially with `only:`) replaces
   the inherited callback. Opt out only with
   `skip_before_action ..., only: [...]` on truly public actions, with the
   reason stated (comment or PR description).
1. **Authorize + scope by tenant** — a record loaded by ID must pass a team
   check before it's returned or changed: the app's authorization (e.g. Pundit
   `authorize`), its team-access helper, or `find_by(id:, team_id:)`. Prevents
   IDOR.
1. **Explicit attribute allowlists** — never mass-assign unchecked request data
   to models. If `permit_all_parameters` is on, `permit` protects nothing: use
   `slice(*ALLOWED)` or typed params instead.
1. **Validate at the boundary** — schema or explicit checks on params, webhooks,
   and job payloads before use.
1. **Parameterized queries only** — ORM bindings for SQL and MongoDB. No string
   interpolation into `where`, `$where`, or raw SQL.
1. **No secrets in code or repos** — Rails credentials, env vars, or secret
   manager; `.env` and keys in `.gitignore`.
1. **Verify new webhooks** — use the provider's documented mechanism (HMAC
   signature, signed token, mTLS). If an existing webhook has no verification,
   flag it and ask; don't add enforcement that could reject live traffic until
   the provider's scheme and secret are confirmed.
1. **CSRF on session-backed mutations** — keep `protect_from_forgery` on;
   don't skip without token alternative (API keys, signed requests).
1. **Generic errors to clients** — no stack traces or internal paths in JSON/HTML
   responses.
1. **Same rules in Sidekiq/workers** — jobs acting on behalf of a user get the
   acting `user_id`/`team_id` and check in `perform` that loaded records belong
   to that team. System and batch jobs don't need user-level authorization;
   never trust client-supplied enqueue args.

## What AI must NOT do

Stop, explain the risk, and ask before generating any of these. This applies to
code you write or change; flag existing occurrences, don't stop on them.

| Never | Instead |
|----------|------------|
| `Model.find(params[:id])` returned or changed with no team check | `authorize @record`, the app's team-access helper, or `find_by(id:, team_id:)` |
| `params.permit!`, `to_unsafe_h`, or request hashes passed to `new` / `update` / `assign_attributes` | Explicit allowlist: `permit(:field1, :field2)`, or `slice(*ALLOWED)` / typed params when `permit_all_parameters` is on |
| `skip_before_action :require_login` on sensitive actions | Documented skip only on truly public endpoints |
| `eval`, `constantize`, or `send` on user-controlled strings | Allowlist enums; map input to known constants |
| MongoDB `$where` / JS queries with user input | Mongoid criteria with bound values |
| `system`, backticks, or `Open3` with request data | Shell-free APIs; allowlist commands if unavoidable |
| `HTTParty.get(params[:url])` or open `Net::HTTP` to user URLs | The app's existing SSRF guard (e.g. `Iam::IpGuard`); else allowlist hosts and block private IPs |
| Hardcoded API keys or copied credential values in source | Env/credentials references only |
| `Rails.logger.info` of tokens, passwords, or full params | Log IDs; redact sensitive fields |
| Disable CSRF/CORS/TLS "to unblock local dev" in committed code | Environment-gated config; fix root cause |

## Stack cheat sheet

**Controllers & APIs**

- Authentication is inherited from `ApplicationController` (e.g.
  `before_action :require_login`); don't redeclare it in subclasses.
- Opt out only with `skip_before_action ..., only: [...]` on truly public
  actions, with the reason stated (comment or PR description).
- `render json:` still needs authz — JSON APIs are not exempt from IDOR.
- Namespace new public webhooks separately; verify them as described under
  **Webhooks & integrations**.

**ActiveRecord / Mongoid**

- Scope or authorize every find: `find_by(id:, team_id:)`, an association from
  an already-authorized parent, or a find followed by `authorize`. Handle a
  nil/not-found result per the app's ORM config (Mongoid may return `nil`
  instead of raising).
- When parent/child teams can share access, use the app's team-access helper
  rather than a raw `team_id ==` comparison.
- A `team:` argument is not proof of scoping — check that the finder actually
  filters by team.
- Avoid `Model.where("field = '#{params[:x]}'")` — use hash criteria or
  `where(field: params[:x])` with validated types.

**Authorization (Pundit / policies)**

- Authorize every action that reads or changes a specific record, using the
  mechanism the controller already uses (Pundit policy, permission checks,
  feature gates). Add a Pundit policy only where the controller already calls
  `authorize` — it raises when the policy is missing.
- Respect existing `skip_authorization` / `verify_authorized` setups.
- Policy `Scope` must filter collections, not only single-record checks.

**Background jobs (Sidekiq, etc.)**

- Pass IDs, not full objects. Jobs acting on behalf of a user also take the
  acting `user_id`/`team_id`; in `perform`, check loaded records belong to that
  team.
- System and batch jobs don't need user-level authorization, but never trust
  client-supplied enqueue args.
- Apply the ownership check to new or changed user-triggered jobs; flag
  existing jobs that lack it, don't stop on them.

**Webhooks & integrations**

- New endpoints: verify with the provider's documented mechanism (HMAC
  signature, signed token, mTLS) before parsing the body.
- Existing webhook without verification: flag it and ask; don't add
  enforcement that could reject live traffic until the provider's scheme and
  secret are confirmed.
- New endpoints: use idempotency keys; guard against replay.

**Sessions & cookies**

- Session/auth cookies are `httponly` + `secure`. Choose `same_site` for the
  app's cross-site needs (extensions and embeds may need `None` plus CSRF
  tokens). Cookies JS must read (e.g. a CSRF token) can't be `httponly`. Ask
  before changing existing cookie attributes.
- Rotate session on privilege change; don't roll custom crypto.

## Attack surfaces AI often misses

- **IDOR** — changing `:id` or `team_id` in URL/body to access another
  tenant's data. #1 Rails API mistake in multi-tenant apps.
- **Mass assignment** — adding `admin: true` or `team_id` via unpermitted params.
- **Insecure direct enqueue** — user triggers a job that operates on another
  user's records because `perform` skipped authz.
- **GraphQL / batch endpoints** — one request touching many IDs needs per-item
  authorization.
- **Export / search endpoints** — broad queries without team scope leak data at
  scale.
- **Debug endpoints** — `/sidekiq`, `/rails/info`, custom `?debug=` left
  enabled in production.
- **File paths** — `send_file`, `File.read`, ActiveStorage with user-supplied
  paths → path traversal.
- **Serialization** — `render json: @user` exposing fields that should be
  hidden; use explicit serializers/view models.

## Injection & input

- SQL: ActiveRecord/Mongoid bindings only. Raw SQL requires bound placeholders.
- NoSQL: never build `$where`, `$regex`, or aggregation pipelines from
  unescaped user strings.
- Command injection: no shelling out with request data.
- SSRF: allowlist outbound HTTP hosts; block `localhost`, `169.254.169.254`,
  and RFC1918 ranges when URL is user-influenced.
- Redirects: `redirect_to params[:return_to]` → open redirect; allowlist paths.

## Auth, CSRF & sessions

- Re-verify permissions on every action — `before_action` in
  `ApplicationController` is the floor, not optional per controller.
- Session-backed browser apps: keep CSRF protection. API-only token auth may
  exempt JSON with explicit design — don't mix patterns accidentally.
- **Auth providers** — extend the app's existing auth stack. Adding or replacing
  an auth provider or auth library is a platform decision: route it to
  **#security-requests**.
- **Admin endpoints** stay behind `require_login` plus the right admin check:
  the app's staff gate (e.g. `require_admin`) for internal endpoints, its
  team-admin permission check for customer-admin actions. Never
  `skip_before_action :require_login` on them.
- Never hand-roll password hashing or session logic.

## Dependencies & secrets

- Commit `Gemfile.lock`. Flag unfamiliar gems before adding.
- Secrets in credentials or env — never committed. Audit for `.env` in git history.
- Pin gem versions for security-sensitive libs (auth, crypto, HTTP clients).

## Transport, logging & errors

- HTTPS/TLS only; never disable certificate verification.
- `rescue` blocks: log details server-side; return generic messages to clients.
- No PII or tokens in logs, error trackers, or Slack notifications.

## Review checklist

When reviewing code or before shipping, verify:

```
- [ ] Every protected action has authentication
- [ ] Records loaded by ID are team/policy scoped (no IDOR)
- [ ] Explicit attribute allowlists on all writes
- [ ] New webhooks verify requests before processing; unverified existing ones are flagged
- [ ] User-initiated jobs check loaded records belong to the acting team
- [ ] No raw queries built from string-interpolated user input
- [ ] No secrets in source or committed config
- [ ] CSRF enabled for session-backed mutations
- [ ] Errors and logs don't leak secrets, stack traces, or PII
- [ ] Outbound HTTP from user input uses host allowlists (SSRF)
```

Format review feedback as: CRITICAL (must fix) / FIX (should fix) /
NOTE (optional).

## When in doubt

Stop, explain the risk in one or two sentences, and point the user to
**#security-requests** for Rails and application-security questions (IDOR, auth,
injection, jobs, webhooks). Do not guess on security tradeoffs.

Platform or stack changes (new database, auth provider, hosting) →
**#security-requests**.
