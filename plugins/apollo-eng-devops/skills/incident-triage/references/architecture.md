# Skill Architecture

End-to-end flow of `/apollo-eng-devops:incident-triage`. Use this as the map when debugging a step or proposing a change.

```mermaid
flowchart TD
    Preflight[Preflight:<br/>Atlassian + Glean + GitHub + PD MCPs] --> Identity
    Identity[Identity resolution:<br/>my team slugs] --> Registry
    Registry[Fetch apollo-dev-teams.yml] --> Scope
    Scope{Scope?} -->|unassigned default| F11741[filter = 11741]
    Scope -->|mine| Mine[assignee = currentUser]
    Scope -->|team| Team[team / component JQL]
    Scope -->|custom| Custom[user JQL]
    F11741 --> Queue[Fetch queue]
    Mine --> Queue
    Team --> Queue
    Custom --> Queue
    Queue --> Classify{Classify ticket}

    Classify -->|PD/Grafana alert| PDPath[Extract PD URL, service group,<br/>metric snapshot]
    Classify -->|Security finding| SecPath[Source label sniff:<br/>kodem/orca/bugcrowd/panther/claude-security]
    Classify -->|Customer report| CustPath[Extract reporter, named service, repro]
    Classify -->|Manual ask| ManualPath[Extract reporter, named service]
    Classify -->|No class| Hygiene[Hygiene flag:<br/>ask reporter]

    PDPath --> PDStatus{PD status?}
    PDStatus -->|triggered/acknowledged| Urgent[Urgent skim]
    PDStatus -->|resolved >24h| ClosePD[Propose Close]
    PDStatus -->|resolved <24h| Watch[Propose watch]
    PDPath --> PDRoute[Route by PD service<br/>or service-group tag]

    SecPath --> OWASP[OWASP bucket]
    OWASP --> CVE[CVE / reachability check<br/>+ CVSS context adjustment]
    CVE --> CODEOWNERS[Resolve path → CODEOWNERS]

    CustPath --> CODEOWNERS
    ManualPath --> CODEOWNERS

    PDRoute --> Validate
    CODEOWNERS --> Validate{Slug in<br/>registry?}
    Validate -->|yes| Decision
    Validate -->|alias match| Decision
    Validate -->|fuzzy match| FlagFuzzy[Flag in proposed comment]
    Validate -->|no match| FlagGap[Hygiene gap:<br/>route as ?]
    FlagFuzzy --> Decision
    FlagGap --> Decision

    Decision{Mine vs owner?} -->|mine ⊇ owner| Keep[KEEP: work / dedupe / downgrade]
    Decision -->|partial overlap| LoopIn[Loop in co-owner]
    Decision -->|disjoint| Reroute[Propose REROUTE]
    Decision -->|empty| Ask[Ask reporter]

    Keep --> Table[Print routing table]
    LoopIn --> Table
    Reroute --> Table
    Ask --> Table
    Hygiene --> Table
    Urgent --> Table
    ClosePD --> Table
    Watch --> Table

    Table --> Proposed[Print proposed comments]
    Proposed --> Approval{User approves<br/>per row?}
    Approval -->|approve KEY| Write[Execute Jira writes<br/>for named keys only]
    Approval -->|no approval| Stop[End session, no writes]
    Write --> Summary[Wrap-up summary]
```

## Source-of-truth wiring

The skill never hardcodes team names, Slack channels, or routing tables. It reads:

| Source | What it provides | URL |
| ---------------------- | ---------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| `apollo-dev-teams.yml` | The canonical list of currently-active team slugs and their metadata. | <https://github.com/apolloio/leadgenie/blob/master/apollo-dev-teams.yml> |
| Repo `CODEOWNERS` | Path → team mapping for each repo. | `.github/CODEOWNERS` in each affected repo |
| PagerDuty (MCP) | Live PD incident status, service ownership, responder assignment. | `claude mcp add --transport sse -s user pagerduty https://mcp.pagerduty.com/sse` |

Team renames are handled gracefully — see the rename-fallback section in [`team-lookup.md`](team-lookup.md).

## When this skill is right vs wrong

**Use it when** you have a queue to work through and want a structured pass: classification, ownership resolution, dedup, and per-row approval gates. Works for weekly reviews, sprint planning, on-call handoff, or just "what's on my plate?"

**Don't use it when** you're working a single specific ticket — use the `plan-from-jira` skill instead.

**Don't use it for** real-time incident response (page-out, active customer impact). This skill is for triage of accumulated tickets, not the on-call playbook.
