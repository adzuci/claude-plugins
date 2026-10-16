# 26 — Authority Policy

> The third narrowing pass. **Outcome → files → actions.** We had the first two.
> **Status: draft for review. The policy itself is data, in [`authority/policy.yml`](./authority/policy.yml).**

## 1. Why this is not hypothetical for us

The gap: our per-stage "must not do" lists are prose, scattered across stage docs, so the union is not auditable and coverage is unknowable. Scope contracts bound which **files** a slice may change. Nothing bounds which **actions** it may take, and actions are where irreversible damage lives.

For a file-scoped harness with `bash`, the exposure is total. Concretely, in our environment:

- An agent in BUILD could run a migration against whatever `MONGODB_URI` resolves to. `CLAUDE.md` says never override it — that is a *rule*, not an *enforcement*.
- A VERIFY pass could trigger a reindex on a live Elasticsearch index.
- **The pilot's own domain has an agent that could upload an audience to a customer's real Google Ads account.** That is the product working as designed, aimed at production, by an agent that was only told which files it could edit.
- A handoff artifact could carry a credential into the repo, which is how the reference failure escalated from data loss to a leaked secret.

None of those require the agent to misbehave. They are reasonable moves toward a ticket.

## 2. The policy is data, not hook code

The correction that motivates this doc:

> The hook enforces; the policy is the written contract stating what it enforces and which named transitions exist.

If the policy lives inside hook code we cannot review it, version it, diff it, or hand it to a cold session — and an unexercised hook is indistinguishable from a dead one.

So: **`authority/policy.yml` is the policy.** A `PreToolUse` hook reads it and enforces. Changing what the harness may do is a reviewable diff to a data file, not a code change nobody notices.

## 3. Action classes

The policy defines a **closed** action space, because an open one cannot be exhaustively routed and an unclassified action defaults to whatever the model decides.

| Class | Examples | Default |
|---|---|---|
| `read_only` | Read, Grep, Glob, read-only queries | **allow** |
| `local_mutate` | Edit and Write inside the slice's file scope, local test runs | **allow within scope** |
| `repo_publish` | Commit, push a branch, open a draft PR | **allow**, draft only |
| `repo_irreversible` | Force push, merge to a default branch, tag, publish a package, rewrite history | **deny** |
| `schema_mutate` | Migrations, index create or drop, reindex | **deny** — human, and migration PRs ship alone |
| `data_destructive` | Bulk delete, collection drop, DB reset, truncate, `removeAll` against any platform audience | **deny**, no exception path |
| `external_side_effect` | Any write to a third-party system: ad-platform upload, CRM push, email or SMS send, Slack post, webhook | **deny** outside a sandbox account |
| `config_mutate` | Feature-flag change, credential rotation, environment variable override | **deny** |
| `spend` | Anything consuming paid quota or ad budget | **deny** above a stated cap |
| `notify_human` | Jira transition, Slack message, PR comment on someone else's PR | **ask** |

Two properties matter more than the specific rows: the space is **closed**, and **`data_destructive` has no exception path at all.** A grant mechanism that can authorise a database reset will eventually authorise one.

## 4. Environment identity must be asserted, not assumed

> Which rows that variable points to is a fact about deployment, and no part of the repository told the agent which fact was true today.

This is our exposure exactly. `MONGODB_URI`, `ELASTICSEARCH_URI` and `REDIS_URI` are environment variables, and lean mode runs deterministic checks locally with nothing asserting where they point.

**Rule: before any action above `local_mutate`, the resolved target environment is asserted and recorded.** Not "the config says test" but the resolved host, compared against an allowlist. A mismatch is a denial, not a warning.

This also closes a subtler hole: an action that is safe in one environment and catastrophic in another cannot be classified by the action name alone. `db:reset` is `local_mutate` against a disposable local database and `data_destructive` against anything else. **Classification is action plus resolved target.**

## 5. Secrets never enter the artifact plane

Three rules, and the third is the one the reference failure violated:

1. The agent receives credentials through the runtime, never by reading a file that contains values.
2. The agent never writes a credential value anywhere — not a file, not a commit, not a log.
3. **The agent never writes a credential into a handoff artifact.** Handoffs are durable and reviewed by cold sessions, which makes them the highest-value place to leak and the easiest to forget.

Our credential surface is `config/credentials_provider/*.yml` plus 1Password. The policy names the paths as read-forbidden rather than trusting the agent not to be curious.

## 6. Denial receipts

**Every denial emits a receipt.** This is the highest-value single mechanic here, and it is our own bug class arriving at a new layer.

A blocked action that produces nothing is indistinguishable from an action that was never needed. So a hook that has never denied anything is indistinguishable from a hook that is dead — the same problem as a gate that never fires, and as a query that returns empty because the name was wrong.

A receipt records: the action, its class, the resolved target, the rule that denied it, the run and event id, and what the agent did next. That last field is what tells you whether the denial worked or the agent simply routed around it.

Receipts go to the ledger. A rising denial rate for one class is a signal that the scope contract is wrong, not that the agent is misbehaving.

## 7. Grants are named, scoped and time-boxed

When a human widens authority, the grant carries: **who** granted it, **what** class and target, **why**, and an **expiry**. No open-ended grants, and no grant that outlives the run it was issued for.

`data_destructive` is exempt from the grant mechanism entirely.

## 8. Where this sits relative to what exists

| Layer | Bounds | Already had it? |
|---|---|---|
| Ledger / initiative | Which **outcome** may consume the session | Yes |
| Scope contract | Which **files** may change | Yes |
| **Authority Policy** | Which **actions** may be taken, against which **environment** | **No — this doc** |

Stage-agnostic on purpose. A per-stage list produces a union nobody can audit; one policy over one closed action space is checkable.

**It composes with, and does not replace, existing human gates.** Sensitive-file approval via policy-bot stays a person. Migration-only PRs stay a rule. G4b rollout readiness stays a checklist. Authority Policy is about what an agent may *attempt*, not about what a human must *approve*.

## 8b. Read back after every outward action

A success code is not evidence the intended state landed: on a past Ads M1 build a design write returned
`written: 1`, and only reading the remote file back confirmed the compliance markers were there. Every
outward or irreversible action (a remote write, a publish, a push, a page update) is followed by a read of
the resulting state before the stage reports it done.

## 9. What this does not solve

- **It cannot classify an action it has never seen.** A new tool or MCP server introduces unclassified actions, and the default must be deny-and-receipt rather than allow. That makes adding a tool a policy change, which is friction — and correct friction.
- **It does not prevent a correctly-authorised action from being wrong.** Authority is about permission, not judgement.
- **It is only as good as environment resolution.** If the resolved target is wrong, the classification is wrong, and the denial fires in the wrong direction.

## 10. Open questions

| # | Question | Owner |
|---|---|---|
| Q-AP1 | What is the allowlist of safe resolved targets per action class? Needs SRE input; guessing it defeats the purpose | author + SRE |
| Q-AP2 | Does the `PreToolUse` hook have enough information to resolve the target environment for a `bash` command, or does it need a wrapper that resolves first? Likely a wrapper, which is more work but also the only reliable version | author + AI Tooling |
| Q-AP3 | Denial receipts belong in the ledger, but the ledger is per-initiative and authority is global. Two stores, or one with a scope field? | author |
| Q-AP4 | The pilot's ad-platform upload is `external_side_effect`. Is there a genuine sandbox ad account to allow it against, or is that action human-only indefinitely? | author + the initiative's DRI |
