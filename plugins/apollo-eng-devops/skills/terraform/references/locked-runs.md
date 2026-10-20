# Locked and Stuck Runs

Check before touching anything: `tfc.py status <ws>`. Note the lock holder, run status, and age.

## Decision Order (least destructive first)

1. **Run is active** (`planning`, `applying`): wait. Do not unlock an applying workspace.
1. **Run is `planned` / `cost_estimated` / `policy_checked`, waiting for confirm**: it holds the lock. Either apply it (if wanted) or `tfc.py discard <run> --yes`.
1. **Run is `pending` behind another run**: the queue head holds the lock. Fix or discard the head run first.
1. **Run is stuck in `planning`/`applying` for far longer than normal**: `tfc.py cancel <run> --yes`. If it stays stuck, a TFC admin may need `force-cancel`.
1. **Run is finished but the workspace is still locked**: `tfc.py unlock <ws> --yes`.
1. **Locked by a user or by a run that no longer exists**: `tfc.py force-unlock <ws> --yes`. Last resort in this skill's ordering (Apollo has no documented force-unlock policy). Confirm with the DevOps owner of the workspace when unsure.

## Apollo Pattern

The usual lock is a merged PR's `tfc-apply` run waiting for confirmation. Confirm it if wanted, or discard it, and the lock clears. Hermes workspaces are a special case: a local operation sets Execution Mode to Local and unlocks the workspace (see `terraform/gcp/apollo-hermes/README.md`).

## Risks

- A cancelled apply can leave partial changes and a stale or corrupt state. After cancel, run a plan and compare before applying.
- Force-unlocking while another apply is live can corrupt state. Verify no run is `applying` first.
- Errored runs do not hold the lock, but a policy check failure or `discarded` plan may. Read the run status, do not guess.
- Locks set manually in the UI (`locked-by` is a user, not a run) need the owner's OK when they are not you.

## Run Statuses That Matter

`pending`, `planning`, `planned`, `cost_estimated`, `policy_checked`, `policy_override` (needs override), `confirmed`, `applying`, `applied`, `errored`, `discarded`, `canceled`.
