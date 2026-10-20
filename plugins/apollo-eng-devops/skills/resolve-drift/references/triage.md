# Drift triage (interactive)

Use the JSON output (`--format json --workspaces <ws>`). For each `drift` entry pick ONE path.
Open the run link for details; never paste attribute values that look like secrets.

## 1. Was it intended?

- Look for the change outside Terraform: use `gcloud logging read
  'protoPayload.resourceName:"<resource>"' --limit=50 --format=json` in the owning GCP project,
  then check Cloudflare **Audit Logs** and Slack/Jira for a hotfix around that time. Read-only
  queries only.
- IAM, firewall, DNS or WAF drift with no known author: **stop**, treat it as a possible security
  incident, and page Security (`incident-response`).

## 2. Pick a fix

| Path | When | Action |
| --- | --- | --- |
| Codify | Intended, should stay (hotfix, console change) | Edit HCL in `apolloio/devops` `terraform/<path>` to match live; open a PR; plan must show no changes for that resource |
| Revert | Unintended | PR not needed if config is right: the next normal apply reverts it. Flag it for the workspace owner; human approves the apply |
| Ignore | Field is managed outside TF by design (autoscaler sizes, labels set by controllers) | PR adding `lifecycle { ignore_changes = [<attr>] }` with a comment saying who manages it |

Common GKE noise: node pool `version` (auto-upgrade) and `node_count`/`autoscaling` (autoscaler) are usually **Ignore** in the shared module, not reverts.

A resource with action `delete` was deleted outside Terraform. Ask the owner before recreating it.

## 3. Hand-off

Print one line per resource: `address · path · owner (if known) · next step`. Draft the PR
only if the user asks; never apply.

`pending` without drift means config merged but not applied. Point at the workspace's
latest non-applied run; it's not drift.
