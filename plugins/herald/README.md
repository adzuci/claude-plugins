# Herald

Seven skills that build a complete GTM launch package for Apollo's PLG motion (VSB and SMB self-serve buyers): up to 17 artifacts across positioning, paid, content, social, and lifecycle, scaled to the launch tier.

## Install

```bash
claude plugin install herald@apollo-plugins
```

All skills are manual-only. Start with `/herald:kickoff`.

If you used the old `apolloio/herald` `setup.sh`, remove its symlinked copies so commands aren't listed twice:

```bash
rm -rf ~/.claude/skills/herald:*
```

## Skills

| Skill | Produces | Needs |
| --- | --- | --- |
| `/herald:kickoff` | Workspace + `brief.md` (status tracker, dependency graph, execution plan template). Rerun inside a launch for a status dashboard. | Nothing |
| `/herald:brief` | Strategic sections of `brief.md`, readiness review, legal flags | kickoff |
| `/herald:foundation` | Strategy (positioning, messaging, value props) + audience segmentation | brief |
| `/herald:paid` | Campaign strategy, ad copy variants, landing page brief | foundation |
| `/herald:content` | Blog post, announcement, SEO brief, help center article | foundation |
| `/herald:social` | Social copy with community talking points, visual direction | foundation |
| `/herald:email` | Lifecycle architecture, email copy (MDS modules), in-app notifications, changelog | foundation |

## Launch Tiers

| Tier | Name | Scope |
| --- | --- | --- |
| **T1** | New Product | All skills, all artifacts, all channels |
| **T2** | Major | All skills, all artifacts, selective channel mix |
| **T3** | Minor | Blog + 1 email + social post + in-app. No paid. |
| **T4** | Internal | Changelog + in-app notification only |

## Execution Order

```text
Stage 1:  /herald:kickoff  →  /herald:brief
Stage 2:  /herald:foundation              [skip for T4]
Stage 3 (any order):
          /herald:paid                     [skip for T3, T4]
          /herald:content                  [skip for T4]
          /herald:social                   [skip for T4]
          /herald:email
```

Each skill loads upstream artifacts, outlines and asks for key decisions, then drafts and updates the Artifacts table in `brief.md`. You review inline. When everything is done, fill in the Execution Plan at the bottom of `brief.md`.

## Workspace

Each launch lives in `campaigns/<feature-slug>/` in your working directory:

```text
campaigns/<feature-slug>/
├── brief.md          # Living document: status + brief + execution plan
├── foundation/       # strategy.md, audience.md
├── growth/           # campaign-strategy.md, ad-copy.md, landing-page-brief.md
├── content/          # blog-post.md, launch-announcement.md, seo-brief.md, help-center.md
├── social/           # social-copy.md, visual-direction.md
└── lifecycle/        # architecture.md, emails/, in-app-notifications.md
```

## Shared Context

Every skill reads `references/shared-context.md` first: launch tiers, Apollo brand voice, PLG segments, pricing, competitive landscape, legal-approved metrics, and the copy coherence rule. Skill-specific references live alongside it:

| Reference | Used by |
| --- | --- |
| `legal-marketing-playbook.md` | brief |
| `paid-acquisition-playbook.md`, `ad-copy-guide.md` | paid |
| `content-platform.md` | content |
| `social-platform.md` | social |
| `lifecycle-platform.md`, `activation-platform.md` | email |

Update pricing and approved metrics in `shared-context.md` when they change. `/herald:brief` optionally searches a qmd brain repo for existing feature docs and skips that step if qmd isn't installed.
