---
name: product-ship-post
description: Generate product ship room posts for Slack announcements. Activate when user asks to write a ship post or feature launch announcement.
argument-hint: '[--length WORDS]'
---

# Product Ship Post Generator

Write product ship room posts for announcing features in Slack.

## Style Guidelines

Follow user's writing style for:

- Tone (formal vs casual)
- Sentence length and complexity
- Technical depth
- Emoji usage

## Length

Default to 120-200 words for the complete post, sized to customer impact:

- 120-140 words for narrow or incremental improvements
- 140-170 words for meaningful workflow improvements
- 170-200 words for broad impact or repeated customer demand

Do not inflate the post to imply more impact than the evidence supports. Count
every whitespace-separated item, including the title, headings, emoji codes,
links, channel names, and @mentions. Use a word-count tool when available.
Otherwise, count best-effort and do not claim the total was verified exactly.

When the user passes `/apollo-eng:product-ship-post --length WORDS`, treat that
positive integer as the hard maximum instead of the default range. Apply it even
when following a custom example. If required links and mentions cannot fit, ask
for a higher value.

- Return the post without an explanatory preamble. After drafting, count the
  words and revise until it is within the active range or limit.

## Step 1: Gather Resources

Start by offering the user a choice:

> "I can help you write a ship post! You have two options:
>
> **Express mode**: Paste all your info at once using this template:
>
> - Feature name & summary:
> - Resources (GitHub PR, Notion doc, Jira ticket, Loom):
> - People to tag (Engineering, Product, Design, EM, QA, Special thanks, For visibility):
> - Feedback channel:
> - What's next (optional):
>
> **Guided mode**: I'll walk you through question by question.
>
> Which do you prefer?"

### Express Mode

If user chooses express mode or pastes structured info upfront:

- Acknowledge all provided information
- Only ask follow-up questions for missing REQUIRED fields (feature summary, at least one resource link, team members, feedback channel)
- Skip to Step 2: Research

### Guided Mode (Sequential Interview)

Ask questions ONE AT A TIME. Wait for response before asking next question.

#### Question sequence:

1. **Feature summary**: "What's the feature called and what does it do in 1-2 sentences?"
1. **Resources**: "Share any relevant links - GitHub PR(s), Notion doc, Jira ticket, Loom demo. Say 'skip' for any you don't have."
1. **People to tag**: "Who should be mentioned? List names for each role (skip any that don't apply):
   - Engineering:
   - Product:
   - Design:
   - EM:
   - QA:
   - Special thanks:
   - For visibility:"
1. **Feedback channel**: "Which Slack channel should people use for questions/feedback?"
1. **What's next**: "Any planned follow-ups to mention? - or say 'skip' to omit this section."
1. **Example post**: "Do you have a specific example post you want me to follow? (paste it or say 'use default')"

#### Rules for the interview:

- Ask ONE question per message
- Wait for the user's response before asking the next question
- Accept "skip", "none", "n/a" as valid answers to skip optional fields
- If the user provides multiple answers at once, acknowledge them and skip to the first unanswered question
- Never ask a question the user has already answered
- Keep your questions short and direct
- After gathering all information, confirm you have everything before proceeding to research

If the user provides a custom example post, follow its structure and style instead of the built-in examples.

## Step 2: Research the Feature

Before writing, you must be able to answer ALL of these:

- [ ] What problem does this solve? (with specific user pain or data)
- [ ] Key user benefit (1 sentence)
- [ ] What was the previous state/limitation?
- [ ] What's the expected impact or outcome?
- [ ] How does it technically work? (high-level)
- [ ] What are 2-3 key user-facing capabilities?

If you cannot answer all of these, you MUST either:

1. Search deeper in the provided resources
1. Ask the user directly: "I need more context on [X] to write a compelling intro. Can you explain [specific question]?"

### Product Context is REQUIRED

The intro paragraph MUST include product context explaining WHY this feature matters. Look for:

- What problem does this solve? (e.g., "users were manually doing X for hours")
- What was the user pain point or business opportunity?
- What's the expected impact? (e.g., "reduces enrichment time by 50%")

If you can't find this context, ask the user directly before proceeding.

### Research sources

Use CLI tools when available (preferred) or MCPs to search internal documentation:

- GitHub: `gh` CLI (preferred) or GitHub MCP
- Jira: Jira MCP or API
- Notion: Notion MCP
- Glean: Glean MCP

