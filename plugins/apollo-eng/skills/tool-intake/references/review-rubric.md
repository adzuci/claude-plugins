# Unknown-Tool Review Rubric

Review only the dimensions relevant to the target. Separate verified facts, reasonable inference, and missing evidence.

| Dimension | Questions |
| --- | --- |
| Identity | Who publishes it? Which domain, repository, package, version, and delivery model are in scope? |
| Install and update | What executes during install? Are there post-install hooks, native code, auto-updates, or remote bootstrap scripts? |
| Supply chain | Are releases pinned, signed, checksummed, maintained, and traceable to the publisher? What dependencies execute code? |
| Access | Can it read repositories, files, environment variables, SSH keys, browser sessions, OAuth tokens, or cloud credentials? |
| Data | Could employee, customer, prospect, source-code, production, email, recording, or analytics data enter the tool? |
| Egress | What endpoints receive telemetry, crash data, prompts, payloads, callbacks, or model requests? Can egress be disabled? |
| Retention and AI use | What is retained, where, for how long, by which subprocessors, and for training or service improvement? |
| Legal and commercial | What license or click-through terms apply? Is a DPA, contract, paid plan, or jurisdiction review likely? |
| Customer trust and brand | Who owns or controls the vendor, where can Apollo data be processed, and could jurisdiction, sanctions, public incidents, or undisclosed data movement create customer-facing trust risk? |
| Apollo fit | Does an approved vendor, internal platform, library, or skill already solve the problem? Who owns it? |
| Operations | What support, availability, incident, deletion, export, and offboarding controls exist? |
| Maturity and market | For OSS, what are the current stars, license, maintainers, and latest release? For a company, what are its location, founding year, disclosed funding or ownership, pricing, and relevant comparable products? |

## Delivery-Specific Checks

For a CLI or OSS tool, explicitly check:

- what prompt, conversation, file, and tool-call content reaches each selected model provider or gateway;
- local and shared-server persistence, including databases, logs, artifacts, and session history;
- usable telemetry opt-out controls, not only the vendor's statement that telemetry exists;
- credential discovery, environment access, repository mounts, connectors, sandboxes, and update behavior.

For a SaaS product, explicitly check:

- what code, configuration, models, weights, inputs, outputs, logs, metrics, and secrets are uploaded or retained;
- API-key and OAuth scope differences, preferring the narrowest team-scoped credential only after review;
- external storage, mirroring, caching, webhooks, subprocessors, regions, deletion, and retention;
- whether an OSS SDK or CLI is only a client for the SaaS product. Link it as an ancillary component without letting it dominate the SaaS assessment.

Treat an internal vendor-intake, contract, MNDA, or Security thread as `in review` unless the controlled approval source contains an exact current approval. Never turn review activity into approval.

Do not infer geopolitical or brand risk from a person's nationality, a company name, or office location. Use verified ownership/control, data-flow, hosting, subprocessor, regulatory, or incident evidence. When an AI provider or its data processing is controlled from a jurisdiction Apollo has decided not to engage, name the verified fact and route it to Legal rather than making a categorical claim about a country or its people.

## Completeness Gate

Before finalizing, account for every relevant delivery-specific check with verified evidence, a labeled inference, or a precise gap. Do one targeted official-source search for each unresolved high-risk path. Do not stop at a repository README when the project has dedicated deployment, telemetry, security, storage, credential, or data-handling documentation.

For a CLI, the report is incomplete until it addresses model-provider payload flow, local/shared persistence, credential discovery, update behavior, and usable telemetry controls. For SaaS, it is incomplete until it addresses code/model/input ingress, external storage or mirroring, key scopes, logs and metrics, retention, deletion, and subprocessors. If evidence remains unavailable, name the source or query checked and why it did not answer the question.

## Low-Risk Test Shape

Shape lightweight exploratory testing around Apollo Security's interim guidance:

- synthetic data only;
- isolated disposable environment;
- a clean environment and blank folder;
- no Apollo confidential data, customer data, PII, credentials, repositories, browser profiles, email, or recordings;
- pinned version and reviewed installer/source;
- egress blocked by default or explicitly allowlisted and observed;
- no corporate integrations, unvetted extensions or plugins, OAuth consent, production connections, or Apollo credentials;
- post-run filesystem and network inspection, teardown, and artifact removal.

Make the plan concrete for the tool. Name the safest command or example workload, disabled integrations, egress boundary, cleanup action, and credentials that must not exist. For SaaS, include account/team isolation, deployment deactivation, and test-key revocation when relevant. For a CLI, start with a blank folder and prefer source review, `--help`, or `--version` before any connected workflow.

If the tool cannot be meaningfully tested under these controls, state what Legal, Security, Procurement, or IT needs to resolve before a useful test. Treat a new AI vendor or a materially new use case as requiring Legal and Security review.
