---
name: rca-doc-review
description: Review an RCA document from Notion or Google Drive against Apollo's RCA standards. Activate when user asks to review an RCA, check an incident report, or provide feedback on a post-mortem document.
---

# RCA Document Review

Review a Root Cause Analysis document against Apollo's internal RCA standards. Fetches the document from Notion or Google Drive, evaluates completeness and quality, and provides structured feedback.

## Steps

### 1. Accept the Document Link

The user provides a Notion or Google Drive URL to an RCA document.

- **Notion URLs** look like: `https://www.notion.so/apolloio/...` or `https://notion.so/...`
- **Google Drive URLs** look like: `https://docs.google.com/document/d/...`

If no URL is provided, ask the user for one before proceeding.

### 2. Fetch the Document Content

**For Notion URLs:**

Use the Notion MCP `notion-fetch` tool with the URL to retrieve the document content.

```
notion-fetch({ url: "<notion_url>" })
```

**For Google Drive URLs:**

Use the Glean MCP `read_document` tool with the URL to retrieve the document content.

```
read_document({ url: "<google_drive_url>" })
```

**If the MCP tool is unavailable or the fetch fails** (permissions, missing MCP configuration, invalid URL, etc.), ask the user to paste the RCA document content directly as markdown. Once they paste it, continue to Step 3 with the pasted content.

### 3. Identify Required Sections

Before evaluating sections, check whether the document is substantive enough to review. If fewer than 3 of the 10 required sections below contain meaningful content (i.e., most sections are empty, placeholder-only, or contain just a heading with no body), stop the review early. Tell the user: "This RCA is still a stub -- only N/10 sections have content. Please fill in more detail before requesting a review." List the sections that need content and link to the RCA template (Step 6) as a reference. Do not produce a full section-by-section review for a stub document.

If the document has sufficient content, proceed with the section check.

Apollo's RCA template requires these sections. Check whether each is present in the document:

| # | Section | What to look for |
|---|---------|-----------------|
| 1 | **Incident Summary** | Brief description of what happened, when, and high-level impact |
| 2 | **Severity and Impact** | Severity classification (SEV-1 through SEV-4), customer/revenue/data impact quantified |
| 3 | **Affected Components** | Systems, services, infrastructure involved |
| 4 | **Timeline of Events** | Chronological sequence with timestamps (not vague relative times) |
| 5 | **Root Cause Analysis** | Technical root cause, not just symptoms; ideally uses 5 Whys or similar method |
| 6 | **Contributing Factors** | Secondary causes, environmental conditions, process gaps |
| 7 | **Resolution / Mitigation Steps** | What was done to stop the bleeding and restore service |
| 8 | **Action Items with Owners and Due Dates** | Concrete follow-ups assigned to specific people with deadlines |
| 9 | **Lessons Learned** | What the team now knows that it did not before |
| 10 | **Prevention Measures** | Structural changes to prevent recurrence (not just "be more careful") |

**Stub document check:** After scanning for required sections, count how many contain substantive content (more than just a heading or placeholder text). If fewer than 3 of the 10 required sections have real content, stop the review and tell the author:

> This RCA document appears to still be in draft with most sections incomplete. A meaningful review requires at least the Incident Summary, Timeline of Events, and Root Cause Analysis sections to be filled in. Please add more content and re-run the review.

If 3--6 sections have content, proceed with the review but note prominently that the document is incomplete.

### 4. Evaluate Each Section

For every section that exists, assess quality on these dimensions:

**Completeness** -- Is the section filled out or just a placeholder/stub?

**Specificity** -- Does it use concrete details?

- Timelines must have timestamps (e.g., "14:32 UTC"), not vague language ("around noon")
- Impact must be quantified where possible ("~2,000 accounts affected" not "many users")
- Components should name specific services, not generic terms

**Root Cause Depth** -- Apply the **5 Whys check**:

- Does the stated root cause explain *why* the failure happened, not just *what* failed?
- Can you ask "but why did that happen?" and get a deeper answer from the document?
- A good root cause identifies a systemic issue (missing validation, absent monitoring, process gap), not a proximate trigger ("a bad deploy")
- If the root cause stops at the surface level, flag this explicitly

**Action Item Quality** -- Evaluate each action item against SMART criteria:

- **Specific**: Clear deliverable, not vague ("add monitoring for X" not "improve monitoring")
- **Measurable**: Success criteria defined or obvious
- **Assignable**: Named owner (a person, not a team)
- **Relevant**: Directly addresses the root cause or contributing factor
- **Time-bound**: Has a due date, not "when we get to it"

**Factual Grounding** -- Flag anything that appears assumed or fabricated:

- Jira should be the authoritative source for severity, affected components, resolution status
- Slack/Zoom threads should inform the timeline and decision-making process
- If facts appear invented or unsourced, call them out

### 5. Generate the Review

Output the review in this exact structure:

______________________________________________________________________

```
## RCA Review: [Document Title]

### Overall Assessment

**Status: [Ready for Review | Needs Work | Major Gaps]**

[2-3 sentence summary of the RCA's overall quality, biggest strengths, and most critical gaps.]

---

### Section-by-Section Review

For each of the 10 required sections, output:

#### [Section Name]

- **Present**: Yes / No / Partial
- **Quality**: Strong / Adequate / Weak / Missing
- **Feedback**: [Specific, actionable feedback. If weak or missing, explain what needs to be added and give an example of what good looks like.]

---

### 5 Whys Check

[Evaluate whether the root cause analysis goes deep enough. Walk through the chain of causation as presented. Identify where the analysis stops and whether it should go deeper. Provide a suggested 5 Whys chain if the document's is insufficient.]

---

### Action Items Quality

| Action Item | Owner | Due Date | SMART Score | Issue |
|------------|-------|----------|-------------|-------|
| [item] | [name or MISSING] | [date or MISSING] | [X/5] | [what's wrong] |

[Summary of action item quality. Call out any items that lack owners, due dates, or specificity.]

---

### Missing Information

- [Bullet list of information that should be in the RCA but is not]
- [Focus on gaps that would prevent learning from the incident]

---

### Suggested Improvements

1. [Numbered list of concrete, prioritized recommendations]
2. [Each should explain what to change and why it matters]
3. [Include example text where helpful to illustrate the improvement]
```

______________________________________________________________________

### 6. Reference Materials

If the user wants to see example RCAs for tone and depth calibration, point them to:

- [Example RCA 1](https://docs.google.com/document/d/1Cye8xvMJcHQHNCHAbccOO8snEx-y5RMQ0uBDomykgBs)
- [Example RCA 2](https://docs.google.com/document/d/104fVOtL2OYfD-bxSfPNQlB-XhzXM5JrEbzAStSZPgIs)
- [Example RCA 3](https://docs.google.com/document/d/1_weHgzWWPjuxO9T7PJVTAA1ob5W1yTuNTcs7XUQSV0g)

Apollo's official RCA template: [RCA Template](https://docs.google.com/document/d/14YqoGSnPTURHgEASx2Qts_D3nRvkudM5NNgGM4hJdws)

## Tips

- Be direct and specific in feedback -- vague suggestions like "add more detail" are not helpful
- Praise sections that are well-written; do not only focus on gaps
- If the RCA is for a high-severity incident (SEV-1/SEV-2), hold it to a higher standard of completeness
- Distinguish between "nice to have" improvements and "must fix before publishing" issues
- If the timeline is missing timestamps, this is always a must-fix -- timelines without timestamps lose forensic value
- When flagging a weak root cause, suggest what a deeper analysis might look like
- Remember: the goal of an RCA is organizational learning, not blame assignment. Flag any language that assigns blame to individuals
