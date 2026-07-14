# Related Mongo Skills

Use this file to avoid rebuilding the wrong workflow inside `mongo-specialist`.

| Skill | Location | Owns |
| --- | --- | --- |
| `/apollo-eng-devops:create-mongo-index` | `plugins/apollo-eng-devops/skills/create-mongo-index` | Read-only planning and handoff for creating Mongo indexes. |
| `/apollo-eng-devops:gameday` | `plugins/apollo-eng-devops/skills/gameday` | Mongo incident tabletop drills from real Apollo failure modes. |
| `/apollo-eng:mongo-pr-guard` | `plugins/apollo-eng/skills/mongo-pr-guard` | PR safety review for Mongo query, sharding, routing, and bulk-write risks. |
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
