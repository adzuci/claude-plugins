---
name: experiment-exposure-order
description: Check that an experiment records exposure before the metric event it is meant to explain, for both arms and on every path. Activates on natural language while writing or reviewing experiment code, including a diff that calls an exposure helper, a new variant branch, or a new metric event on an experiment surface.
---

# Experiment Exposure Order

Exposure must precede the measured event.

Scope: this skill checks **ordering** — that the exposure is recorded before the
metric event it explains. If the question is *where* exposure should fire, *who*
reaches it, or whether the eligibility/targeting design is right, that is
`/apollo-eng-experimentation:experiment-exposure-design-beta`. The
two complement each other: it owns placement; this owns the race. (Its "expose at
the first visible divergence" and this skill's "start the exposure at the
eligibility point" are not in conflict — one picks *which user moment counts*,
the other says *when to initiate the call* inside that flow so the round trip
overlaps the action.)

This skill is natural-language activated on purpose, unlike the other skills in this
plugin. The bug it catches is silent, is introduced while writing ordinary feature code,
and nobody thinks to run a slash command for it. See "Why This One Auto-Activates".

## The Invariant

An experiment only counts a metric event that happens **after** the user's exposure event.
Exposure recorded late means the analysis silently drops the action that made the user
eligible, and the read looks flat even when the treatment worked. Nothing fails, nothing
logs, no test goes red. Only reading the code catches it.

The trap is that the two events are usually stamped by different clocks. A client-side
metric event is stamped in the browser at call time. An exposure that travels to a backend
before reaching the analytics provider is stamped when it arrives there. Firing both from
one handler therefore puts the metric event first every time. It is not a race, it is the
default outcome, and it survives every retry and every fast network.

Whenever the two events take different routes, source order in the handler tells you
nothing about recorded order. Check the routes, not the lines.

## Checklist

Run all six. Each is a separate way to lose the read.

1. **Ordering.** A metric event that can fire in the same user action as the exposure must
   wait for the exposure to be recorded. Starting the exposure earlier is not enough: two
   independent round trips finish in either order.
1. **Both arms.** Exposure fires on the same condition for control and treatment. An
   exposure inside a variant branch, or behind anything only the treatment renders, makes
   control unmeasurable and the comparison invalid.
1. **Eligibility, not outcome.** The gate is what makes the user eligible, and it must be
   known before the action starts. Gating on the action's result drops exposures on the
   error path and biases the denominator.
1. **No user-visible delay.** Only the metric call waits on the exposure. The rendered
   feedback and the caller's callbacks stay off the await path.
1. **Other call sites of the same event.** Grep the metric event name. For each other
   place it fires: either that surface needs exposure too, or the treatment cannot change
   behaviour there. Say which. Size the second case as a share of total event volume when
   you can reach the analytics provider, and say it is unsized when you cannot. If you find
   a path where the event never fires at all, stop and read "A Gap In A Live Event".
1. **Event reaches the provider at all.** A metric event dropped by a tracking allowlist,
   a sampling rule, or a consent gate under-counts before ordering even matters.

## A Gap In A Live Event

Check 5 turns up paths where the metric event simply never fires, and the missing path is
often the one the treatment changes most. Flag it. Do not close it here.

Closing it means either widening what the existing event covers or adding a second event
next to it. Both are out of scope for an ordering fix:

- The event already has history and already sits on dashboards nobody asked you about.
  Changing what it counts steps its volume, and the step lands inside the experiment
  window, where it cannot be told apart from the treatment effect.
- A new event name is a taxonomy decision with an allowlist entry, a dashboard and an
  owner. It needs a ticket and a person, not a line in this diff.

Report it instead, in three lines:

1. Who the gap drops, as a share of the measured population when you can size it.
1. Whether it biases the comparison or only dilutes it. Identical on both arms is
   dilution, and the experiment still reads, just weaker.
1. That it needs its own ticket, and what shipping without it costs the current read.

Then finish the ordering fix and leave the gap out of the diff.

Adding the metric event to a tracking allowlist (check 6) is not this. That changes
delivery, not meaning, and belongs in the same change.

## Red Flags To Grep For

- An exposure call and a metric call in the same function with no `await` between them.
- An exposure promise discarded (`void`, a bare call, a floating `.then`) ahead of a
  metric call.
- An exposure call placed after the `await` of the action it is meant to explain.
- An exposure call inside a variant branch.
- A new metric event on an experiment surface with no allowlist entry.

## Shape Of The Fix

Start the exposure at the eligibility point so its round trip overlaps the action, then
await it only in front of the metric call.

**Bad:**

```ts
const result = await performAction();
showResult(result);
recordExposure();
trackActionCompleted();
```

**Good:**

```ts
// Start the exposure the moment the user is eligible, so its round trip
// overlaps the action instead of queueing behind it.
const exposure = isEligible ? recordExposure() : undefined;

const result = await performAction();
showResult(result);   // does not wait on the exposure
onComplete?.(result); // does not wait on the exposure

// The metric event, and only the metric event, waits for the exposure.
void (async () => {
  await exposure;
  trackActionCompleted();
})();
```

Pulling those last four lines into a named helper is fine, as long as the `await` stays
directly in front of the metric call. A helper that takes the metric call as a callback
and awaits somewhere else reads as fire and forget at the call site, which is the shape
this check exists to catch.

`isEligible` must be readable from state the client already holds, otherwise the exposure
cannot start early and there is nothing to overlap.

## Proving It

A test that only asserts "both were called" passes on the broken order. The test has to
hold the exposure response open, assert the metric call has **not** fired, then release it
and assert the metric call lands. Add a second test for the error path, so a later
refactor cannot quietly move the exposure back behind the action's result.

Run the mutation check: put the plain metric call back and confirm exactly those tests go
red.

## Reporting A Finding

State what the business loses, not what the code does. "Experiment reads flat even if the
change works" beats "exposure fires after the event". Name the affected experiment and,
where the fix is already known, the one-line shape of it.

## LeadGenie Specifics

Where the exposure is built, which leg stamps it, and what the allowlist is called:
`references/leadgenie-exposure.md`.

## Why This One Auto-Activates

The other three skills in this plugin are lifecycle steps with an obvious moment to run
them, so they set `disable-model-invocation: true`. This one is a correctness check on
code an engineer is already writing, and the failure it prevents produces no error, no
failing test, and no alert. An engineer who knew to invoke it would not have written the
bug. The routing-context cost is one short description, paid only by engineers who
installed an experimentation plugin.
