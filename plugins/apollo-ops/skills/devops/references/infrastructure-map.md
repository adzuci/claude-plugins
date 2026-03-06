# Apollo Infrastructure Map

Apollo-specific infrastructure topology, data flow, ownership, and Terraform patterns for production operations.

---

## Data Flow

```
MongoDB clusters → Redpanda (CDC via source connectors) → downstream consumers
```

### MongoDB Clusters

| Cluster name | Contents |
|---|---|
| `mongo-main` | Core application data |
| `mongo-accounts` | Account records |
| `mongo-contacts` | Contact records |
| `mongo-customobjects` | Custom object records |
| `mongo-email` | Email records |
| `mongo-emailermessages` | Emailer message records |
| `mongo-noncustomer` | Non-customer data |

**Rule**: Before any MongoDB schema change or cluster-level operation, check Redpanda consumer lag. If consumers are lagging, a schema change that breaks the CDC connector will cause downstream data loss or outage.

### Elasticsearch Clusters

Four ES clusters in both prod and staging:

| Cluster | Primary use |
|---|---|
| `main` | Core search |
| `activities` | Activity feed indexing |
| `field-enrichment` | Field enrichment pipeline |
| `custom-objects` | Custom object search |

Prod clusters: GCP project `indigo-lotus-415`, zone `us-central1-c`.
Staging clusters: internal IPs in `10.129.x.x` range.

### Cloudflare

- Only public ingress path to production
- Multiple tunnel pods running on a **dedicated node pool** — do not drain or cordon this pool without verifying tunnel continuity first
- Separate `gke-cluster-web` handles TLS termination
- Let's Encrypt cert management: owned by Engagement team (Golang tracking domain service)

### Redis

- Present in staging; flushed via `FLUSHALL ASYNC` during the weekly staging refresh
- Do not run `FLUSHALL` against prod

---

## Terraform / devops Repo Structure

Repo: `github.com/apolloio/devops`

Key folders:
- `terraform/` — all infrastructure-as-code
- `ansible/` — configuration management (used for DB provisioning during staging refresh)

### State

Terraform state stored in Terraform Cloud. Every folder containing a `terraform.lock.hcl` file is a separate Terraform state boundary.

### Layout Patterns

| Pattern | Description |
|---|---|
| V1 (legacy) | Resource-type-based: e.g., `/terraform/gcp/iam/` contains all IAM for all envs |
| V2 (current) | Environment/account-based: e.g., `/terraform/gcp/prod/` contains IAM co-located with resources |

When navigating the devops repo, check whether a folder follows V1 or V2 layout before proposing changes. Mixing the patterns in a single PR is a review red flag.

---

## Ownership Model

| Domain | Owner | Scope |
|---|---|---|
| GKE, Cloudflare, Terraform, ES host-level (size/version upgrades), MongoDB host-level | DevOps (Infra) | Infrastructure layer |
| ES app-level (mappings, aliases, ingest pipelines) | BE-Platform (Neil, Ken) | Application layer |
| ES shard counts, index decisions | Search Platform | Data modeling layer |
| Let's Encrypt certs, tracking domain Golang service | Engagement team | Application-specific infra |

ES sharding plan lives at `config/es_sharding_plan` in the `leadgenie` repo (Search Platform owns this).

**Rule**: When an ES issue arises, identify the layer before paging. A red cluster is DevOps. A broken mapping is BE-Platform. A shard count discussion is Search Platform.

---

## Operational Checklists

### Pre-Terraform Apply

- [ ] Is this a V1 or V2 folder? Confirm layout before adding resources
- [ ] Does this change touch a separate Terraform state? (Check for `terraform.lock.hcl` in the target folder)
- [ ] Does the plan output match the intended change — no accidental destroys or replacements?
- [ ] Sensitive resources (IAM, firewall rules, service accounts): second reviewer required before apply
- [ ] For prod: is there a rollback path if apply fails midway? (Terraform state can drift on partial apply)
- [ ] No manual GCP Console changes before or after — keep state in sync

### Before Touching Cloudflare Tunnel Node Pool

- [ ] Confirm the tunnel pod count and which nodes they are scheduled on (`kubectl get pods -n <cloudflare-ns> -o wide`)
- [ ] Verify traffic is routing through tunnels before draining (Cloudflare dashboard or `cloudflared` metrics)
- [ ] Plan for zero-downtime: drain one node at a time; confirm tunnel pods reschedule before proceeding
- [ ] TLS termination lives on `gke-cluster-web` — if changing node pool config, confirm cert serving is unaffected
- [ ] Notify #eng-infrastructure-alerts before starting; post completion or rollback when done

### Before MongoDB Changes

- [ ] Check Redpanda consumer lag for all source connectors on the target cluster
- [ ] Confirm connector configuration: which Mongo collections are captured for this cluster?
- [ ] If lag is non-zero, hold the change until consumers have caught up
- [ ] For schema changes (field renames, collection drops): verify CDC connector will not break downstream consumers
- [ ] After change: monitor Redpanda consumer lag for at least 10 minutes to confirm no new lag accumulation
- [ ] For host-level changes (version upgrades, failovers): coordinate with DevOps; application-level concerns go to BE-Platform

### Data Flow Incident Diagnosis

When data appears stale, missing, or duplicated across services:

1. **Check ES cluster health first** — red/yellow cluster can cause writes to be rejected silently
2. **Check Redpanda consumer lag** — lag on a source connector means Mongo changes are not reaching downstream
3. **Check Mongo oplog** — if the source connector has stalled, look for oplog overflow or connector errors
4. **Check the specific cluster** — `mongo-contacts` issues affect contact search; `mongo-accounts` affects account search; etc.
5. **Check `#eng-infrastructure-alerts`** — if there's an active alert for any of these, treat as known incident, not a new issue
6. **Escalate**: data pipeline issues that span Mongo → Redpanda → ES involve DevOps (infra layer) + BE-Platform (app layer)
