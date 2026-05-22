# Apollo Template with Counterparty Redlines — Sub-workflow

When Phase 0 classifies the uploaded document as an Apollo NDA template with the
counterparty's tracked changes, follow this sub-workflow instead of the normal Ironclad scan
and redline pipeline.

- Skip Phases 1–4 entirely (no Ironclad scan, no download, no PDF conversion needed).
- Go directly to **Phase 5 — Analyze and Redline**, with the modified workflow below.

## 5a — Read the NDA Text with Tracked Changes Visible

```bash
pandoc --track-changes=all '<uploaded_file_path>' -o /tmp/nda-working/uploaded-redlines.md
```

Read the markdown carefully. The counterparty's tracked changes are their proposed edits.

## 5b — Classify Each Counterparty Change

For every tracked change (insertion or deletion) made by the counterparty, apply the Apollo
NDA Playbook (Phase 5d) and the Core Philosophy (Phase 5c) to decide:

| Decision | Action |
|----------|--------|
| **ACCEPT** — change is acceptable under the playbook and minimal-redlines philosophy | Accept the counterparty's change: remove deletion markup and keep their insertion as clean text. In the output DOCX this section will appear clean with no tracked changes. |
| **REJECT** — change is not acceptable under the playbook | Reject the counterparty's change: restore the original Apollo language using Apollo Legal's tracked changes (delete their insertion, restore their deletion). |
| **MODIFY** — change is partially acceptable but needs adjustment | Reject their version and insert Apollo's preferred alternative using tracked changes. |

## 5c — Generate the Reviewed DOCX

Produce a DOCX where:
- Accepted counterparty changes appear as clean text (no markup)
- Rejected or modified changes appear as Apollo Legal tracked changes showing the
  corrected language
- The author on all Apollo Legal tracked changes is `Apollo Legal`
- No comments or annotations are added to the document body

Save to `~/Downloads/uploaded-reviewed.docx`.

## Wrap-up

Proceed to **Phase 6 (Save and Report)** and **Phase 7 (Update State)** as normal. Use
`"status": "redlines-reviewed"` in the Phase 7 log entry for this document type.
