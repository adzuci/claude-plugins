---
name: jira-task
description: Create a well-structured Jira ticket from a Notion roadmap item or plain description, with an adversarial review pass before submission.
disable-model-invocation: true
requires_config: true
---

# Jira Task Creator

Create a well-structured Jira ticket from provided context, with a draft review before submission. The skill routes between two project keys based on who the work is aimed at.

Usage: `/apollo-growth-product:jira-task <description or Notion roadmap URL> [--project KEY]`

## Configuration

Before doing anything else, read `config.md` from this skill's directory. It contains a YAML frontmatter block of variables this skill depends on.

For every `{{placeholder}}` you encounter while running this skill, substitute the matching value from `config.md`'s frontmatter.

`config.md` ships with the skill, so treat it as **defaults and documentation, read-only**. A plugin update replaces it.

Your own answers live in `~/.claude/plugin-config/apollo-growth-product/jira-task.md`. Read that file first when it exists and let it override the shipped values, remembering that a saved empty string is a deliberate answer, not a missing one.

If a value is still `<UNSET>` after that merge, ask the user for it, then write the answer to `~/.claude/plugin-config/apollo-growth-product/jira-task.md` (creating the directory if needed). Never write answers back into the skill's own `config.md`; they'd be wiped on the next plugin update. Do this once per session.

If a `{{placeholder}}` has no matching key in `config.md`, that's a bug in this skill. Tell the user and proceed with a sensible default if you can.

If you only have one Jira project, set the secondary project variables to an empty string. The skill then skips all routing and files everything to the primary project.

## Workflow

Execute these steps **in order**.

### Step 1: Parse arguments and pick the project

Check the arguments for:

- A brief task description
- Links to writeups, designs, or related tickets
- **A Notion roadmap item URL** — the source of truth for the ticket
- A project key override

**Pick the project from the work's audience.**

| Audience | Project | When |
|---|---|---|
| {{primary_audience_description}} | **{{jira_primary_project_key}}** ({{primary_team_name}}) | Default |
| {{secondary_audience_description}} | **{{jira_secondary_project_key}}** ({{secondary_team_name}}) | Always for this audience |

If a Notion roadmap item was provided, its `{{roadmap_team_property}}` decides. State which project you picked in the Step 5 draft so a wrong read gets caught before the ticket exists. Ask when the audience straddles both.

**Watch the name/key gap.** A project's *name* and its *key* can differ, so JQL like `project = "Growth Conversion"` resolves against the name while `createJiraIssue` needs the key. Always pass the key.

**If a Notion roadmap item is provided**, fetch it and use it as the primary context source: pull the pitch, hypothesis, acceptance criteria, design links, and effort. Record the page ID. After the ticket is created you'll write the link back to the page (Step 7).

If no arguments were given, go to Step 2.

### Step 2: Gather context

Ask for any missing information:

> "What's the task? Include as much as you have:
>
> - What needs to change (current → desired)
> - Links to writeups, designs, Figma, Slack threads
> - Any specific acceptance criteria
> - Who it's for, so I can pick the right project"

Then review relevant local context. Glob and read `{{team_context_dirs}}` for team context, prior experiment results, and product surface maps that may inform acceptance criteria. Skip this when the value is empty.

### Step 3: Draft

Build the ticket using the **Template Structure** below. This is a working draft, don't show it yet.

### Step 4: Adversarial review (internal)

Re-read the draft as a senior engineer with strong product sense who has none of your context. Run the **Adversarial Review** checklist below and rewrite the draft to fix everything it surfaces. Do this silently and present only the revised version.

The bar: requirements are extremely clear and actionable, there are as few of them as make sense, and the whole ticket is short and easy to digest.

### Step 5: Present and revise

> "Here's the draft ticket. Review the summary, description, and all fields before I create it in Jira. Let me know if anything needs adjusting."

Show the summary, the full description, and every field value (project, type, priority, parent, assignee). Wait for approval or change requests.

### Step 6: Create in Jira

After approval, call `createJiraIssue` with the final values, using the project defaults below for anything unspecified. Build the ticket URL from the returned key: `{{jira_base_url}}/browse/<KEY>`.

### Step 7: Link back to the roadmap item (conditional)

**Only if** a Notion roadmap item was provided in Step 1, write the new ticket URL to that page:

```javascript
notion-update-page({
  page_id: "<roadmap page ID from Step 1>",
  command: "update_properties",
  properties: { "{{roadmap_jira_link_property}}": "{{jira_base_url}}/browse/<KEY>" }
})
```

Always do this when a roadmap item was the source. Never skip it. Confirm creation with the ticket URL and note that the link field was updated.

## Project defaults

Re-verify these before trusting them. Team-managed project screens change more often than company-managed ones. If a create call fails on an unexpected field, run `getJiraIssueTypeMetaWithFields` for the project and issue type and follow what it returns.

