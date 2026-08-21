---
name: k8s-safe-exec
description: Manual-invocation only. Safety-gated wrapper for one-off commands against Apollo's GKE stage/prod clusters — advisory by default, opt-in live execution, memory-headroom pod selection, post-run health check. Run via /apollo-eng-devops:k8s-safe-exec.
argument-hint: <stage|prod> [live] [-n <namespace>] [--pod <pod>] [--] <command>
disable-model-invocation: true
---

# K8s Safe Exec

**Invoke directly.** This skill runs real commands against Apollo's staging and production GKE clusters, so it never auto-activates.

Use it as the wrapper around any ad hoc diagnostic command an oncall engineer wants to run in a cluster — especially `kubectl exec` into a live serving pod. It gates **before** the command runs and verifies health **after**. **By default it executes nothing** — it hands you the commands to run. Pass `live` to let it run them itself, still asking before each one. It does not replace `/apollo-eng-devops:kubernetes-specialist`, which is the triage reference for after something breaks. See [`references/related-runbooks.md`](references/related-runbooks.md) for the boundary between this skill, that skill, and the Notion runbook.

**Why this exists**: a one-shot `rails runner` executed inside a live `sidekiq-google-search-linkedin-shared` pod in prod OOM-killed the container. The retry pushed the node over its memory threshold and the pod came back `Evicted`. Prod pods run close to their memory limits, and nothing in the flow forced a preflight, a blast-radius statement, or a post-run check.

## Usage

```text
/apollo-eng-devops:k8s-safe-exec <stage|prod> [live] [-n <namespace>] [--pod <pod>] [--] <command>
```

| Argument | Required | Meaning |
|---|---|---|
| `stage` or `prod` | yes | Target environment. Never inferred, never defaulted. |
| `live` | no | Let the skill execute commands itself. Omitted = advisory, nothing runs. |
| `-n <namespace>` | for anything namespaced | Validated against [`references/namespaces.md`](references/namespaces.md) |
| `--pod <pod>` | optional for `exec` | Target pod. Omit it and the skill picks the one with the most memory headroom. |
| `--` | recommended | Everything after it is the literal command to run |

```text
# advisory — prints a run sheet, executes nothing
/apollo-eng-devops:k8s-safe-exec prod -n leadgenie -- rails runner 'puts Rails.env'

# live — executes, asking yes/no before each command
/apollo-eng-devops:k8s-safe-exec prod live -n leadgenie -- rails runner 'puts Rails.env'
```

## Modes

**Advisory is the default. The skill runs nothing unless `live` is typed.**

| Mode | Invocation | Behavior |
|---|---|---|
| **Advisory** | no `live` | Prints every command in run order — preflight, memory check, the command itself, post-run health check — and states plainly that nothing was executed. |
| **Live** | `live` | Executes commands itself, showing each one and waiting for an explicit yes/no first. |

`live` must be typed by the user. Never infer it, never enable it because the conversation seems to want it, and never carry it over from an earlier invocation. If the user's intent is ambiguous, stay advisory.

### What Live May Execute

| Command class | In live mode | Notes |
|---|---|---|
| Reads — `get`, `describe`, `logs`, `top`, `events` | Runs after a yes | Cheap and reversible; may be grouped into one prompt |
| `preflight.sh`, `memcheck.sh`, `posthealth.sh` | Runs after a yes | Read-only by construction |
| `exec`, `run` | Runs after a yes | One prompt each, never grouped, blast radius stated |
| `delete`, `patch`, `apply`, `scale`, `cordon`, `drain`, `rollout`, `annotate`, `label`, `edit` | **Never** | Printed for the operator to run by hand, even in live mode |
| `cp`, `port-forward` | **Never** | Printed only |

This table is not negotiable by argument. There is no flag that lets this skill run a `delete` or a `patch` — if that is what you need, it prints the command and you run it.

## Workflow

