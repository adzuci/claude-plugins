# Execution gate: the six items

The gate from Execution into Impact. Passing it means the experiment is ready
to start its ramp. Each item is a thing that should exist and work before the
experiment starts collecting the data a decision will rest on. The "What this
means" and "Complete when" text under each item is read to the DRI as written,
so it stays the same from run to run; "More, if asked" is held back for a
dig-in or a question.

## Artifacts for this gate

This gate is more definitive than Discovery. Discovery checks that thinking was
written down, so documents and the DRI's word are the evidence. Execution
checks that things exist and work, so the skill looks at them directly before
proposing a status: the code, the Amplitude experiment, and what has landed in
Amplitude. The DRI still decides; the proposal just starts from what was
verified rather than what was read.

**Required.**

- **The Experiments DB entry** (the DB entry from here on), in the Growth &
  Acquisition Experiments DB
  (`https://app.notion.com/p/apolloio/1a6ab2b3b496804dad43d766beb7be29`). Read
  it as it is; templates change and teams fill them differently.
- **The Amplitude experiment**, reached through the DB entry's Amplitude link
  or the flag key. Read the **production** project's experiment (project
  `241072`), not the staging one (`168367`); teams often create both from the
  same key, and only production decides what users get. If the DB entry links
  the staging config, say so and resolve the production one by key. Through
  the Amplitude MCP, read its state, rollout,
  variants, targeting, bucketing, deployments, metrics, and whether the events
  the experiment needs exist and have recent volume. Without the Amplitude
  MCP, say so: every "landing" and "configured" claim then rests on what the
  DRI pastes, and the status says so.
- **The code**, in a leadgenie checkout with the experiment's branch or PR, or
  merged on master. The experiment's registry entry, variant reads, exposure
  call, and analytics calls are confirmed here. Without a checkout, ask for
  the PR links and read them through GitHub; without either, the code items
  are "couldn't verify".

**For context, in whatever form the team keeps them:** the analytics audit
from Discovery, the exposure design or review, the A/A results if one was run,
the dashboard, the bug bash or QA notes, the deployment or rollout plan, and
the team's work items. Follow the DB entry's links first, then the links on
the Amplitude experiment itself (it usually carries the Jira ticket, the ERD,
and the design). When a work-item link is available and a tool can read it,
read it; do not propose a status for item 1 without having looked.

**Preflight for this gate**, beyond the skill's defaults: the Amplitude MCP
(`get_amplitude_context` returns the org) and the leadgenie checkout
(`assets/types/experiments.ts` exists, or ask for the path). Check both before
the first item; mention only what is missing.

**DB entry content this stage depends on.** Only the Amplitude experiment link
(or the flag key), since that is how this gate verifies anything. Do not
re-check Discovery content here.

**Verdict note.** When an A/A or early live data shows exposures well below the
weekly volume the runtime was sized on, add to the verdict line that the
runtime will stretch and the team should decide now whether to wait or
reshape. The call is the PM's.

## 1. Implementation complete and tested

**What this means.** The build is finished, someone other than its author
has used it in both control and treatment, no P0 or P1 bugs are open, and the
people who need to sign off have.

**More, if asked.** "Finished" means everything the team planned to ship is
done or deliberately left out; a half-built treatment tests something nobody
designed. QA has to cover control too, because a bug that hits only one
variant shows up in the results as a behavior difference. Sign-offs, usually
developers, PM, design, and whoever owns the data, mean nobody learns about
the launch after the fact.

**If no or unsure, ask.**

- Is any planned work still open? If so, is it deferred on purpose or just
  not done?
- Did a bug bash or QA pass happen, and did it cover both control and
  treatment? Did someone other than the author walk through the documented
  test scenarios, with a test user who is actually in the target audience?
- Are any P0 or P1 bugs still open?
- Has everyone who needs to sign off done so?

