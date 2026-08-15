---
name: image-review
description: Manual-invocation only. Review Docker/OCI image size and layer efficiency with dive. Run via /apollo-eng-devops:image-review.
argument-hint: "<Dockerfile-path-or-image-ref>"
disable-model-invocation: true
---

# Image Review

Review a Docker/OCI image for size and layer-efficiency waste using
[`dive`](https://github.com/wagoodman/dive), propose only evidence-backed Dockerfile
fixes, and verify that an approved fix actually improves the measured metrics before
offering a PR. This is a build-time skill — it does not debug running workloads. For
runtime GKE triage, use
[`kubernetes-specialist`](../kubernetes-specialist/SKILL.md).

## Invocation

```text
/apollo-eng-devops:image-review <Dockerfile-path-or-image-ref>
```

Example:

```text
/apollo-eng-devops:image-review us.gcr.io/indigo-lotus-415/sidekiq:latest
```

## Safety Contract

- Never install `dive`, Docker, or any tool automatically. Detect first; if missing, stop
  and show the official install path — do not run it.
- Never configure registry auth or run `gcloud auth configure-docker` yourself. On a
  private-registry pull failure, tell the operator the exact command to run themselves.
- Never push, tag for a registry, or run any command that could publish an image. Local
  tags only (`image-review-tmp:<slug>-before` / `-after`).
- Never write to a Dockerfile or `.dockerignore` before showing a unified diff and getting
  explicit approval. Approval to edit is not approval to build, commit, or push — each is
  a separate gate.
- Four separate mutation gates, each requiring explicit approval: (1) build or pull, (2)
  write the source diff, (3) rebuild + validate, (4) commit/push/open a PR.
- Read `git status --short` on the target repo before proposing any change. Never overlap
  edits with the operator's existing uncommitted work — stop and ask if the diff would
  touch already-modified lines.
- Clean up only the Docker tags and temp directory this run created. Never remove the
  operator's original image or pre-existing tags.

## Input Resolution

- **Dockerfile path**: confirm build context directory, `--platform`, `--target`, and any
  `--build-arg`/secrets needed before the first build. Reuse identical inputs for the
  before and after build so the comparison is valid.
- **Image reference already local**: show its image ID/digest and ask whether to analyze
  that artifact as-is or refresh (`docker pull`) first.
- **Image reference not local**: get approval before `docker pull`. On failure against a
  private Apollo Artifact Registry path, derive the registry host from the reference and
  tell the operator to run `gcloud auth configure-docker <region>-docker.pkg.dev`
  themselves — do not attempt it.
- **Image with no discoverable source**: inspect `docker history --no-trunc` and OCI
  labels (e.g. `org.opencontainers.image.source`) for a source hint. If none is found,
  give evidence-linked hypotheses only — do not fabricate a diff, and disable the
  apply/rebuild/PR steps until the operator supplies or approves a source checkout.

## Preflight

Detect before touching Docker state:

```bash
command -v docker && docker info
command -v dive && dive --version
command -v jq
```

If `dive` is missing, stop with the exact platform detected and the official install path
(Homebrew `brew install dive` on macOS, the official `.deb`/release binary from
[dive's releases](https://github.com/wagoodman/dive/releases/latest) elsewhere) — do not
install it.

Also resolve the local Docker engine's OS/architecture. Do not assume it matches Apollo's
GKE node architecture. If the deployment platform can't be verified from a manifest, image
index, or cluster evidence, label the whole analysis `local-platform-only` in the output.

If the target repo has `.dive-ci`, use it (`dive --ci-config <path>`) and report against
its real thresholds. If it's invalid, stop and report the config error — don't silently
fall back. If none exists, label results against an `upstream-example baseline` using the
default thresholds documented in
[`references/image-review-playbook.md`](references/image-review-playbook.md), and note
that no repo policy exists yet.

## Workflow

Full commands, the slug algorithm, the `.dive-ci` schema, and the anti-pattern → fix
catalog are in
[`references/image-review-playbook.md`](references/image-review-playbook.md). At a high
level:

1. Resolve input and preflight (above); state the exact command plan before running it.
1. Get approval, then build or pull the target as a local-only temp tag.
1. Export dive JSON (`--json`) and run `dive --ci` (existing `.dive-ci` or the fallback
   baseline) for a pass/fail signal — a `FAIL` is a normal result, not an execution error.
1. Report evidence: total size, efficiency score, inefficient bytes, largest layers, and
   top inefficient files — only the fields dive actually exports, correlated best-effort
   to Dockerfile instructions.
1. If nothing material is found, say so explicitly: `Recommendation: no Dockerfile change`. Do not invent a fix to justify the run.
1. Otherwise, propose a diff from the anti-pattern catalog. Show the diff only — do not
   write it.
1. On approval, write the diff, rebuild with identical inputs as `-after`, and run any
   functional validation the target repo has (tests, smoke test, entrypoint/health check).
   A smaller image that fails validation is a regression — reject it even if dive improved.
1. Re-run dive to `-after.json` and `jq`-diff the two reports for the before/after table.
1. Clean up the temp tags and run directory; report exact names if cleanup fails.
1. Only after separate, explicit approval, hand off to the standard PR flow: check
   `gh auth status` (point to `/apollo-eng:gh-setup` if missing/unauthenticated), follow
   the target repo's branch/commit conventions, run `/apollo-eng:pr-description`, show
   the draft, and stop before `gh pr create`.

## Output

Always report in this shape:

```text
Target: <Dockerfile or immutable image ID/digest>
Source: <repo/path/revision, or "unavailable">
Platform: <value and evidence, or local-platform-only>
Policy: <.dive-ci path, or "upstream-example baseline">
Result: <PASS | FAIL | analysis-error>
Metrics: <size, efficiency score, inefficient bytes, user-waste result>
Evidence: <largest layers, top inefficient files>
Recommendation: <no change | source hypotheses | proposed diff>
Validation: <build/test/smoke-check result, or "unverified">
Cleanup: <complete, or exact leftover tags/paths>
Limitations: <explicit gaps — e.g. local-platform-only, no source found>
```

## PR Handoff

Never create a branch, commit, or PR without a separate explicit approval beyond the
source-diff approval. Follow the target repository's own branch and commit conventions.
Always run `/apollo-eng:pr-description` before `gh pr create` and stop for approval on the
draft.

## References

- [`references/image-review-playbook.md`](references/image-review-playbook.md) — exact
  dive/docker/jq commands, slug algorithm, `.dive-ci` schema, before/after comparison, and
  the anti-pattern → fix catalog with evidence requirements
