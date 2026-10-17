---
name: abuse-ring-blocker
description: Identify an abuse ring behind a not-yet-blocked team or domain, check Glean for a past-ring match, decide monitor-first vs. block-now, and draft a block PR as text for human review. Never blocks or opens a PR itself.
disable-model-invocation: true
---

# Abuse Ring Blocker

Given a team, domain, or other entity showing fraud signals, identify the abuse ring behind it, check whether it's a resurgence of a past ring, and decide whether to block now or gather more information first. Read [ioc-methodology.md](../../references/ioc-methodology.md) for the fields used to identify a ring, and [references/pr-template.md](references/pr-template.md) before proposing a block PR. For a domain that is *already* blocked, use `/apollo-eng-fraud:abuse-ring-tracker` instead — this skill is for entities not yet blocked.

```text
/apollo-eng-fraud:abuse-ring-blocker <team-id|domain|entity> [--mode=monitor-only] [--max-turns=N] [--time-budget=Ns] [--ensemble]
```

## Workflow

1. **Resolve the entity.** Accept a team ID, domain, or a looser description (e.g. "the signups from this fingerprint"). Validate the entity before using it in any command (bare domain matches `^[a-z0-9.-]+\.[a-z]{2,}$`, team ID is a 24-char hex ObjectId; reject anything else) and pass it only as a quoted argument, never via `eval` or string-built shell. Pull the team's `domain`, signup metadata, and any existing `Fraud::SignupFraudClassification`/`risk_level_cd` for it.
1. **Identify the ring.** Using the IOC fields (JA4 fingerprint, Darwinium behavioral fingerprint, device-signature consistency, CF bot-score distribution, shared IP/UA from `http_requests_v3` — see the shared reference), find every other team/domain sharing the same fingerprint(s). This set is "the ring."
1. **Check for a past ring match via Glean.** Search Glean (MCP Glean tools if available; otherwise the `glean` CLI) for prior incidents, RCAs, or Slack threads mentioning the same domain, fingerprint, or a structurally similar pattern (e.g. free-mail-domain signup bursts hitting search/enrichment endpoints, per `packs/fraud/scripts/fingerprint_fraud_analysis.rb`'s `VALUABLE_ENDPOINTS`). Run `which glean` first. If it is missing, do not install anything: report "Glean CLI missing — past-ring check not performed" with the org's setup instructions and continue. Never treat a missing CLI as a true zero-match.
1. **Assess ring complexity.** Score on: number of distinct fingerprints/domains found, ARR at risk (`Fraud::ScraperSignature#cached_total_arr`), whether the ring shows adaptive behavior (any IOC 4/4b drift already observed), and whether it matches a known past ring (step 3).
   - **Simple, single-fingerprint, no prior match, low ARR:** monitor-first is usually enough. Do not block and do not hand off to `abuse-ring-tracker` (it only handles already-blocked domains). Report the fingerprints/queries to re-check, recommend a re-check window, and stop after this step.
   - **Multiple fingerprints/domains, adaptive behavior, or a match to a known past ring:** block-now is usually justified — continue to step 5. Before step 5, list every team that would be soft-deleted (team ID, `Team#domain`, ARR) so the human confirms the exact blast radius.
1. **Propose the PR.** Follow [references/pr-template.md](references/pr-template.md), mirroring the style of PR #99593 (mark domain(s) `is_scraper_domain: true`, soft-delete matching teams via `LoginDestroyer.soft_delete_abusive_team`, apply the fraud label, scope strictly to exact `Team#domain` equality unless evidence supports more). State scope limitations explicitly (e.g. root-cause fixes to shared invite/signup paths are out of scope for a reactive block PR) rather than silently expanding scope.
1. **Optional ensemble pass.** If `--ensemble` is passed, run [references/ensemble-mode.md](references/ensemble-mode.md) — an independent Codex/Sol pass over the same evidence before finalizing the block recommendation.
1. **Report.** Report domains, team IDs and counts only; never include individual user emails or names (PII). Ring membership + evidence, past-ring match (or "no match found" / "Glean unavailable — not checked"), complexity score and rationale, decision (monitor vs. block), and — if blocking — the proposed PR diff/description for human review. Never open the PR without explicit confirmation. Include an audit trail: the queries run, record IDs or links for each claim, UTC timestamp, and who confirmed which step.

## Constrained / Operator Mode

See [operator-mode.md](../../references/operator-mode.md) for the full contract shared with `abuse-ring-tracker`. `--mode=monitor-only` disables step 5 (PR proposal) entirely — the skill stops after step 4 and hands the complexity assessment back to a human. `--max-turns`/`--time-budget` cap investigation depth in steps 2–4; on exceeding either, stop and report partial findings labeled "capped — not exhaustive," never a silent guess.

## Example Report

```text
Entity: example-ring.test (team 0000...0002)
Ring: 3 domains share JA4 f1 + Darwinium pair d1 (IOC 1, 3); 14 teams, ARR at risk $9,800
Past ring: no match found (Glean checked: 2 queries, <links>)
Complexity: multiple domains, no adaptive drift observed, no prior match -> moderate
Decision: block-now (rationale vs thresholds: >1 domain)
Free-mail guard: not free-mail, not .edu, not in WHITELISTED_DOMAINS (checked <date>)
Teams to soft-delete: <ID list with domain + ARR>
Draft PR: <text per references/pr-template.md> (not opened; awaiting human confirmation)
```

## Workflow Contract

- **Deterministic (this skill provides):** the IOC-based ring-identification method, the Glean-check-before-concluding-no-match rule, the complexity scoring inputs, the monitor-vs-block threshold guidance, the PR template and its scope-limitation statement, the never-open-without-confirmation rule.
- **Agent judgment:** where exactly a ring falls on the complexity spectrum, how much weight to give a past-ring match, whether the evidence in hand is strong enough to recommend blocking vs. monitoring longer.
- **Human (fraud/eng reviewer):** confirms the block decision, reviews and merges the proposed PR, owns any team-visible consequence (see the free-mail-domain guard in Safety).

## Safety

Never blocks a domain, deletes a team, opens a PR, or pushes a commit without explicit human confirmation at each of those steps — this skill proposes, it does not execute: it never creates a branch, commit, PR, block, or team deletion. A human performs those steps outside the skill, using the drafted text. Before recommending any block, explicitly check the proposed domain/pattern is not a free-mail or otherwise broad domain — `BlockedDomain.block_team` (`packs/billing/app/models/blocked_domain.rb`) already refuses to auto-block when `EmailUtil.free_domain?(domain)` is true (or `.edu`, or an entry in `WHITELISTED_DOMAINS`), and that guard is being actively hardened in-repo (see `packs/billing/spec/lib/blocked_domains/abuse_prevention_spec.rb`) precisely because a free-mail domain slipping through would be high-blast-radius. State in the report that this check was done, not just that it exists in code. Never print `password_reset_token`, `encrypted_old_password`, or other secret-adjacent fields.

## Checklist

- [ ] Ring identified from IOC fields, not domain-name similarity alone
- [ ] Glean checked for a past-ring match; CLI-missing vs. true-negative distinguished
- [ ] Complexity scored on fingerprint count, ARR, adaptive behavior, past-ring match — not on gut feel alone
- [ ] Monitor-vs-block decision states its rationale against the thresholds above
- [ ] If blocking: PR scope stated explicitly, including what's intentionally out of scope
- [ ] Explicit free-mail/broad-domain guard applied and stated before any block recommendation
- [ ] No PR opened without explicit human confirmation
- [ ] No secret-adjacent fields printed
- [ ] Constrained-mode caps (if passed) respected; partial results labeled as such

## Further Reading

- [../../references/ioc-methodology.md](../../references/ioc-methodology.md) — IOC fields shared with `abuse-ring-tracker`
- [../../references/operator-mode.md](../../references/operator-mode.md) — constrained/capped invocation contract
- [references/ensemble-mode.md](references/ensemble-mode.md) — optional independent Codex/Sol verification pass
- [references/pr-template.md](references/pr-template.md) — block-PR structure, mirroring PR #99593
- `/apollo-eng-fraud:abuse-ring-tracker` — track an already-blocked domain's timeline and effectiveness
