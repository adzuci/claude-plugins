---
name: Plan from Jira
description: Fetches a Jira ticket using the Jira MCP, analyzes the requirements, and generates a structured implementation plan. Activate when the user provides a Jira issue key and asks to plan or implement it, says "plan from jira", "plan this ticket", or "create a plan for <TICKET-ID>".
trigger: User provides a Jira ticket ID and asks to plan or implement it, or says "plan from jira" / "plan this ticket"
---

# Instructions

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
     > Get an API token at https://id.atlassian.com/manage-profile/security/api-tokens, then re-run this skill.

2. **Get the Jira ticket ID**: If not already provided, check the current git branch name (`git branch --show-current`) for a ticket key (e.g. `ENG-1234`). If still not found, ask the user.

3. **Check for an existing plan**: Look in the `.context/` folder for a file matching that ticket ID.
   - If found, ask the user whether to use the existing plan or create a fresh one.
   - If they choose to reuse it, display the existing plan and stop.
   - If they choose to redo it, delete the existing file and continue.

4. **Fetch the ticket**: Use the `getJiraIssue` MCP tool to retrieve the ticket details.

5. **Fetch linked issues**: If the ticket has linked subtasks or blocking issues, fetch each with `getJiraIssue` to understand the full scope.

6. **Analyze the ticket**:
   - Review the title and description.
   - Extract acceptance criteria if present.
   - Note relevant labels, priority, linked issues, and status.

7. **Assess completeness**:
   - If the description is empty or too vague, summarize what is available and ask the user to fill in the gaps before continuing.
   - If the description is sufficient, proceed.

8. **Analyze the codebase**: Using Glob, Grep, and Read, identify files and patterns most relevant to the work. Be targeted — focus on what the ticket points to, not the entire codebase.

9. **Generate the plan**: Produce a structured markdown plan (see Output Format below) grounded in both the ticket content and the actual codebase.

10. **Present the plan**: Show the draft plan to the user and ask for confirmation. **Do not write any files or make code changes before the user approves.**

11. **Save context** (optional): Ask the user if they want to save the plan for future reference.
    - Default filename: `.context/PROJ-123_plan.md`

12. **Enter plan mode** (optional): If the user approves the plan, offer to enter plan mode to begin implementation.

# Output Format

```markdown
# Plan: [Issue Title] ([TICKET-ID])

## Summary
[1-3 sentence description of the goal and why it matters]

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

# Example

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
2. Create `app/middleware/rate_limit.rb` with per-IP and per-token limits
3. Configure throttle rules matching acceptance criteria
4. Mount middleware in `config/application.rb`
5. Return `429 Too Many Requests` with a `Retry-After` header on limit breach

## Edge Cases / Open Questions
- Should authenticated users get a higher limit than anonymous requests?
- What happens to in-flight requests when a limit is hit mid-burst?

## Suggested Tests
- Request within limit returns 200
- Request exceeding limit returns 429 with `Retry-After` header
- Limit resets after the window expires

Does this match your understanding? Should I save this plan or proceed to implementation?
