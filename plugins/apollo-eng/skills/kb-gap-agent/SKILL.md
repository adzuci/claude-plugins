---
name: kb-gap-agent
description: Engineering wrapper for KB gap detection. Use only when the user explicitly invokes /apollo-eng:kb-gap-agent or asks where the KB gap agent moved.
disable-model-invocation: true
---

# `kb-gap-agent` — Engineering Wrapper

The canonical KB gap detection skill moved to Support ownership:

```text
/apollo-support:support-kb-gap-agent
```

Use that skill for stale, missing, or drifted KB article detection across branch diffs, PRs, time ranges, product surfaces, PRDs, Jira epics, quick audits, or batch audits.

If `apollo-support` is not installed, tell the user to install or enable the Apollo Support plugin, then re-run:

```text
/apollo-support:support-kb-gap-agent
```

Do not duplicate the KB gap workflow here. This wrapper exists only to preserve discoverability for existing engineering users while the skill ownership moves to Support.
