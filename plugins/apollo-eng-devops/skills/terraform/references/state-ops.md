# Tricky State Situations

Prefer code-based fixes (reviewable in a PR) over CLI state edits.

## Rename or Move a Resource

Use a `moved` block, not `state mv`:

```hcl
moved {
  from = google_project_iam_member.old
  to   = google_project_iam_member.new
}
```

Plan must show "has moved", with no destroy and create.

## Adopt an Existing Resource

Use an `import` block (Terraform 1.5+) so the PR shows it:

```hcl
import {
  to = google_storage_bucket.b
  id = "my-project/my-bucket"
}
```

Run `terraform plan -generate-config-out=generated.tf` to draft config, then trim it. Check the provider docs for the import ID format.

## Stop Managing Without Destroying

Use a `removed` block (1.7+) with `lifecycle { destroy = false }`. Fallback: `terraform state rm <addr>` locally against the remote backend. This is a state mutation, so confirm first and take a state version note.

## Rollback

TFC keeps state versions. Restoring one is a workspace admin action in the UI. Always record the current state version ID before any state edit.

## Gotchas

- Remote runs in TFC use the workspace's pinned Terraform version, which may differ from your local one. Match it (`tfenv use`).
- `-target` plans are not a fix. They leave drift behind.
- IAM `_member` vs `_binding` vs `_policy` resources fight each other if mixed on the same target.
