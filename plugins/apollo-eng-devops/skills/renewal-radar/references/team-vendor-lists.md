# Team Vendor Lists

Per-team vendor short-lists the renewal radar sweeps in step 3 of `/apollo-eng-devops:renewal-radar`. Look up the section matching the resolved `TEAM`/department. If there is no section for it yet, skip the sweep and say so — do not guess at a list.

## This Is An Example List — Edit It Per Team

**These names are illustrative, not a hardcoded universal list.** DevOps/Infrastructure is the only section populated today because it's this skill's primary user. Any other team adopting this skill should add its own section with the vendors it actually owns. Keeping a stale or borrowed list is worse than an empty one, because it produces confident "no visible contract" lines about vendors nobody on that team cares about.

Keep each team's list short. The sweep is one `list_vendors` call per name, so a list of 40 turns a fast digest into a slow one for little added signal. A dozen or so of the vendors that would genuinely hurt to miss is the right size per team.

## Why The Sweep Exists

Agreement reads are scoped to what the caller can see, and a contract filed by Procurement or by a former owner may not appear in the digest at all. The sweep catches the specific failure mode where **Zip knows about the vendor but no agreement surfaced** — which usually means the contract exists and is invisible to this caller, not that there is no contract.

That distinction matters, so report it explicitly. A vendor in the resolved team's list with a Zip vendor record but no agreement in the digest gets a "Zip has this vendor, no visible contract" line. Never report it as silence, and never report it as "no contract exists".

A vendor in the list with no Zip vendor record at all is a different and less interesting result. It usually means the vendor is billed on a corporate card or through a reseller rather than contracted directly.

## DevOps / Infrastructure

| Vendor | Notes |
|---|---|
| Cloudflare | Edge, WAF, tunnels |
| Google Cloud / SADA | GCP is resold through SADA, so the agreement may be filed under either name. Search both |
| Redis | Managed Redis |
| Redpanda | Streaming. Renewed early in mid-2026 (a new 3yr term started before the prior 2yr term's own end date) — expect two POs, one closed out with `$0` open balance and one live with an open balance and a line item that may read as a "correction" from that early switch-over. See the PO-ranking signal in `SKILL.md` step 3.3 before assuming either PO is wrong. |
| Grafana | Observability |
| Dragonfly | In-memory datastore |
| Darwinium | Fraud/bot defense |
| Dopple | Data tooling — this is **Dopple**, not a typo for "Doppler" (the secrets manager). Different vendor; don't "correct" it. |

## Add Your Team

Copy this shape for a new team section:

```markdown
## <Team Name>

| Vendor | Notes |
|---|---|
| <name> | <what it's for, and any aliasing/reseller note like the SADA one above> |
```

## Matching Notes

The `list_vendors` `name` filter is a case-insensitive **substring** match against the indexed `name_key`, so a partial name works and is usually safer than a full legal entity name. `Redis` matches `Redis Labs, Inc.`; `Redis Labs, Inc` may not match a record stored as `Redis Ltd`.

Prefer the shortest distinctive fragment. Watch for the opposite failure: a fragment short enough to match unrelated vendors. If a name returns several vendor records, list them rather than guessing which one is the team's.
