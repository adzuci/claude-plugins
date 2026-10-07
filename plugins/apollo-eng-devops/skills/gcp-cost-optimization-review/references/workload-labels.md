# Workload Label Vocabulary

Valid `infra_workload` values (from `terraform/gcp` label definitions, 2026-09): `elasticsearch`,
`gke`, `mail-server`, `mongo`, `pritunl`, `redis`. Valid `infra_cluster` values (31 total in
terraform): `accounts`, `activities-v1`, `agent-platform`, `ai-tooling`, `contacts`,
`custom-objects`, `custom-objects-v1`, `email`, `emailermessages`, `es8-activities`,
`es8-custom-objects`, `es8-field-enrichment`, `es8-main`, `field-enrichment-v1`, `kafka-connect`,
`leadgenie-web`, `main`, `main-v1`, `mongo-pritunl`, `noncustomer`, `ops`, `pocus-udm-mongo`,
`pritunl`, `production`, `ratelimiter`, `redis-db`, `staging`, `staging-dualstack`,
`staging-sandbox`, `va-mongo`, `va-mongo-canary`. An unrecognized `workload=` value prints a
warning and continues **unscoped**. An unrecognized `/cluster` value drops only the cluster filter and
keeps the valid workload scope. Neither is a hard failure.