### Primary project — {{jira_primary_project_key}}

| Field | Value |
|-------|-------|
| **Cloud ID** | `{{jira_cloud_id}}` |
| **Project Key** | `{{jira_primary_project_key}}` |
| **Issue Type** | `{{jira_primary_issue_type}}` |
| **Priority** | `{{jira_primary_default_priority}}` |
| **Labels** | None. Do NOT add labels unless the user explicitly specifies them |
| **Assignee** | `{{jira_default_assignee}}` for eng POV review, unless the user specifies otherwise |
| **Parent** | `{{jira_primary_parent_guidance}}` |

### Secondary project — {{jira_secondary_project_key}}

Skip this whole section when `jira_secondary_project_key` is empty.

| Field | Value |
|-------|-------|
| **Cloud ID** | `{{jira_cloud_id}}` |
| **Project Key** | `{{jira_secondary_project_key}}` |
| **Issue Type** | `{{jira_secondary_issue_type}}` |
| **Labels** | None unless explicitly specified |
| **Assignee** | `{{jira_default_assignee}}` unless specified otherwise |
| **Parent** | `{{jira_secondary_parent_guidance}}` |

### Fields to check before sending

Team-managed projects take a lean field set. Before the first create of a session, confirm which of these the project's create screen actually has:

- **`components`** — many team-managed projects have none. Sending one fails the call.
- **`priority`** — some projects drop it entirely. Sending P2/Medium to a project without it fails or is silently dropped.
- **Sprint** — Kanban boards have no sprints to assign.

Only `project`, `issuetype`, and `summary` are universally required. Everything else is optional: `description`, `assignee`, `priority`, `labels`, `duedate`, `parent`, and team/start-date custom fields.

### Parent epic selection

When `{{jira_secondary_parent_guidance}}` names a set of KR epics, always parent the ticket to the most relevant one and say which you chose in the draft. Pick by what the work actually moves, using the ticket's **primary** metric as the tiebreak. If the roadmap item names a KR property, use that directly. If none fits, ask rather than guessing or leaving it unparented.

Epic keys go stale when the quarter rolls over. Re-query `project = <KEY> AND issuetype = Epic ORDER BY created DESC` before relying on any key written down here. If the summaries no longer match the KRs in your config, the quarter has turned and the config is stale.

## Template structure

```text
[Short imperative phrase, e.g. "Add high-contrast CTA to bulk select feature gate"]

**Links:**
- [Project writeup title](URL)
- [Figma designs title](URL)
- [Additional context title](URL)

### Acceptance Criteria

- [ ] [High-level UX change the user sees or experiences]
- [ ] [Set up the experiment, if applicable]
- [ ] [Ping {{qa_reviewer}} when changes are on staging for review]
- [ ] [Post in {{deploy_notification_channel}} when deployed to production]
```

The **Summary** field gets the short imperative phrase. The **Description** field gets the full content.

**Summary format:** verb-first imperative phrase, 5-10 words. For experiments, prefix with `Experiment:`.

- Good: `"Add high-contrast CTA to bulk select feature gate"`
- Good: `"Experiment: high-contrast CTA on bulk select paywall"`
- Bad: `"Bulk Select feature gate modal: current yellow CTA → high-contrast blue CTA for users selecting >25 contacts"`

## Adversarial review

Before showing any draft, read it once as a skeptical senior engineer who has strong product sense and zero context beyond what's on the ticket. Pressure-test it against these six checks, then rewrite so every one passes. Keep the pass light: the goal is a sharper ticket, not a longer one.

1. **Clarity.** Could this engineer build the right thing without asking a question? Flag jargon, undefined acronyms, ambiguous pronouns, and anything assuming context they don't have. Name the surface, feature, or audience explicitly.
1. **Unnecessary detail.** Cut any word, criterion, or link that doesn't change what gets built.
1. **Too prescriptive.** Strip implementation the engineer should own: layout, components, styling, copy specifics, environments, instrumentation, config. Pull each one back to the outcome the user experiences.
1. **Missing context.** Add only what's load-bearing: the "why" behind the change, a link they'll need, or a constraint they can't infer. One sentence of intent often prevents the wrong build.
1. **Actionable criteria.** Each acceptance criterion must be a single, checkable outcome. Rewrite anything vague ("works well," "is intuitive") into something a reviewer can verify.
1. **Fewest that make sense.** Merge overlapping criteria and drop ones the engineer would do by default. Aim for the smallest set that fully defines "done."

If a check surfaces a real gap you can't fill from context, ask in Step 5 rather than guessing.

## Acceptance criteria guide

Write criteria from a PM's point of view. State the outcome, not the implementation. Be extremely concise without losing essentials. Bias toward explicit over clever.

### 1. User experience changes

