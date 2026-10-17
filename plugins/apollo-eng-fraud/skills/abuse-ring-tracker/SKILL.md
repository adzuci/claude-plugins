---
name: abuse-ring-tracker
description: Track an already-blocked abuse-ring domain. Builds a block timeline, then monitors for early evasion (recent block) or analyzes block effectiveness and tactic shift (older block). Read-only.
disable-model-invocation: true
---

# Abuse Ring Tracker

Given a domain (or team ID), reconstruct when and how it was blocked, then continue in one of two modes depending on how long ago that happened. Read [ioc-methodology.md](../../references/ioc-methodology.md) before the analysis step — it defines the exact fields this skill checks and why typosquat-domain matching is intentionally excluded. For identifying a *new*, not-yet-blocked ring and deciding whether to block it, use `/apollo-eng-fraud:abuse-ring-blocker` instead.

```text
/apollo-eng-fraud:abuse-ring-tracker <domain-or-team-id> [--mode=monitor-only] [--max-turns=N] [--time-budget=Ns]
```

## Workflow

1. **Resolve the target.** Accept a bare domain (`triquetra.life`), a `Team#domain`, or a team ID. If a team ID is given, look up its `domain` first. Validate the target before using it in any command: a bare domain must match `^[a-z0-9.-]+\.[a-z]{2,}$` and a team ID must be a 24-char hex ObjectId; reject anything else. Always pass it as a quoted argument, never via `eval` or string-built shell.
1. **Build the block timeline.** The block itself is a **runtime `BlockedDomain` record**, not a code change — query it directly (Mongo `blocked_domains` collection, or `BlockedDomain.where(domain: ...)`) for `created_at` and whether/when `is_scraper_domain` was set to `true`; these two dates can differ by months (a domain can sit in `blocked_domains` unenforced until `is_scraper_domain` is flipped). Separately, `git log --all --oneline -S"$domain" -- db-migration-files/` (content search, so commit subjects need not mention the domain) or `gh pr list --search "$domain"` finds the PR/migration that flipped `is_scraper_domain` or ran the team deletion — treat this as the *enforcement* date, not the *first-seen-blocked* date. Do not rely on a fixed migration-filename glob (e.g. `*delete_*_teams.rb`) to find the deletion migration — naming isn't consistent enough (the triquetra.life/ardour.life migration itself doesn't match that pattern); search by content or PR instead. Present the timeline as: first-seen signup → fraud label applied → `BlockedDomain` record created → `is_scraper_domain` enforcement began (date/PR) → teams soft-deleted (date/PR) — call out explicitly if the "created" and "enforcement began" dates differ.
1. **Branch on block age.**
   - Age = now minus the **enforcement** date from step 2 (when `is_scraper_domain` became `true`, not `BlockedDomain.created_at`), in UTC. If no enforcement date is found, stop and report "enforcement date unknown" instead of guessing.
   - **Age < 7 days:** switch to active-monitoring mode — go to step 4.
   - **Age >= 7 days:** run effectiveness analysis — go to step 5.
1. **Active-monitoring mode.** Using the IOC fields in the reference doc, check for signup/request activity in the lookback window that matches the ring's known fingerprints but is *not yet* caught by the current block (e.g. a new domain sharing a JA4 fingerprint or Darwinium behavioral fingerprint with the blocked ring, per IOC 1/3). Report anything found as a possible early evasion attempt — do not take any blocking action yourself; hand findings to `/apollo-eng-fraud:abuse-ring-blocker` for the identify-and-decide step.
1. **Effectiveness analysis.** Compare signup/request volume for the domain before vs. after the **enforcement** date from step 2 (not the `BlockedDomain.created_at` date — a record can exist for months with `is_scraper_domain` unset while the domain keeps growing, which looks like "blocked but ineffective" but is actually "not enforced yet"). Sample historical `Fraud::ScraperSignature` / `Fraud::SignupFraudClassification` records for the ring's known fingerprints and check whether:
   - Volume on the blocked domain actually dropped to ~0 after enforcement began (confirms the block itself works). Note this needs a real post-enforcement window to be conclusive — a couple of days of zero volume is suggestive, not proof.
   - The *same* fingerprints (JA4, Darwinium behavioral, device signature per IOC 1–3) reappeared under a **different** domain after the block date — this is the tactic-shift signal, not domain-name similarity.
   - `cf_bot_score_distribution` for the ring's fingerprints shifted toward "looks human" after the block (IOC 4) — a sign the ring adapted its scraping behavior specifically to evade the Cloudflare bot heuristic.
