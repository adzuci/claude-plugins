# Output Format

Use this in Step 5. A full run returns the sections below, in order.

## 📊 Metrics Summary

Always lead with a quick stats line:

```text
Total questions: N  |  Pre-existing answers: N  |  Originally unanswered: N
Filled by bot: N  |  Needs review: N  |  Avg confidence score: N/100
```

## 📋 Ticket Summary (3–6 Bullets)

- Ticket key and short description
- Overall answer status (e.g., "18/22 questions answered from approved sources; 4 need SME input")
- Urgent risks (tight deadline, unusual ask, missing context)
- Key sources used

## ✍️ Draft Answers

Full proposed answers in the questionnaire's structure. Include all confidence labels, numeric scores, reasoning notes, and source cues (see `answer-format.md`).

## ❓ Unanswered / Empty Questions

After the draft answers, always produce a **separate, clearly separated section** listing every question that could not be confidently answered:

```text
## ❓ Unanswered Questions — Needs Follow-Up

Q[N]: [Question text]
Status: [Why it's unanswered — e.g., "No source found", "Conflicting info", "Needs SME", "Legal review required"]
Suggested next step: [Who to ask / where to look]
```

This section must always be present. If all questions are answered at High confidence, write: `✅ All questions answered — no open items.`

## 📥 Download Output

After presenting results, always offer two download formats:

- **CSV (with scores)** — columns: Question Number, Question, Status, Answer, Confidence Level, Confidence Score, Source, Reasoning, Needs Review. Ready to paste into ZenGRC / OneTrust / Aravo.
- **HTML report** — polished table with score bars, metrics summary at top, filter tabs (All / Filled / Pre-existing / Needs Review), and an Apollo footer. Good for sharing with AEs or attaching to Jira.

Remind the user they can filter the results by tab (All / Filled / Pre-existing / Needs Review) before downloading.

## Slack-Friendly Output

If the user says output will go to Slack:

- Use bullets and numbered lists throughout
- Avoid wide tables; convert to vertical Q/A format if needed
- Keep the Summary section short and skimmable
- Include key links: Jira ticket, source docs
