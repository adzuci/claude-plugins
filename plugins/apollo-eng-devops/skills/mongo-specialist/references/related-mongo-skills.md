# Related Mongo Skills

Use this file to avoid rebuilding the wrong workflow inside `mongo-specialist`.

| Skill | Location | Owns |
| --- | --- | --- |
| `/apollo-eng-devops:check-mongo` | `plugins/apollo-eng-devops/skills/check-mongo` | Read-only first-pass health check for one prod cluster; hands off to `mongo-specialist` on ESCALATE. |
| `/apollo-eng-devops:create-mongo-index` | `plugins/apollo-eng-devops/skills/create-mongo-index` | Read-only planning and handoff for creating Mongo indexes. Not for health or restart triage. |
| `/apollo-eng-devops:incident-response` | `plugins/apollo-eng-devops/skills/incident-response` | Declare, track and communicate when `check-mongo` ESCALATEs or 2+ routers reset. |
| `/apollo-eng-devops:systematic-debugging` | `plugins/apollo-eng-devops/skills/systematic-debugging` | Root-cause method once restart or router evidence is collected. |
| `/apollo-eng-devops:grafana-observability` | `plugins/apollo-eng-devops/skills/grafana-observability` | Alert tuning and gaps (for example alerting on `up==0` or an absent mongos series). |
| `/apollo-eng-devops:check-uptime`, `/apollo-eng-devops:check-apdex` | `plugins/apollo-eng-devops/skills/check-uptime`, `check-apdex` | Site-level uptime and apdex; complementary to Mongo-level `check-mongo`. |
| `/apollo-eng-devops:gameday` | `plugins/apollo-eng-devops/skills/gameday` | Mongo incident tabletop drills from real Apollo failure modes. |
| `/apollo-eng:mongo-pr-guard` | `plugins/apollo-eng/skills/mongo-pr-guard` | PR safety review for Mongo query, sharding, routing, and bulk-write risks — proven-incident patterns only. |
| `mongo-specialist` host-restart triage | `plugins/apollo-eng-devops/skills/mongo-specialist/references/host-restart-triage.md` | Triage for the "MongoDB Host has restarted" alert. |
| `mongo-specialist` review mode | `plugins/apollo-eng-devops/skills/mongo-specialist/references/pr-review-mode.md` | One-stop PR review: delegates to `mongo-pr-guard` for incident patterns, adds an experimental WARN-only general query/schema health pass. |
| `mongo-specialist` router restart | `plugins/apollo-eng-devops/skills/mongo-specialist/references/router-rolling-restart.md` | Human-run rolling mongos restart runbook (memory retained by tcmalloc). |
| `mongo-index-discrepancies` | `leadgenie/.claude/skills/mongo-index-discrepancies` | Checks prod indexes not declared in source and looks for incoming PRs. |
| `mongo-unused-indexes` | `leadgenie/.claude/skills/mongo-unused-indexes` | Processes unused-index emails, `$indexStats`, hide/drop planning. |
| `mongo-shard-collection` | `leadgenie/.claude/skills/mongo-shard-collection` | Shard-key recommendation for new or existing collections. |
| `mongo-analyze-incident` | `leadgenie/.claude/skills/mongo-analyze-incident` | Mongo incident-oriented analysis. |
| `mongo-collection-check` | `jarvis/.agents/skills/mongo-collection-check` | Collection change audit over recent code history. |

## Sharing model

Task-specific skills should reference `mongo-specialist` for shared Mongo facts:

- cluster/client mapping
- Slack channels
- TapData/Mason context
- consult targets
- read-only command templates
- stale-data warnings

Task-specific skills should keep their own workflow logic. For example,
`create-mongo-index` owns index timing gates, while `mongo-unused-indexes` owns hide/drop
cleanup.
