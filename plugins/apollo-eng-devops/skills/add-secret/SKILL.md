---
name: add-secret
description: Manual-invocation only. Safely plan Google Secret Manager setup and perform approved non-payload changes. Run via /apollo-eng-devops:add-secret.
argument-hint: <Slack URL or secret details> [live]
disable-model-invocation: true
---

# Add Secret

Safely handle an Apollo Google Secret Manager request from a Slack link or supplied
details. Default to an evidence-backed plan. `live` allows the skill to run approved
metadata and IAM mutations, but the operator always adds the payload from their own
terminal so the value never enters model or tool context.

## Usage

```text
/apollo-eng-devops:add-secret <Slack URL or secret details> [live]
```

- Without `live`: run read-only discovery and return an operator-ready plan.
- With `live`: run the same discovery, then ask for confirmation immediately before
  each secret creation or IAM change. Give the operator the version-add command to run
  locally; do not execute it. Never infer or carry `live` from an earlier invocation.

## Hard Safety Boundaries

- Treat the secret payload as write-only. Do not fetch, display, log, summarize, or
  verify it by reading it back.
- Do not open shared-secret links or retrieve a payload through a browser, connector,
  or tool. The user must paste the value into the silent local prompt for the approved
  version-add step; the value never needs to enter model context.
- Never put a secret in command arguments, shell history, exported environment
  variables, files, chat, or tool output. Have the operator use a silent local prompt
  and pipe standard input directly to `gcloud secrets versions add --data-file=-`.
- A request in Slack is not authorization to mutate Google Cloud. Distinguish the
  requester, the intended workload principal, and the authenticated operator.
- Stop on an ambiguous project, secret ID, environment, principal, access requirement,
  or operator authorization. Do not infer production from canary, or vice versa.
- Do not change the active `gcloud` project. Pass `--project` on every command.
- Do not grant project-wide access to make one request work. Prefer existing
  prefix-scoped IAM and Terraform-managed durable access.

## Workflow

### 1. Resolve The Request

For an Apollo Slack URL, use Glean to retrieve the message and replies. Search by the
permalink, channel ID plus timestamp, and distinctive secret name or repository terms
when necessary. Treat Glean as indexed evidence that may lag; say so if the relevant
reply is missing. Do not substitute an ambient browser view or guess from the URL.

Extract and report separately:

- requester identity
- repository or service
- environment (`canary`, `staging`, `production`, or other explicit value)
- exact secret ID
- Google Cloud project
- workload principal that needs read access
- requested role and any follow-up commands
- source links and unresolved fields

If details were supplied directly, preserve their provenance and still resolve missing
fields rather than assuming them. Never treat a secret-share URL as the secret value.

Validate names before interpolating them into commands: a secret ID may contain letters,
digits, hyphens, and underscores; a project ID must use its Google Cloud project-ID
form; and a service-account principal must end in
`.iam.gserviceaccount.com`. Also ensure the environment encoded in the secret ID matches
the intended workload principal. Ask one bounded question when a required field cannot
be resolved safely.

### 2. Establish Operator Context

Run read-only checks and show the result:

```bash
gcloud auth list --filter=status:ACTIVE --format='value(account)'
gcloud config get-value project
gcloud projects describe <project> --format='value(projectId)'
```

The ambient project is evidence only; it is never the target by default. Identify the
authenticated operator independently from the Slack requester. If the current operator
lacks access, return the appropriate authorized operator or team when evidence supports
it; otherwise report that authorization is unresolved.

### 3. Check Existing State And Authorization

Use only metadata and IAM reads:

```bash
gcloud secrets describe <secret-id> --project=<project> \
  --format='yaml(name,createTime,replication,labels)'
gcloud projects get-iam-policy <project> --format=json
```

Only fetch the secret-level policy when the secret exists:

```bash
gcloud secrets get-iam-policy <secret-id> --project=<project> \
  --format=json
```

Distinguish `NOT_FOUND` from `PERMISSION_DENIED`; neither is interchangeable with the
other. A failed describe is evidence that the state is unresolved unless the error
explicitly says the resource was not found.

Also inspect the relevant infrastructure-as-code repository read-only when available.
Search for the project, secret prefix, workload principal, `secretAccessor`, IAM
conditions, and Terraform resources such as `google_project_iam_*` and
`google_secret_manager_secret_iam_*`.

