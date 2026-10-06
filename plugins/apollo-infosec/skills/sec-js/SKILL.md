---
name: sec-js
description: >-
  Frontend and JavaScript/TypeScript security — client/server boundary, secrets
  in bundles, auth tokens, XSS, open redirects, CORS, dependencies, and AI
  anti-patterns. Use when writing or reviewing React, Next.js, Vite, Vue,
  browser-facing code, or server code inside a frontend app (Next.js route
  handlers, Server Actions, middleware). Standalone Node backends → sec-node.
---

# JavaScript / TypeScript & Web Security

This skill covers browser-facing code and the framework server code that lives
inside the frontend app (Next.js route handlers, Server Actions, middleware) —
the stack where insecure defaults show up most often in vibe-coded apps.
**Apollo's baseline security rules always apply**; this is the FE depth behind
them.

**Related skills:** standalone Node web servers and APIs (Express, Fastify, Hono,
NestJS) → `sec-node`.

**Questions?** Web and app-security help, platform changes, and policy
exceptions → **#security-requests**.

## The one rule (plain language)

Anything that runs in the browser or ships in a JavaScript bundle is **public**.
Users can read it, change it, and replay it. Hiding a button or checking a role
in React is UX — not security. Every real security decision (who you are, what
you can do, what data you see) must happen on a **server you control**.

## Top 10 easy wins

Apply these automatically, in priority order:

1. **No secrets in client code or public env vars** — nothing in bundles,
   `NEXT_PUBLIC_*`, `VITE_*`, `REACT_APP_*`, or any `process.env.*` / `define`
   value substituted at build time, except values designed to be public (e.g. a
   publishable analytics or maps key).
1. **Re-check auth on every server route** — API handlers, Server Actions, and
   webhooks are reachable directly, not only from your UI.
1. **Validate input on the server** — use `zod` (or equivalent) at every
   boundary. Client-side validation is UX only.
1. **No `eval` or `new Function` on untrusted data** — including "just for
   prototyping."
1. **Avoid raw HTML from user data** — no `dangerouslySetInnerHTML` /
   `innerHTML` without sanitization and a documented reason.
1. **Session tokens in httpOnly + Secure cookies** — not `localStorage` or
   `sessionStorage` (XSS steals them there).
1. **Don't disable security controls to unblock** — no turning off TLS
   verification, CSP, CSRF, or CORS restrictions. Fix the cause.
1. **Generic errors to clients** — no stack traces, internal paths, or raw
   exception messages in HTTP responses.
1. **No open redirects** — never set `window.location` or redirect URLs from
   unvalidated query params (`?next=`, `redirect_uri`, etc.).
1. **Commit the lockfile; scrutinize new packages** — use the lockfile the
   repo already uses (Apollo default `pnpm-lock.yaml`); never switch package
   managers or add a second lockfile. Flag unfamiliar or freshly published deps
   before adding.

## What AI must NOT do

Stop, explain the risk, and ask before generating any of these. This applies to
code you write or change; flag existing occurrences, don't stop on them.

| Never | Instead |
|----------|------------|
| Put secret API keys, tokens, or `service_role` in client files, `NEXT_PUBLIC_` / `VITE_` / `REACT_APP_` vars, or any `process.env.*` / `define` value substituted at build time. Public-by-design values (publishable or site keys, analytics IDs, Sentry DSN, public encryption keys) are fine | Server-only env vars; proxy calls through the app's backend |
| `rejectUnauthorized: false` or `NODE_TLS_REJECT_UNAUTHORIZED=0` | Fix cert/hostname issues; use proper CA bundle |
| `localStorage` / `sessionStorage` for session, access, or refresh tokens or API keys | httpOnly, Secure, SameSite cookies via server. UI flags, analytics IDs, and CSRF tokens in JS-readable cookies are fine |
| `dangerouslySetInnerHTML` without sanitization | Framework rendering, or the app's shared sanitizer (else DOMPurify + allowlist), reason stated (comment or PR description) |
| `eval()` / `new Function()` on request or URL data | Parse with a schema; use safe APIs |
| Trust client-side role checks, hidden fields, or JWT claims without server verification | Re-verify session + permissions on every protected route |
| CORS `Access-Control-Allow-Origin: *` with `credentials: true` | Allowlist specific origins |
| `fetch(userSuppliedUrl)` from a server route | Allowlist hosts; block internal IPs (SSRF) |
| `console.log` of tokens, passwords, or full request bodies | Log IDs server-side; redact sensitive fields |
| Recommend alternate platforms when user is frustrated | Help within approved stack; route platform changes and web/appsec questions to **#security-requests** |

## Stack cheat sheet

**React / Next.js**

- `'use client'` files and anything they import ship to the browser — no secrets
  in that import chain.
- Server Actions and route handlers are public POST endpoints — auth + validate
  inside each one; middleware alone has gaps.
- Server Components can hold secrets; Client Components cannot.

**Vite / CRA**

