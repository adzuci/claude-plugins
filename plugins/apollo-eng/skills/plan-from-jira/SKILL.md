---
name: plan-from-jira
description: Fetches a Jira ticket using the Jira MCP, analyzes the requirements, and generates a structured implementation plan. Activate when the user provides a Jira issue key and asks to plan or implement it, says "plan from jira", "plan this ticket", or "create a plan for <TICKET-ID>".
---

> **Based on a skill originally written by Farhad.**

# Plan From Jira

## When to Activate

- User provides a Jira issue key (e.g. `ENG-1234`) and asks to plan, implement, or start work
- User says "plan from jira", "plan this ticket", or "create a plan for [ticket]"
- User shares a Jira URL and asks what needs to be done

## Instructions

Follow these steps when generating an implementation plan from a Jira ticket:

1. **Check for the Jira MCP**: Verify that the Atlassian MCP is available by checking whether `getJiraIssue` is listed in your available tools.

   - If it is not available, tell the user it needs to be configured and stop:

     > The Atlassian MCP isn't configured in this environment. To use this skill, add it to your Claude Code settings:
     >
     > ```json
     > {
     >   "mcpServers": {
     >     "atlassian": {
     >       "command": "npx",
     >       "args": ["-y", "@anthropic-ai/mcp-server-atlassian"],
     >       "env": {
     >         "ATLASSIAN_EMAIL": "you@example.com",
     >         "ATLASSIAN_API_TOKEN": "<your-api-token>",
     >         "ATLASSIAN_DOMAIN": "your-org.atlassian.net"
     >       }
     >     }
     >   }
     > }
     > ```
     >
     > Get an API token at <https://id.atlassian.com/manage-profile/security/api-tokens>, then re-run this skill.

1. **Get the Jira ticket ID**: If not already provided, scan the current git branch name for a ticket key using the pattern `[A-Z][A-Z0-9]+-\d+` (matches keys like `ENG-123`, `APOLLO-456`, `ENGOPS-12`):

   ```bash
   git branch --show-current
   ```

   - If exactly one key is found, use it.
   - If multiple keys are found, list them and ask the user which one to use.
   - If no key is found, ask the user to provide one before continuing.

1. **Check for an existing plan**: Look in the `.context/` folder for a file named `<TICKET-ID>_plan.md`.

   - If found, ask the user: **reuse** the existing plan, or **redo** it?
   - If reuse: display the existing plan and stop.
   - If redo: keep the existing file for now and generate a fresh draft. Only after the user approves the new plan, rename the old file to `<TICKET-ID>_plan.old.md` as a backup and save the new one.

1. **Fetch the ticket**: Use the `getJiraIssue` MCP tool to retrieve the ticket. Capture:

   - Title / summary
   - Description and acceptance criteria
   - Priority, labels, components, and status
   - Linked issue keys (subtasks, blocks, is blocked by)

1. **Fetch linked issues**: Fetch linked issues with `getJiraIssue`, but with these constraints:

   - Only fetch **subtasks** and **blocks / is blocked by** relationships by default. Skip "relates to" or "duplicates" links unless the user asks.
   - Fetch at most **5 linked issues**. If more exist, list the remaining keys and ask the user which ones to include before fetching further.

1. **Analyze the ticket** — check for:

   - A clear goal or intended outcome
   - Explicit acceptance criteria or requirements
   - Impacted component hints (labels, components, stack references)

1. **Assess completeness** — a ticket is **sufficient** if it has all three: (a) clear goal, (b) acceptance criteria or explicit requirements, and (c) at least one component/area hint.

   - If one or more are missing: produce a **draft plan with an Assumptions section** listing what you inferred, then ask 2–4 targeted questions to fill the gaps. Do not stop completely — a partial plan is more useful than nothing.
   - If sufficient: proceed directly to codebase analysis.

1. **Analyze the codebase**: Using Glob, Grep, and Read, identify files and patterns most relevant to the work. Be targeted:

   - Search for the ticket key in code, comments, and recent commits (sometimes referenced).
   - Extract 3–5 keywords from the title and acceptance criteria; grep for those.
   - Identify entry points first (API routes, feature flags, service boundaries) before scanning broad directories.
   - Read at most **10 files** unless the user asks for deeper analysis.

1. **Generate the plan**: Produce a structured markdown plan (see Output Format below) grounded in both the ticket content and the actual codebase.

1. **Present the plan**: Show the draft plan to the user and ask for confirmation.

   - **Do not write any files or make code changes before the user approves.**
   - If the user requests edits, revise the plan and re-present it for confirmation.
   - If the user approves, you may proceed to implementation or plan mode — but still make no code changes until they explicitly say to implement.

1. **Save context** (default: ask): Ask the user if they want to save the plan. Default to **yes** unless they decline.

   - Derive the filename from the actual ticket key: `.context/<TICKET-ID>_plan.md`
   - Create `.context/` only after the user approves — consistent with the no-writes-before-approval rule.

1. **Enter plan mode** (optional): Offer to enter Claude Code's plan mode to begin structured implementation. Plan mode lets you lay out tasks and get step-by-step approval before any code is written.

# Output Format

```markdown
# Plan: [Issue Title] ([TICKET-ID])

## Summary
[1-3 sentence description of the goal and why it matters]

## Assumptions
[Only include if ticket was incomplete — list what you inferred and flag what needs confirmation]

## Affected Areas
- `path/to/file` — [what changes here]

## Implementation Steps
1. [Step 1]
2. [Step 2]
...

## Edge Cases / Open Questions
- [item]

## Suggested Tests
- [test description]
```

> Only include the **Assumptions** section when the ticket was incomplete. Omit it for well-specified tickets to keep the plan clean.

## Example

**User**: "Plan ENG-1234"

**Assistant**:
*[Fetches ticket ENG-1234]*

Here's the implementation plan for **ENG-1234: Add rate limiting to the API**.

# Plan: Add rate limiting to the API (ENG-1234)

## Summary

Protect public API endpoints from abuse by enforcing per-user request limits. This prevents denial-of-service from misbehaving clients and ensures fair resource usage.

## Affected Areas

- `app/middleware/rate_limit.rb` — new middleware to track and enforce limits
- `config/routes.rb` — apply middleware to public endpoints
- `spec/middleware/rate_limit_spec.rb` — new tests

## Implementation Steps

1. Add `rack-attack` gem to `Gemfile`
1. Create `app/middleware/rate_limit.rb` with per-IP and per-token limits
1. Configure throttle rules matching acceptance criteria
1. Mount middleware in `config/application.rb`
1. Return `429 Too Many Requests` with a `Retry-After` header on limit breach

## Edge Cases / Open Questions

- Should authenticated users get a higher limit than anonymous requests?
- What happens to in-flight requests when a limit is hit mid-burst?

## Suggested Tests

- Request within limit returns 200
- Request exceeding limit returns 429 with `Retry-After` header
- Limit resets after the window expires

Does this match your understanding? Should I save this plan to `.context/ENG-1234_plan.md`, or would you like any changes first?
