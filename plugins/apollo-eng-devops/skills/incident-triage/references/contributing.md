# Contributing to incident-triage

The skill is owned collectively. If it misroutes, mis-dedupes, or proposes a bad comment, the fix is almost always a small change to a reference file. **Please open a PR — don't work around it.**

## Quick checklist for a fix PR

1. **Identify the layer.** Misbehavior usually traces to one file:

   - Wrong class detection (treated a PD alert as a security finding, etc.) → `SKILL.md` ticket-classes table or `pd-alerts.md` / `finding-sources.md` identification rules.
   - Wrong owning team for a finding → `reroute-rules.md` heuristic table or the source-specific extraction in `finding-sources.md` / `pd-alerts.md`.
   - Wrong severity → `cve-triage.md` (CVSS adjustment) or `owasp-ranking.md` (bucket severity floors).
   - Wrong dedup decision → `duplicate-heuristics.md`.
   - Bad proposed-comment wording → `comment-templates.md`. (Templates are the easiest contribution — just edit the block.)
   - Misresolves a team after a rename → `team-lookup.md` rename fallback, but the *real* fix is usually updating `apollo-dev-teams.yml` and/or the affected repo's CODEOWNERS.

1. **Cite an example.** Include 1–3 INCIDENT/SEC keys (or PD URLs) where the new rule helps and the old rule fails. The whole skill is grounded in the real queue — references without examples tend to bit-rot.

1. **Keep it short.** A new heuristic is one row in a table plus an example line, not a new section. If you find yourself writing a multi-paragraph rationale, split it into a separate Notion doc and link to it.

1. **Validate before pushing.** From the repo root:

   ```bash
   mdformat plugins/apollo-eng-devops/skills/incident-triage/
   claude plugin validate .
   ```

   CI runs both, plus a `skill-name-check` that enforces directory == frontmatter `name`.

1. **Run `/apollo-eng:pr-description`** before opening the PR (per CLAUDE.md).

## What to send vs what to ship as a PR

- **Send a Slack message** to the skill owners (currently DevOps + Security) for: a one-off bad routing decision, a request for a new ticket class, or "the skill said X about my ticket — is that right?" If the answer is "no, file a fix," promote it to a PR.
- **Ship a PR** for: a wrong heuristic that will keep firing, a new source label that needs handling, a new alert pattern in the PD queue, a wording change to a template, or a Notion link rot.
- **File an INFRA ticket** for: missing or broken upstream data — outdated `apollo-dev-teams.yml`, stale CODEOWNERS in a high-volume repo, missing Notion runbook the skill cites. These are upstream-data fixes, not skill fixes.

## Security-team-specific contributions

The CVE/finding side benefits from Security-team input the most. If you triage findings as part of your role and notice the skill is wrong about:

- **CVSS context-adjustment** (e.g. a new "low-impact path" pattern the skill should recognize) → add a row to `cve-triage.md`.
- **A new finding source** (e.g. Snyk, GitHub Advanced Security) → add a new entry to `finding-sources.md` and a row to `reroute-rules.md`.
- **A team-rename or split** that the rename fallback didn't catch cleanly → the fix is usually upstream (`apollo-dev-teams.yml`) but a small note in `team-lookup.md` about the specific case can prevent repeats.
- **Bugcrowd / claude-security findings being miscategorized as automated** → check the source-label sniff order in `SKILL.md` (manual review should always outrank automation).

## Eng-team-specific contributions

Engineering teams can help most with:

- **Service-group tag mappings.** When `[Engagement]` doesn't reliably mean your team, or your team owns a service that isn't tagged consistently — add it to the `pd-alerts.md` mapping table with the canonical tag.
- **Alert tuning patterns.** If a PD alert flaps repeatedly and the skill should recognize the pattern as tuning-candidate vs real, capture it in `pd-alerts.md` and a comment template.
- **New customer-report shapes.** Support/GTM reports follow patterns the skill can learn — if you spot a common shape, add it to the symptom-triage section in `SKILL.md`.

When in doubt, open the PR and ask for review — small contributions are better than no contributions.
