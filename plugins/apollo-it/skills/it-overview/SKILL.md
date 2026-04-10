---
name: it-overview
description: IT environment overview — devices, access, and support process. Use when the user asks about device setup, Okta/Kandji enrollment, how to request software access, IT support channels, or new hire provisioning.
---

# IT Overview

Use this skill when someone asks about device setup, access requests, IT tooling, or how to get help from IT.

## Device Setup

- **Mac provisioning**: Kandji MDM — new devices are enrolled automatically via Apple Business Manager. Kandji pushes security policies, required software, and configuration profiles.
- **Windows provisioning**: Contact IT via Jira Service Management — Windows devices are provisioned on a case-by-case basis.
- **New hire process**: IT provisions accounts (Okta, Slack, email) before day one. The new hire activates Okta MFA, enrolls their device in Kandji, and follows the onboarding checklist in their welcome email.

## Identity & Access

| Tool | Purpose |
|------|---------|
| Okta | SSO / Identity provider — all SaaS apps federated, MFA enforced |
| Kandji | MDM — device management, security policies, software deployment |
| Jira Service Management | IT ticketing — access requests, hardware, incidents |

## Getting Help

| Channel | When to use | Response time |
|---------|-------------|---------------|
| `#it-help` (Slack) | Quick questions, "how do I..." | Same business day |
| Jira Service Management | Access requests, hardware, formal tickets | SLA-based (varies by priority) |
| `#it-incidents` (Slack) | Outages, security incidents | Immediate (tag IT on-call) |

## Common Requests

| Request | How to do it |
|---------|-------------|
| **Software access** | Check Okta app catalog first (self-service). If not listed, open a Jira Service Management ticket with the app name and business justification. |
| **VPN** | Follow the VPN setup guide in Kandji KB. For issues, post in `#it-help`. |
| **Hardware replacement** | Open a Jira Service Management ticket under "Hardware Request". Include device type, reason for replacement, and shipping address. |
| **Snowflake / data tool access** | Not IT — go through `#data-infra` or `#xfn-team-discovery-and-analytics` (see apollo-analytics plugin). |
| **New tool evaluation** | Contact Patrick Sullivan (Sr Director, Business Systems) for vendor evaluation and procurement. |

## Gotchas

- Okta MFA is required — if locked out, IT can reset via Jira Service Management ticket (not Slack)
- Kandji enrollment must complete before accessing company resources on a new device
- Some SaaS apps have limited licenses — check with IT before assuming access is available
- Claude Enterprise plugin visibility is managed by Patrick Sullivan in the admin console