Look for:

- Jira tickets: look for "Problem statement", "JTBD", or "Why" sections
- Product specs and design docs
- Previous announcements about this feature area
- Customer feedback or requests that motivated this work
- Internal discussions or decisions

### If tools unavailable:

- Ask user to paste relevant content directly from PR descriptions, Jira tickets, etc.
- Provide specific questions: "What problem statement is in the Jira ticket?"
- Proceed with manual information gathering rather than failing

Read the provided resources thoroughly:

- GitHub PRs: understand the implementation details
- Notion docs: understand the product vision and user value
- Jira tickets: understand the scope, context, and **problem statement**

Do NOT write the post until you deeply understand the feature AND have clear product context.

## Step 3: Write the Post

### Writing Style Rules

**MUST follow these rules exactly:**

- NO em dashes or double-hyphen substitutes - use commas, periods, or rewrite
  the sentence
- Use only straight quotation marks and apostrophes
- NO overly formal language - write like a human, not a press release
- Avoid canned contrasts such as "not just X, but Y," generic superlatives, and
  self-congratulatory launch language
- Remove generic setup, repeated claims, filler, and headings that do not help
  the reader act
- Keep bullet points concise and scannable
- Use direct, active voice
- Use Slack emoji codes (e.g., :rocket:, :sparkles:, :movie_camera:)

### Post Structure

Follow this structure (adapt sections as needed):

```text
:rocket: *[Feature Name] - [Brief tagline]*

[2-3 sentence intro with PRODUCT CONTEXT: problem statement, opportunity, or impact data + what shipped to address it]

:sparkles: *What's new*
[Bullet points of key features/changes - focus on user value]

:movie_camera: *Demo*
[Loom link]

:clock1: *What's next* (optional - only if there are clear next steps)
[Bullet points of planned follow-ups]

:teamwork_hands: *Team:* @engineers *(Eng)* @qa *(QA)* @product *(PM)* @em *(EM)* @reviewers *(Reviewers)*

For visibility: @names @groups

:thinking_face: *Questions or ideas?*
Share them in #[relevant-channel]!
```

### Section Guidelines

**Title:** Use :rocket: emoji. Keep it punchy. Add a short tagline after the
feature name.

**Intro:** 2-3 sentences. MUST include product context: the problem being solved,
the opportunity, or data showing why this matters. Don't just say "we shipped
X" - explain WHY it matters.

**What's new:** Focus on user-facing value, not technical details. Use simple
language. Each bullet should be scannable.

**Demo:** Include the Loom link with the :movie_camera: header. Do not replace
the Demo section with a generic resource link.

**What's next:** Only include if there are concrete next steps. Skip if
uncertain.

**Team:** Keep contributors on one line. Put each role after its mentions:
`@names *(Eng)* @names *(QA)* @names *(PM)* @names *(EM)* @names *(Reviewers)*`.
Separate multiple names with commas inside a role. Group all reviewers before one
`*(Reviewers)*` label. Omit roles that have no contributors. `:teamwork_hands:`
is an Apollo workspace custom emoji.

**For visibility:** Tag relevant stakeholders and groups.

**Questions:** Point to a relevant Slack channel for feedback.

### Optional Sections

Add these only if relevant:

- `:test_tube: Growth hack experiments` - for A/B tests or experiments
- `:white_check_mark: New JTBDs unlocked` - for major capability expansions
- `:hand::skin-tone-2: Want access?` - for beta features with limited access

## Quality Checklist

Before presenting the draft, verify:

- [ ] Estimated word count is within the active range (120-200 by default) or requested limit
- [ ] Every sentence or section adds distinct, specific value
- [ ] **Intro includes product context** - explains WHY (problem, opportunity, or impact data), not just WHAT shipped
- [ ] No em dashes or double-hyphen substitutes used anywhere
- [ ] No curly quotes used anywhere
- [ ] Bullet points are concise and scannable
- [ ] Technical jargon is minimal or explained
- [ ] Team section has all contributors properly tagged
- [ ] Demo link is included
- [ ] Feedback channel is mentioned

## Final Step

After presenting the draft and making any requested edits, remind the user:

"Use `/copy` to copy the post to your clipboard. Then in Slack: paste, select all (Cmd+A), and press Cmd+Shift+F to apply formatting."

Send this reminder separately from the post. Do not include it in the word count
or copied post.
