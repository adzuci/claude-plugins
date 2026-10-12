# Zip Agreements Reference

Parameter and payload reference for the Zip MCP tools used by `/apollo-eng-devops:renewal-radar`. All three tools are read-only.

## `list_agreements`

Lists agreements (contracts) for the configured company. Returns up to 50 per page; `page_size` accepts 1-100.

### Filter parameters

| Parameter | Type | Notes |
|---|---|---|
| `vendor_guid` | string | Exact match |
| `department_guid` | string | Exact match. Falls back to the vendor's primary department on agreements with no direct department |
| `subsidiary_guid` | string | Exact match |
| `category_guid` | string | Top-level category, exact match |
| `subcategory_guid` | string | Exact match |
| `creator_guid` | string | Agreement creator, exact match. This is what `--mine` sets |
| `owner_guid` | string | Owner currently resolves to the creator, so it behaves like `creator_guid` |
| `agreement_number_str` | string | Single agreement by number |
| `renewal_status` | list of enum names | See below |
| `agreement_status` | list of enum names | See below |
| `total_cents_min` / `total_cents_max` | integer | Cents, not dollars. Combine for a closed range |
| `end_date_after` / `end_date_before` | ISO-8601 date | Combine for a closed range |
| `sort_by` | enum | `created_at` (default), `updated_at`, `end_date_or_max_date`, `total_cents` |
| `sort_order` | enum | `desc` (default), `asc` |
| `cursor` | string | Opaque pagination cursor |
| `page_size` | integer | 1-100 |

### `renewal_status` enum

| Value | Meaning |
|---|---|
| `UPCOMING` | A renewal alert is scheduled. `display_renewal_status` renders as "Alert scheduled" |
| `NOT_SCHEDULED` | **No renewal alert configured at all.** The highest-risk bucket, and why it is in this skill's default status set |
| `RENEWAL_IN_PROGRESS` | Renewal actively being worked |
| `CANCELLATION_IN_PROGRESS` | Cancellation actively being worked |
| `RENEWAL_COMPLETE` | Already renewed |
| `CANCELLATION_COMPLETE` | Already cancelled |
| `CANCELED` | Cancelled |

`--all-open` adds `RENEWAL_IN_PROGRESS` and `CANCELLATION_IN_PROGRESS` to the default `UPCOMING,NOT_SCHEDULED` set. The three terminal states are never in a default query, because a completed renewal is not a thing to act on.

### `agreement_status` enum

`ACTIVE`, `INACTIVE`, `TERMINATED`. The radar filters to `ACTIVE` only.

## ZContract field map

Each hit is a full `ZContract`, the same shape `get_agreement` returns. Renewal-date fields and queue-related fields are intentionally not returned by this endpoint.

### Scalars

`guid`, `agreement_link`, `agreement_number`, `name`, `currency`, `total_cents`, `start_date`, `end_date`, `execution_date`, `status`, `contract_status`, `renewal_status`, `display_renewal_status`, `type`.

### To-one associations

- `vendor` — `guid`, `name`, `status`, `erp_currency`, `address`, `vendor_link`
- `department` — `guid`, `name` (the full ERP path, e.g. `Research and Development : Engineering : Engineering Leadership`), `display_name`, `hide_in_zip`, `is_active`, `status`
- `creator` — `guid`, `email`, `first_name`, `last_name`, `employee_number`, `is_active`. This is the agreement owner
- `request_for_amendment`

### To-many associations

`subsidiaries`, `categories`, `subcategories`, `attachments`, `purchase_orders`, `requests`, `requests_for_master_contract`, `child_contracts`.

### What the radar extracts, and what it drops

Extract only: `vendor.name`, `name`, `agreement_number`, `total_cents`, `currency`, `end_date`, `renewal_status`, `display_renewal_status`, `department.name`, `creator.first_name`, `creator.last_name`, `agreement_link`.

Drop everything else. The to-many associations are the bulk of each record's weight, and `requests[].description` and `purchase_orders[].description` in particular carry free-text commercial detail such as rate cards and negotiation notes that has no place in a renewal digest.

