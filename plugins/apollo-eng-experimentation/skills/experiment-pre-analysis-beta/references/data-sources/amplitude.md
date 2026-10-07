# Amplitude: baselines and exposures for pre-analysis

Amplitude is where experiments are run and where product-event baselines and
exposures live. This covers pulling the numbers a pre-analysis needs and the
platform quirks worth knowing while you plan.

## Where the statistical dials live (and don't)

- **Confidence** is a setting on the experiment (Amplitude's default is **90%**;
  our standard is **95%**, so bump it per experiment — see `../defaults.md`).
  "Confidence" and "significance" are the same dial.
- **Power is NOT a live setting.** Amplitude bakes an assumed power (~80%) into
  its sample-size/duration estimate; you can't drag a power slider on the running
  test. So "running at 90% power" means: compute the larger sample target
  yourself (with `power_calc.py`) and **run until you hit that number**, rather
  than stopping at Amplitude's default-80% duration estimate.
- **Sequential testing:** Amplitude's significance is sequential (built to let
  you peek safely). For pre-analysis this matters when you write the monitoring
  plan — you can pre-commit to safe interim checks instead of a strict
  no-peeking fixed horizon. (Interpreting those interim readings is
  post-analysis, out of scope for this skill.)

## How to pull

Apollo Claude sessions have the Amplitude MCP (enterprise-provisioned; Codex gets
it from this plugin's `.mcp.json`). Projects: **241072 prod**, **168367 staging**
— baselines come from prod. The tools that matter here:

- `search_amp_data_taxonomy` / `get_amp_taxonomy` — resolve real event and
  property names first; never guess them.
- `query_amplitude_data` — build and run the funnel/segmentation query that
  reads the baseline.
- `get_amplitude_charts` + chart read tools — reuse a team's saved chart when one
  exists.
- `use_amp_experiments` / `use_amp_flags` — the experiment's own config
  (variants, targeting, rollout) when sizing against an existing setup.

Exposure anchoring at Apollo: exposures are the `[Experiment] Exposure` event;
segment by the `gp:[Experiment] <key>` user property (the MCP validator rejects
filtering `$exposure` by `flag_key` — only `variant` is registered on that event).
Pre-launch there is no exposure event yet, so the weekly volume comes from a
**proxy**: distinct eligible users hitting an existing event at the planned
exposure surface (this is also what Amplitude's `proxyExposureEvent` wants at
experiment creation).

## Finding the proxy event

- `search_amp_data_taxonomy` (kind `events`) with the surface's words; match on
  the raw `name`, not `display_name`. Hits carry `first_seen` / `last_seen` and
  flag zero-volume events.
- Prefer the event that fires when the eligible user reaches the surface where
  the first visible difference will render, and no earlier. A page-view fires
  before eligibility is known; a success event fires too late and undercounts.
- Check its 30-day volume with `query_amplitude_data` on the eligible segment
  before trusting it. Day-sampled events (Mon/Tue only) and extension-only
  events undercount by design.
- Show the candidates with what each misses; the user picks. Record the pick as
  a proxy, never as the exposure event.

If the MCP is missing, ask the user to read the numbers off a chart and paste
them — don't block.

## Getting baselines

Amplitude's own charts give the cleanest baselines for event-based metrics:

- **Rate metric baseline** — build a conversion/funnel chart on the eligible
  segment over a recent representative window (≥1 week); read the conversion %.
  That's your `--baseline`.
- **Per-user count/continuous** — build a chart of the event count/value **per
  user** (not total) over the window and read the mean; for the standard
  deviation you need user-level data, which charts don't give — pull it from
  `ANALYTICS_DB.ANALYTICS.FCT_AMPLITUDE_EVENTS` in Snowflake (see
  `snowflake.md`). The formulas need per-user σ, not a total.
- **Weekly exposure** — count distinct eligible users hitting the proxy
  event per week. That's your `--weekly-exposure`.

Placeholders: `<exposure_event>`, `<outcome_event>`, `<eligible_segment>`,
window. The Activation team's real event names and segment definitions belong in
`teams/activation/metrics.md`; resolve anything else through the taxonomy tools,
not from memory.

> Scope note: interpreting a test that's already running (reading significance
> mid-flight, deciding whether to stop) is **post-analysis** and out of scope for
> this pre-analysis skill. The sequential-testing note above matters here only so
> the pre-analysis can pre-commit the right monitoring/peeking plan.

## Sanity checks to plan for

- **Sample-ratio mismatch (SRM):** compare observed arm split to the intended
  split; a significant deviation on large n means assignment/logging is broken
  and results are void. Check on day one.
- **Novelty/primacy:** a broad UI change causes a temporary reaction; inspect the
  effect over time and, if needed, read a later stable window.

## Maintenance

- **Event names and segment definitions** are placeholders here; the real ones
  live in the team file or come from the taxonomy tools at run time.
- **Owner:** the apollo-eng-experimentation plugin maintainers
