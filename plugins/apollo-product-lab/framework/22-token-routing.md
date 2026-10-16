# 22 — Worker-model routing for I/O-heavy reads

> A cost technique borrowed from the wider field, evaluated against our evidence rules.
> **Verdict: adopt selectively. We have every piece but one, and the exclusion boundary is the whole design.**

## 1. The technique

Two `PreToolUse` hooks intercept file or artifact reads above a size threshold. Intercepted reads are routed to a cheap worker model, which reads the corpus and returns a structured digest. **The corpus never enters the expensive model's context.**

Reported savings elsewhere are around 90% *on bulk reads specifically* — not on total usage. Measured on a small number of scenarios in one repository. Treat as directional.

The framing that makes it click: most of what a coding agent does is not thinking, it is I/O.

## 2. The genuinely new idea

**A `PreToolUse` hook can substitute, not just block.**

We have used hooks purely as the enforcement layer — deny, gate, `exit 2`. The same primitive works as a *router*: intercept the call, do the work somewhere cheap, return something different. Same hook point, different job, and it costs zero context because hooks consume none.

That reframing is worth more than the headline number.

## 3. Where it breaks our design

**Our findings require verbatim quotes from both sides.** The two-quote rule (Stage A), the citation rule (Stage B), source tiering (external knowledge) and evidence-or-drop (adversarial review) are all the same mechanism: a claim without a quotable source is deleted.

A digest is exactly the thing [15-degradation-and-roi](./15-degradation-and-roi.md) §1 names as how this class of system produces confident wrong output — **summarisation drift.** Each hop compresses, and what is lost is not detail but the *source*. Routing a read through a summarizer inserts a summarisation hop at precisely the point our evidence comes from.

So: **we cannot route the contradiction-detection read.** A finding built on a digest has second-hand quotes, and second-hand quotes are the failure mode the whole design is arranged against.

Two other limits reported in the source and worth carrying: reasoning does not delegate (the worker model found surface patterns and missed a subtle concurrency bug), and each delegation is a 10–30 second round-trip, which makes it uneconomical for small reads.

## 4. The version that works: route the search, read the citation

| Work | Route it? | Why |
|---|---|---|
| Stage A deterministic phases — schema, freshness, coverage, self-consistency | **Yes** | Structural checks. No quotes in the output |
| Stage A Phase 4 — pairwise contradiction detection | **No** | The output *is* verbatim quotes with locations |
| Stage B precedent search | **Yes** | Orientation only; the specialist re-reads what it finds |
| Stage B codebase reality | **Partly** | Route the survey; read the file before citing `file:line` |
| Stage B external acquisition | **Yes** | Already tiered with URLs, and a URL survives a digest |
| Adversarial review of a diff | **No** | Findings need `{claim, location, evidence}` |
| Oversized artifact read for orientation | **Yes** | See §5 |

**The rule: a worker model may tell you *where* to look. It may not be the source of what you quote.**

## 5. A case already encountered

Building this framework required reading a 66,313-character document. It exceeded context and was handled by hand — delegating to a sub-agent with instructions to slice it and return a bounded digest.

That is this pattern, implemented manually, once, badly. A `check-artifact-size` hook would have done it automatically and cheaper, and every audit run against a large PRD or a 30-item constraint register hits the same wall.

That is the strongest argument for adopting it: not a projected saving, but a problem already met and solved worse.

## 6. We have every piece but one

| Needed | Have it? |
|---|---|
| Interception point | **Yes.** `PreToolUse` hooks, already the gate layer |
| A cheap worker model reachable server-side | **Yes.** The dapi LLM gateway fronts ten providers including `vertexai_v2` |
| A documented need | **Yes.** ~78k tokens per artifact pair; a 10-pair run projects to ~780k |
| The routing hook | **No.** The only missing piece |

Small build, not a platform project.

## 7. Decisions recorded

**Vendor approval — decided 2026-09-07, by the framework author (EM, Warm Outbound).**

Gemini is already in production use in the conversations product, so no new vendor approval is required for worker-model routing. Recorded rather than argued so it is traceable: the AI Policy's clause about "a new use case for an existing vendor" was considered and judged not to apply here, on the basis that the vendor relationship and data path are established.

