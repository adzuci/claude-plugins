# apollo-gtm-enablement

Creates facilitator-ready Apollo enablement decks and training materials for GTM teams (Sales, Customer Success, Product). Turns Notion calendar topics, Salesforce activity data, and Gong conversation examples into evidence-backed, Apollo-branded PPTX training sessions.

## Problem this solves

Enablement leaders spend days manually researching topics, pulling Salesforce data, reviewing Gong calls, and building decks. This plugin compresses that into minutes by combining internal source systems with Apollo-branded deck generation — producing a polished, facilitator-ready PPTX with speaker notes, interactive exercises, and real internal evidence.

## Frequency

On-demand or recurring (weekly for GTME team, varies by team)

## Audience

Apollo GTM enablement teams:

- **Sales Enablement (GTME):** Feature launches, competitive training, intervention deep-dives, new hire onboarding
- **CS Training:** Customer onboarding, adoption playbooks, renewal strategies
- **Product Enablement:** Beta programs, feature education, demo best practices

Common users: GTME team, Sales enablement managers, CS managers, Product managers running internal training

## Connected systems

These connectors are enterprise-provisioned — they appear automatically in Claude once your admin enables them. You do not install or configure them yourself.

| System | What it's used for |
|---|---|
| Notion | Read the enablement calendar to identify the session topic and linked source materials |
| Google Drive | Access session assets, supplementary docs, and shared resources |
| Salesforce | Pull activity data: intervention completion rates, deal velocity, adoption metrics |
| Gong | Review call recordings, scored calls, and smart trackers for real conversation evidence |

If a connector is not yet enabled for your workspace, the plugin runs in partial mode and flags what's missing.

## How it works

The plugin writes a fresh `python-pptx` build script per deck — one script per topic, owning every layout decision. Brand compliance is enforced by the bundled `apollo_brand` toolkit, which provides Apollo's color palette, typography, logo assets, and chrome helpers. The output is an Apollo-branded `.pptx` file saved to `/tmp/gtme-decks/<topic-slug>.pptx`.

## Getting started

### Install

```
claude plugin marketplace add apollo-plugins
claude plugin install apollo-gtm-enablement@apollo-plugins
```

### First run

```
/gtme-setup
```

This checks which connectors are active and guides you through any missing setup.

### Build a deck

```
/gtme-init                          # pull topic from Notion calendar
/gtme-build "AI Prospecting Tools"  # build a specific topic
/gtme-run-next                      # build the next upcoming session
```

## Kill criteria

Retire this plugin if Cowork ships native GTME enablement deck generation from Notion, Salesforce, and Gong, if usage drops below 1 run per month for 6 consecutive weeks, or if the workflow no longer produces materially better outputs than the default Apollo GTM system.
