---
name: sec-node
description: >-
  Node.js backend security — Express, Fastify, Hono, NestJS: middleware auth,
  IDOR/scoping, zod validation, SQL/NoSQL injection, SSRF, child_process,
  workers, webhooks, CORS, and AI anti-patterns. Use when writing or reviewing
  server-side Node/TypeScript APIs, not browser code. Browser/client → sec-js.
---

# Node.js Backend Security

This skill covers **server-side** Node.js and TypeScript — APIs, middleware,
workers, and webhooks. It does not cover browser/React code (see `sec-js`).

**Apollo's baseline security rules always apply**; this is the Node backend
depth behind them.

**Related skills:** browser/client/React → `sec-js`.

**Questions?** App-security help, platform changes, and policy exceptions →
**#security-requests**.

## The one rule (plain language)

Every `req.body`, `req.query`, `req.params`, header, WebSocket message, and
queue job payload is **untrusted**. Middleware that runs "globally" can still
have gaps — each route handler must **authenticate** the caller and
**authorize** access to the specific resource, not just check that *someone* is
logged in.

## Top 10 easy wins

Apply these automatically, in priority order:

1. **Auth middleware on every protected route** — per-route guards in NestJS,
   explicit middleware chains in Express/Fastify; don't assume mount order is
   enough.
1. **Authorize + scope by tenant** — `findUnique({ where: { id, teamId } })`, not
   `findUnique({ where: { id } })` alone. Prevents IDOR.
1. **Validate with zod (or equivalent) at the boundary** — parse `req.body` once;
   don't pass raw `req.body` deeper into services.
1. **Parameterized queries only** — Prisma, Knex, Sequelize, `pg` with `$1`
   placeholders. No template-string SQL or NoSQL.
1. **No secrets in code** — `process.env` only; `.env` in `.gitignore`; never
   commit tokens or `DATABASE_URL` with credentials.
1. **No `eval` / `new Function` / `vm` on request data**.
1. **SSRF guard on outbound `fetch`/`axios`** — allowlist hosts when URL is
   user-influenced; block localhost and metadata IPs.
1. **Secure session cookies** — `httpOnly`, `secure`, `sameSite` on
   `express-session` / Fastify session; not `localStorage` for tokens.
1. **Lock down CORS** — allowlist origins; never `origin: true` + credentials
   for all comers, never `*` with credentials.
1. **Commit lockfile** — the one the repo already uses (Apollo default
   `pnpm-lock.yaml`); never switch package managers or add a second lockfile.
   Flag unfamiliar npm packages before adding.

## What AI must NOT do

Stop, explain the risk, and ask before generating any of these. This applies to
code you write or change; flag existing occurrences, don't stop on them.

| Never | Instead |
|----------|------------|
| `` db.query(`SELECT * FROM users WHERE id = ${id}`) `` | Prisma/Knex/`pg` with bound parameters |
| `Model.findById(req.params.id)` without tenant check | Scope by `teamId` / `userId` from verified session |
| `child_process.exec(req.body.command)` | No shell; allowlist fixed commands if unavoidable |
| `fetch(req.query.url)` or `axios.get(userUrl)` | Host allowlist; SSRF protections |
| `eval(req.body.code)` or `new Function(userInput)` | Parse with zod; safe interpreters only |
| `rejectUnauthorized: false` / `NODE_TLS_REJECT_UNAUTHORIZED=0` | Fix certs; proper CA bundle |
| `cors({ origin: '*', credentials: true })` | Explicit origin allowlist |
| `console.log(req.body)` with passwords/tokens | Log IDs; structured redacted logging |
| `mongoose.model.find({ $where: userInput })` | Typed criteria with bound values |
| Skip auth on "internal" routes exposed to the network | Same authz as public API; network ≠ trust |

## Stack cheat sheet

**Express**

- `router.use(authMiddleware)` per router, not only `app.use` at root — nested
  routers are easy to mis-wire.
- `express.json({ limit: '...' })` — set body size limits.
- `helmet()` for baseline security headers.

**Fastify**

- `preHandler` hooks for auth on each route schema.
- Use `@fastify/jwt` or session plugin — don't parse JWT manually without
  verification.

**Hono**

