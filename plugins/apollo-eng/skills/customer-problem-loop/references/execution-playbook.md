# Execution playbook

Read this reference before starting stage 2. Section numbers match the stages in `SKILL.md`. Apply
only the sections relevant to the approved delivery scope.

## 2. Locate the customer and inspect through godmode

- Resolve email to user and team through the admin
  `mongo_doc?modality=user&id=<email>` flow. The Team ID Lookup page maps emails to godmode links.
- If the lookup returns no match or multiple plausible users, stop and ask the invoker to clarify.
- Use `https://<preview-or-staging-host>/?godemail=<url-encoded-email>#/<route>` only after the
  impersonation gate. URL-encode the email (`+`, `&`, and other reserved characters change the
  parsed query) and confirm the resolved team after opening the session. The session must belong
  to a real Apollo employee whose team passes `team.apollo?`.
- Flags evaluate against the impersonated team. The flag drawer's "Targeted Teams" control can add
  the current team, so verify the exact staged target id instead of trusting the label.
- Keep the session read-only. Never spend credits or mutate customer data while godmoded.
- If the customer is absent from the staging copy, use a representative staging team and disclose it.

## 3. Implement a flag-gated change and open the PR

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

## 4. Verify the preview environment

- Derive the host using the current repository convention, commonly
  `app-<branch>.preview.staging-gcp.apollo.io`.
- Poll for a 2xx and inspect the actual deploy job with `gh run view --json jobs`. A green image-build
  job is not evidence that the frontend deployed.
- Before writing the flag in the next stage, identify the deploy run that owns the environment and
  confirm the host is serving that run's revision (its commit SHA), not a stale or unrelated one.
  Block the flag write if the serving revision cannot be confirmed.
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

## 5. Change the preview or staging flag

- Immediately before writing, repeat the environment, staged team id, flag name, current value, new
  value, and rollback to the user. Continue only after approval.
- The API shape is `PUT /api/v1/feature_flags/<flag>` with
  `{team_ids:[<team>], disabled_team_ids:[]}`, the CSRF cookie, and `credentials: include`.
- `fast_load: true` flags are immediate, but the SPA still needs a hard reload. Other flags can have
  an in-memory TTL of about a minute per pod; wait and hard-reload before declaring failure.
- Do not toggle a shared flag off and back on while someone else is testing. Set the approved target
  state explicitly and restore the recorded prior state when the run ends.

## 6. Capture evidence

- Reuse the existing Chrome and Playwright runtime. Pantheon already includes Chrome, Playwright,
  and Xvfb; do not require browser extensions or propose a new capture worker without fresh evidence.
- Three screenshots are the deliverable. Do not record video, parse frames, or transcribe a session
  unless the invoker asked for it.
- Hand screenshots off by file path. Confirm each file exists and is non-empty; do not read the
  image back to confirm the capture worked, the DOM assertion below is the check.
- Apollo authentication cookies may be scoped to `.apollo.io`. Verify authentication on the actual
  preview host and request an interactive login only if that check fails; do not assume every
  subdomain requires a new login.
- Capture three real states:
  - **Before:** the approved preview/staging target with the flag genuinely off.
  - **After:** the flag on after a hard reload, with the new element asserted in the DOM.
  - **Interaction:** the new control activated and its resulting picker, modal, or state visible.
- Do not remove elements from the DOM to manufacture a before screenshot.
- Surface visibility is not verification: after/interaction captures must enter the feature and
  confirm its data-bearing API calls succeed (no 403s in the network log), not just that a nav
  item or button appeared.
- Stage states by flipping the real server-side flag/feature/permission through supported admin
  flows; frontend-only network interception cannot exercise backend gates and can produce
  convincing screenshots of a broken feature. This is limited to the flag stage 5 already
  approved — do not flip any additional flag or permission during capture without going back
  through that gate.
- Treat an unexplained redirect or bounce during capture as a bug signal to investigate.
- Use data that demonstrates the feature. Do not seed or mutate customer data; use approved staging
  fixtures or disclose that representative data was unavailable.

## 7. Assemble the Notion 1-pager

Use this structure: Status; Problem; Current state; Solution; Plain-English behavior; captioned
Before/After; Mechanism; Edge cases and risks; Success metric; Ownership and rollout; Open questions;
and `How this was built`.

- Open with the feature, affected user, and customer problem. Keep process jargon out of the intro.
- Put process narration in `How this was built` at the bottom.
- State exactly what changes and what remains unchanged.
- Size demand with more than one anecdote when evidence exists; otherwise label the evidence gap.
- Name permissions, sync effects, performance, race, deduplication, and loop risks when relevant.
- Add dated updates when implementation or review resolves an open question.
- Link the approved godmode URL only in an access-controlled internal page.
- Create the page under the parent confirmed at intake. If none was confirmed, stop and ask before
  publishing rather than guessing a destination.

If connector-native Notion tools are unavailable and the write was approved, the REST sequence is:

1. Send the `Notion-Version` header on every request.
1. Create a page with `POST /v1/pages` using `parent.page_id` and `children`; the title goes under
   `properties.title`, not at the request's top level.
1. For each screenshot: create the upload with `POST /v1/file_uploads` (send its filename and MIME
   type), send the file content to the returned upload URL, then add an image block whose type is
   `file_upload` referencing the returned upload id — only once its status is `uploaded`.
1. Insert after a block by patching that block's parent. For a top-level block, patch the page.

If any step fails, stop further writes and report the partial state and page URL so the user can
decide whether to repair or remove it.

## 8. Prepare the Amplitude experiment

- Use the approved `create-amplitude-experiment` flow. Stop before enabling the experiment.
- Bucket by `gp:account_id` so a team receives one variant. Exclude the Apollo team.
- Use 90% confidence and Bonferroni off unless the experiment owner specifies otherwise.

## 9. Hand off human decisions

Report the PR and preview revisions, checks, screenshots, 1-pager, experiment status, rollback, and
unverified assumptions. List experiment enablement, PR merge, and customer contact as separate
pending decisions.

- Name anything a cap cut short. A run that hit one reports its partial artifact set and stops; it
  does not queue a retry.
