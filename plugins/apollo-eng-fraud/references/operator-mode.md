# Constrained / Operator Mode

Shared invocation contract for `abuse-ring-tracker` and `abuse-ring-blocker` when run from a lower-trust or automated caller (a scheduled job, or in theory a broader internal agent platform like Apollo Operator).

## Why This Exists and Its Actual Scope

There is currently no self-service integration point for a new skill to be *directly* callable from Apollo Operator's broader agent platform (that platform's tool/skill registration is code-based, in a separate repo, and out of scope here). What this section actually delivers is the skill's own internal constrained mode: explicit flags that any caller — human or automated — can pass to bound what the skill does. If/when a real Operator integration point exists, it should call the skill with these same flags rather than needing a new contract.

## Flags

- `--mode=monitor-only` — disables every write-adjacent or proposal step. For `abuse-ring-tracker` this changes nothing observable (it never writes), but it still caps query volume. For `abuse-ring-blocker` this stops the workflow after the complexity assessment (step 4) — no PR is drafted, and the report ends with "monitor-only mode: stopping before PR proposal; escalate to a human for the block decision."
- `--max-turns=N` — caps the number of agent-tool-call turns (searches, queries, Glean calls) spent on the investigation. Track turns explicitly; when the cap is hit mid-step, stop and report what was gathered so far, labeled "capped at N turns — not exhaustive," rather than silently truncating the report to look complete.
- `--time-budget=Ns` — caps wall-clock seconds. Same reporting rule as `--max-turns`: state the cap was hit, don't hide it.
- There is no write mode. `abuse-ring-blocker` always outputs the PR description/diff as text and never creates a branch, commit, PR, block, or team deletion; a human does that outside the skill.

## Defaults

Without any flags, both skills default to full investigation depth. They still never open a PR, push a commit, block a domain, or delete a team; a human performs those actions outside the skills.

## Degradation

If Glean, the Mongo read replicas, or `gh` are unavailable, say so explicitly in the report ("Glean unavailable — past-ring check not performed") rather than proceeding as if the check passed. This applies with or without constrained mode active.
