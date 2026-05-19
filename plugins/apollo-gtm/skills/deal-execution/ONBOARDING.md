# Onboarding + Help — Apollo GTM System

This file serves two purposes:

1. **First-run walkthrough** — guided experience for new AEs after preflight passes
2. **Help system** — always-available reference invoked by "help," "how do I...," or any system question

---

## First-Run Walkthrough

Run this when `onboarding_complete` is not set in the config block (first time setup). After preflight passes and configuration is confirmed, walk the AE through the system.

**Returning user check:** If the AE has previously completed Steps 1-2 in a prior session (detectable from conversation history or session context), skip to Step 3. Do not repeat the Welcome message or sample triage. If uncertain whether they completed Step 2, present an abbreviated re-entry:

> "Welcome back. Last time we started the walkthrough — want to pick up where we left off, or skip to the action menu?"

If they choose to skip → set `onboarding_complete: true`, present the ROUTER.md action menu, done.

### Step 1: Welcome

Present this to the AE:

> **Welcome to your Sales OS.**
>
> This system connects to your email, calendar, and Slack. It does three things:
>
> 1. **Inbox triage** — reads your unread email twice a day, drafts replies for sales threads, and delivers a prioritized summary to your Slack DM.
> 2. **Email processing** — when you paste a sales email thread, it figures out the right move and drafts a response grounded in what the buyer actually said.
> 3. **Call follow-up** — after a call, paste the transcript or your notes and get a follow-up email tied to what was discussed.
>
> **What it will never do:**
> - Send an email. It creates drafts. You review and send.
> - Mark emails as read. Your inbox stays exactly as it was.
> - Post to a shared Slack channel without asking you first.
> - Make up information. Every claim in a draft traces to something real.
>
> **Everything runs through a reasoning pipeline** that validates claims, maps constraints, and eliminates unsafe actions before composing any message. If the system can't produce a safe output, it escalates to you with an explanation instead of guessing.

Then present:

```
Question: "Ready to try it out?"
Header: "Onboarding"
Options:
  - Label: "Yes, let's go"
    Description: "Run a quick triage on your recent inbox to see how it works."
  - Label: "Skip to action menu"
    Description: "I'll figure it out as I go. Just show me what I can do."
```

If "Skip to action menu" → set `onboarding_complete: true`, present the ROUTER.md action menu, done.

If "Yes, let's go" → continue to Step 2.

### Step 2: Try a Triage (Interactive)

Run a narrow-window triage to show the system in action. Use `newer_than:3h` instead of the full triage window. Before each phase, explain what's happening in plain language:

**Before Phase 1:**
> "I'm checking your inbox, calendar, and Slack for context. This is how I build the full picture before making any decisions."

**Before Phase 2:**
> "Now I'm classifying each thread. Sales threads go through the sales engine. Everything else goes through the general pipeline."

**Before Phase 3:**
> "Processing each thread now. For sales threads, I'm analyzing the deal context, selecting the right action, and drafting a reply. For everything else, I'm figuring out what kind of response is needed."

**Before Phase 4:**
> "Building your summary. Every claim in this summary has been verified against the source material."

After the summary is delivered, explain the tiers:

> **How to read your triage summary:**
>
> - **ACT** — needs your attention now. Escalations, blocks, and high-priority items.
> - **WATCH** — drafts ready for your review, threads to monitor. "[Draft ready]" means there's a Gmail draft waiting for you.
> - **FYI** — informational only. No action needed.
>
> When you see "[Draft ready]," open Gmail and check your drafts. Review the draft, edit if needed, then send. The system always creates drafts, never sends.

### Step 3: Try Processing a Thread (Interactive)

```
Question: "Want to try processing a single email thread?"
Header: "Onboarding"
Options:
  - Label: "Yes, I'll paste one"
    Description: "Paste a sales email thread and see how the system analyzes it and drafts a reply."
  - Label: "Skip this step"
    Description: "I've seen enough. Show me the action menu."
```

If "Yes, I'll paste one":
- Prompt: "Paste a sales email thread below."
- Run GEN-SE on it.
- After processing, explain the result in plain language:

