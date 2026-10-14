# Entry format

The format every experiment entry in the learnings doc follows. Match it exactly — the doc's value is that a reader can scan 60 entries with the same eye movement, and one off-format entry costs more than it looks like it should.

## Heading

```
### [<Short Name> (GA-<ExpID>)](https://www.notion.so/<page-id-no-dashes>) — <OUTCOME>
```

**Outcome** is one of:

| Status in DB | Outcome in doc |
|---|---|
| `Done : 🚢` | `SHIPPED` |
| `Done : Rollback` | `ROLLBACK` |

Append the estimated annual impact in parentheses when `[Post] Est. Annual Impact -- Rollout Only` has a value:

```
— SHIPPED ($1.83M est. annual)
— SHIPPED ($755K est. annual)
```

Round to two significant figures. Use `$X.XXM` above a million, `$XXXK` below.

Where the outcome needs a qualifier the status can't carry, add it in plain words after the outcome, as the doc already does for GA-314:

```
— ROLLBACK then re-enabled as baseline
```

Link with `https://www.notion.so/<id>` (dashes stripped) to match the ~60 existing entries, not the `app.notion.com` form the SQL query returns.

## Body

Three bullets, in this order, no others:

```
- **What:** <one sentence: what changed, and on which surface>
- **Result:** <the 2–3 numbers that matter, each with p-value or significance>
- **Learning:** <what a different team should take away> **<High|Medium|Low> confidence** (<why that label>)
```

**What** — one sentence. The surface plus the change. A reader who has never seen the experiment should be able to picture the screen.

**Result** — the primary metric first, then at most two supporting numbers that change the interpretation. Include sample size and duration when they bound the read (underpowered, killed early, ran long). Skip every metric that was flat and uninteresting; "all 9 supporting metrics flat" is one clause, not nine bullets.

**Learning** — the mechanism, not the outcome. Then the confidence label, bolded, with a short parenthetical justifying it.

## Confidence labels

These are defined in the doc's header block and mean what a reader should trust, which is not the same thing as the DB's `[Post] Confidence / StatSig` property. That property rates statistical confidence in one result. The doc label rates how much weight another team should put on the *learning*. A stat-sig result from a tiny sample is `Very high : 95%+` in the DB and `Medium` in the doc.

- **High** — stat-sig on a well-powered primary metric, durable signal, ideally replicated.
- **Medium** — directional with strong leading indicators but underpowered on revenue, or stat-sig with a small sample.
- **Low** — underpowered, ambiguous, or weak signal.

A clean, well-powered null is **High confidence**. Knowing something reliably doesn't work is a real finding, and the doc treats it as one.

______________________________________________________________________

## Worked examples

### 1. Shipped win with a real revenue read

```
### [Free Trial — Interactive Trial Indicator (GA-176)](https://www.notion.so/246ab2b3b496809abf3dd8f31a6a4cc1) — SHIPPED ($1.83M est. annual)
- **What:** Persistent UI indicator showing trial status, days left, and value during auto-enrolled Pro trials.
- **Result:** F2P 2.37% → 2.61%, $1.83M annual impact, 90–95% stat-sig.
- **Learning:** The biggest team-validated win in this DB. Trial users need persistent visibility into status + value, not just a banner at signup. Pattern: prominent, persistent, non-dismissible status indicators on time-bound resources. **High confidence** (stat-sig, large impact, replicated mechanism in other wins).
```

Why it works: the learning generalizes past the specific UI into a reusable pattern, and it says which part of the mechanism mattered (persistent, not contextual).

### 2. Clean null

```
### [Bulk Select Feature Gate Animation (GA-471)](https://www.notion.so/341ab2b3b496813eb5c7ce48134f560c) — ROLLBACK
- **What:** Replaced static visual on bulk-select FG with looping UI animation showing the feature in action.
- **Result:** +0.21% relative lift (p=0.79), n=21,272 over 17 days.
- **Learning:** Animation alone doesn't move conversion. Reinforces visual-only treatment pattern. **High confidence** (clean null, decent sample).
```

Why it works: three lines, high confidence on a *null*, and it explicitly ties into an existing pattern instead of standing alone.

### 3. Thin evidence

When the tracker page has no usable results section, collapse to a single bullet and let the gap show. Don't reconstruct a finding from the title.

```
### [Search Limit FG — Alt Copy (GA-274)](https://www.notion.so/2a2ab2b3b4968005bcd1e95e7dba1f5c) — ROLLBACK
- Results section incomplete in tracker. No actionable learning to extract. **Low confidence.**
```

Where it still contributes to a pattern even without numbers, say that much and no more:

```
### [Compare Free vs. Pro — Top 5 Highlights (GA-218)](https://www.notion.so/276ab2b3b49680dfa7eae1bbec0360b4) — ROLLBACK
- Results not fully documented, rolled back. Reinforces "more content on FG hurts" pattern. **Low confidence** standalone.
```

### 4. Invalidated result

An experiment that broke doesn't get a learning about user behavior. It gets a learning about the instrumentation, which is genuinely useful to the next person who touches that surface.

```
### [Finder Empty State Upgrade Prompt Copy (GA-484)](https://www.notion.so/352ab2b3b49681fa895cea14fea112f5) — ROLLBACK
- **What:** New upgrade-prompt copy on the Finder empty state.
- **Result:** Invalid. The CTA rendered during the loading state in treatment but stayed hidden until load completed in control, so exposure wasn't comparable.
- **Learning:** No read on the copy. Loading-state parity between arms has to be verified before launch on any surface that renders progressively. **Low confidence** (test invalid, not a null).
```

Never label an invalidated test as a null. "We learned nothing because the test broke" and "we learned the change does nothing" point at opposite next actions.

______________________________________________________________________

## Quarter sections

Newest quarter first, directly under the TL;DR. Each is a toggle:

```
## FY27Q2 (May 1 – Jul 31, 2026) {toggle="true"}
```

Within a quarter, order entries by ExpID descending (most recent first). Existing quarters roughly follow this, so it's what a returning reader expects.

FY quarters: **Feb–Apr, May–Jul, Aug–Oct, Nov–Jan.** Note that the existing FY27Q1 heading reads `(Feb 3 – Apr 30, 2026)` — it uses the actual first experiment date rather than Feb 1. Either is fine; don't rewrite existing headings to match a new one.
