# Execution Playbook

Read this reference before stage 2. Section numbers match the stages in `SKILL.md`. Apply
only the sections relevant to the approved delivery scope.

## 2. Locate the Customer and Inspect Through Godmode

- Resolve email to user and team through the admin
  `mongo_doc?modality=user&id=<email>` flow. The Team ID Lookup page maps emails to godmode links.
- If the lookup returns no match or multiple plausible users, stop and ask the invoker to clarify.
- Build `https://<preview-or-staging-host>/?godemail=<email>#/<route>` with a standard URL builder
  that percent-encodes the email value, and open it only after the impersonation gate. Keep the raw
  URL inside the approved, access-controlled lookup/browser flow. The session must belong to a real
  Apollo employee whose team passes `team.apollo?`.
- Flags evaluate against the impersonated team. The flag drawer's "Targeted Teams" control can add
  the current team, so verify the exact staged target id instead of trusting the label.
- Keep the session read-only. Never spend credits or mutate customer data while godmoded.
- If the customer is absent from the staging copy, use a representative staging team and disclose it.

## 3. Implement a Flag-Gated Change and Open the PR

- Enter this stage only after the problem, approach, and human plan checkpoints in
  [checkpoint-flow.md](checkpoint-flow.md) pass. Bind the selected approach and approved scope to the
  attempt. A material implementation departure returns to the human plan checkpoint.

- Confirm the working directory per
  [references/pre-push-checks.md](pre-push-checks.md) before running any repository command.

- Preserve today's behavior when the flag is off. Scope the flag to the minimum team/user surface.

- Reuse shipped primitives where possible, but call out confusing or unreviewed UI choices.

- Read the repository PR template and fill every required section.

- Add `Need_Preview_Env` using the repository's current PR workflow. Without it, the workflow can be
  green while the preview deploy is skipped.

Implementation traps observed in prior runs:

- Treat `null` and `''` separately when deciding whether a field has a value. Use a check such as
  `x != null && x !== ''` when both represent missing data.
- Keep Fabric `Modal` slots as direct children of `<Modal>`. Put per-step conditionals inside each
  slot rather than wrapping all slots in a fragment.
- Aggregate list credit or usage data in one grouped query. Do not issue a query per row.

## 4. Verify the Preview Environment

- Derive the host using the current repository convention, commonly
  `app-<branch>.preview.staging-gcp.apollo.io`.
- Poll for a 2xx and inspect the actual deploy job with `gh run view --json jobs`. A green image-build
  job is not evidence that the frontend deployed.
- Record the reviewed PR-head SHA immediately before verification. Obtain the served revision from
  authoritative deploy metadata for the serving host, such as the completed deploy job's immutable
  revision output or the repository's supported revision endpoint. Require an exact match to the
  reviewed SHA. A 2xx, DNS resolution, preview comment, or green job without this mapping is
  inconclusive; stop before stage 5 rather than mutating a flag against an unknown revision.
- Bound the wait: at most 10 polls with backoff over at most 15 minutes. Narrow each poll to the
  fields you need (`--jq` over `.jobs[].conclusion`) so a retry loop does not re-read whole run
  payloads. On exhaustion, stop and report the last known state rather than polling on.
- If the branch is stale or conflicted, update it from the current base branch using the repository's
  required rebase or merge workflow, then push the new revision.
- Do not toggle `Need_Preview_Env` during an active run; concurrency can cancel the deployment and
  make unrelated checks appear failed.
- If a rails-api pod repeatedly fails its startup probe, a rerun in the same namespace may not help.
  Recreate the preview namespace through the supported label flow or escalate to `#eng-devops`.
- A new PR can trigger both PR-open and label-event workflows. Inspect both runs to find the deploy
  that actually owns the environment.

## 5. Capture Before and Change the Preview or Staging Flag

- Before any write, verify the approved target currently has the flag genuinely off, assert the
  unchanged behavior, capture the before screenshot, and confirm its path exists with non-zero size
  (`test -s <path>` or the platform equivalent). If a shared target is already on, do not toggle it
  merely to manufacture a before state; use an approved isolated staging target or hand off the gap.
- Immediately before writing, repeat the environment, staged team id, flag name, current value, new
  value, and rollback to the user. Continue only after approval. Preserve the before artifact and
  rollback across any repair round.
- The API shape is `PUT /api/v1/feature_flags/<flag>` with
  `{team_ids:[<team>], disabled_team_ids:[]}`, the CSRF cookie, and `credentials: include`.
- `fast_load: true` flags are immediate, but the SPA still needs a hard reload. Other flags can have
  an in-memory TTL of about a minute per pod. Cap propagation at six checks over two minutes, then
  hard-reload before declaring failure.
- Do not toggle a shared flag off and back on while someone else is testing. Set the approved target
  state explicitly. Do not repeat the write during repair when the target already has that state.
  Restore the recorded prior state when the run ends or hand off the exact pending rollback if
  restoration is not authorized or cannot be verified.

## 6. Verify and Capture After Evidence

- Use only the flag state approved and applied in stage 5. Do not flip another flag or permission
  during capture; return to the relevant authorization gate if verification requires one.