> **What just happened:**
>
> 1. **Ingested** the thread — identified who said what and in what order.
> 2. **Extracted** deal state — stage, buyer intent, open questions, commitments, risks.
> 3. **Classified** the deal stage as [X] and the buyer's intent as [Y].
> 4. **Selected** [Action name] because [reason]. Other options were [eliminated because...].
> 5. **Drafted** a reply using Apollo's value framework. Every claim traces to something in the thread or your product context.
> 6. **Validated** all claims — stripped anything that couldn't be sourced.
>
> The draft is in your Gmail. Review it, adjust to your voice, and send when ready.

### Step 4: Help System Introduction

**Note:** If the user asks for help during an active walkthrough step (e.g., while the sample triage is running or while they're pasting a thread), answer the help question and then return to the active step rather than presenting the action menu. The action menu is only presented after completing or skipping the walkthrough.

> **Anytime you need help, just ask.**
>
> Try things like:
> - "Help" — system overview and action menu
> - "How does triage work?" — explanation of the triage flow
> - "What does ACT mean?" — triage tier definitions
> - "How do I review a deal?" — deal review workflow
> - "What won't this system do?" — safety rules
>
> You can also say "run preflight" to reconfigure connections or "check setup" to verify everything is working.

### Step 5: Launch

Set `onboarding_complete: true` in the config.

Present the ROUTER.md action menu:

```
Question: "What would you like to do?"
Header: "Action"
Options:
  - Label: "Run inbox triage"
    Description: "Process your unread email, check calendar and Slack context, draft replies, and deliver a summary to your Slack DM."
  - Label: "Process an email thread"
    Description: "Paste a sales email thread and get a drafted reply grounded in the deal context."
  - Label: "Write a call follow-up"
    Description: "Paste a call transcript or notes and get a follow-up email tied to what was discussed."
  - Label: "Review a deal"
    Description: "Name a deal and get stage validation, MEDDPICC gap analysis, and recommended next actions."
```

---

## Help System

When the AE asks for help at any point during a session, match their question to the closest topic below and respond. After responding, present the action menu.

### System Overview
**Triggers:** "help," "what is this," "what can you do," "what does this do"

This is your sales operating system. It connects to your email, calendar, and Slack and helps you in three ways: inbox triage (twice-daily prioritized summary with drafted replies), email processing (paste a thread, get a drafted reply), and call follow-up (paste notes, get a follow-up email). It never sends emails, marks things as read, or makes up information. Everything goes through a reasoning pipeline that validates claims before composing any message.

### Triage
**Triggers:** "how does triage work," "explain triage," "what's the summary," "what does ACT mean," "triage tiers"

Triage reads your inbox, checks your calendar and Slack for context, classifies each thread, and processes it. Sales threads get a drafted reply. Everything else gets categorized. Results land in a Slack DM with three tiers: **ACT** (needs your attention now), **WATCH** (drafts ready, threads to monitor), **FYI** (informational only). AM triage covers overnight email. PM triage covers the day and includes "tomorrow's first 3" — your highest-priority items for the morning.

### Email Processing
**Triggers:** "how do I process an email," "paste a thread," "how does GEN-SE work," "email reply"

Say "process an email thread" or just paste the thread directly. The system analyzes the deal context (stage, buyer intent, open questions, risks), selects the right action (answer, escalate, gather info, propose meeting, etc.), and drafts a reply. The draft goes to Gmail. You review, edit if needed, and send. Every claim in the draft traces to something in the thread or your product context — nothing is invented.

### Call Follow-Up
**Triggers:** "how do I write a follow-up," "call follow-up," "post-call," "transcript"

Say "write a call follow-up" and paste your transcript, notes, or recording summary. The system extracts the pain, next steps, MEDDPICC fields, and deal state from what was discussed, then composes a follow-up email tied to specific moments in the conversation. Every assertion in the email traces back to something said on the call.

### Deal Review
**Triggers:** "how do I review a deal," "MEDDPICC," "deal stage," "pipeline review"

Say "review a deal" and name the deal. The system checks the deal against Apollo's three frameworks: Command of the Message (are you communicating value effectively?), Sales Process (are you at the right stage with the right exit criteria met?), and MEDDPICC (is the deal real and where are the gaps?). It will flag missing fields, unvalidated champions, and stage-gating issues.

### Drafts
**Triggers:** "where are my drafts," "how do I review drafts," "Gmail drafts"

Every reply the system creates goes to Gmail as a draft — never sent automatically. Open Gmail, go to Drafts, and you'll find them. Review, edit to match your voice, and send when ready. If a draft doesn't feel right, don't send it. The system would rather you adjust than send something that doesn't sound like you.

### Safety
**Triggers:** "what won't it do," "will it send emails," "is it safe," "safety rules"

The system follows strict safety rules: (1) Never sends emails — drafts only. (2) Never marks emails as read. (3) Never posts to shared Slack channels without asking. (4) Never invents information — every claim must trace to a real source. (5) If it can't produce a safe output, it escalates to you with an explanation instead of guessing. (6) One ask per message — it won't pile up requests on the buyer. (7) No manufactured urgency — if there's no real deadline, it won't create one.

### Pipeline
**Triggers:** "how does the pipeline work," "what's L1," "what's the reasoning," "how does it decide"

Every message goes through a multi-layer reasoning pipeline before it reaches you: (1) **Reality filter** — validates every claim against its source, strips anything ungrounded. (2) **State extraction** — parses who's involved, what's happening, what's known vs unknown. (3) **Constraint mapping** — identifies what limits the possible actions (timing, authority, missing info, risks). (4) **Action routing** — eliminates invalid actions, selects the one right move. (5) **Composition** — writes the message within the constraints. (6) **Humanization** — removes AI patterns, compresses, matches your voice. If any layer fails, the system stops and escalates rather than producing a bad output.

### Understanding Blocks
**Triggers:** "why was this blocked," "what does block mean," "why did the system block," "blocked email," "pipeline failure"

When a thread is blocked, it means the pipeline determined that no safe action could be taken without human judgment. This happens when: (1) a claim in the thread can't be verified, (2) the thread involves legal, financial, or contractual content that requires human review, (3) competing constraints make any automated response risky, or (4) the thread is missing critical context the system can't infer. Blocked threads always appear in the **ACT** tier of your triage summary. Review the block reason, decide how to respond yourself, and act directly. Blocks are a safety feature — they prevent the system from guessing.

### Settings
**Triggers:** "change settings," "update config," "change my email," "change Slack ID," "customize," "can I customize," "change triage," "adjust volume"

Your settings are stored locally at `~/Documents/apollo-gtm/config.yaml` and persist across sessions. You never need to re-enter them.

**Identity settings** (email, domains, Slack ID, timezone): Say "run preflight" to re-detect or override.

**Triage preferences** (how much email to scan, filtering mode): Say "change triage settings" or "adjust my triage." You can change:
- **Triage mode:** "Scan everything" (all threads), "Sales-focused" (full pipeline for prospects/customers, quick scan for the rest), or "B2B only" (skip internal and automated email)
- **Thread limit:** How many threads per triage run (5-50, default 25)
- **Time window:** How far back to scan (4-24 hours)
- **Priority ordering:** When thread limit is hit, what to keep first (most recent, Apollo contacts, or starred)

The triage summary format (ACT/WATCH/FYI tiers) is not customizable — it's designed around a validated prioritization model. If you need something not covered here, describe what you're trying to do and the system will advise.

### Setup
**Triggers:** "reconfigure," "new connector," "setup," "preflight," "run preflight"

Say "run preflight" to re-verify connections and reconfigure settings. This re-checks Gmail, Calendar, and Slack connections, re-detects your email and Slack ID, and runs a smoke test.

---

## Maintenance Notes

**Action menu sync:** The action menu presented in Steps 1/5 of the walkthrough and in the help responses is replicated from ROUTER.md. Keep these in sync when modifying either file. If a new path is added to ROUTER.md, add a corresponding option to the action menu here.