Describe what the user sees or experiences at a high level. Leave layout, component, and styling details to the engineer.

- Good: "User sees a high-contrast CTA on the bulk select feature gate"
- Bad: "Bulk Select modal displays blue (#0066FF) CTA at 16px font weight 600 when user selects >25 contacts via the contacts table"

### 2. Experiment setup (if applicable)

Reference the experiment without prescribing config. The engineer follows the standard pattern.

- Good: "Set up the experiment"
- Good (when specifics matter): "Set up the experiment with key `bulk-select-high-contrast-cta`"
- Bad: "Create experiment with 50/50 split, bucketed by account, targeting free and trial teams, confidence threshold 90%, deployments prod-server + prod-client"

### 3. Instrumentation

Do **not** add instrumentation criteria unless the user explicitly provides event names, properties, or requirements. Trust the engineer to instrument the change appropriately.

### 4. Stakeholder communication

Always include both:

- "Ping {{qa_reviewer}} when changes are on staging for review"
- "Post in {{deploy_notification_channel}} when deployed to production"

**Rules:** state WHAT, not HOW. Stay PM-level. Trust the engineer with implementation, environments, and instrumentation details.

## Experiment constants

These defaults apply to **experiment-related tasks only** (A/B tests, feature gate experiments, conversion experiments). Do NOT apply them to bug fixes, refactors, or analytics-only work.

| Constant | Default |
|----------|---------|
| Feature flag platform | {{experiment_platform}} |
| Bucketing unit | {{experiment_bucketing_unit}} |
| Traffic split | {{experiment_traffic_split}} |
| Rollout | 100% to target audience at launch |
| Confidence threshold | {{experiment_confidence_threshold}} |
| Primary metric | {{experiment_default_primary_metric}} |
| Experiment key format | kebab-case (e.g. `first-sequence-add-contacts`) |
| Deployments | {{experiment_deployments}} |
| QA review | Ping {{qa_reviewer}} when on staging |
| Deploy notification | Post in {{deploy_notification_channel}} when live |

Only include experiment key, traffic split, bucketing, deployments, metrics, or instrumentation as separate criteria when the user explicitly provides those specifics. Otherwise the engineer follows the standard pattern from the table above, so don't restate it in the ticket.

## Jira markdown formatting

Use standard markdown when building the description, Jira auto-converts it:

| Element | Syntax |
|---------|--------|
| Links | `[Text](URL)` |
| Bold | `**bold**` |
| Headers | `#`, `##`, `###` |
| Code | `` `code` `` |
| Unordered lists | `- item` |
| Checkboxes | `- [ ] item` |

**Checkbox caveat:** in team-managed projects the converter renders `- [ ]` as a bullet with literal `[ ]` text, not a native tickable checkbox. Readable, but not interactive. Don't retry the create to fix it. Mention it so the user can convert them in the UI if they want.

## MCP call reference

```javascript
createJiraIssue({
  cloudId: "{{jira_cloud_id}}",
  projectKey: "{{jira_primary_project_key}}",
  issueTypeName: "{{jira_primary_issue_type}}",
  summary: "Add high-contrast CTA to bulk select feature gate",
  description: "Full markdown description with links and acceptance criteria",
  contentFormat: "markdown",
  additional_fields: {
    // priority only when the project's create screen has it
    // parent only when an epic clearly fits
  }
})
```

If a create call rejects the assignee, they may not be a member of that project yet. Create the ticket unassigned and say so rather than failing the whole call.

## Related skills

1. `/apollo-growth-product:experiment-pitch` — shape the initiative and push to the roadmap
1. `/apollo-growth-product:experiment-writeup` — design the experiment
1. `/apollo-growth-product:experiment-record` — create the experiment tracker entry
1. `/apollo-growth-product:jira-task` (this skill) — create the engineering ticket
1. `/apollo-growth-product:experiment-results` — analyze results and write the post-mortem

This skill is also used for non-experiment work (bug fixes, analytics, refactors) where the experiment constants should be ignored.

## Safety rules

- **Always run the adversarial review** (Step 4) before showing the draft. Present only the revised version.
- **Always show the complete draft** before creating the ticket.
- **Do NOT add labels** unless explicitly specified.
- **Do NOT fabricate context.** Only use information provided or found in local context files.
- **Write from a PM point of view.** Outcomes, not implementation. No environments, deployment targets, code paths, or component/style details.
- **Stay high-level on UX.** What the user sees, not pixel-level layout.
- **Do NOT specify instrumentation** unless explicitly provided.
- **Be extremely concise.** Cut every word that doesn't earn its place.
- **Remove all placeholder text.** Never leave `[bracketed placeholders]` in the final ticket.
- **Always link back.** When the ticket came from a Notion roadmap item, write the ticket URL to that page (Step 7). Never skip this.
