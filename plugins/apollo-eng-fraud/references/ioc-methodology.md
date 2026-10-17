# IOC Methodology

Concrete, field-level indicators of compromise for tracking a blocked-domain abuse ring's evasion attempts. Shared by `abuse-ring-tracker` and `abuse-ring-blocker`.

**Typosquat/lookalike domain-name matching is intentionally excluded.** For a two-domain ring like triquetra.life/ardour.life, scanning for visually- or lexically-similar new domains has a poor signal-to-noise ratio — real rings rotate to unrelated domains, and near-miss string matching mostly finds coincidental noise. Prefer the behavioral/fingerprint IOCs below, which follow the actor rather than the domain string.

## IOC 1 — Shared JA4 TLS Fingerprint

`Fraud::ScraperSignature.find_fingerprint(ja4_fingerprint, cached: false)` — look up the ring's known JA4 fingerprint(s) (captured from `Fraud::ZpDeviceId#ja4` on the original blocked signups). If a *new* signup or request carries the same JA4 fingerprint, that's a direct re-identification regardless of domain. Check `analysis_summary` / `high_confidence_scraper?` (request_total ≥ 100, teams_total_arr ≤ 10000, > 75% of requests at `cf_bot_score` ≤ 30) to see if the new activity already crosses the existing scraper threshold.

## IOC 2 — Device Signature Consistency Break

`check_consistency(user_agent, ja4)` is an **instance** method on `Fraud::ZpDeviceId` (call it on the record you looked up, e.g. `zp_device_id.check_consistency(user_agent, ja4)` — not `Fraud::ZpDeviceId.check_consistency(...)`), returning `:consistent` / `:needs_update` / `:inconsistent`. A ring evading detection by spoofing `user_agent` while keeping the same JA4 (or vice versa) shows up as `:inconsistent` — the TLS-level fingerprint and the presented browser/OS (`browser`, `os`, `os_version` on `Fraud::ZpDeviceId`) stop matching. Flag any inconsistent pairing tied to a domain/team under investigation.

## IOC 3 — Darwinium Behavioral Fingerprint Pairing

`Fraud::SignupFraudClassification` records `behavioral_ja4_fingerprint` and `behavioral_fingerprint` (Darwinium) alongside `domain`/`team_id`/`risk_level_cd`. Pair these two fields for the known ring and search for the same pairing under a different `domain`. A ring that changes domain but reuses the same automation/browser profile will keep the same Darwinium behavioral fingerprint even when the JA4 rotates.

## IOC 4 — Cloudflare Bot-Score Drift

`Fraud::ScraperSignature#cf_bot_score_on_create` and `#cf_bot_score_distribution` (a Hash of score buckets) for the ring's fingerprint(s). A ring actively adapting to evade the block will show its score distribution drifting from low ("looks like a bot") toward high ("looks human") over time for the *same* fingerprint — that shift is itself the IOC, independent of whether the domain changed.

## IOC 4b — Shared IP / User-Agent Across `http_requests_v3`

Cross-reference `http_requests_v3.ip` and `http_requests_v3.user_agent` for the domain/team under investigation against the ring's known values. Pull via read-only `bin/rails runner` (run from the leadgenie repo root, `~/code/apolloio/leadgenie`) or a Mongo query, not raw credentialed shell access. **This IOC is a stretch goal, not a required step** — `http_requests_v3` was not reachable through the available staging MongoDB MCP tools when this skill was last tested; if it's not reachable, say so in the report rather than skipping the caveat. **Exclude** `password_reset_token` and `encrypted_old_password` and any other secret-adjacent field from any query, output, or report — never print these even incidentally.

## Applying These IOCs

For each IOC, report: which fingerprint/field matched, the record(s) it matched against, and the date range. A single IOC match is a lead, not a conclusion — `abuse-ring-tracker`'s effectiveness analysis and `abuse-ring-blocker`'s complexity assessment should look for at least two independent IOCs pointing the same direction before calling it a confirmed tactic shift.
