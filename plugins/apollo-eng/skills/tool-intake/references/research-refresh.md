# Research Refresh

Refresh the assessment after the caller interview so the final report reflects the best available evidence, not the order in which facts arrived.

1. Build a draft evidence map for identity, approval, intended use, data, permissions, pricing, company or OSS maturity, Apollo overlap, policies, and process links.
1. Search Apollo sources with Glean CLI first. Use exact tool and vendor names for approval, Apps DB, owner, Zip, Security, Legal, and existing-tool queries. Open only the strongest results.
1. Search `#zip-help-desk`, `#security-requests`, and the current Legal request channel for the exact identity. Link only matching requests.
1. Use primary public sources for the product, pricing, security, privacy, terms, canonical repository, releases, company facts, and comparable products. Record when pricing requires a custom quote.
1. Identify the three gaps most likely to change the approval state, test boundary, or Zip packet. Run one targeted follow-up query for each. Ask the caller only when the fact is not discoverable.
1. Replace superseded claims and gaps in the JSON. Do not preserve an old “unknown” after the caller or a source resolved it. Do not duplicate the same fact across sections.
1. Recheck the bottom line, approval scope, next action, safe test, and intake packet together. A broad data or capability scope should produce broader review controls than a synthetic, isolated pilot.
1. Set `generated_at` to the refresh time, validate the JSON, and render the HTML from the refreshed report.

For an approved product, prioritize the exact approved scope, conditions, accountable owner or approvers, Apps DB record, initial request, and support channel. If those sources disagree, show the disagreement and choose `STALE_RECONFIRM` rather than silently broadening approval.
