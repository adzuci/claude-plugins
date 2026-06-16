# Renewal Discovery

Use this when the user asks for vendor renewal dates, Grafana email review, or a procurement
calendar. Build a sourced inventory, not a vibes list.

## Search Order

1. **Gmail** for vendor notices and Grafana emails:
   - `from:grafana renewal`
   - `from:grafana vendor`
   - `from:grafana contract`
   - `renewal has:attachment`
   - `("renewal" OR "expires" OR "auto-renew" OR "contract") <vendor>`
1. **Glean** for internal docs, Slack threads, Jira, and Drive:
   - Query short terms: `<vendor> renewal`, `<vendor> contract`, `<vendor> Zip`, `procurement <vendor>`.
1. **Google Drive / Notion** for working docs, renewal trackers, pricing notes, and business
   cases.
1. **Zip / Procurement source** if available. Search Glean for `Zip procurement process`,
   `Zip renewal`, or the vendor name plus `Zip` before assuming there is or is not a Zip
   intake.
1. **Ironclad** only when the user asks for legal contract records or when the renewal table
   needs executed-agreement evidence.

## Renewal Table

Return:

| Vendor | Product / use | Renewal date | Notice deadline | Current annual spend | Proposed annual spend | Owner | Source | Next action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

Rules:

- Use exact dates when found.
- Mark unknowns as `unknown`, never blank.
- Distinguish renewal date from signature deadline and notice deadline.
- Distinguish annual spend from TCV and one-time cash due.
- Link or cite each source in the `Source` column.
- Do not mark a vendor "safe" if the cancellation notice window is unknown.

## Grafana Email Handling

Grafana emails are usually alerts or dashboard subscriptions, not procurement truth. Use them
as discovery signals:

- Extract vendor/tool names mentioned in alert titles, panels, or dashboard labels.
- Use those names to search Gmail/Glean/Drive for actual contract or renewal evidence.
- If a Grafana email points to usage, reliability, or business impact, cite it as value
  evidence, not renewal evidence.

## Output Summary

Lead with:

```text
Found <n> vendors with sourced renewal signals. <m> have exact renewal dates; <k> need Procurement/Zip/Ironclad lookup.
```
