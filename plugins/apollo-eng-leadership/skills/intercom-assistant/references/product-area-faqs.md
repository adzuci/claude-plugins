# Product Area FAQs

Use this reference in `live`, `monitor`, and `triage` for questions about the Apollo API or the Chrome extension. It is read-only: verify and route; do not mutate any account settings.

Post-Fin context: Fin handles the standard how-to questions, so a human on these threads usually has an issue Fin could not resolve (broken integration, rate limit hit, extension stopped working). Lead with what to verify, not with a help-center link.

## Apollo API

- **Developer docs**: `https://apolloio.github.io/apollo-api-docs/`
- **API key location**: Settings > Integrations > API
- **Rate limits**: vary by plan tier. Verify the account's plan in GodMode before quoting a specific limit.
- **Common errors**:
  - 401 Unauthorized: invalid or missing API key; the customer should regenerate the key in Settings.
  - 429 Too Many Requests: rate limit hit; advise the customer to add backoff/retry logic and verify their plan tier.
  - 422 Unprocessable Entity: request body issue; the customer should cross-check the docs for required fields.
- **Complex or account-specific API issues** (wrong data returned, webhook failures, bulk-export errors): route to the technical support queue.

## Chrome Extension

- **Update path**: Chrome Web Store -> Apollo.io extension -> Update. Most issues are resolved by updating.
- **LinkedIn DOM changes**: after a LinkedIn update, the extension may stop injecting on LinkedIn pages until Apollo ships a patch. This is a known intermittent cause; confirm whether Apollo has an open incident or patch in progress.
- **Extension not loading after update**: try disabling and re-enabling the extension, then reload the page.
- **Export limits**: Chrome extension exports count against the account's export credit balance. Verify in GodMode before advising more exports.

## Guardrail

Read-only. Suggest the fix or route. Do not reset API keys, change rate-limit settings, or mutate the account.
