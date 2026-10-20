# Apollo Devops Repo Conventions

Source: `apolloio/devops` (`AGENT.md`, `.github/workflows/tfc-plan.yml`, `tfc-apply.yml`). Verified via Glean on 2026-10-15.

## Layout

- TFC org: `apolloio`. Workspaces are defined in `terraform/tfc/core/workspaces.tf`.
- Paths under `terraform/gcp/` vary. Examples: `terraform/gcp/data-platform/iam` and `terraform/gcp/prod/mongo-main`. Do not assume `<env>/<workspace>`.
- Some workspaces set no explicit working directory. Use `provider.tf` in the changed dir to find the workspace name.
- Run Terraform from the specific workspace directory, never a shared top-level directory.

## Workspace Naming

PR plans use a derived name: the changed file's directory under `terraform/`, with `/` and `_` replaced by `-`. Example: `terraform/gcp/data-platform/iam/x.tf` becomes `gcp-data-platform-iam`. `tfc.py pr-plans` applies this rule.

## Workflows

- `tfc-plan.yml`: PR plan for changed workspaces.
- `tfc-apply.yml`: post-merge apply run. A human must confirm it in TFC or it auto-discards. A pending run holds the workspace lock.
- These paths get no plan or apply run: any `modules`, `tfc-permissions`, `terraform/gcp/prod/{ops_agent,validation,cf-functions}`, staging mongo paths, `cf-functions`. A "no plan" PR touching them is expected.
- PR plans are speculative, plan-only API runs. TFC hides them from the default workspace run list, so list with `filter[operation]=plan_only`.
- The bot PR comment ("Terraform Cloud Plan Output on <workspace>") is one comment updated by every workspace job. On multi-workspace PRs it can show only one workspace, so do not trust it alone.
- Both workflows build the workspace list from `git diff --name-only` with no delete filter, so removing a directory can queue a plan to destroy everything.

## Policy Checks

Sentinel policies and run tasks exist (network/CIDR safety, NAT IP detection). Enforcement was advisory during rollout and the current level is unconfirmed. Read the run's task results and report them. Do not assume a failure blocks apply.

## Gotchas

- Wrong `working_directory` or a workspace name mismatch between `provider.tf` and `workspaces.tf` targets the wrong workspace.
- Module changes use two PRs: publish the module version first, then update the calling workspace.
- Private modules at `app.terraform.io/apolloio/*` need TFC credentials, so local `init` fails without `terraform login`.
- Stop on replacement (`-/+`) of GKE, Cloud SQL, KMS, or Pub/Sub resources.
- TFC runners cannot reach private Redpanda APIs. Broker users, topics and ACLs are not managed by TFC.
