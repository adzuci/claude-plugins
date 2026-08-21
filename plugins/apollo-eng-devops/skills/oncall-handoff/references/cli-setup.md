# CLI Setup And Fallbacks

Use this reference during preflight when the handoff needs PagerDuty or Jira evidence.

## PagerDuty CLI (`pd`)

Check:

```bash
command -v pd
pd rest:get -e /users/me
```

If `pd` is missing, suggest:

```bash
npm install -g @pagerduty/cli
pd login
```

If `pd` is installed but unauthenticated, suggest:

```bash
pd login
```

Fallbacks:

1. Use a PagerDuty MCP only if it is already available in the current tool list.
2. Use Glean-indexed PagerDuty/Jira/Slack evidence as degraded context.
3. Mark PagerDuty current-state checks incomplete if neither CLI nor MCP can read live PD.

## Atlassian CLI (`acli`)

Check:

```bash
command -v acli
acli jira workitem view INCIDENT-1 --help
```

If `acli` is missing, suggest Atlassian's official install path for the user's platform and
then authentication. On macOS, that is typically:

```bash
brew tap atlassian/tap
brew install acli
acli jira auth login
```

If `acli` is installed but unauthenticated, suggest:

```bash
acli jira auth login
```

Fallbacks:

1. Use Jira/Atlassian MCP read tools only if already available in the current tool list.
2. Use Glean/Notion indexed Jira results as a degraded fallback.
3. Mark Jira status/assignee/update-age checks incomplete if neither CLI nor MCP can read
   live Jira.

## Slack Fallback

If live Slack access is unavailable (no local CLI token, no MCP OAuth), use this fallback
order rather than treating missing Slack access as a dead end:

1. **Jira/PagerDuty ticket descriptions and comments that reference a Slack thread** are a
   first-party fallback source. Prefer reading the quoted or linked Slack content directly
   from the ticket over trying to re-find the same thread in Glean's Slack index.
2. **Glean's indexed Slack messages** are a second-tier source. Glean's Slack index has real
   gaps — a specific permalink or timestamp not turning up in Glean does not mean the
   message did not happen, it means Glean has not indexed it. Report this as "not found in
   Glean's index," not as evidence the content doesn't exist.
3. If neither source confirms a piece of Slack context, mark it degraded/unverified rather
   than omitting it or asserting it did not occur.

## Reporting Language

Use precise source labels in the tool table:

- `PagerDuty pd-cli`
- `PagerDuty mcp`
- `PagerDuty missing`
- `Jira acli`
- `Jira mcp`
- `Jira via Glean`
- `Jira missing`

Do not install CLIs or authenticate tools during a handoff unless the caller explicitly
approves that separate setup action.
