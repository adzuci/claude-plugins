---
name: gantt-generator
description: Generate a quarterly Gantt chart and engineer resourcing timeline from two CSVs (projects and headcount). Activate when a user asks to generate a gantt chart, plan resourcing, visualize project timelines, or says "/gantt-generator".
---

# Gantt Chart Generator

All chart logic lives in `scripts/gantt_generator.py` alongside this skill. Your job is to collect inputs and run it.

## Step 1 — Collect Inputs

Ask the user (batch into one question):

| Input | Default |
| --- | --- |
| Projects CSV path | — |
| Resourcing CSV path | — |
| Start date | `2026-05-01` (FY27Q2 start) |
| End date | `2026-10-31` (FY27Q3 end) |
| Eng overhead multiplier | `2.0` |
| Design overhead multiplier | `1.5` |

The default span covers **FY27Q2 + FY27Q3** (May 1 – October 31). Override `--start` / `--end` at runtime to change the range.

Output always defaults to `~/Downloads/gantt.html`.

If the user already provided paths or values in context, use them without re-asking.

## Step 2 — Run

Locate the bundled Python script and run it:

```bash
SCRIPT=$(find ~/.claude -name "gantt_generator.py" -path "*/gantt-generator/*" 2>/dev/null | head -1)
python3 "$SCRIPT" \
  --csv "projects.csv,resourcing.csv" \
  --start 2026-05-01 \
  --end   2026-10-31 \
  --eng-multiplier 2.0 \
  --design-multiplier 1.5 \
  --output ~/Downloads/gantt.html
```

Substitute the actual CSV paths and parameter values the user provided.

If the script exits with an error, show it to the user and ask them to verify inputs.

## Step 3 — Open and Report

Run `open ~/Downloads/gantt.html` to open in browser, then print the JSON summary verbatim.

## CSV Column Reference

**Projects:** `Project`, `Eng Effort (dev days)`, `Design Effort (design days)`, `Experiment Runtime (weeks)`, `Stack Rank`, `Category`, `Application Surface`, `Dependencies` (comma-separated project names)

**Resourcing:** `Dev`, `Capacity` (e.g. `100%`, `50%`)
