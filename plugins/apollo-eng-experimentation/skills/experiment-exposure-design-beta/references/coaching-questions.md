# Coaching questions

These get the engineer into the right headspace before any code is read. Pick the few that matter for
this experiment; ask one or two per message; restate what you heard before moving on. Most are drawn
from how Growth Engineering already runs kickoffs. Each has a one-line "why" you can share if asked.

## Always (Step 1)

1. **"Give me the hypothesis in one sentence — if we do X, then Y happens because Z."**
   Why: every exposure and eligibility decision is downstream of this. If it takes a paragraph, the
   experiment probably has two hypotheses in it.
1. **"Walk me through the happy path of a treatment user — what do they see and do, in order, from the
   moment they land on the surface?"**
   Why: this surfaces the surfaces, routes and states you'll need to trace, and it flags "did we think
   about this?" moments early.
1. **"At what exact moment does a treatment user's experience first differ from control — as they'd
   perceive it, not where the code branches?"**
   Why: that moment is the exposure point. Follow-ups: "Is that difference tied to the hypothesis?"
   "Could that moment be off-screen, empty, or still loading?" "Could it happen at more than one moment
   (e.g. renders vs hover)?"
1. **"Who is eligible? For each condition — is that fact known about the team at the moment they're
   assigned, or does it back-populate later?"**
   Why: eligibility must be evaluable identically for every team at assignment time, or the population
   drifts. Data that arrives after onboarding (enrichment, Salesforce-derived size) is a classic trap.
1. **"How many different routes or entry points lead to that moment? Do control and treatment users
   arrive there at the same rate by design?"**
   Why: the most common SRM cause here is one arm being routed to (or away from) the exposure surface.

## Planning (Stage A)

6. **"What is the control experience today on this surface — and has it changed since the design was
   made? Are there user segments (trial vs paid, admin vs member) that already see something different?"**
   Why: unmapped control variants (SafeSearch Overhaul's trial/non-trial split) reshape the experiment.
1. **"Is the goal a KR-driving uplift, or a 'no harm' change we already believe is better?"**
   Why: changes what metrics matter and how confident the read needs to be; affects guardrail breadth.
1. **"What else is running on this surface — other experiments, flags, anyone else's in-flight work?"**
   Why: concurrent conditionals between exposure and render silently block treatment.
1. **"Roughly how many eligible teams hit that moment per week? Has DS sized it?"**
   Why: stacked conditions multiply; Alchemy got 2 exposures on day one. You don't compute this — you
   make sure someone does, before build.
1. **"Where does the eligibility check live today (Amplitude targeting, FE, BE) — and where do you
   think it should?"**
   Why: gets them to choose one place deliberately, with the trade-off (Amplitude is simple but only
   knows properties it's sent; code is precise but invisible to DS unless documented).
1. **"Why do you *not* need a dry run?"**
   Why: inverts the default. The clean answers are "same eligibility and same exposure point as an
   already-validated experiment" or "simple, stable page both arms load identically". Anything with
   routing, multi-condition eligibility, BE+FE checks, or a new exposure moment earns the 48–72h.

## Review (Stage B)

12. **"Show me the control user's path to the exposure call."** (Then treatment's.)
    Why: makes asymmetry visible to them, not just to you.
01. **"What does the user see on screen the instant this call fires?"**
    Why: mount ≠ visible divergence.
01. **"What happens for a team that isn't eligible — what do they see, and does anything fire?"**
    Why: nil-variant handling.
01. **"If this were the dry run, what would the flip to A/B change?"**
    Why: should be "the key and the render". Anything else means the A/A didn't prove the A/B.
01. **"How will you know exposure actually reached Amplitude, not just that the hook ran?"**
    Why: the console log fires before the guards; check the network call and Amplitude's event stream.
01. **"Was the A/A result actually reviewed — exposures balanced, volume close to the estimate,
    guardrails flat — and by whom?"**
    Why: the skill can't see Amplitude results; someone has to have looked.
01. **"Has anything shipped on this surface since the A/A went live?"**

## Scope change (Stage C)

17. **"What changed, and what prompted it?"** then **"Does the DS volume estimate still hold?"** and
    **"Is the prior dry run still representative of this population?"**

## Phrasing notes

- Ask, don't quiz. "Help me understand…" beats "Did you consider…".
- When the answer reveals a gap, name the risk in one plain sentence and, if useful, the one real
  example that shows it (catalog). Then ask what they'd like to do — the decision stays theirs.
- If they don't know an answer, that's a finding, not a failure: "Worth confirming with DS/PM before
  we go further — want me to note it as open in the hand-over?"
