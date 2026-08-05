# Jira Filing Rules (opt-in only — not part of any phase's default flow)

**Default behavior: Notion first, Jira optional.** Every genuine bug this skill finds is already
logged as a Notion Bugs DB row by the time Phase 4 finishes (per
`notion-bugs-and-evidence.md`) — that's the durable record, unconditionally, every run. Jira
ticket creation is a **separate, standalone action** that only ever happens when the user or team
**explicitly asks for it**, naming a **specific epic**. Never file to Jira automatically, never infer
that filing was wanted from context, and never skip the Notion logging step in favor of Jira — Notion
logging always happens regardless of whether Jira is ever touched.

This can be requested at any point — mid-run, right after a feature's bugs are logged, or well after
the whole campaign is done, by pointing back at the Notion bug rows already created. There is no
per-feature-vs-batch timing choice to make; filing (when requested) just happens at the point it's
requested, for whichever bugs are named or implied.

Filing a real Jira ticket is a visible, hard-to-reverse action against a shared system — treat it
with the same care as any other action in that category (see the top-level "Executing actions with
care" guidance). This never runs unattended.

## What counts as a genuine bug (file it) vs. an environment/access issue (don't)

File a ticket only for a **genuine product defect** — something wrong in the application itself that
will still be wrong for the next person who hits it, regardless of this run's specific environment
state. (Note: this same distinction already governed *whether a bug got logged to Notion at all* in
Phase 4 — an environment/access issue that got resolved mid-run was never logged as a Notion Bugs row
in the first place, so at the point Jira filing is requested, every already-logged Notion bug is
already a candidate by definition. Re-apply the same judgment here as a final check, not a redundant
first pass.)

The one exception: if an environment/access blocker itself revealed a real product gap (e.g. "this
limit being hit produces zero user-facing error in any failure mode"), that gap should already exist
as its own genuine-bug Notion row (distinct from the access/quota issue itself) — file that one
normally if asked.

When genuinely unsure whether a specific Notion bug row qualifies, ask the user rather than guessing
— this determines whether a ticket gets created, which is the harder-to-reverse action.

## Prerequisites before filing anything

1. **MCP check:** confirm the Jira/Atlassian MCP connection is available now — this wasn't checked
   upfront in Phase 0 (since most runs never touch Jira), so verify it at this point instead of
   assuming it's connected.
1. **Target epic:** ask which epic to file under if it wasn't already given as part of this request.
   Don't guess an epic from unrelated context, and don't reuse an epic from a different run/feature
   without confirming it still applies.

## Confirmation gate (required, every time)

1. List every candidate bug this request covers (a specific bug, "everything found for feature X," or
   "everything logged this campaign") by pulling from the already-created Notion Bugs rows — don't
   re-derive the list from memory or local files.
1. Use `AskUserQuestion` (or present the list in chat if there are many) and get explicit confirmation
   per bug, or an explicit "file all of these" for a named batch — never file on an assumed yes.
1. Only after confirmation, create the ticket(s).

Never auto-fix an underlying environment/access blocker (flipping a feature flag, upgrading a billing
plan, rotating a credential) as a side effect of this — surface it and let the user decide, same as
any other shared-system, hard-to-reverse action.

## Filing mechanics

- Prefer the Jira MCP tool for creating issues (e.g. `createJiraIssue` — exact tool name may vary by
  environment; if the Jira MCP is unavailable, tell the user rather than falling back to any other
  write path).
- **Ticket body:** reuse the corresponding **Notion Bugs DB row's own content** (its `Description` /
  `Steps to Reproduce` / `Expected Result` / `Actual Result` sections) verbatim as the ticket
  description — Notion is the source content now, not a local file. Don't rewrite or summarize it
  into something thinner than what's already there.
- **Ticket title:** the bug's `Title` property value from its Notion row.
- **Severity/priority:** map the Notion row's `Priority` property directly (P0→Critical/Highest,
  P1→High, P2→Medium, P3→Low) unless the target Jira project uses different labels — ask if unclear.
- **After the ticket is created, the last step is always the Notion link-back:**
  `notion-update-page` (`update_properties`) on that same Bugs DB row, setting `Jira` to the new
  ticket URL. This links the existing row to the new ticket — it is never a new/duplicate Notion
  page, and never removes or archives anything from Notion.

## Confirming back to the user

After filing, state plainly which epic the tickets were filed under and which Notion bug row(s) got
linked back (per the "Output Expectations" this skill is held to) — don't leave the user to infer it
from a diff of Notion properties.