- Middleware on route groups; remember edge deployments still expose handlers
  publicly.

**NestJS**

- `@UseGuards(AuthGuard)` on controllers **and** verify per-method if guards are
  omitted on new methods.
- DTOs with `class-validator` + `ValidationPipe({ whitelist: true })` strips
  unknown fields (mass-assignment defense).

**Prisma / ORM**

- `where` clauses must include tenant scope from session, not from client body.
- Raw queries: `prisma.$queryRaw` with tagged template or parameters only.

**Workers (Bull, BullMQ, pg-boss)**

- Re-validate job data in `process()` — enqueue payload is attacker-controlled
  if anything client-side can enqueue.

**Webhooks**

- Verify HMAC signature (`crypto.timingSafeEqual`) before parsing body.
- Use `express.raw()` / raw body for signature verification when required.

## Attack surfaces AI often misses

- **IDOR** — swapping `:id` in REST paths or GraphQL node IDs.
- **Mass assignment** — spreading `req.body` into ORM `create()` / `update()`.
- **Prototype pollution** — `lodash.merge`, `Object.assign` with untrusted JSON;
  use `whitelist: true` validation.
- **NoSQL injection** — Mongo operators (`$gt`, `$ne`) in query objects built
  from `req.query` without schema validation.
- **JWT in query strings** — tokens leak via logs, Referer, browser history.
- **Open redirects** — `res.redirect(req.query.next)`.
- **GraphQL** — introspection enabled in prod; missing per-field authz.
- **Server-Sent Events / WebSockets** — connection auth at handshake; re-check on
  subscription to sensitive channels.
- **Dev-only bypasses** — `if (process.env.NODE_ENV !== 'production')` auth
  skips left in shared middleware.

## Injection & input

- SQL: ORM or `pg`/`mysql2` placeholders — never string concat.
- NoSQL: validate query shape with zod; reject keys starting with `$` from user
  input unless explicitly intended and safe.
- Command: `child_process.spawn` with `shell: false` and fixed argv.
- Path: `path.join(UPLOAD_DIR, path.basename(userName))` — block `../`.
- Template: don't render user HTML server-side without escaping; prefer JSON APIs.

## Auth, sessions & JWT

- **Auth providers** — extend the app's existing auth stack. Adding or replacing
  an auth provider or auth library is a platform decision: route it to
  **#security-requests**.
- Never hand-roll password hashing, session, or token logic — no bare
  `crypto.pbkdf2`, no signing your own JWTs.
- Verify JWT signature, `exp`, and `iss` on every request — don't trust decoded
  payload alone.
- Store sessions in httpOnly cookies; refresh rotation server-side.
- API keys: compare with `crypto.timingSafeEqual`.
- Re-verify permissions per route — "logged in" ≠ "allowed."

## Dependencies & deployment

- Commit lockfile; audit with `pnpm audit` / `npm audit`.
- Treat `postinstall` scripts as supply-chain risk.
- Don't bind `0.0.0.0` without confirming exposure is intended.
- Run containers as non-root.

## Transport, logging & errors

- HTTPS/TLS only; never disable cert verification.
- `res.status(500).json({ error: err.message })` leaks internals — generic client
  message, log server-side.
- No tokens, cookies, or PII in logs or APM breadcrumbs.

## Review checklist

When reviewing code or before shipping, verify:

```
- [ ] Every protected route has authentication middleware/guard
- [ ] DB queries scoped by tenant/user from session (no IDOR)
- [ ] zod/schema validation on all external input
- [ ] No template-string SQL or unsafe NoSQL operators from user input
- [ ] No eval, vm, or child_process with user-controlled strings
- [ ] CORS allowlist; not wildcard + credentials
- [ ] Secrets in env only; lockfile committed
- [ ] Webhooks verify signatures before processing
- [ ] Workers re-authorize job payloads
- [ ] Outbound HTTP from user URLs has SSRF protections
- [ ] Errors don't leak stack traces or internal paths
```

Format review feedback as: CRITICAL (must fix) / FIX (should fix) /
NOTE (optional).

## When in doubt

Stop, explain the risk in one or two sentences, and point the user to
**#security-requests** for Node and application-security questions. Do not guess on
security tradeoffs.

Platform or stack changes → **#security-requests**.