**Complete when:** planned work is finished or deliberately deferred, a bug
bash or QA pass covered both control and treatment, no P0 or P1 is open, and
sign-offs are in (the DRI's word is enough).

**What can help.** The team's bug bash doc or QA notes; the open items for
the experiment wherever the team tracks its work; QE or whoever runs the bug
bash, if the team has them.

## 2. Tracking verified

**What this means.** The code sends the events the experiment needs, and
the events behind your primary, secondary, and guardrail metrics fire under
the same conditions for both control and treatment.

**More, if asked.** The events the experiment needs are the ones your metrics
are read from, the ones that will explain the result, and anything new the
treatment does. The same-conditions check is easy to miss: if the treatment
hides a button, changes a route, or moves a click target that one of those
events depends on, the metric counts control and treatment differently and
the result looks real when it is an artifact of the tracking.

**If no or unsure, ask.**

- Is there a written list of the events this experiment needs? Does the code
  match it? If there is no list, what do your metrics need, and does the code
  send that?
- Does anything the treatment changes, a click area, a route, a hidden
  element, sit on the path to an event behind one of your metrics?

**Complete when:** the code sends the events the experiment needs, and the
events behind the primary, secondary, and guardrail metrics are confirmed to
fire the same for both control and treatment.

**What can help.** `/apollo-eng-experimentation:experiment-analytics-audit-beta`
run after build checks the code against the list event by event; whoever owns
analytics for the team, if anyone.

## 3. Exposure verified

**What this means.** Exposure is the moment a user starts counting toward
the results. It has to happen at the same point for control and treatment, on
every path that reaches that point, or the comparison is not fair.

**More, if asked.** Exposure should fire for both control and treatment at
the exact moment the experience diverges, with the variant fetched just
before that moment rather than at app load, and a missing variant should fall
through to control rather than an undefined state. If one variant can reach
the exposure point by a route the other cannot, the two populations differ before the treatment has done
anything, and no analysis fixes that afterward. An A/A test is how teams
prove the plumbing: both variants get the identical experience, so any
difference in arrival volume, split, or Amplitude-versus-Snowflake counts is
a setup problem, not a product effect. Skipping the A/A is a judgment call the
team should be able to explain, usually because the exposure logic is reused
from a prior experiment that already proved it.

**If no or unsure, ask.**

- Where in the code does exposure fire, and is that the point the design
  called for?
- Is there any path where control reaches that point and treatment does not, or
  the reverse?
- Was an A/A run? If so, did volume, split, and source agreement come back
  clean? If not, why was it skipped?
- Do assignments and exposures land within about a percent of each other per
  variant? A larger gap usually means exposure fires in the wrong place.

**Complete when:** exposure is confirmed in code to fire at the designed point
for both control and treatment on every path, and if an A/A was run it came
back healthy.

**What can help.** `/apollo-eng-experimentation:experiment-exposure-design-beta`
reviews where exposure fires and who reaches it;
`/apollo-eng-experimentation:experiment-aa-run-verification-beta` checks a
running A/A's volume, split, and source agreement;
`/apollo-eng-experimentation:experiment-exposure-order` checks that exposure
is recorded before the metric events it explains.

## 4. Amplitude experiment configured correctly

**What this means.** The experiment as defined in Amplitude matches the
plan: bucketed at the team level, targeting the sized audience with its
exclusions, with the planned rollout weights, deployments, and metrics
attached.

**More, if asked.** Some of this cannot be fixed once users are assigned.
Bucketing by user instead of team would show teammates different experiences
and corrupt the comparison beyond repair. Targeting that does not match the
sized audience makes the runtime estimate wrong. Missing deployments mean the
flag never reaches the app. Metrics attached with the primary marked make the
analysis read the right thing, and links to the plan and the DB entry keep the
config findable.

**If no or unsure, ask.**

- Is the bucketing unit set to the team (group), not the user?
- Does the targeting match the audience, and are the exclusions in place?
- Are the staging and prod deployments attached, and the metrics with the
  primary flagged?

**Complete when:** bucketing is at the team level, targeting matches the
audience with its exclusions, rollout weights match the plan, deployments and
metrics are attached with the primary flagged, and the links are present. All
read from the production experiment's config.

**What can help.** `/apollo-eng-experimentation:create-amplitude-experiment`
documents Apollo's required settings and the manual steps the API cannot set;
whoever owns experimentation setup for the team, if anyone.

## 5. Monitoring in place

**What this means.** Once live, the team can see how the experiment is
doing without asking anyone, and is told when something goes wrong: a
dashboard that has shown real data, error alerts someone reads, and a check
for an uneven split or stalled exposures.

**More, if asked.** A dashboard that nobody has opened against real data is a
plan, not a monitor, so launch day should not be the first look. Amplitude's
Data Quality card on the experiment flags sample ratio mismatch on its own;
the entry in `config/experiments/<team>.yml` is what routes stale-experiment
alerts to the team's Slack channel. Error alerts
(Sentry, Grafana) need to route to a channel someone actually reads. The
split and stall checks catch the two setup failures that silently ruin
experiments and are invisible in the product itself.

**If no or unsure, ask.**

- Is there a dashboard for this experiment, and has it shown real data?
- Where will errors in this code show up, and who sees them?
- What tells you if the split goes wrong or exposures stop? Is the
  experiment's entry in the team's experiments YAML, so its alerts reach
  your channel?

**Complete when:** a dashboard exists and has shown real data with exposures
per variant and the primary and guardrail metrics, error alerts route to a
channel someone reads, and a split or stall check is in place.

**What can help.** `/apollo-eng-experimentation:experiment-metrics-dashboard`
builds the Amplitude dashboard; the team's Sentry or Grafana setup; the
readout-integrity monitor, if the team has it running; whoever owns analytics
for the team, if anyone.

## 6. Rollout and rollback plan defined

**What this means.** There is a written plan for rolling out the experiment
and, if needed, for turning it off. The rollout plan says how the percentage
will ramp up over time and what checks to make at each stage to confirm it is
looking healthy before the next increase. The rollback plan says what
conditions or scenarios would warrant a rollback and lists the exact steps to
do so.

**More, if asked.** A ramp lets a problem hit a small slice of users first:
start at 5 percent, leave it alone for 24 to 48 hours while watching the
assignment-to-exposure ratio, the guardrails for a sharp early drop, error
monitoring, and Amplitude's Data Quality card, then step up through 10, 25,
and 50; never jump from 5 to 100. Teams with cached assignments from before
launch enter only when their cache expires, so thin data in the first hours
is normal. Rollback conditions are usually a guardrail moving the wrong way,
error alerts past a threshold, or regressions reported by support; writing
them down beforehand means nobody argues about them at 5pm on launch day.
Flat early results, a slightly negative secondary, or a primary that has not
moved yet are not reasons to stop; a significant guardrail breach or a bug
means consult PM and DS; a large, clear hit to a key guardrail means stop
now and debrief after. Rollback steps
should include anything beyond turning the flag off, such as clearing a cache.
Launch-day rules are the usual ones: no Friday launches, on-call knows, the
launch is announced wherever the team announces things.

**If no or unsure, ask.**

- What is the ramp schedule, and what has to look healthy before each step?
- What would make you roll back during the ramp?
- If you had to roll back this afternoon, what are the steps?

**Complete when:** a ramp schedule exists and rollback conditions and steps are
written down.

**What can help.** The team's deployment plan template, if it has one; whoever
owns releases for the team; the on-call engineer for launch day.