**Consequence:** this technique is **not** blocked on M2, unlike cross-family adversarial review. It can proceed independently, which makes it the cheaper of the two to start.

**Digest anchors — decided 2026-09-07.**

Digests need not preserve structural anchors (section headings, item IDs) if dropping them saves cost without hurting quality.

Recorded with one caveat, because the clause matters: anchors are what make a *follow-up* read cheap and targeted. Without them, either the follow-up does not happen (quality cost) or the whole artifact gets re-read (cost returns). So the default is no anchors, and the first real run measures both against accepted-findings-per-100k-tokens. If anchor-less digests hold up, the question is closed.

## 8. Three corrections after reviewing an existing implementation

An open-source proxy that does provider diversion was evaluated and **rejected** — it routes by model id at the inference layer with no tool-level visibility, so *"a proxy that routes whole turns can never protect a single quote-bearing read inside a turn."* Its other half duplicates our internal gateway, meaning adoption would add a redundant hop. But three things came out of the review that change this design.

### 8.1 Express the exclusion declaratively, not as a hook predicate

My original plan put the routing decision inside the hook, opt-in per phase. **Better: bind the model in the agent definition.**

Claude Code already supports a `model:` field in sub-agent frontmatter. So "this phase uses the cheap model" becomes a declarative binding, and — the part that matters — **the exclusion becomes "this phase's agent is bound to the expensive model."**

That is auditable in a way a hook predicate is not. It is greppable, diffable, and visible to anyone reading the agent file. A hook predicate is behaviour nobody reads, which is the same objection that moved the Authority Policy out of hook code and into a data file.

### 8.2 Never route a full turn — only a discrete call

**The most important finding, and it would have cost us money silently.**

Routing Claude Code to a non-Anthropic model strips `defer_loading` markers and tool-search entries, because other hosts reject them. Tools then arrive **eagerly with full schemas**, so tool search reclaims no context. And on the translation path, each revealed tool invalidates the cached tools prefix.

Given internally reported prompt-cache hit rates of 90–96%, **routing a full agent turn off Anthropic can cost more than the model you routed away from.** The saving is real for a single bounded digest call; it inverts for a turn.

**Rule: worker-model routing applies to a discrete digest call with a fixed input and a bounded output. It never applies to an agent turn.** And the cost ledger must record cache-hit rate alongside token count, or this failure is invisible — a rising token count with a falling cache rate looks like a busier run rather than a broken one.

### 8.3 Replace the manual opt-in with a deterministic classifier

Better than per-phase opt-in: **classify the output type and compress only the noise.**

Source-like output — file contents, diffs, anything whose value is its exact text — passes through unchanged. Search results and repetitive tool noise get compressed. `cat`, `git diff`, `git show` and arbitrary scripts are returned verbatim, by rule.

That gives the same guarantee as my exclusion list with **no human decision per read and no model call to make the decision.** It also removes the failure mode where a new phase silently inherits routing, because the classifier keys off output shape rather than off someone remembering to opt out.

**Note what does not transfer:** the same source strips line-number prefixes for a further saving. **Inapplicable to us** — our findings require quotable evidence *with locations*, so line prefixes are load-bearing here in exactly the way they were not there.

## 9. Recommendation

1. **Bind models declaratively** in agent frontmatter (§8.1). Cheapest change, biggest audit gain.
2. **Build the output-type classifier** (§8.3) rather than a per-phase opt-in flag.
3. **Restrict routing to discrete digest calls** (§8.2) and record cache-hit rate in the ledger.
4. **Measure with our metric** — accepted findings per 100k tokens, before and after, on the same document set. Not a borrowed percentage.
5. **Skip the proxy.** Wrong layer for our problem, and redundant with the gateway we already have.

## 9. Open questions

| # | Question | Owner |
|---|---|---|
| Q-T1 | What size threshold? Code and documents differ — a 3,000-word PRD may be worth reading whole while a 30-item register is worth routing. Needs a measured answer | author |
| Q-T3 | Latency of 10–30s per delegation is probably free in Stage A (already minutes per edge) but real at an interactive gate. Where does it actually hurt? | author |
| Q-T4 | Is there a usable open-source routing implementation to read rather than reinvent? | author + AI Tooling |
