# IAM Workspaces

Applies to workspaces like `gcp-data-platform-iam`.

## Review Checklist

- Any `delete` or `replace` of an IAM resource removes access immediately. Name who loses it.

- Authoritative resources (`_iam_policy`, `_iam_binding`, `_iam_audit_config`) overwrite everything else on the target. Flag them.

- New grants of `owner`, `editor`, `*.admin`, `iam.serviceAccountTokenCreator`, `iam.serviceAccountUser`, or `roles/*admin` need an explicit callout.

- Grants to `allUsers`, `allAuthenticatedUsers`, or external domains are a stop.

- `google_service_account_key` creates a long-lived credential. Flag it.

- Replacing a service account changes its identity and breaks every binding and workload using it.

- Check the workspace is not already locked before merging an IAM PR. A pending apply from an earlier PR will queue behind it.

- Add members to the existing authoritative binding. A competing IAM resource on the same target can strip access on a later apply.

- No documented permission matrix exists for applying or force-unlocking IAM workspaces. Do not assume any DevOps engineer may; confirm with the DevOps/IAM owner when unclear.

## Apply Hygiene

- Apply during a quiet window when many bindings change.
- After apply, spot-check one affected principal if access was removed.
- Lockouts: never remove the last admin binding. Check the plan for it.