Evaluate IAM conditions, not just role names. Assess whether the operator can create or
version this exact secret and whether the workload already receives access through a
project-level name-prefix condition. Include condition resource type, name, and any time
boundary. Account for group-based grants when membership evidence is available; do not
claim authorization solely because a similarly named user or group has a role. A
prefix-scoped binding such as `resource.name.startsWith(...)` can make a requested
per-secret binding redundant. Treat source configuration plus live IAM as stronger
evidence than a Slack command, but label authorization as unresolved when the available
policy and identity evidence is incomplete.

Never use an access attempt against the secret payload as an authorization probe.
Permission errors and unavailable IAM evidence are blockers, not evidence that access
is absent.

### 4. Classify The Idempotent Action

- **Secret absent:** plan creation, then one version addition. Include IAM only if the
  workload is not already covered by live, durable policy.
- **Secret exists, no new value requested:** do not recreate it or add a version.
- **Secret exists, new value explicitly requested:** plan only a version addition.
- **Workload already covered by prefix-scoped IAM:** omit the redundant per-secret
  binding and cite the matching condition.
- **IAM missing:** prefer a reviewed Terraform change for durable access. Provide a
  one-off `gcloud` binding only when explicitly requested as an urgent exception, scoped
  to the exact secret and principal, with a follow-up to codify it.
- **Authorization insufficient or uncertain:** stop with the exact failed check and the
  operator or owning team needed next. Do not ask for broader permissions by default.

### 5. Present The Plan

Before any mutation, show:

- target project, secret ID, and environment
- requester, authenticated operator, and workload principal
- existing-secret verdict
- operator authorization evidence
- effective workload IAM, including any matching prefix condition
- exact actions that remain, with redundant actions removed
- how the payload will enter through standard input without being exposed

In advisory mode, stop here. Commands are operator-ready instructions, not evidence
that the work is complete.

### 6. Execute Or Hand Off Only With Fresh Confirmation

`live` permits supported execution but is not approval by itself. Ask for explicit
confirmation immediately before each mutation the skill will run, naming the project,
secret, principal when relevant, and exact effect. A confirmation for secret creation
does not approve IAM changes.

For a new secret:

```bash
gcloud secrets create <secret-id> \
  --project=<project> \
  --replication-policy=automatic
```

For the payload, show the following **zsh** command for the operator to run in their own
terminal. Do not start the prompt through an agent shell or ask the operator to paste the
value into chat. The subshell keeps `SECRET_VALUE` local and drops it when the command
finishes or is interrupted:

```zsh
(
  read -rs 'SECRET_VALUE?Secret value: '
  printf '\n'
  printf '%s' "$SECRET_VALUE" | gcloud secrets versions add <secret-id> \
    --project=<project> \
    --data-file=-
)
```

Do not echo the value or enable shell tracing. Ask the operator to paste back only the
non-secret success or error line. If the version-add command fails, stop; do not retry
without a concrete correction and fresh confirmation. If creation succeeded but version
addition did not, leave the empty secret in place and report that partial state; do not
delete it as an automatic rollback.

For an explicitly approved urgent per-secret exception only:

```bash
gcloud secrets add-iam-policy-binding <secret-id> \
  --project=<project> \
  --member='serviceAccount:<service-account>' \
  --role='roles/secretmanager.secretAccessor'
```

### 7. Verify Without Reading The Payload

Verify only metadata, enabled version state, and effective IAM:

```bash
gcloud secrets describe <secret-id> --project=<project> \
  --format='yaml(name,createTime,replication,labels)'
gcloud secrets versions list <secret-id> --project=<project> \
  --filter='state=ENABLED' --format='table(name,state,createTime)'
gcloud secrets get-iam-policy <secret-id> --project=<project> \
  --format=json
```

Do not run `gcloud secrets versions access`. Report which actions completed, which were
skipped as redundant, the non-payload verification evidence, and any Terraform follow-up.

## Output

Keep the handoff concise:

- **Verdict:** ready, already satisfied, or blocked.
- **Resolved target:** project, secret, environment, principal.
- **Identity:** requester and authenticated/authorized operator.
- **Evidence:** existence, authorization, effective IAM, and source links.
- **Plan or result:** proposed actions in advisory mode; confirmed actions and
  non-payload verification in live mode.
- **Next step:** exact missing input, approver, or Terraform change when blocked.
