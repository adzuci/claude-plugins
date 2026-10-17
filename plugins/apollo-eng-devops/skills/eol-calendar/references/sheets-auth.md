# Sheets Auth For `--push`

An API key cannot write to a Google Sheet (keys only read public data). Writing
needs OAuth or a service account. The supported path is **service account
impersonation**: no key file, and your own `gcloud` login is the audit trail.

## One-Time Setup (DevOps)

Create the service account through the devops Terraform repo, not by hand, so
it is reviewed. Pick a DevOps-owned GCP project (confirm which one); the
commands below show what Terraform should produce.

1. Enable the API and create the service account:

   ```bash
   gcloud services enable sheets.googleapis.com --project PROJECT
   gcloud iam service-accounts create eol-calendar --project PROJECT \
     --display-name "EOL calendar Sheets writer"
   ```

1. Share the Sheet with `eol-calendar@PROJECT.iam.gserviceaccount.com` as
   **Editor** (Sheet → Share). It needs no project IAM roles for the Sheet itself.
   If Drive sharing policy blocks service accounts, ask IT to allow it for this
   Sheet.

1. Let the engineers who will refresh the Sheet mint tokens for it:

   ```bash
   gcloud iam service-accounts add-iam-policy-binding \
     eol-calendar@PROJECT.iam.gserviceaccount.com --project PROJECT \
     --member "group:GROUP@apollo.io" --role roles/iam.serviceAccountTokenCreator
   ```

## Each Run

```bash
gcloud auth application-default login          # once per machine/day
pip install google-auth requests pyyaml          # once
export EOL_SHEETS_SA=eol-calendar@PROJECT.iam.gserviceaccount.com
python scripts/eol_calendar.py --push SHEET_ID --dry-run
python scripts/eol_calendar.py --push SHEET_ID
```

`SHEET_ID` is the long id in the Sheet URL (`/spreadsheets/d/<SHEET_ID>/edit`).

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `403 ... caller does not have permission` | Sheet not shared with the service account | Share it as Editor |
| `403 ... iam.serviceAccounts.getAccessToken` | Not a Token Creator on the SA | Add the binding above |
| `403 ... Sheets API has not been used` | API not enabled in the SA's project | `gcloud services enable sheets.googleapis.com` |
| `invalid_scope` or "app blocked" without `--impersonate` | Workspace blocks the Sheets scope for the default gcloud OAuth client | Use impersonation, or paste the Apps Script instead |

## Fallbacks

- **Apps Script paste:** no auth; see `SKILL.md`.
- **Claude Google Sheets connector:** if your Claude workspace has it enabled,
  Claude can edit the Sheet in place. The Google Drive connector alone cannot
  edit cell contents.
