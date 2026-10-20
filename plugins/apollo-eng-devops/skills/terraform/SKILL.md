---
name: terraform
description: Review, apply, unlock, and check the status of Terraform Cloud workspaces from a PR or run URL using the terraform CLI and TFC API.
argument-hint: "<review|apply|unlock|status> <PR number/URL | run URL | workspace>"
disable-model-invocation: true
---

# Terraform

Run as `/apollo-eng-devops:terraform <mode> <target>`.

```text
/apollo-eng-devops:terraform review 1234
/apollo-eng-devops:terraform review https://github.com/apolloio/devops/pull/1234
/apollo-eng-devops:terraform apply https://app.terraform.io/app/apolloio/workspaces/<ws>/runs/run-XXXX
/apollo-eng-devops:terraform unlock <workspace | run URL>
/apollo-eng-devops:terraform status <workspace | run URL>
```

`<PR>` is a PR number or URL in `apolloio/devops` (override with `--repo`). A TFC run or workspace URL works anywhere a target is expected.

## Setup

1. Run `scripts/ensure-terraform.sh` (installs the CLI via tfenv, Homebrew, or a checksummed HashiCorp download; no-op if present).
1. TFC auth: `terraform login` or `TFE_TOKEN`. Never print the token.
1. All TFC calls go through `scripts/tfc.py` (path relative to this skill). It prints compact summaries, never raw plan JSON.

## Safety Rules

- `review` and `status` are read-only.
- `apply` and `unlock` change production state. Show the summary, name the exact run or workspace, and wait for an explicit yes in chat before passing `--yes` to `tfc.py`.
- Never use `force-unlock`, `discard`, or `cancel` without reading `references/locked-runs.md` and offering the safer option first.
- Stop on any plan that deletes or replaces resources, or touches IAM, until the user acknowledges those lines.

## Modes

### review

1. Run `tfc.py pr-plans <PR>`. It maps changed files to workspaces (same naming as devops `tfc-plan.yml`), finds each PR plan run (bot PR comment first, TFC plan-only runs as fallback), and prints compact summaries per workspace.
1. If it reports excluded paths, workspaces with no run, or a stale comment, read `references/apollo-conventions.md`. If a workspace name lookup fails, verify the name in `provider.tf` of the changed dir.
1. Optionally validate locally: `terraform fmt -check -recursive` and `terraform validate` in the changed dir (`init -backend=false` first).
1. Report per workspace: counts, then destroy, replace and IAM lists first, then your verdict. Say if the plan ran against an older commit than the PR head. Use `references/iam-workspaces.md` for IAM workspaces.

### apply

1. Run `tfc.py run <run>`. Proceed only if `status` is `planned`/`cost_estimated`/`policy_checked` and `actions.is-confirmable` is true.
1. If the workspace is locked by a different run, stop and use `unlock` flow.
1. Show `tfc.py plan <run>` and get an explicit yes, then `tfc.py apply <run> --yes`.
1. Re-run `tfc.py status` after, and report the final run status.

### unlock

1. Run `tfc.py status <target>`. Identify the lock holder, its status and age.
1. Pick the least destructive fix from `references/locked-runs.md` (wait, discard a pending run, cancel a stuck run, then `unlock`, last `force-unlock`).
1. Confirm with the user, run it with `--yes`, then re-check status.

### drift

Use `/apollo-eng-devops:resolve-drift [workspace]`. It is the canonical Apollo
drift check: plan-only, attribute-level, and safe for scheduled or interactive use.

### status

Run `tfc.py status <target>` and print its output (lock, current run, link).

## References

Load only when the situation matches:

- `references/locked-runs.md`: locked workspace, stuck or errored runs.
- `references/state-ops.md`: import, `moved` blocks, `state mv/rm`.
- `references/iam-workspaces.md`: IAM-specific review risks.
- [`resolve-drift`](../resolve-drift/SKILL.md): canonical scheduled and interactive drift detection.
- `references/apollo-conventions.md`: Apollo devops repo layout, plan/apply workflows, gotchas.
