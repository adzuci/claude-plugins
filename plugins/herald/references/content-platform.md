# Apollo Content Platform Reference

Source of truth for Apollo's owned content publishing: where content gets published, in what format, who owns it, and how SEO is planned. `herald:content` should reference this doc when planning blog posts, help center articles, and SEO briefs so deliverables match the systems they ship into.

> **As of:** April 2026. Verify with the Content team if anything looks stale.

______________________________________________________________________

## Publishing platforms

Apollo publishes owned content into three distinct surfaces, each on a different system with a different format requirement.

| Surface | Platform | Format | Owner | Use |
|---------|----------|--------|-------|-----|
| `/magazine` blog | ButterCMS (custom CMS) | Rich text (paragraphs, headings, bullets, blockquotes — no Markdown-only constructs) | Content team (human-written) | **Launch posts**, strategic narratives, customer stories |
| `/insights` blog | Programmatic — Google Sheet → frontend automation | AI-agent-generated, published automatically by frontend engineering's automation | Content / AI agents | High-volume SEO/AEO content at scale |
| Help Center | Zendesk | HTML | CX / Content | How-to articles, troubleshooting, getting-started guides |

### Launch posts default to `/magazine`

`herald:content` is **scoped to `/magazine`-style launch posts only**. The AI content agent produces `/insights` content separately on its own cadence — launch skills should not generate `/insights` briefs or try to slot launches into the `/insights` automation. If a launch genuinely warrants additional scaled SEO support beyond the launch moment, flag it to the Content team as a separate ask.

### Format expectations per skill output

| Skill artifact | Required format | Why |
|---|---|---|
| `blog-post.md` | ButterCMS-ready rich text | The Content team will paste the post into ButterCMS; rich-text constructs translate cleanly. Avoid Markdown-only syntax (e.g., reference-style links, fenced code blocks). |
| `help-center.md` | HTML | Zendesk requires HTML. Don't write Markdown and assume conversion. |
| `seo-brief.md` | Markdown (working doc) | Internal brief; format is for human reading. |
| `launch-announcement.md` | Markdown (working doc) | Internal brief used by multiple channels. |

______________________________________________________________________

## SEO keyword strategy

Apollo maintains a **curated set of non-brand, sales-related SEO keywords** that the Content team has researched and loaded into the AI content agents. The agents are trained on SEO and AEO (answer engine optimization) best practices for automated content creation at scale.

**Implication for `herald:content`:**

- New launch SEO briefs should **align the launch to existing keywords from the curated set**, not invent fresh keywords per launch.
- If the launch concept doesn't map cleanly to a curated keyword, **flag the gap to the Content team** in the SEO brief — don't silently invent a new target.
- Don't re-research keywords from scratch when the curated set already covers the topic space.

The actual curated keyword list lives outside this repo (in the AI content agent's configuration). When in doubt, ask the user to point at the relevant subset for the launch domain, or flag that the SEO brief needs Content team input to confirm the target.

______________________________________________________________________

## Gold-standard examples (house style)

These three `/insights` posts are house-style references for tone, structure, and the practitioner-to-practitioner voice that Apollo content uses. Read them when calibrating a new blog post or SEO brief — the same voice and structure apply to `/magazine` launch posts.

- <https://www.apollo.io/insights/what-are-high-ticket-sales>
- <https://www.apollo.io/insights/what-factors-affect-sales>
- <https://www.apollo.io/insights/how-to-find-hiring-manager-email>

Apollo voice rules in `apollo-voice.md` (Blog Posts section) apply to both `/magazine` and `/insights` content.

______________________________________________________________________

## What this reference does NOT cover

- **Paid landing pages** — see `paid-acquisition-playbook.md` and the landing page brief artifact in `paid-copy`.
- **In-app copy and notifications** — see `activation-platform.md`.
- **Email content** — see `lifecycle-platform.md`.
- **Press releases / investor content** — different voice and approval flow; see `legal-marketing-playbook.md` and `apollo-company-fact-sheet-feb-2026.md`.

______________________________________________________________________

## Known unknowns / open questions

- **Curated keyword list location** — the actual list of curated SEO keywords is not in this repo. If the user needs the skill to pick a specific keyword, they should point at the source or confirm with Content.
- **`/insights` request channel** — if a launch deserves a `/insights` companion piece, the path to request it from the AI content agent is owned by Content team and not documented here.
- **Help center publishing approval** — who signs off on a help center article before it goes live in Zendesk.
