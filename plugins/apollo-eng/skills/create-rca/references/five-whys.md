# Five-Whys Guidance for Apollo RCAs

Apollo RCAs use three scoped 5-Whys chains: **Detection**, **Mitigation**, and **Prevention**. Each chain is independent — a different causal thread, not a continuation of the previous.

## How to Construct Each Chain

**Derive from incident sources first.** Before consulting example RCAs, extract the causal chain entirely from this incident's Slack threads, Zoom transcript, Jira ticket, and PagerDuty data. Example RCAs calibrate tone and structure; they must never be the source of why-answers.

**Cite at least one artifact per answer.** Every why-answer must link to evidence — a Slack permalink, PagerDuty incident/alert URL, PR or commit link, Sentry issue, or Grafana snapshot. An uncited why is a claim; a cited why is a finding.

**Branch when a why has parallel causes.** When two independent causes both contributed to the same effect, branch explicitly rather than picking one: "Why did X fail? (A) ... and independently (B) ..." The 5 is a guideline, not a quota.

**Stop at an actionable systemic cause.** A good terminal why names a missing process, absent automation, or architectural gap — something that can be fixed. Stopping at "the engineer did X" is stopping too early.

**"Human error" is never the terminal why.** If someone made a mistake, ask why the system made that mistake easy or likely. That is the actionable cause.

**Abbreviate when a metric was healthy by design.** If detection was fast because an alert was deliberately tuned, note it briefly and don't over-expand the chain. Conversely, challenge metrics that looked healthy by luck rather than design — e.g. if detection was fast only because an on-call engineer happened to be in the right Slack channel at the right moment.

## Framing Each Chain

Open each chain with one sentence scoping the thread:

- **Detection**: why we found out when we did (fast or slow), not why the incident occurred.
- **Mitigation**: why recovery took as long as it did, not why the incident occurred.
- **Prevention**: why this class of failure was possible, and what would stop it from recurring.

## Mapping to Action Items

Each terminal why should map to an action item. If a chain branches, each branch terminal is a candidate action item. Action items without a traceable terminal why are proposals, not findings — flag them "(Proposed)" accordingly.

## Health Check

Before handoff, verify:

- Every why-answer cites ≥1 source artifact (Slack permalink, PagerDuty URL, PR, commit, Sentry issue).
- No why-answer copies a cause, phrase, or framing from an example RCA or from this guide's illustrative text — all causal content comes from this incident's sources.
- At least one chain branches where the incident had parallel contributing causes.
- Each terminal why maps to an action item (or is explicitly noted as not actionable).
- No terminal why is "human error" alone — the chain continues to the systemic cause.
