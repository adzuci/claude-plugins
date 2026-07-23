# career plugin

Job search intelligence tools for senior technical candidates. Currently includes one skill:

## Skills

### `/career:market-sweep`

Runs a full job market intelligence sweep for a senior technical candidate, produces a structured report with tier-ranked role list, writes it to the vault, runs an automated recruiter review, and improves the report in-place. Optionally sets up a weekly scheduled agent to keep the report current.

**Designed for:** Staff/Director/Principal-level engineering, data, and analytics candidates targeting remote US roles at $150k+.

## Install

```
claude plugin marketplace add adzuci/claude-plugins
claude plugin install career@adzuci-plugins
```

Then run `/career:market-sweep` and answer the setup questions.
