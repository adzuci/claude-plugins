# Shared On-Call Pending-Digest Workflow

Use this workflow for `/apollo-eng:oncall-daily-pending-digest` and
`/apollo-eng:oncall-weekly-pending-digest`. Each skill defines its own time window,
delivery, sections, and display limits where they differ.

## Access And Team Resolution

- Jira, Slack, and canonical `apollo-dev-teams.yml` access are required. Stop before
  sending if any is unavailable; report the failure in run output. PagerDuty and GitHub PR
  discovery are optional enrichment and must not block a digest.
- Read `apollo-dev-teams.yml` from the current workspace when present. Otherwise fetch
  `apolloio/leadgenie`'s default-branch raw file with authenticated `gh api` into per-run
  `/tmp` scratch space. Extract only the exact `teams[].name` match; never infer a partial
  match or cache the file in this plugin.
- Resolve explicit flags first. Defaults are the configured XFN channel, delivery channel
  (`team_slack_channel_id`, then `pr_review_channel_id`), Jira Impacted Team, and configured
  PagerDuty services. Never use `team_slack_usergroup_id` as an on-call group.
- Resolve `on_call_usergroup_name` only by exact Slack handle/name; omit its mention when
  lookup is absent or ambiguous. Resolve primary schedules from explicit IDs or clear team,
  service, description, and on-call-group evidence. Log ambiguity rather than guessing.

Run independent Jira, Slack, PagerDuty, and GitHub reads concurrently when the tool surface
permits. The managed runtime must never install dependencies or use third-party Python YAML.

## Source Rules

### Jira And Pantheon

- Search `INCIDENT` with an exact escaped Impacted Team value. Link rendered issues, truncate
  summaries to 100 characters, and retain priority.
- A qualifying existing Pantheon run is a current diagnosis comment containing both
  `Classification:` and `Outcome:`, or either legacy initial/retry-start comment. A label or
  unrelated comment is not evidence of a run.
- Find Pantheon Slack threads by exact Jira key or URL across the workspace with relevance
  ranking. If an incident has a matched Pantheon PR and no valid result, search once by that
  PR number. Accept only a valid top-level incident-diagnosis action or legacy announcement,
  choosing the most recently active valid parent when several exist.
- Search open `pantheon-apollo` incident PRs across `apolloio`, newest first; match each PR's
  single extracted `INCIDENT-<number>` to the exact selected Impacted Team. Do not block on a
  failed PR search; log the coverage gap.
- Before triggering, read [Pantheon trigger safeguards](pantheon-trigger.md). Outside a dry
  run, start at most three eligible displayed Jira incidents that have no qualifying Jira
  comment, Pantheon thread, or open Pantheon PR. Do not poll or retry failed starts.

### PagerDuty

- Treat PagerDuty as best-effort. After one authorization, schema, timeout, or tool failure,
  do not retry; continue the digest and log one short coverage note.
- Inspect `list_incidents` schema first. When server-side `service_ids` and `limit` exist,
  query each resolved service independently for `triggered` incidents with limit 25 and
  verify every returned incident belongs to that service. Paginate only that same filtered
  service request.
- If the managed connector lacks service filtering but offers `request_scope`, make exactly
  one `teams` request for triggered incidents, a 24-hour UTC window, and limit 25; locally
  retain exact service-ID matches only. Never widen, paginate, or retry it. If bounded
  querying cannot be guaranteed, discard the response and log unavailable coverage.
- For daily mode, additionally filter the valid response by the digest's 24-hour timestamp
  cutoff. For weekly mode, use current triggered state under the same bounded-query rules.

### Slack

- Scan the configured XFN channel over the invoking skill's lookback. Keep concrete asks of
  the team, a member, or its on-call group; exclude bots, announcements, clearly other-team
  requests, and asks solely for another bot/agent.
- An ask is handled when a roster member posts a substantive reply, applies a check/approved
  reaction, or approves a linked Apollo GitHub PR when authenticated access is available.
- Use parent-message time for daily-new filtering. Preserve full section counts while obeying
  the invoking skill's rendering cap.

## Operational Rules

- Jira, PagerDuty, and GitHub reads are read-only. Send exactly the messages required by the
  invoking skill; do not edit, react, reply, or post elsewhere.
- Never expose credentials. Never imply delivery succeeded if a send fails.
- Keep source-coverage, configuration-resolution, and Pantheon-thread-lookup failures in run
  logs. They are not recipient-visible digest content.