- Detect a supported headed Chrome/Playwright runtime and verify it can reach the authenticated
  preview host. Do not assume Pantheon or another worker includes a usable browser, extensions,
  egress, or persistent sessions. If the check fails, hand off the verification gap rather than
  installing a capture worker or claiming evidence.
- Three screenshots are the deliverable. Do not record video, parse frames, or transcribe a session
  unless the invoker asked for it.
- Reuse the valid stage-5 before screenshot. Capture only after and interaction in this stage. Cap
  the stage at five minutes and each browser action or assertion at 30 seconds.
- Hand screenshots off by file path. Confirm each path exists with non-zero size (`test -s <path>` or
  the platform equivalent), but do not read the image back to confirm it; the DOM and network
  assertions below verify behavior.
- Store captures in the runtime-provided durable evidence location bound at intake, then verify the
  returned artifact references remain accessible to the invoker. A non-empty file that exists only
  inside an ephemeral worker is incomplete evidence and must be reported that way in stage 9.
- Apollo authentication cookies may be scoped to `.apollo.io`. Verify authentication on the actual
  preview host and request an interactive login only if that check fails; do not assume every
  subdomain requires a new login.
- Complete three real states:
  - **Before:** the stage-5 artifact from the approved target with the flag genuinely off.
  - **After:** the flag on after a hard reload, with the new element asserted in the DOM.
  - **Interaction:** the new control activated and its resulting picker, modal, or state visible.
- Do not remove elements from the DOM to manufacture a before screenshot.
- Surface visibility is not verification: after/interaction captures must enter the feature and
  confirm its data-bearing API calls succeed (no 403s in the network log), not just that a nav
  item or button appeared.
- Stage states by flipping the real server-side flag/feature/permission through supported admin
  flows; frontend-only network interception cannot exercise backend gates and can produce
  convincing screenshots of a broken feature.
- Treat an unexplained redirect or bounce during capture as a bug signal to investigate.
- Use data that demonstrates the feature. Do not seed or mutate customer data; use approved staging
  fixtures or disclose that representative data was unavailable.
- If an assertion, data-bearing call, or artifact check fails, record the failed check and observed
  evidence. Under the repair contract, update the same PR, prove the new head SHA at stage 4, and
  rerun only the affected checks plus relevant regressions. After two failed repair rounds or when
  browser verification is unavailable, proceed to stage 9 with an explicit partial handoff.

## 7. Assemble the Product Brief

Create the page only under the parent confirmed during intake. If no parent was confirmed, stop and
ask before publishing rather than guessing a destination.

Use only the sections the decision needs: Status; Problem; Current state; Solution; Plain-English
behavior; captioned Before/After; Mechanism; Edge cases and risks; Success metric; Ownership and
rollout; Open questions; and `How this was built`. There is no one-page target: keep a narrow change
short, and use additional length when evidence, mechanisms, risks, or rollout need it.

- Open with the feature, affected user, and customer problem. Keep process jargon out of the intro.
- Put process narration in `How this was built` at the bottom.
- State exactly what changes and what remains unchanged.
- Size demand with more than one anecdote when evidence exists; otherwise label the evidence gap.
- Name permissions, sync effects, performance, race, deduplication, and loop risks when relevant.
- Add dated updates when implementation or review resolves an open question.
- Link the approved godmode URL only in an access-controlled internal page.

If connector-native Notion tools are unavailable and the write was approved, the REST sequence is:

1. Authenticate with the approved integration, resolve and verify `parent.page_id`, and create the
   child with `POST /v1/pages`. Put its title in the child-page `properties.title.title` value, not a
   top-level `title`, and include `children`.
1. Create image uploads with `POST /v1/file_uploads`, upload each file to the returned URL, and add
   an image block whose type is `file_upload`.
1. Insert after a block by patching that block's parent. For a top-level block, patch the page.

If any step fails, stop further writes and report the partial state and page URL so the user can
decide whether to repair or remove it.

Cap an approved publication attempt at three minutes. Prefer connector-native Notion tools. For a
REST fallback, resolve and verify the parent first, use the currently supported `Notion-Version`,
send each filename and MIME type, wait for upload completion, validate the returned file id, attach
that id, and read back the created blocks before claiming publication.

## 8. Prepare the Amplitude Experiment

- Use the approved `create-amplitude-experiment` flow. Stop before enabling the experiment.
- Bucket by `gp:account_id` so a team receives one variant. Exclude the Apollo team.
- Use 90% confidence and Bonferroni off unless the experiment owner specifies otherwise.
- Cap the create request at 30 seconds with no more than five attempts. If availability or final
  disabled state cannot be verified, hand off instead of retrying indefinitely.

## 9. Hand Off Human Decisions

Report the PR and preview revisions, checks, screenshots, product brief, experiment status, rollback, and
unverified assumptions. Include the attempt start/end time, repair count, each failure, the change
made for it, and the checks reverified. List experiment enablement, PR merge, and customer contact
as separate pending decisions.

Include the problem-review, approach-review, human plan, code-quality, solution-quality,
verification, and final-quality statuses defined in
[checkpoint-flow.md](checkpoint-flow.md). Preserve the original verdicts and unresolved
disagreements; do not compress missing evidence into an overall pass.

- Name anything a cap cut short. A run that hit one reports its partial artifact set and stops; it
  does not queue a retry.
