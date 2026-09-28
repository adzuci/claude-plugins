# Local Export Format

Use after the user approves the draft and chooses local delivery.

## Do not use Notion MCP

This path writes a markdown file only — skip all Notion MCP steps and the sample-case gate (`EXPORT TO LOCAL` is sufficient approval).

## File location & naming

| Rule | Requirement |
| ---- | ----------- |
| **Directory** | `tmp/` at repository root |
| **Filename** | `tmp/bug-bash-<feature-slug>-test-cases.md` |
| **Slug** | Lowercase feature name; spaces/special chars → hyphens (e.g. `builder-sheet-automation`) |

## File header (required)

```markdown
# [Feature Name] — Bug Bash Test Cases

**Canonical source:** [supplied Bug Bash/Test Plan URL, other source URL, or "User-provided description"]
**Generated:** [YYYY-MM-DD]
**Source docs:** [ERD, PRD, Jira, etc.]
**AI-Generated:** Yes
**Total cases:** [N] (P0: x, P1: y, P2: z)
```

## Per-test-case structure

Each case MUST include:

| Field | Notes |
| ----- | ----- |
| Name | `Verify [description]` — no priority prefix |
| Priority | P0, P1, P2, or P3 |
| Test Case Type | Same allowed values as Notion path |
| Test Suite | Sanity / Regression / Smoke per priority mapping |
| Group | Feature/component grouping |
| Status | `Not started` |
| Preconditions | Setup, permissions, data state |
| Test Steps | Numbered, actionable |
| Expected Result | Clear success criteria |

## Section layout

Preserve the Phase 2 review structure:

1. **Journey / E2E test cases** (grouped)
1. **Atomic risk test cases** (grouped)
1. **Summary tables** — counts by priority and by group

## Completion output

Return to the user:

1. Full path to the created file
1. Summary with counts by priority and Group
