# Block PR Template

Mirrors the structure of PR #99593 ("Mark triquetra.life/ardour.life as scraper domains, delete their teams"), the precedent this skill follows for a reactive abuse-ring block.

## What the PR Should Do

1. Set `is_scraper_domain: true` (or the equivalent `BlockedDomain` flag) on each identified domain.
1. Soft-delete every team whose `Team#domain` **exactly equals** one of the identified domains, via `LoginDestroyer.soft_delete_abusive_team`. Do not expand this to cross-domain invited members or fuzzy domain matches without separate, explicit justification — that was intentionally out of scope in the precedent PR.
1. Apply the fraud label used in the precedent (`human_confirmed_data_scraping`) plus a system note recording the evidence (IOC matches, ring size, Glean past-ring result).
1. Follow the migration-file pattern used before (e.g. `2026_07_20_delete_xintaitong_teams.rb`) for the team-deletion piece if a migration file is the right vehicle in context.

## What the PR Description Must State Explicitly

- **Scope**: exact domains blocked, exact `Team#domain` equality rule, and what's intentionally excluded (e.g. root-cause fixes to shared invite/signup paths enforcing the blocked-domain check generally).
- **Evidence**: which IOCs matched, the ring size, and the Glean past-ring result (or "not checked — Glean unavailable").
- **False-positive guard**: state explicitly that the domain(s) being blocked are not a free-mail or otherwise broad domain, and confirm this against `EmailUtil.free_domain?`/the `WHITELISTED_DOMAINS`/`.edu` checks in `BlockedDomain.block_team` — this check is not optional regardless of how confident the fingerprint evidence looks.
- **Rollback**: how to undo the block (unset `is_scraper_domain`, and note that soft-deleted teams are recoverable via whatever `LoginDestroyer` soft-delete already guarantees — don't claim a rollback path that doesn't exist).

## Before Opening

Run `/apollo-eng:pr-description` and follow this repo's PR conventions (Conventional Commit-style title, `NOTICKET:` prefix if no ticket exists yet, per the precedent). Never open the PR itself without explicit human confirmation — this skill's job ends at producing the reviewed draft.