- `import.meta.env.VITE_*` and `REACT_APP_*` are inlined at build time into the
  bundle. Treat them as public.

**Vue / Nuxt**

- `runtimeConfig.public` = browser-visible. Private config stays server-side.

**Framework server code** (Next.js route handlers, Server Actions, middleware)

- Validate, authenticate, authorize, then act. Standalone Node backends
  (Express, Fastify, Hono, NestJS) → `sec-node`.

**Browser APIs**

- `postMessage`: always check `event.origin` against an allowlist.
- `target="_blank"`: add `rel="noopener noreferrer"`.
- WebSockets: authenticate after connect; don't trust the connection alone.

**Chrome extensions**

- Extension code and `chrome.storage` are user-readable — same rules as client
  code. OAuth and API calls with secrets go through your backend.

## Attack surfaces AI often misses

- **Open redirects** — `?next=`, OAuth `redirect_uri`, login "return to" URLs.
  Use the app's redirect-allowlist helper if one exists; otherwise allowlist
  destinations and reject protocol-relative (`//evil.com`) and off-site URLs.
- **Reflected input** — search terms, error messages, or URL params rendered into
  `<title>`, meta tags, or DOM without escaping.
- **Third-party scripts** — analytics, chat widgets, CDN `<script>` tags. Prefer
  CSP; use Subresource Integrity when loading from a CDN.
- **File uploads** — enforce type, size, and content checks server-side; never
  trust the browser `accept` attribute alone.
- **Deep links / client routing** — `/admin` in the router is not protection;
  the API behind it must enforce access.
- **Dev shortcuts left in prod** — mock auth, `?debug=true` gates, hardcoded test
  users. Strip or guard with environment checks.

## Auth & session

- Re-verify session and permissions on every protected server route. Middleware
  is a first pass, not the only check.
- **Auth providers** — extend the app's existing auth stack. Adding or replacing
  an auth provider or auth library is a platform decision: route it to
  **#security-requests**.
- Never hand-roll password hashing, session, or token logic.
- Cookies: session/auth cookies are `httpOnly` + `Secure`. Choose `SameSite`
  for the app's cross-site needs (extensions and embeds may need `None` plus
  CSRF tokens). Cookies JS must read (e.g. a CSRF token) can't be `httpOnly`.
  Ask before changing existing cookie attributes.
- OAuth: validate `state`; allowlist `redirect_uri` values — never reflect
  arbitrary URLs from the request.
- Scope and expire tokens. Short-lived access + refresh rotation is fine;
  inventing your own crypto is not.

## XSS & DOM

- Let the framework escape by default (React, Vue).
- Treat `dangerouslySetInnerHTML`, `innerHTML`, and `document.write` with user
  data as XSS risks.
- If sanitization is unavoidable: use the app's shared sanitizer if one exists
  (otherwise DOMPurify with a tag/attribute allowlist), with the reason stated
  (comment or PR description).
- Reject `javascript:` URLs in `href` / `src` built from user input.

## Dependencies & build

- Commit the lockfile the repo already uses (Apollo default `pnpm-lock.yaml`);
  follow the repo's lockfile policy.
- Treat `postinstall` scripts of new packages as supply-chain risk — flag
  unfamiliar or freshly published packages before adding.
- Surface `npm audit` / `pnpm audit` findings; don't auto-bump major versions
  without calling it out.

## Transport, headers & errors

- HTTPS/TLS only. Never disable certificate verification to fix a connection.
- Don't weaken existing security headers. Adding or tightening CSP or
  `X-Frame-Options` is an app-wide change — propose it rather than applying it,
  since embeds and extensions may rely on framing.
- Adding a specific host to an existing CSP directive for an approved
  integration is routine. Stop only for wildcards, `unsafe-inline` /
  `unsafe-eval`, or removed directives.
- Lock down CORS: allowlist origins; never wildcard + credentials.
- Generic client-facing errors; detailed logs server-side without secrets or PII.

## Review checklist

When reviewing code or before shipping, verify:

```
- [ ] No secrets in client bundle or public env vars
- [ ] Every API route / Server Action checks auth + permissions
- [ ] Server-side input validation on all external input
- [ ] No raw HTML from user data without sanitization
- [ ] Auth tokens not in localStorage / sessionStorage
- [ ] No security controls disabled for convenience
- [ ] Lockfile committed; new deps are known packages
- [ ] Errors don't leak stack traces or internal paths
- [ ] Redirects and OAuth callbacks use an allowlist
```

Format review feedback as: CRITICAL (must fix) / FIX (should fix) /
NOTE (optional).

## When in doubt

Stop, explain the risk in one or two sentences, and point the user to
**#security-requests** in Slack for web and application-security questions (auth,
XSS, client/server boundary, dependencies, etc.). Do not guess on security
tradeoffs.

Platform or stack changes (new hosting, database, or auth provider) are
security-team decisions — route those to **#security-requests** as well.
