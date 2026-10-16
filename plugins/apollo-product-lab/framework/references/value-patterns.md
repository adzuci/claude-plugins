# Value Patterns — Framework-Canonical Redaction Reference

> **Status**: framework-canonical. Closes Phase D batch-1 [InfoSec D-4 MAJOR] — patterns previously inlined in `cost-attribution-schema.md` § Value-level scrubbing are now centralized here so the Pantheon redactor implementation, the `eval/cost-attribution-redaction/` corpus, the daily PII audit query, and InfoSec quarterly review all read from one source.
>
> **Binding**: Pantheon redactor implementation reads `references/value-patterns.md` as its source of truth. Any change here is a behavior change to every harness's redaction pipeline. Edits require InfoSec review.

---

## Why this file exists

The InfoSec persona review surfaced a duplication risk: redaction patterns were inlined in three places (cost-attribution-schema.md, the redactor implementation we're about to ship, and the eval corpus). Drift between them silently weakens redaction. Centralizing here gives:

- One file InfoSec quarterly-reviews
- One file the redactor unit-tests against
- One file the daily audit query mirrors

Every other location links here instead of repeating patterns.

---

## Value patterns (regex-driven)

These run on every string value in allowlisted JSON, recursively. Scrubbing is left-to-right, first-match-wins per substring.

| ID | Pattern name | Regex | Replacement | Notes |
|---|---|---|---|---|
| `vp-email` | Email | `\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b` (case-insensitive) | `<email>` | Greedy match; deliberately broader than RFC 5321 — better to over-scrub. |
| `vp-phone-na` | Phone (NA / E.164) | `\b\+?1?[\s.-]?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b` | `<phone>` | North-American formats. |
| `vp-phone-intl` | Phone (international E.164) | `\+\d{7,15}\b` | `<phone>` | Generic E.164. |
| `vp-api-key` | API key shape | `\b(sk-\|sk_\|pk_\|ghp_\|xoxb-\|AKIA)[A-Za-z0-9]{16,}\b` | `<secret>` | OpenAI, Stripe, GitHub, Slack, AWS prefixes. |
| `vp-opaque-long` | Long opaque string (token / base64 candidate) | `\b[A-Za-z0-9+/]{40,}={0,2}\b` | `<opaque>` | Catches JWTs, SAS tokens, base64-encoded blobs. |
| `vp-truncate-200` | User content > 200 chars | string field length > 200 chars (not regex; a length test) | first 200 chars + `… <truncated>` | Last-line defense against accidental free-text leakage. |

### Order of application

1. `vp-email` (highest specificity)
2. `vp-phone-na`
3. `vp-phone-intl`
4. `vp-api-key`
5. `vp-opaque-long`
6. `vp-truncate-200` (string-length test, applied AFTER all regex scrubbing)

Earlier rules take precedence. An email is never re-evaluated as `vp-opaque-long` because `vp-email` matched first.

---

## Field patterns (key-driven, override value scrubbing)

These run on JSON keys at any nesting depth and override value-level scrubbing. Drop-key wins over scrub-value.

| ID | Key match | Treatment | Rationale |
|---|---|---|---|
| `fp-email-key` | `email`, `email_address` | drop | Even safe-looking values may be team distribution lists |
| `fp-phone-key` | `phone`, `phone_number` | drop | Same — never carry phone fields |
| `fp-free-text` | `body`, `message`, `text`, `content` | drop | Free text is too risky to allowlist by accident |
| `fp-stack` | `stack_trace`, `stacktrace` | drop | Stack frames echo file paths, sometimes user content |
| `fp-diff` | `diff`, `patch`, `code` | drop | Source code is a frequent leak path |
| `fp-prompt` | `prompt`, `prompt_text` | drop | Raw prompts often echo user content |
| `fp-id-hash` | `user_id`, `account_id` | hash with `sha256(salt + value)` | Salt rotated quarterly; preserves cardinality without identifying |
| `fp-suffix-secret` | any key matching `*_token`, `*_secret`, `*_key`, `*_password` | drop | Catch-all suffix rule |

### Order of application (field vs value)

For each `(key, value)` pair in the JSON tree:

1. Apply field-pattern check first.
2. If a field pattern matches → drop or hash per its rule. **Stop.**
3. Else, apply value patterns in the order listed above.

This means a field named `body` with the value `"hello@apollo.io"` is dropped, NOT scrubbed to `<email>`. The drop is more conservative.

---

## What "drop" vs "redact" mean precisely

- **Drop**: the key is removed entirely from the persisted JSON. The output schema must accommodate missing keys. Consumers cannot distinguish "key was present but redacted" from "key was never there" — by design.
- **Redact / scrub**: the key remains, the value is replaced by a placeholder (`<email>`, `<phone>`, `<secret>`, `<opaque>`) or truncated.
- **Hash**: the key remains, the value is replaced by a hex-encoded `sha256(salt + value)`. Salt is rotated quarterly via the `pantheon-redactor-salt` secret in Vault. Old salts are preserved for 90 days so analytics can reconcile cohorts across rotation.

---

## Salt rotation policy

- Salt: 32-byte random, stored in Vault under `pantheon-redactor-salt` (current) and `pantheon-redactor-salt-prev-N` (last 4 quarters).
- Rotation: first Monday of each quarter.
- After rotation, the redactor uses the new salt. The PII audit query checks against current + last-quarter salts.
- Effect on analytics: a `user_id` will hash to a different value across quarters. Cohort-tracking dashboards must collapse using the period-aware salt or accept quarter-boundary discontinuities.

---

## What this file does NOT cover

- **Allowlists**: those live per-harness in each descriptor under `cost_attribution.input_summary_allowlist` / `output_summary_allowlist`. The redactor uses this file's patterns AFTER allowlisting.
- **Application code redaction**: skill / sub-agent / harness implementations should never log raw user content; this file is about post-run summaries written to `analytics.harness_runs`. Operational logging is a separate Platform-team concern with its own redaction rules.
- **Vendor-side redaction**: prompts sent to model vendors (Anthropic, OpenAI) are redacted at the Apollo proxy layer. That redaction is more aggressive (no per-key allowlisting); it lives in `proxy/redaction.md` (Platform team).

---

## Eval coverage

`${CLAUDE_PLUGIN_ROOT}/framework/eval/cost-attribution-redaction/` contains 7 cases (case-01 through case-07) covering each pattern category. The redactor's CI test suite must run this corpus and score zero regressions before merging any change to:

1. This file.
2. The redactor implementation.
3. Any harness's allowlist.

See `eval/cost-attribution-redaction/README.md` (lands alongside the cases) for the schema each case file uses.

---

## Quarterly review

InfoSec quarterly walkthrough (per `cost-attribution-schema.md` § Audit & monitoring):

1. Diff this file against the prior quarter's revision. Any regex relaxation requires sign-off.
2. Walk the case corpus. Confirm coverage for any new pattern added.
3. Walk per-harness allowlists. Confirm no net-new free-text keys.
4. Sample 100 random `harness_runs` rows from the past quarter. Manually inspect for residual PII the redactor missed.

The fourth step is the load-bearing one — it's the only check that catches patterns this file doesn't yet anticipate.