### Field gotchas

- `total_cents` is cents. Divide by 100 and format with the record's own `currency`, which is not always USD.
- Date fields come back as `2027-09-04T00:00:00Z`. Render the date part only.
- `agreement_number` is an integer, not a string, even though the filter parameter is `agreement_number_str`.
- `agreement_link` is a full URL of the form `https://apollo.ziphq.com/manage/agreement/<guid>`. Use the field as returned rather than constructing the URL.
- `renewal_status` is the enum name; `display_renewal_status` is the human-readable label. Show the display form to users.
- `status` and `contract_status` are opaque integers. Prefer the `renewal_status` / `agreement_status` enums over interpreting them.
- **There is no auto-renewal or notice-window field.** `end_date` is the term end, not the date by which cancellation notice is due. This isn't a permissions gap — the `get_agreement` tool's own description names the ticket: FIO-1440. `auto_renews`, `opt_out_date`, `renewal_workflow`, `renewal_stakeholders`, and `cancellation_workflow_config` exist in Zip's data model but are deliberately withheld from the API today because the underlying DB columns are misleadingly named; Zip's CLM team is renaming them behind an `enable-new-renewal-fields` flag before exposing them. A real Apollo incident (Terraform Cloud/HashiCorp, 2027) nearly missed a 60-day notice deadline that was invisible in exactly this kind of end-date-only view. Treat `end_date` as a lower bound on urgency, never the actual deadline, and say so (see the notice-deadline caveat in `SKILL.md`).
- **Per-row visibility is not consistent across query filters.** An unfiltered or department-scoped `list_agreements` call can hide an agreement that a `vendor_guid`-filtered call on the same agreement will return (confirmed live: Cloudflare and Grafana). The reverse also happens — an agreement referenced by a PO's `agreement_number` can stay invisible even when queried directly by `agreement_number_str` (confirmed live: a Redpanda agreement, #87, referenced by PO #90). Don't treat one empty result as proof an agreement doesn't exist; the vendor sweep in `SKILL.md` step 3 exists specifically to retry with a different filter before concluding that.

## Cursor pagination

The response carries `hits`, `total`, and `cursor`. Pass the returned `cursor` back on the next call to get the next page. A null or absent `cursor` means the last page.

**Page-size rationale.** Each hit is a fat nested record of roughly 2KB even before attachments. At `page_size: 100` a single page can exceed 200KB of JSON, most of it fields the radar discards. `page_size: 25` keeps each round trip cheap while still resolving most single-team windows in one or two pages.

**Hard cap.** Stop after 8 pages or 200 rows, whichever comes first, and report `showing N of <total>`. A team with more than 200 renewals in the window has a scoping problem, not a pagination problem; steer the user to `--days` or `--min-amount`.

## `list_departments`

Lists active departments. Filters: `name` (case-insensitive substring on the display name), `hide_in_zip`, `external_id` (ERP-prefixed, e.g. `netsuite:abc123`, prefix required for an exact match). Sort by `created_at` or `updated_at`. Up to 50 per page.

This tool requires a department read permission that many Apollo tokens do not have. See [`zip-mcp-setup.md`](zip-mcp-setup.md) for the fallback.

## `list_vendors`

Lists vendors. The `name` filter is trimmed and matched as a case-insensitive **substring** against the indexed `name_key`, so `Arista` matches `Arista Networks Solutions, Inc`. This is deliberately looser than the underlying REST handler's full-string match.

Other filters: `department_guid` (the vendor's primary department), `subsidiary_guid`, `status` (`ACTIVE`, `INITIAL`, `DRAFT`, `DELETED`), and a `last_updated_after` / `last_updated_before` range. Sort by `created_at`, `updated_at`, `last_updated` (default), or `name_key`.

Vendor payloads can carry tax, banking, and contact detail. The radar reads the vendor name and nothing else.

## `whoami`

Returns `user_guid`, `email`, and `organization_guid` for the authenticated user. Used for the preflight scope line and for `--mine`.