1. **Report.** Timeline, current status (contained / shifted / inconclusive), and evidence for each claim (link the query or record, not just a conclusion). If evidence suggests a shift, name the new domain/fingerprint and hand off to `/apollo-eng-fraud:abuse-ring-blocker` rather than proposing a block yourself — Tracker only observes.

## Constrained / Operator Mode

This skill can run in a token/time-capped mode so it is safe to invoke from a lower-trust caller (see [operator-mode.md](../../references/operator-mode.md) for the full contract shared with `abuse-ring-blocker`). In this mode: `--mode=monitor-only` is implied (no PR proposal, no write actions — Tracker never writes anyway, but the cap still applies to query volume), `--max-turns` bounds investigation depth, `--time-budget` bounds wall-clock. On exceeding either cap, stop and report partial findings labeled "capped — not exhaustive" rather than truncating silently.

## Example Report

```text
Target: example-ring.test (team 0000...0001)
Timeline: first signup 2026-07-01 | fraud label 2026-07-03 | BlockedDomain created 2026-07-10 | is_scraper_domain enforced 2026-08-02 (PR #NNNN) | teams soft-deleted 2026-08-02
Branch: enforcement age 66 days -> effectiveness analysis
Evidence: volume 412/day before vs 0/day after (query: <link>); JA4 f1 reappeared on other-domain.test 2026-08-09 (IOC 1)
Status: shifted (2 IOCs agree: IOC 1, IOC 3)
Next: hand other-domain.test to /apollo-eng-fraud:abuse-ring-blocker
```

## Workflow Contract

- **Deterministic (this skill provides):** the timeline sources to check, the 7-day enforcement-age branch rule (UTC), the IOC field list, the monitor-vs-analyze split, the constrained-mode caps.
- **Agent judgment:** whether volume/fingerprint evidence adds up to "contained" vs. "shifted" vs. "inconclusive," which historical sample size is enough to be confident.
- **Human (fraud/eng reviewer):** decides whether a detected shift warrants action; owns any resulting block decision (via `abuse-ring-blocker`).

## Safety

Read-only. Never blocks a domain, deletes a team, or modifies `BlockedDomain`/`blocked_domains` state — this skill only queries and reports. All Mongo access is read-only queries against existing collections; never print `password_reset_token`, `encrypted_old_password`, or other secret-adjacent fields even if a query happens to return them.

## Checklist

- [ ] Target resolved to a concrete domain before querying
- [ ] Timeline includes first-seen, fraud label, block date/PR, team-deletion date/PR (or "not found" stated explicitly)
- [ ] Branch (monitor vs. analyze) chosen based on actual block date, not assumed
- [ ] Every IOC claim cites the specific field/record it came from
- [ ] No typosquat-domain-name matching performed (see reference doc for why)
- [ ] No secret-adjacent fields printed
- [ ] Constrained-mode caps (if passed) respected; partial results labeled as such

## Further Reading

- [../../references/ioc-methodology.md](../../references/ioc-methodology.md) — exact IOC fields and the fraud-pack methods that read them
- [../../references/operator-mode.md](../../references/operator-mode.md) — constrained/capped invocation contract shared with `abuse-ring-blocker`
- `/apollo-eng-fraud:abuse-ring-blocker` — identify a new ring and decide whether to block it
