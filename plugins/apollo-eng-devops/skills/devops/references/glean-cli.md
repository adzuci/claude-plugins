# Glean CLI (Runbook and Postmortem Lookups)

Use this reference when an SRE task needs Apollo's internal knowledge (runbooks,
postmortems, RCAs, prior incident history) and you want source-backed answers
rather than model recall. It mirrors the intercom-assistant Glean bridge so
production work uses the same authenticated Glean path.

## Runtime

Prefer the local Glean CLI:

```bash
python3 scripts/ask_glean.py --mode runbook --question "<what you need to find>"
```

Modes: `runbook`, `postmortem`, `rca`, `incident`, `ask`. Add `--context` to pass
incident/service framing that must not be treated as a verified fact.

The script calls:

```bash
glean agents run --json '{"agent_id":"<AGENT_ID>","input":{"query":"<question and context>"}}'
```

## Agent ID (must be confirmed)

There is no Apollo SRE Glean agent id hardcoded in the script. Supply it with
`--agent-id` or the `GLEAN_SRE_AGENT_ID` environment variable:

```bash
export GLEAN_SRE_AGENT_ID="<apollo-sre-glean-agent-id>"
python3 scripts/ask_glean.py --mode postmortem --question "es8 latency RCA follow-ups"
```

> Note: The SRE Glean agent id is intentionally left unset — no value is shipped
> or guessed. An SRE lead must confirm and set the real id (via `--agent-id` or
> `GLEAN_SRE_AGENT_ID`) before use, including whether SRE should target a Glean
> agent at all versus plain Glean search.

## Authentication

If `glean` is missing or unauthenticated, tell the user:

```text
Glean CLI is needed for source-backed runbook/postmortem lookups. Install/authenticate it, then run `glean auth login` or set `GLEAN_API_TOKEN`.
```

You may use Glean MCP/search as a clearly labeled degraded fallback for general
research, but do not present that output as a CLI-backed source answer.

## When To Call It

- You need the canonical runbook step for a service or alert.
- You need a prior postmortem or RCA for a recurring failure mode.
- You need incident history before declaring an issue novel.
- You need source-backed internal guidance before proposing a mitigation.

## When Not To Call It

- Live production state (pod status, queue depth, cluster health): use the
  matching MCP tools, not Glean.
- Customer-specific facts or account state.
- Cases where the user already pasted the runbook or postmortem content.

## Output Integration

Separate the Glean answer from live production state:

```text
Glean finding:
<brief source-backed runbook/postmortem/RCA answer, with links>

Live state still to verify:
<pod/queue/cluster/SLO facts Glean does not prove>

Recommended next step:
<mitigation or investigation that combines verified live state with the Glean-backed guidance>
```
