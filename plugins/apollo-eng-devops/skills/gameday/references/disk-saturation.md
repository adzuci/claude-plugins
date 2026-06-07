# Scenario: Slow-burn disk saturation (the precursor)

- **SEV:** 1 (by the time it pages)
- **Source:** [RCA: email-3 MongoDB Shard Outage](https://www.notion.so/335ab2b3b49681cbb5ffcf2744b37fc1) — the *precursor* lesson, not the trigger.
- **Prevention guardrail:** early disk-throughput alerting at the 10M-doc threshold, not 100M.

This card trains the thing that's hardest to drill: catching the slow burn **before** it
becomes the page. Run it as a "what should have paged us?" exercise.

## Inject (show this first)

```
[FIRING:1] MongoDB disk write throughput at limit [Infra] email-3 (high devops prod-app)
Value: write_MBps=1200/1200 — SATURATED
This is the first page. Customers are already impacted.
```

## Symptom layers (reveal one at a time)

1. **No runway:** the first alert fired only at the *hard limit* — there was no warning at
   70% or 85%. By the time it paged, mitigation options were already narrow.
1. **It was visible for weeks:** disk write throughput had been sitting at **70%+ for two
   weeks**. The metric existed; nobody was alerted on it. Growth was steady, not sudden.
1. **A known grower:** a collection had been climbing toward tens of millions of docs.
   The original alarm threshold was set at 100M — far past the point where action is cheap.

## Red herrings

- "It spiked out of nowhere." (It didn't — the trend was visible for two weeks.)
- "We just need a higher alert threshold." (Higher is later; the fix is *earlier* + trend.)
- "Add disk." (Throughput, not space, is the wall; and it's reactive.)

## Discriminating question

"When did this *start* trending, and why didn't a warning fire at 70%?" The incident is
the missing leading indicator, not the moment of saturation.

## Expected diagnosis path

Page fired only at 100% → metric was available all along → no warning threshold + no
trend alert + alarm set far too late (100M docs vs. the 10M action point).

## Correct mitigation (reversible-first) + rollback

This card's "mitigation" is observability, since the live fix mirrors `unsharded-hotspot`:

1. **In-incident:** throttle the heaviest writer (reversible) to get under the limit.
1. **The real deliverable — alerting:** add a **warning** burn alert at 70–85% of disk
   throughput, a **trend/forecast** alert ("will hit limit in N days"), and a per-collection
   document-count alert at the **10M** action threshold.
1. **Verify:** simulate the trend and confirm the warning fires with days of runway.

**Rollback:** alert tuning is config — revert the rule if it's too noisy, then re-tune.

## Debrief questions

- What's the difference between an alert that pages at the *limit* vs. one that pages with
  *runway*? Which do we have for our Mongo shards today?
- The 10M-doc action threshold beat the 100M alarm. Why is "earlier and cheaper" the rule?
- Which collections are trending toward a limit right now with no warning alert? (Tie this
  back to `mongo-pr-guard` Check 5 — new models with no shard key.)
