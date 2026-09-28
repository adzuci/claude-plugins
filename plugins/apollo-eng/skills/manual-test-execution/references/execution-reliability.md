# Execution Reliability

Read this before turning a written scenario into browser actions. These rules are product-agnostic;
apply them to any live web application.

## Prove the intended path

- Reproduce the same identity, role, entry point, persisted configuration, and execution context as
  the scenario or reported defect. A new user with safe defaults is not equivalent to a built-in
  role with legacy state; a direct login is not equivalent to role preview or impersonation.
- Assert every customer-visible boundary that matters. For access control, this commonly means
  navigation visibility, the feature's root route, a specific resource route, and absence of
  protected data—not one redirect alone.
- For systems that separate preview/configuration from queued, scheduled, worker, or webhook
  execution, test both sides. Interactive success does not prove background execution has the same
  user, team, timezone, permission, entitlement, or filter context.
- When a known bug remains open, a faithful regression scenario should fail until the product is
  fixed. A surprise pass requires checking whether the case ran, used the correct fixture and
  persona, reached the same code path, and asserted the final outcome.

## Establish trustworthy test data

- Record the fixture version or checksum, exact rows/IDs, environment, deployed revision, acting
  identity and role, configuration, filters, limits, and relevant feature flags.
- Treat persona labels and setup roles as requirements, not credentials. Do not substitute a
  convenient admin account when the assertion depends on a fresh, denied, billing, integration, or
  cross-tenant persona.
- Treat file contents as inputs, not proof that external records, search indexes, providers, or
  integrations are seeded. Verify required live dependencies before classifying a failure.
- Start independent variants from fresh or explicitly reset artifacts when counts, deduplication,
  ordering, or autorun behavior matter. Remove default/blank rows before asserting exact counts.
- Delete only disposable artifacts created by the run. Never free quota by deleting shared data
  without explicit authorization.

## Assert outcomes, not acceptance

- A successful HTTP response, toast, completed job, or populated JSON cell proves only that stage.
  Verify the persisted record and final downstream effect relevant to the scenario.
- Validate semantic values inside structured output. A provider returning an object does not prove
  a usable email, phone, identity match, or destination write.
- Compare previewed/filter-derived counts with persisted results, while accounting for documented
  pagination, filtering, deduplication, and concurrency behavior.
- When behavior depends on an update/merge policy, record the selected policy before calling a
  changed field a defect.

## Control risk and side effects

- Before a run, determine row count, recipient set, destination, credit/cost impact, and whether the
  action can send messages or modify an external system. Use controlled recipients, inactive or
  task-only destinations, sandbox integrations, and the smallest useful dataset.
- Do not infer permission to send, enroll, bill, toggle team-wide flags, alter plans, delete shared
  resources, or repair external state merely because execution was requested.
- If the UI offers “save without running,” use it when configuration—not execution—is the assertion.
- Restore only settings or fault controls changed for the case.

## Browser and network discipline

- Re-check authentication between cases and after long waits. If the session expired, preserve the
  current evidence, re-authenticate through the approved path, and distinguish session expiry from
  a product failure unless session handling is itself the assertion.
- Save large accessibility snapshots to files and inspect targeted labels/ranges. After any DOM
  change, refresh the snapshot before reusing element references.
- If a click is intercepted or the element detached, dismiss the obstruction or capture a new ref;
  do not repeatedly retry an unchanged stale ref.
- Discover the installed CLI syntax with `--help` when versions differ. In particular, verify how
  video output is specified and confirm the file exists before closing the browser.
- For uploads, click the control that opens the native chooser, confirm the chooser is pending, then
  upload the absolute path. Do not claim evidence was attached until the destination shows it.
- Distinguish client validation from backend failure. A missing required mapping is not evidence of
  an HTTP 500 path.
- A browser route block simulates a client-observed response; it does not reproduce a real
  server-side worker, provider, ingestion, or queue failure. Label mocked and live failures clearly.
- Account for client caching when mocking retries. Confirm the expected request was actually issued
  and intercepted before interpreting the UI.

## Evidence quality

- Capture the state immediately around a failure, then the persisted/final state when those differ.
- Record relevant request, job, run, and destination IDs, but redact passwords, cookies,
  authorization headers, tokens, signed URLs, and sensitive payload fields.
- Separate the functional verdict from evidence delivery. A failed upload does not change Pass or
  Fail, but it leaves evidence status Pending and the run incomplete.
- Classify product bugs only after ruling out missing prerequisites, unsupported environments,
  expired sessions, unavailable integrations, stale builds, and incorrect fixtures.
