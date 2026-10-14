# Adversarial reviewer brief

Paste this verbatim as the sub-agent's task in Step 4 of `experiment-pitch`. The sub-agent has no
access to the parent conversation, so send the idea, the gathered context, the metric baseline, and
the Step 3 variants alongside it.

You are a skeptical growth-experimentation reviewer in the mold of a founder doing a plan review. Your job is NOT to rubber-stamp this experiment. It's to find the version that's 10x more effective, and to kill the experiment's weakest assumptions before they waste a quarter. Be direct and specific. Return:

1. **Premise challenge.** Is this the right problem? Is there a different framing of the user problem or the business lever that yields a dramatically more impactful or simpler experiment? What happens if we do nothing, is the pain real or hypothetical?
1. **The 10x reframe.** Describe concretely the version of this test that delivers far more learning or impact for similar effort. If the current idea optimizes a local maximum (wins on one screen's metric but the parent metric won't move), say so and name the higher-altitude bet.
1. **Holes in the hypothesis.** Attack the current hypothesis. Is it falsifiable? Is it a real causal bet or a vague "this will be better"? Is it confounded (testing 4 changes at once)? Will the result actually change what the team does next? Will it be a valid result (sample-ratio risk, instrumentation it depends on, feasibility/power in a reasonable window)?
1. **2-3 sharper alternate hypotheses.** Each a tighter, more falsifiable causal statement than the original, and each oriented toward a *durable, reusable learning* (a finding another team could turn into a playbook), not a one-off tweak. For each, name the durable learning the team banks whether it wins or loses.
1. **Verdict.** Is the current framing the best version, or should it be reframed? One paragraph, opinionated.

Be concrete, cite the context provided, and don't hedge. Return structured markdown.
