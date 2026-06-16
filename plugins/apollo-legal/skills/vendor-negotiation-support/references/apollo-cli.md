# Apollo CLI

Use the `apollo` CLI when vendor domain or company data would improve negotiation leverage.

## Setup Check

```bash
which apollo
apollo auth
apollo usage credits
```

If `apollo` is missing, install it with Homebrew:

```bash
brew install apolloio/apollo-io-cli/apollo-io-cli
```

Authenticate before searching. If auth fails, ask the user to run the auth flow.

## Company Lookup

Search by vendor domain:

```bash
apollo companies search --domains <domain> --format json
```

Fetch the selected organization:

```bash
apollo companies get --id <org_id> --format json
```

Use the returned revenue, headcount, funding, industry, and company-size fields only as
directional context. Cite the command or source field used.

## Credit Safety

Run `apollo usage credits` before operations that may consume credits. Ask for user approval
before enrichment or bulk lookup if it consumes credits. Prefer non-enrichment company search
and get commands when they answer the negotiation question.
