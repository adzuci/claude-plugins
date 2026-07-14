# Mongo Clusters

This file is stale-prone. It captures useful current context, but Apollo Mongo routing
changes over time. Before important production decisions, verify against
`leadgenie/config/mongoid.yml`, DevOps Terraform, and a live Rails console.

## Known leadgenie clients

Observed from `leadgenie/config/mongoid.yml` during skill creation:

| Mongoid client | Cluster intent / known cluster | Database |
| --- | --- | --- |
| `default` | main | `leadgenie_default_production` |
| `noncustomer_default` | noncustomer | `leadgenie_default_production` |
| `people` | noncustomer | `leadgenie_people_production` |
| `scraped_web_pages` | noncustomer | `leadgenie_scraped_web_pages_production` |
| `organizations` | noncustomer | `leadgenie_organizations_production` |
| `places` | main | `leadgenie_places_production` |
| `enrichment_statuses` | main | `leadgenie_enrichment_statuses_production` |
| `performance_insensitive_customer_data` | email | `leadgenie_default_production` |
| `performance_insensitive_noncustomer_data` | email | `leadgenie_noncustomer_default` |
| `accounts` | accounts | `leadgenie_accounts_production` |
| `contacts` | contacts | `leadgenie_contacts_production` |
| `emailermessages` | emailermessages | `leadgenie_emailermessages_production` |
| `custom_objects` | custom-objects | `leadgenie_default_production` |

## Prod mongos clusters

Single source of truth is `MONGOS_CLUSTERS` in `leadgenie/config/application.rb`
(verified at skill authoring; re-check the constant before acting):

| Cluster | Port | mongos count | Notes |
| --- | --- | --- | --- |
| `main` | 27017 | 16 | `default`/`places`/`enrichment_statuses` clients; `max_mongos_per_pod: 2` |
| `noncustomer` | 27017 | 12 | `noncustomer_default`/`people`/`scraped_web_pages`/`organizations`; `max_mongos_per_pod: 2`. Also fronts a change-stream router observed live |
| `email` | 27018 | 6 | backs `performance_insensitive_customer_data` and `performance_insensitive_noncustomer_data` clients |
| `accounts` | 27019 | 6 | |
| `contacts` | 27019 | 6 | |
| `emailermessages` | 27019 | 6 | |
| `custom-objects` | 27019 | 6 | `custom_objects` client, database `leadgenie_default_production` |

mongos hostnames are generated as
`mongos-<cluster>-<n>.us-central1-c.c.indigo-lotus-415.internal:<port>` for
`n = 0..count-1` (e.g. `mongos-noncustomer-3.us-central1-c.c.indigo-lotus-415.internal:27017`).
`<CLUSTER>_MONGOS_HOST` env vars can override the generated list.

### Pod → mongos distribution

`get_mongos_distribution` (in `application.rb`, called from `mongoid.yml`) pins each Rails
process to a **subset** of a cluster's mongos rather than all of them — so a single sick
mongos only affects the pods pinned to it. In prod, for clusters with ≥ 6 mongos:

- **Web pods** (`*-api`, not sidekiq) take the **first half** of the mongos list; sidekiq
  and cron take the **second half**.
- Each half is then chunked into groups of `max_mongos_per_pod`, and the pod is hashed
  (SHA1 of hostname) onto one group.
- Only `main` and `noncustomer` pass `max_mongos_per_pod: 2` (pairs); every other cluster
  uses the default of **3**. So the "pods run in pairs" pattern — first-half pairs
  `(0,1),(2,3),(4,5)…` for web — is specific to `main`/`noncustomer`.

Implication for triage: when one mongos is sick, only the pods hashed onto its group fail;
retries from other pods succeed. This is why partial-pod impact is common and why a mass
pod restart (which re-rolls the hashing) can re-trigger a connection storm — see
`live-incident-mode.md` §6.

### Staging endpoints

Staging uses SRV records, not the internal mongos host list
(`leadgenie/config/mongoid.yml`). Each cluster resolves to
`mongodb+srv://<cluster>-active-cluster.staging-gcp.apollo.io`, or the
`-passive-cluster` variant when `SHADOW_MONGO` is set (e.g.
`noncustomer-active-cluster.staging-gcp.apollo.io` /
`noncustomer-passive-cluster.staging-gcp.apollo.io`). Staging DB names match prod because
staging is restored from a prod backup.

## Verification rules

- A client name can be misleading. Confirm the actual hosts/replica set/cluster before
  reasoning about blast radius.
- For a model, ask Rails for the actual database, collection, and cluster rather than
  guessing from the model name.
- For infra work, verify Terraform under DevOps production Mongo paths such as
  `terraform/gcp/prod/mongo-main`, `mongo-noncustomer`, `mongo-email`,
  `mongo-accounts`, `mongo-contacts`, `mongo-emailermessages`, and
  `mongo-custom-objects`.

## Canonical architecture references

- Mongo Architecture Overview:
  `https://app.notion.com/p/6a691e7869524469b39f3414cea5c4e3?pvs=1`
- MongoDB 7.0 upgrade epic:
  `https://apollopde.atlassian.net/browse/INFRA-1528`
