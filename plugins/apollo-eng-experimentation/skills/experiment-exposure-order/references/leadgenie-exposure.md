# Exposure Plumbing In LeadGenie

How the generic checks in `SKILL.md` land in this codebase. Verified September
2026\. Re-check line numbers before quoting them in a review.

## Client

`assets/common/hooks/useExperimentExposure.ts` returns
`{ variant, exposeExperiment }`.

- `exposeExperiment` is `async`, returns `Promise<boolean>`, POSTs to
  `/experiments/expose`.
- It catches internally, so it never rejects. Awaiting it is safe and cannot
  break the calling flow.
- It short-circuits for god mode, test and e2e runs, an empty variant, and any
  user already `exposed` / `exposing` / `failed`. So awaiting it costs nothing
  on the repeat path, which removes the usual argument against check 1.

Experiment names live in `assets/types/experiments.ts`.

## Server, And Which Leg Stamps The Event

`packs/experiments/lib/experimentation/experiments.rb`

- `build_exposure_event` sets `event_type: '$exposure'`, `user_id`, and
  `event_properties: { flag_key:, variant: }`. **It sets no `time` key.** That
  is the concrete form the two-clock trap takes here: Amplitude stamps the
  exposure when the request lands, while a browser-side metric event carries
  its own `Date.now()`.
- `make_amplitude_exposure_request` posts to Amplitude with a blocking
  `Net::HTTP` call inside the Rails request. The client promise therefore
  resolves after Amplitude has answered, which is what makes awaiting it worth
  anything at all. Best effort, not a guarantee.
- Exposure is deduped per user for one week. Within that window only a repeat
  action can be counted, so an ordering bug in the first action costs almost
  the whole population rather than a slice of it.

Stamping `time` server side in `build_exposure_event` would kill this class of
bug at the root. It sits in shared experiment infrastructure owned by another
team, so it is a proposal, not a drive-by edit.

## The Allowlist (Check 6)

`shared/configs/always_tracked_events.yml`. A user on tracking level
`whitelisted` emits only the listed events; level `all` emits everything. A
client metric event missing from this list under-counts for a large slice of
users.

The same file is read from Ruby as `Zenalytics::ALWAYS_TRACKED_EVENTS`
(`packs/iam/lib/zenalytics.rb`), and `.tia/guards.yml` triggers
`packs/iam/spec/lib/zenalytics_spec.rb` whenever the yml changes.

## Reading The Data Back In Amplitude

- The variant surfaces as a user-scope property, `gp:[Experiment] <flag-key>`.
  Segment on that.
- Filtering `$exposure` by `flag_key` is rejected by the MCP validator: only
  `variant` is registered on that event in the tracking plan. Segment on the
  user property instead.
