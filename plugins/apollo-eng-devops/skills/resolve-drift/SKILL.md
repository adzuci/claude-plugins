---
name: resolve-drift
description: "Read-only Terraform drift check for key HCP Terraform workspaces. Scripted plan-only runs, compact Slack report, and interactive codify/revert/ignore triage."
argument-hint: "[workspace[,workspace]] [--headless] [--post-channel <id>] [--timeout 900]"
disable-model-invocation: true
---

# Resolve Drift

Finds drift between live infra and the last **applied** Terraform config. A script queues a
**plan-only** run (cannot apply) per workspace on HCP Terraform (TFC) and prints a short
summary: resource addresses and changed attribute **names**, never values. All TFC work
happens in the script; do not call the TFC API or read plan JSON yourself.

## Usage

```text
/apollo-eng-devops:resolve-drift                    # all key workspaces, report only
/apollo-eng-devops:resolve-drift --headless         # routine / Apollo Operator: report, deliver, stop
/apollo-eng-devops:resolve-drift gcp-prod           # one workspace, then triage
```

Key workspaces live in [`references/workspaces.json`](references/workspaces.json).

## Preflight

| Need | Verify | If missing |
| --- | --- | --- |
| `python3` 3.9+ | `python3 --version` | Stop; say so |
| TFC token with `plan` on the workspaces | `TFE_TOKEN` / `TF_API_TOKEN` set, or `~/.terraform.d/credentials.tfrc.json` exists (check existence only) | Stop. Locally: tell the user to run `terraform login`. Operator: report the missing `TFE_TOKEN` secret |

Never print, echo or read the token value.

## Flow

1. Run `python3 scripts/drift_check.py [--workspaces <list>] --format slack` (paths relative to this skill). It takes 2-15 min; run it in the background if you can, and don't poll.
1. **Headless**: deliver the script's stdout verbatim as ONE message, per [`references/delivery.md`](references/delivery.md). Ask no questions. Stop.
1. **Interactive, no workspace arg**: print the report. Offer triage for each drifted workspace. Stop.
1. **Interactive, workspace given**: rerun with `--format json --workspaces <ws>`, then follow [`references/triage.md`](references/triage.md) for each drifted resource.

## Statuses

| Status | Meaning |
| --- | --- |
| clean | No drift, no pending changes |
| drift | Live infra differs from last applied config (`resource_drift`) |
| pending | No drift, but the plan still has changes (config not fully applied) |
| error | Couldn't check (token, API, timeout). Never report as clean |

## Guardrails

- Read-only. Never apply, confirm, discard-and-reapply, `terraform apply`, `import` or `state` commands. Fixes go in a PR a human reviews.
- Plan-only runs don't lock state or change infra; the script cancels runs that pass `--timeout`.
- Report attribute names only. If you open a run in TFC to see values, don't paste values that look like secrets.

## See also

- [`devops`](../devops/SKILL.md): reliability review for a risky revert.
- [`incident-response`](../incident-response/SKILL.md): drift that looks like an unauthorized change (IAM, firewall, DNS) is a security incident; page Security.
