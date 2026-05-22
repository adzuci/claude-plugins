# Finding Sources

Security routes findings into the `INCIDENT` project (and adjacent projects like `SEC`, `INFOSEC`, `ITBS`) with a Jira **label** identifying the source. The label is the primary signal — description text parsing is fallback only.

## Source-label cheatsheet

| Label | Scanner / source | Coverage | FP profile | Confidence in CVSS | Default disposition for DevOps queue |
| -------------------- | ----------------------- | -------------------- | ---------- | --------------------- | --------------------------------------------------------------------------------- |
| `kodem` | Kodem (SAST + SCA) | App code, deps | Medium | Inflated for CI-only paths | Keep iff base image / Dockerfile / `terraform/` / `scripts/` in DevOps repos; else reroute by CODEOWNERS |
| `orca` | Orca Security | Cloud + IaC | Low-Med | Reasonable, prod-vs-non-prod matters | Keep for IaC, GKE node-level, cloud posture; reroute app-level workload misconfigs by CODEOWNERS |
| `bugcrowd` | Bugcrowd bug bounty | Manual pen-test | Very low | Trustworthy | Almost always reroute to the pack/feature owner; keep only when the finding is infra/IaC |
| `panther` | Panther SIEM | Endpoint + log rules | Low | No CVSS — alert severity | Reroute to Corp Eng / IT unless it's infra-attributable |
| `claude-security` | Internal manual review (often Claude-assisted) | Code, design | Very low | Trustworthy | Treat as Bugcrowd — manual, high signal, reroute by CODEOWNERS |
| *(no source label)* | Manual/Slack escalation | Anything | Variable | None | Hygiene issue — propose a reporter clarification comment before any other action |

If a ticket has multiple source labels (e.g. `kodem` + `bugcrowd` for a manual verification of an automated finding), the manual label wins: trust the human signal and treat it as Bugcrowd. See `duplicate-heuristics.md` for how to link the pair.

## Per-source field extraction

The skill must pull three things from each finding: **repo**, **affected path(s)**, and **severity context**. Each source exposes them differently.

### Kodem (`kodem`)

- **Repo:** description block contains `Repository: apolloio/<repo>` or `**Repository:** \`apolloio/<repo>\`\`.
- **Path(s):** listed under `Update all package-lock.json files in:` (for SCA) or as `**File:** <path>` (for SAST). Multiple paths are common.
- **Severity context:** `CVSS Score`, `Kodem Score` (0–1000), `Exploit Maturity` (Undetermined / PoC / Functional / High).
- **Known quirks:**
  - Inflates severity on CI tooling: a CVSS 10.0 in `scripts/jira-incident-failed-tests/` is not equivalent to the same CVE in production serving code. Apply the path-shape adjustment in `cve-triage.md`.
  - Can flag unscoped `Model.find(params[:id])` as IDOR when the action is actually gated downstream — see INCIDENT-28885 for the pattern.
  - Often duplicates itself across package-lock files; treat them as one ticket via `duplicate-heuristics.md`.

### Orca (`orca`)

- **Repo:** under `Repository.Name` and `Repository.Url`. Many Orca findings are IaC in `terraform/` paths inside an app repo.
- **Path(s):** `Origin: <path>:<line>` (e.g. `terraform/modules/tailscale-relay/main.tf:37`). Also exposes `Origin Url` linking to the GitHub blame view.
- **Severity context:** Orca's own severity plus `Account` (the cloud account/project). **Prod vs non-prod account is the single biggest severity modifier** — same misconfig in a feature/staging account is far lower priority.
- **Alert UI link:** `https://app.orcasecurity.io/alerts/orca-<id>` — always cite this in the proposed comment instead of paraphrasing.
- **Known quirks:** flags intentional configurations (e.g. Tailscale relay legitimately needs a public IP). Use the `orca-accepted-risk` comment template when remediation is "won't do" with documented justification.

### Bugcrowd (`bugcrowd`)

- **Repo:** named in the description by the researcher, often as a relative file path (e.g. `packs/iam/app/controllers/...`). Skill must infer the repo from the path prefix — `packs/` paths live in `leadgenie`; `terraform/` paths in `pocus-mirror` or service infra repos.
- **Path(s):** in the `File:` line of the finding body.
- **Severity context:** Bugcrowd's severity reflects the researcher's exploit and is trustworthy. Do not downgrade without explicit Glean/CODEOWNERS evidence of why the researcher's claim doesn't apply.
- **Known quirks:** Always has reproduction steps. If they're missing, the ticket is invalid — propose a reporter clarification.

### Panther (`panther`)

- **Repo:** N/A (detection-time alert, not source-code).
- **Affected:** `hostname` + `user` fields, plus detection rule name. The "path" equivalent is the **detection rule** — owned by the team that wrote it (usually Corp Eng / Security).
- **Severity context:** rule-defined alert severity. No CVSS.
- **Known quirks:** endpoint detections (e.g. unauthorized tool execution) almost always reroute to Corp Eng / IT — DevOps owns infra, not laptops.

### `claude-security`

Internal manual review, typically high-fidelity. Treat the same as Bugcrowd for routing purposes. The description usually includes file paths and a remediation block written in the same shape as a Bugcrowd report.

## Mapping a source label to the lookup

```
1. Read ticket.labels                            → source_label
2. Look up source_label in this file             → extraction recipe
3. Extract repo + affected_paths + severity_ctx
4. For each path: resolve via CODEOWNERS         → see team-lookup.md
5. Classify against OWASP                        → see owasp-ranking.md
6. Apply CVSS context adjustment + SLA           → see cve-triage.md
7. Decide KEEP vs REROUTE vs ASK                 → see reroute-rules.md
8. Compose proposed comment (never post)         → see comment-templates.md
```
