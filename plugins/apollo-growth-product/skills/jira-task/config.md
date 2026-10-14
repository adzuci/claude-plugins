---
jira_cloud_id: "<UNSET>"
jira_base_url: "<UNSET>"
jira_primary_project_key: "<UNSET>"
jira_primary_issue_type: "Task"
jira_primary_default_priority: "P2"
jira_primary_parent_guidance: "Parent only when an epic clearly fits, otherwise leave unparented."
primary_team_name: "<UNSET>"
primary_audience_description: "<UNSET>"
jira_secondary_project_key: ""
jira_secondary_issue_type: "Story"
jira_secondary_parent_guidance: ""
secondary_team_name: ""
secondary_audience_description: ""
jira_default_assignee: "<UNSET>"
roadmap_team_property: "Delivery team"
roadmap_jira_link_property: "Jira link"
qa_reviewer: "<UNSET>"
deploy_notification_channel: "<UNSET>"
experiment_platform: "<UNSET>"
experiment_bucketing_unit: "<UNSET>"
experiment_traffic_split: "50/50 control/treatment (2 variants)"
experiment_confidence_threshold: "90% (alpha 0.1)"
experiment_default_primary_metric: "<UNSET>"
experiment_deployments: "<UNSET>"
team_context_dirs: ""
---

# Setup Guide

This file ships with the skill. Treat it as defaults and documentation: a plugin update replaces it,
so don't save your answers here.

Just run the skill. It prompts for anything still `<UNSET>` the first time and writes your answers to
`~/.claude/plugin-config/apollo-growth-product/jira-task.md`, which survives updates. To set values up front, create
that file yourself with the same frontmatter keys.

An empty string is a real answer meaning "intentionally blank", not a missing one, so the skill won't
re-ask for keys you deliberately left empty.

If your team files to a single Jira project, leave every `secondary_*` value empty. The skill skips
routing and files everything to the primary project.

## Jira connection

### jira_cloud_id

Your Atlassian cloud ID (a UUID). Get it from `getAccessibleAtlassianResources`, or from the Jira
MCP server's own resource listing.

### jira_base_url

The base URL of your Jira site, no trailing slash, e.g. `https://yourcompany.atlassian.net`. Ticket
URLs are built as `<base>/browse/<KEY>`.

## Project routing

### jira_primary_project_key

The Jira project key most of your tickets file to, e.g. `CVR`. This is the key, not the project
name. They often differ, and only the key works with `createJiraIssue`.

### jira_primary_issue_type

The default issue type name for new tickets in the primary project, e.g. `Task` or `Story`.

### jira_primary_default_priority

The default priority for the primary project, e.g. `P2` or `Medium`. Set this to an empty string if
the project's create screen has no priority field.

### jira_primary_parent_guidance

One or two sentences telling the skill how to pick a parent epic in this project. If the project has
a stable set of epics worth naming, list them with their keys and what each covers. If parenting is
usually not appropriate, say so.

### primary_team_name

The team that owns the primary project, e.g. `Growth Conversion`. Used in the draft so the user can
catch a wrong routing read.

### primary_audience_description

Who the primary project's work is aimed at, e.g. `Free / trial / not-yet-paying users`. This is the
routing signal, so make it concrete enough to distinguish from the secondary audience.

### jira_secondary_project_key

The Jira project key for a second audience, e.g. `GXP`. Leave empty if you only have one project.

### jira_secondary_issue_type

Default issue type name for the secondary project.

### jira_secondary_parent_guidance

How to pick a parent in the secondary project. If the project carries one epic per quarterly KR,
list each epic key, the KR it represents, and the kind of work that belongs to it. Also note that
these keys go stale when the quarter rolls over, so the skill re-queries before trusting them.

### secondary_team_name

The team that owns the secondary project, e.g. `Growth Expansion`.

### secondary_audience_description

Who the secondary project's work is aimed at, e.g.
`Existing paid teams: add-on credits, seats, tier upgrades, expansion revenue`.

## People and channels

### jira_default_assignee

The default assignee for new tickets, as an Atlassian account ID, plus the person's name in
parentheses so the draft is readable, e.g. `5b10a2844c20165700ede21g (Jamie Rivera)`. Set to an
empty string to create tickets unassigned by default.

### qa_reviewer

Who engineers should ping when a change hits staging, e.g. `the PM (+ secondary DRI if applicable)`.
Goes into every ticket's acceptance criteria.

### deploy_notification_channel

The Slack channel engineers post in when a change ships to production, including the `#`, e.g.
`#growth-conversion-pd`.

## Notion roadmap link-back

### roadmap_team_property

The property on your Notion roadmap database that names the delivery team. Used to route between
Jira projects when a roadmap item is the ticket's source. Often `Delivery team` or `Team`.

### roadmap_jira_link_property

The URL property on your roadmap database where the new ticket link gets written after creation.
Often `Jira link`.

## Experiment defaults

These apply to experiment tickets only. They keep acceptance criteria short by letting engineers
follow a standard pattern instead of restating it every time.

### experiment_platform

Your feature flag / experimentation platform, e.g. `Amplitude Experiments` or `Statsig`. Naming it
explicitly matters when your org has more than one.

### experiment_bucketing_unit

The default randomization unit, e.g. `group_name (account-level)` or `user_id`.

### experiment_traffic_split

The default split, e.g. `50/50 control/treatment (2 variants)`.

### experiment_confidence_threshold

The default confidence threshold, e.g. `90% (alpha 0.1)`.

### experiment_default_primary_metric

The metric most of your experiments target unless stated otherwise, e.g.
`Free-to-Paid Conversion (FTP)`.

### experiment_deployments

The deployment targets an experiment flag goes out to, e.g. `prod-server + prod-client`.

## Local context

### team_context_dirs

Optional. Comma-separated local directories the skill globs for team context, product surface maps,
and prior experiment results that inform acceptance criteria, e.g.
`resources/app/screen-map, areas/growth/experiments/results`. Leave empty to skip the local scan.
