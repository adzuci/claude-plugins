# Changelog

## [1.3.0](https://github.com/apolloio/claude-plugins/compare/apollo-eng-devops-v1.2.0...apollo-eng-devops-v1.3.0) (2026-08-31)


### Features

* add glean-cli bridge to devops skill ([#230](https://github.com/apolloio/claude-plugins/issues/230)) ([968805e](https://github.com/apolloio/claude-plugins/commit/968805e6ad9cbe148403a65cb130b226de6bca10))
* **apollo-eng-devops:** add k8s-safe-exec — advisory-by-default safety gate for cluster one-offs ([#234](https://github.com/apolloio/claude-plugins/issues/234)) ([f31a412](https://github.com/apolloio/claude-plugins/commit/f31a412cb0734b77250e65f4d21462fb3fccb39c))


### Bug Fixes

* **oncall-handoff:** resolve daily shift to most recently completed one ([#237](https://github.com/apolloio/claude-plugins/issues/237)) ([e014df3](https://github.com/apolloio/claude-plugins/commit/e014df3c0494f0818959debcf29b120aeccec6a8))

## [1.2.0](https://github.com/apolloio/claude-plugins/compare/apollo-eng-devops-v1.1.0...apollo-eng-devops-v1.2.0) (2026-08-20)


### Features

* add es-specialist skill codifying es8 latency RCA methodology ([#198](https://github.com/apolloio/claude-plugins/issues/198)) ([e7fcdc8](https://github.com/apolloio/claude-plugins/commit/e7fcdc880565b69a3de95a9cb8712f3af8b219a7))
* **apollo-eng-devops:** add --versions GKE cluster EOL report to kubernetes-specialist ([#197](https://github.com/apolloio/claude-plugins/issues/197)) ([ad89197](https://github.com/apolloio/claude-plugins/commit/ad89197eae0df18f262c57b536872e139cfbf9bd))
* **apollo-eng-devops:** add image-review skill for dive-based Dockerfile efficiency review ([#223](https://github.com/apolloio/claude-plugins/issues/223)) ([fcd12c9](https://github.com/apolloio/claude-plugins/commit/fcd12c93b65ddcae991772300782adf354089be2))
* **apollo-eng-devops:** cron OOM remediation skill (PLAT-1451) ([#224](https://github.com/apolloio/claude-plugins/issues/224)) ([57b6109](https://github.com/apolloio/claude-plugins/commit/57b6109f5521b7a5ff79f94690568d039b635fea))
* **apollo-eng-devops:** harden wtf-does-this-do triage skill ([#203](https://github.com/apolloio/claude-plugins/issues/203)) ([aef06a5](https://github.com/apolloio/claude-plugins/commit/aef06a5cf7c5ead104204cdbc78142254005a8f5))
* **apollo-eng, apollo-eng-devops:** Mongo hint/partial-index check + gated PR review mode ([#219](https://github.com/apolloio/claude-plugins/issues/219)) ([16d2197](https://github.com/apolloio/claude-plugins/commit/16d2197bb51755461b23fbfd909870902fe72cd3))
* **apollo-eng:** HarnessBench skill-eval pilot — auto-pr staging skill, fixtures, CI (INFRA-2087) ([#182](https://github.com/apolloio/claude-plugins/issues/182)) ([aaf9611](https://github.com/apolloio/claude-plugins/commit/aaf9611b09e2593b210fa2a6a8d0af32f1488382))


### Bug Fixes

* align apollo-eng-devops skill routing metadata with actual behavior ([#211](https://github.com/apolloio/claude-plugins/issues/211)) ([abafa9d](https://github.com/apolloio/claude-plugins/commit/abafa9d540cdf090cd21cdfb51281e279782e9bc))

## [1.1.0](https://github.com/apolloio/claude-plugins/compare/apollo-eng-devops-v1.0.0...apollo-eng-devops-v1.1.0) (2026-07-30)


### Features

* **apollo-eng-devops:** add Mongo specialist skills with live-incident mode ([#131](https://github.com/apolloio/claude-plugins/issues/131)) ([2e06f3b](https://github.com/apolloio/claude-plugins/commit/2e06f3bc98c8d7b3ccf82ed989560a457a80b068))
