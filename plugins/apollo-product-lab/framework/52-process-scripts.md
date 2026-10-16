# 52: Process scripts

These scripts turn common review catches into repeatable checks. They are advisory. They do not install
hooks, push branches or merge PRs.

| Script | Run it when | Exit 1 means |
|---|---|---|
| `scripts/preview-status.py --pr N` | Before a UI PR is called ready | The current head is not deployed successfully |
| `scripts/ci-doctor.py --pr N` | Before reporting CI status | A check is failing or still running |
| `scripts/stack-sync.py --tip BRANCH` | Before reviewing a stacked PR | A branch conflicts with its base |
| `scripts/verify-claims.py REPORT.md` | Before sending a status report to a human | A completion claim has no evidence beside it |

All four accept `--json`. Exit 0 means the check passed, 1 means a person or agent must act, and 2 means
the script could not decide. Every problem includes one `Next:` line.

`stack-sync.py` prints bottom-up merge commands. `--apply` runs those local merges and stops at the first
conflict. It checks ancestry before printing push commands, but never pushes.

`ci-doctor.py` reads failure patterns from `framework/references/ci-patterns.yml`. Add a known flake there
only after the team has evidence that it is a flake. It fetches each failed job's own log so another job
in the same workflow cannot change its diagnosis.

`preview-status.py` limits the previous successful deployment to the PR's branch and the current preview
run's exact workflow. `verify-claims.py` splits sentences on `.`, `!`, `?`, `;` and newlines before it
checks completed claims. Negative status and planned work are not completion claims.