1. Parse args. Reject a missing or unrecognized environment. Note whether `live` was passed.
1. Classify the command and check the table above — decide whether the skill may run it at all.
1. Preflight: run it in live mode, print it in advisory mode. Any non-zero exit stops the flow.
1. Validate the namespace, then confirm it exists.
1. For `exec`/`run`: run `scripts/memcheck.sh` to estimate cost, report available memory, and choose the pod with headroom.
1. Steer to the least risky form (ephemeral pod vs `exec -it`).
1. Show the literal command and ask yes/no. **Advisory stops here** and hands over the run sheet.
1. Live only: run the approved command.
1. Run `scripts/posthealth.sh` — bundled into the same approval as the command it follows.
1. Report — including when nothing went wrong.

## 1. Environment Argument Is Mandatory

Accept exactly `stage` or `prod`. Anything else — including `staging`, `production`, `prd`, `stg`, an empty value, or a bare namespace — is rejected. Do not map fuzzy synonyms silently. This is the same failure `scripts/preflight.sh` reports as exit `2`. Print the usage line and stop:

```text
Usage: /apollo-eng-devops:k8s-safe-exec <stage|prod> [-n <namespace>] [--pod <pod>] [--] <command>
```

Never infer the environment from `kubectl config current-context`, from the namespace, or from earlier turns in the conversation. On the machine this skill was developed against, the ambient current context was already `gke_indigo-lotus-415_us-central1-c_prod` — prod is a plausible default for an Apollo engineer's kubeconfig, which is exactly why the target must be stated explicitly every time.

## 2. Preflight

```bash
plugins/apollo-eng-devops/skills/k8s-safe-exec/scripts/preflight.sh <stage|prod> [-n <namespace>]
```

The script owns these checks — do not re-implement them inline:

- `gcloud version` and `kubectl version --client`; if outdated it prints `gcloud components update` / `gcloud components install kubectl` rather than proceeding silently.
- Resolves the expected context for the environment from `kubectl config get-contexts` (never hardcoded — context names vary per engineer) and compares it to `kubectl config current-context`. A mismatch is a hard stop with the exact `kubectl config use-context <name>` fix.
- Cheap connectivity read (`kubectl get ns`). Failure is a hard stop pointing at VPN: staging VPN for stage, the **separate, restricted** prod VPN for prod.
- Validates `-n <namespace>` against the known table and the allowed dynamic patterns for that environment. The flag is optional — preflight only validates a namespace if you pass one, so pass it whenever the command is namespaced.

| Exit code | Meaning | Action |
|---|---|---|
| `0` | All clear | Continue |
| `1` | Hard stop — context mismatch, connectivity failure, invalid or unknown namespace, missing required tooling | **Stop and report the script's message. Do not attempt the command anyway.** |
| `2` | Usage or argument error — missing/invalid environment arg, bad flags | Stop. Print the usage line and ask for a corrected invocation. Do not guess the intended value. |
| `3` | Warnings only — stale tool version and similar | Report the warnings verbatim and get the operator's acknowledgement before proceeding |

## 3. Namespace Validation

Namespaces are a guard rail, not free text. Check `-n` against [`references/namespaces.md`](references/namespaces.md). Reject anything not in the table or matching an allowed dynamic pattern for that environment.

`preview-*` and `fabric-studio-*` are staging-only. A `preview-*` namespace passed with `prod` means the operator mixed up environments — reject, say so, and ask them to re-run against `stage`.

Dynamic namespaces are allowed by pattern but still must be confirmed to exist before use:

```bash
kubectl --context <ctx> get ns <namespace>
```

Do not enumerate workloads to "help" — prod `leadgenie` alone has over 750 Deployments. Namespace-level validation is the right granularity; pod and deployment existence is resolved live at run time.

## 4. Classify The Command

**Plain reads** — `get`, `describe`, `logs`, `top`, `events`. No blast-radius statement needed and no post-run health check. In live mode they still get a yes/no, but may be grouped into one prompt.

