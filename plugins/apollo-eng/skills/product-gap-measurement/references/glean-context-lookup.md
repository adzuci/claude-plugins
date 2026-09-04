# Glean Internal Context Lookup

Use this only in Pre-Ticket Mode, especially for raw ideation, to check whether a
product gap already has internal context (PRDs, Jira tickets, Slack threads, docs)
before sizing it from scratch. Not for pre-merge or post-merge — those modes already
have a PR or dashboard as source of truth, and Glean surfaces internal discussion,
not measurement.

## Runtime

Use the local `glean` CLI, not the Glean MCP connector — the CLI is token-cheaper.

```bash
glean auth status
```

If not authenticated or the CLI is missing, tell the user:

```text
Glean CLI isn't set up, so I'll skip internal-context lookup for this gap. To enable it,
run `glean auth login` in your own terminal (not via the inline `!` runner — it needs a
live prompt for your work email and a browser step), then say "ready".
```

Then continue the rest of the workflow without Glean. This step is optional and
best-effort only — never block pre-ticket sizing on it.

If authenticated, search first:

```bash
glean search "<product gap topic>" --limit 10
```

Use `glean chat` only when you need synthesis across multiple docs rather than a link list:

```bash
glean chat "Has Apollo previously discussed or scoped <product gap topic>? Summarize related PRDs, tickets, or threads with links."
```

## Output Integration

Add a `## Prior Internal Context (Glean)` section to the pre-ticket answer only when
Glean returned something relevant:

```md
## Prior Internal Context (Glean)
<relevant docs/tickets/threads found, each with a link>
```

Omit the section entirely when Glean is unavailable, unauthenticated, or returns nothing
relevant. Do not pad the answer with "no results found" noise.

## Rules

- Optional and best-effort only. Never block pre-ticket sizing on Glean.
- Glean results are internal discussion, not measurement evidence. Do not let them
  substitute for Amplitude exposure data or Enterpret support-severity data in the claim
  boundary.
- Prefer `glean search` for quick link-finding. Use `glean chat` only when synthesis adds
  value over a raw result list.
