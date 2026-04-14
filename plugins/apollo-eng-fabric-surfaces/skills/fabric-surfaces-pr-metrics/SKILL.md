---
name: fabric-surfaces-pr-metrics
description: Use when running the fabric-surfaces sprint retro, asking about fabric-surfaces PR health, lead time, velocity, or cycle time, or when someone asks how fast fabric-surfaces (pux) PRs are merging. Pulls data from Snowflake via the snow CLI.
---

# Fabric Surfaces PR Metrics

A team-specific wrapper around `apollo-eng:pr-metrics`. Follow the instructions in that skill, but skip Steps 1 and 2 — use the pre-filled values below instead, then proceed directly from Step 3.

## Pre-filled Context

**Teams:** `fabric-surfaces` and `pux` (same team, renamed ~Feb 2026 — always include both)

**Default date range:** last 2 weeks ending today, with a rolling 4-week baseline. If the user provides a specific date range, use that instead.

______________________________________________________________________

## Adapting This for Your Team

To create a wrapper for your own team, copy this skill into your plugin and update:

1. **`name`** — match the directory name (e.g. `my-team-pr-metrics`)
1. **`description`** — add your team name and natural trigger phrases
1. **Teams** — replace `fabric-surfaces`/`pux` with your team's name(s) in Snowflake
1. **Default date range** — adjust if your team has a fixed cadence (e.g. anchor to last Friday for a sprint team)