**Everything else** — full gate, and a post-run health check if it touched a real pod. Whether the skill may run it at all is decided by the table in [Modes](#what-live-may-execute), not by the mode alone.

If the command is a shell pipeline or a wrapper that ends up in one of the gated verbs, treat it as gated. Judge the *effective* verb, not the leading word.

## 5. Memory Estimate And Pod Selection

Before any `exec` or `run`, estimate what the command will need, report what is actually available, and target a pod that has the headroom. This is the check that would have caught the incident.

```bash
plugins/apollo-eng-devops/skills/k8s-safe-exec/scripts/memcheck.sh <stage|prod> \
  -n <namespace> (--deploy <deploy> | --pod <pod> | --selector <k=v>) \
  [--estimate <class|size>] [--safety-factor 1.5] [--top 5] [--json]
```

Choose the estimate class from the shape of the command:

| Class | Default | Use for |
|---|---|---|
| `trivial` | 32Mi | shell builtins, `cat`, `env`, `ls`, `ps` |
| `light` | 128Mi | small script, `jq`/`awk` on small input, `redis-cli ping` |
| `rails-boot` | 768Mi | `rails runner` / `rails console` — full app boot, gems, AR schema cache |
| `rails-query` | 1536Mi | rails runner with large result sets, external API calls, JSON parsing |
| `heavy` | 3Gi | bulk backfill, large payload parsing, mass ActiveRecord instantiation |

Override with an explicit size when you know better: `--estimate 900Mi`. The default is
`rails-boot`, since a `rails runner` one-shot is the dominant use case here.

`--json` emits pure JSON on stdout (progress goes to stderr), so the skill can parse the
recommendation directly rather than scraping the table.

**These are heuristics, not measurements.** Report the estimate *as* an estimate — never tell the user a snippet "will use" a number. See [`references/memory-estimation.md`](references/memory-estimation.md) for how the classes were calibrated and how to get a real figure instead of a guess.

### Let The Script Pick The Pod

Do not exec into the first pod in `get pods`. Replicas of the same Deployment are **not** interchangeable — in observed prod Sidekiq deployments they differed by ~283Mi of free memory against a 4Gi limit.

Pass `--deploy` (or `--selector`) and let `memcheck.sh` rank candidates by **effective headroom**, which is `min(pod headroom, node headroom)`. A pod with 2Gi of its own headroom sitting on a node with 200Mi free is not a good target — that node axis is what turned the incident's retry into an eviction rather than another OOMKill.

Report all three numbers: the estimate, the chosen pod's headroom, and its node's headroom.

| Exit | Meaning | Action |
|---|---|---|
| `0` | At least one viable pod | Use the pod it recommends |
| `1` | No viable pod, or a hard failure | **Do not fall back to the least-bad pod.** Switch to the ephemeral-pod path and say why |
| `2` | Usage error | Fix the invocation and re-run |
| `3` | Inconclusive — metrics unavailable | Unknown usage is not zero usage. Say headroom could not be determined and prefer the ephemeral pod |

If the node reports `MemoryPressure=True`, treat it as a hard steer to the ephemeral pod regardless of what the pod-level numbers say.

## 6. Prefer The Least Risky Option

`kubectl exec` runs your process inside the target container, sharing its memory cgroup. Your allocation counts against the pod's limit. An ephemeral pod gets its own cgroup and its own limit, so an OOM kills only the throwaway pod — never a pod serving traffic or draining a Sidekiq queue.

| Use `exec -it` | Use an ephemeral pod |
|---|---|
| Read a file, env var, or config | Anything that boots the full app |
| Tail a process, check a PID | External network or API calls |
| Trivial one-liner with bounded memory | Parsing large payloads |
| Confirm a mount or DNS resolution | Bulk queries or backfills |
| | Any snippet whose allocation you cannot predict |

When in doubt, use the ephemeral pod. Clone the target deployment's pod spec rather than guessing at image, env, or volumes:

```bash
CTX=<context>; NS=<namespace>; DEPLOY=<deployment>
POD="rails-oneoff-${USER}-$(date +%s)"
SNIPPET='puts Rails.env'

IMAGE=$(kubectl --context "$CTX" -n "$NS" get deploy "$DEPLOY" \
  -o jsonpath='{.spec.template.spec.containers[0].image}')

# Clone the real pod spec; override name, command, resources; drop probes.
OVERRIDES=$(kubectl --context "$CTX" -n "$NS" get deploy "$DEPLOY" -o json \
  | jq -c --arg snip "$SNIPPET" '
      .spec.template.spec as $s
      | {spec: ($s
          | .containers = [ ($s.containers[0]
              | .name = "oneoff"
              | .command = ["bundle","exec","rails","runner",$snip]
              | .stdin = true
              | .tty = true
              | .resources = {requests:{cpu:"500m",memory:"2Gi"},
                              limits:{memory:"4Gi"}}
              | del(.args, .livenessProbe, .readinessProbe,
                    .startupProbe, .lifecycle, .ports)) ]
          | .restartPolicy = "Never")}')

kubectl --context "$CTX" -n "$NS" run "$POD" \
  --rm -it --restart=Never --image="$IMAGE" --overrides="$OVERRIDES"
```

Notes on this pattern:

- `--image` is required by `kubectl run` even though `--overrides` replaces the container — pull it from the live deployment so you never guess a tag.
- The overrides carry the deployment's `envFrom`, `env`, `volumes`, `volumeMounts`, and service account because the whole pod spec is cloned. Confirm with `echo "$OVERRIDES" | jq '.spec.containers[0].envFrom'` before running if you need the config to be right.
- Set the one-off's `resources.limits.memory` explicitly. Do not inherit a huge limit from a Sidekiq deployment — the point is that this pod cannot starve the node.
- Cloning the pod spec also clones `nodeSelector`, `affinity`, and `tolerations`, so the one-off can be scheduled onto **the same node pool — possibly the same node — that is already under memory pressure**. The separate cgroup still protects the serving pod from your allocation, but it does not protect the node. If the memory-risk pre-check showed `MemoryPressure=True`, check where the one-off actually landed (`kubectl get pod "$POD" -o jsonpath='{.spec.nodeName}'`) and size its limit against that node's free memory, not just the pod's.
- `initContainers` are cloned too. They will run again before your snippet — usually harmless, but check them if they do migrations, warm caches, or wait on a dependency, and `del(.initContainers)` if they are not needed.
- `--restart=Never` means no restart loop if the snippet crashes. `--rm` deletes the pod when the attached session exits.
- `--rm` does **not** reliably clean up if your client disconnects (VPN drop, laptop sleep). Always verify and clean up:

```bash
kubectl --context "$CTX" -n "$NS" get pod "$POD" 2>/dev/null \
  && kubectl --context "$CTX" -n "$NS" delete pod "$POD" --now
```

## 7. Confirmation Gate

This gate applies in **both** modes. The only difference is what happens after a yes: advisory hands you the command, live runs it.

For every gated command, state four things before asking:

1. The **literal** command that will run, fully expanded — no placeholders.
1. The target: cluster context, namespace, pod or deployment.
1. The blast radius in plain language.
1. The safer alternative, if one exists.

Model the blast radius on the real incident. For an exec into a live pod:

> This execs into a live serving pod and shares its memory cgroup — if the pod is near its memory limit this can OOM-kill the container or, if the node is under pressure, get the pod Evicted.

Then ask, verbatim, and wait:

```text
This is what it will do: <literal command>
Are you sure you want to run this?
```

In live mode, include the mandatory post-run health check in the same prompt, so one yes covers the whole sequence and nothing runs unshown:

```text
This is what it will do:
  1. kubectl --context gke_indigo-lotus-415_us-central1-c_prod -n leadgenie \
       exec -it sidekiq-account-domain-fetcher-6bc9db8cf9-77trd -- \
       bundle exec rails runner 'puts Rails.env'
  2. scripts/posthealth.sh prod -n leadgenie \
       --pod sidekiq-account-domain-fetcher-6bc9db8cf9-77trd --baseline-restarts 0
Are you sure you want to run this?
```

Approval rules:

- A general go-ahead earlier in the conversation does **not** authorize a new or different command. Each distinct command needs its own yes.
- Re-running the exact same approved command is fine.
- Changing the snippet, pod, namespace, deployment, or environment makes it a **new** command requiring a new yes.
- Silence, "sounds good", or "go ahead" aimed at something else is not approval. Ask again.
- Anything that is not a clear yes means **do not run it**. Print the command instead and continue in advisory form for that step.
- Reads may be grouped into a single prompt. `exec` and `run` never are.
- Approval never persists across invocations. A new `/apollo-eng-devops:k8s-safe-exec` call starts with zero standing approval, even for an identical command.
- Passing `live` is **not** itself approval to run anything. It only makes the yes actionable.

## 8. Post-Run Health Check

**Mandatory.** After any `exec` or `run` against a real pod, this runs — in live mode automatically as part of the approved sequence, in advisory mode as the last entry on the run sheet with an explicit instruction to run it. This is the step that was missed during the incident. Never present a command as finished without it.

```bash
plugins/apollo-eng-devops/skills/k8s-safe-exec/scripts/posthealth.sh <stage|prod> \
  -n <namespace> --pod <pod> [--deploy <deploy>] [--since 3m] [--baseline-restarts N]
```

Pass `--baseline-restarts N` with the restart count you observed during the memory-risk pre-check, so a pre-existing restart is not misread as damage you caused.

It rechecks:

- Pod status, restart count, and `Last State` reason
- The owning Deployment/ReplicaSet ready and available replica counts
- Recent `kubectl get events` for that pod, filtered to `Evicted`, `OOMKilled`, `Killing`, `FailedScheduling`, `BackOff`

The script's `== Verdict ==` section ends with a line whose first word is the verdict below. Quote that line verbatim when reporting back, so the operator sees the same term their terminal showed them.

| Verdict | Exit | Triggers | Action |
|---|---|---|---|
| `HEALTHY:` | `0` | Phase nominal, ready, no restart regression, replicas at desired count, no concerning events | Report the clean result explicitly |
| `DEGRADED:` | `1` | Pod phase not `Running`, container `ready=false`, restart-count regression, replica shortfall, or a `Killing`/`FailedScheduling`/`BackOff` event | Hand off to `/apollo-eng-devops:kubernetes-specialist`, and say it is a possible problem, not a confirmed severe incident |
| `INCIDENT:` | `1` | `OOMKilled`, an `Evicted` or `OOMKilled` event, or the pod not being found at all | Hand off to `/apollo-eng-devops:kubernetes-specialist` |
| `INCONCLUSIVE:` | `3` | No confirmed problem, but `--since` reached the ~1h events retention window so "no events" cannot be trusted | Do not report this as healthy. Widen `--since` and re-run, or check the Deployment directly |
| *(none)* | `2` | Usage error — exits before any verdict | Fix the invocation and re-run; an unrun health check is not a pass |

Then:

- **Report the result plainly, including when nothing went wrong.** Never assume success silently.
- On `INCIDENT` or `DEGRADED`, hand off for triage. Do not improvise triage in this skill.
- A "pod not found" result is **a finding, not a clean pass** — after an eviction the pod object may be gone entirely. The script already classifies it as `INCIDENT`; report it as a possible eviction rather than a missing-argument mistake.

For what the two failure modes actually mean and where each one surfaces, read [`references/oom-vs-evicted.md`](references/oom-vs-evicted.md).

## Guardrails

- **Advisory is the default. Never execute anything unless the user typed `live`.**
- Live never runs `delete`, `patch`, `apply`, `scale`, `cordon`, `drain`, `cp`, or `port-forward`. No argument changes that.
- Every command the skill runs in live mode is shown first and needs its own yes.
- An estimate is an estimate. Do not report a heuristic as a measured figure.
- Never exec into a pod chosen for convenience when `memcheck.sh` named a roomier one.
- Preflight exit `1` is final. Do not retry the command, do not work around the check.
- Never set `K8S_SAFE_EXEC_SKIP_CLUSTER=1` in a real run. It exists for the scripts' own tests and does local-only validation.
- Never infer the environment. Never default to prod.
- One approval per distinct command.
- Never run a gated command with an unvalidated namespace.
- Prod is a separate, restricted VPN — if connectivity fails, report it instead of retrying in a loop.
- Do not print secret values from a pod's environment. Names and keys are fine; values are not.

## References

- [`references/oom-vs-evicted.md`](references/oom-vs-evicted.md) — Container OOMKilled vs node-level Evicted, where each surfaces, and the incident walkthrough
- [`references/namespaces.md`](references/namespaces.md) — Verified namespaces per environment, dynamic staging patterns, and how to refresh the table
- [`references/memory-estimation.md`](references/memory-estimation.md) — How the estimate classes were calibrated, why they are heuristics, and how to measure for real
- [`references/related-runbooks.md`](references/related-runbooks.md) — How this skill composes with the Notion runbook and the other DevOps skills
