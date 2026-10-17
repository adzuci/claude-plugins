# Output Contract

Keep the default response short enough to scan in a terminal.

```markdown
# Tool Intake: <tool>

Tool: <resolved identity>
Type: <CLI/SaaS/OSS/library/extension/MCP/hybrid>
Approval: <approval state>
Next action: <action>
Bottom line: <one sentence>

## Evidence
- [VERIFIED] <claim>: <source>
- [INFERRED] <claim>: <basis>
- [GAP] <missing evidence and why it matters>

## What It Touches
- Execution and install:
- Files, credentials, and permissions:
- Data and network egress:
- Retention, telemetry, and subprocessors:

## Apollo Policy And Customer Trust
- Related Apollo policy or Legal training and why it applies:
- Brand, jurisdiction, ownership/control, or customer-trust risk when relevant and verified:

## Apollo Fit
- Existing tools or internal capabilities:
- Duplication or owner evidence:

## Related Requests
- <verified matching request in #zip-help-desk, #security-requests, or the Legal request channel; omit when none is found>

## Project Or Company Snapshot
- Canonical repository and GitHub stars for OSS; or company, location, founding year, disclosed funding/ownership, and pricing link for a company product
- Up to two linked comparable products when useful

## Low-Risk Test
- <synthetic-data, isolated, credential-free test controls, or why no safe test exists>

## Safest Next Step
<one practical action; prefer an isolated exploration path when Security's lightweight-testing guardrails fit>

## Process
- <current Zip/Procurement links>
- <direct Start a Zip request link and #zip-help-desk link>
- <specific information Zip still needs: owner, use, users, data, permissions, integrations, egress/subprocessors, retention/training/deletion, terms, pricing, alternatives, and test scope>
```

Always include a brief low-risk test plan for an unknown tool. Add a detailed plan and Zip packet when the user wants to pursue it. Put long source lists and implementation detail in HTML or expandable sections, not the terminal summary.
