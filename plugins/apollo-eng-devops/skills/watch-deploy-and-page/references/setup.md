# Preflight Setup Reference

Read this when `/apollo-eng-devops:watch-deploy-and-page` preflight reports something missing.
Name what is missing, give the caller the exact command below, and stop or degrade as the skill's
Step 0 table says. Do not work around a missing prerequisite by skipping the step it gates.

## `gh` — GitHub CLI

Required. Without it there is no way to resolve a PR to a merge commit or to read the
`Production deployment` workflow runs.

```bash
gh auth status
gh auth login --git-protocol ssh --web   # if unauthenticated
```

For install and SSH-remote setup, use `/apollo-eng:gh-setup`.

Every `gh` call in this skill takes `-R apolloio/leadgenie`, so `gh` does not need to be run from
a leadgenie checkout. Access to the `apolloio` org is required — request it via
`/apollo-it:comp-access-request` if `gh -R apolloio/leadgenie repo view` returns a 404.

## Prod kubectl context

Required. The skill only ever reads (`get deployment`, `rollout status`).

```bash
kubectl config get-contexts | grep gke_indigo-lotus-415_us-central1-c_prod
kubectl --context gke_indigo-lotus-415_us-central1-c_prod -n leadgenie get deployment rails-api -o name
```

If the context is absent:

```bash
gcloud container clusters get-credentials prod --project indigo-lotus-415 --location us-central1-c
```

`get-credentials` only writes the local kubeconfig; it changes nothing in the cluster.

If the context exists but the read times out, this is almost always the **prod VPN** — a separate,
more restricted VPN than staging. Report that rather than retrying in a loop. Cluster access
itself is granted through `/apollo-it:comp-access-request`.

## Grafana MCP

Optional. Without it the skill still verifies the deploy, then reports
`live, performance unverified` and never pages.

```bash
claude mcp get grafana
claude mcp add --transport http --scope user grafana https://grafana-mcp.ops-gcp.apollo.io/mcp
```

Restart Claude Code after adding — MCP tool namespaces load at session start. Apollo VPN may be
required to reach the Grafana MCP server.

## Paging route

Optional for a one-shot run; **required before arming an unattended watch**. This skill does not
own paging — it delegates to the `page` skill, which owns route selection, the approval gate, and
the check that a page actually notified someone.

Check whether it is installed:

```bash
ls ~/.claude/skills/page/SKILL.md
```

`page` is currently a personal skill, not a marketplace plugin, so a fresh Apollo engineer will
not have it. If it is missing, the caller has two workable options:

1. **Run report-only.** Pass `--no-page`. The verdict is still produced; nobody is woken.

1. **Set up a personal PagerDuty route first.** A page needs a service whose escalation policy
   targets exactly the intended recipient. Self-assigning an incident on a shared service
   auto-acknowledges it at creation and notifies **nobody** — the incident looks correct in the
   API while the phone stays silent. Verify any new route once before trusting it:

   ```bash
   pd rest:get -e "/incidents/<id>/log_entries" | grep notify_log_entry
   ```

   No `notify_log_entry` means nobody was told, whatever the incident status says.

Never hand-roll a `pd` send from this skill, and never page a shared on-call rotation for one
engineer's own deploy watch. If no route is available, say so in the report instead of
downgrading silently to a desktop notification the recipient will not see while asleep.

## Repo checkout

The ancestry check in Step 2 (`git merge-base --is-ancestor`) needs a local leadgenie clone.
Resolution order, in full:

1. `git rev-parse --show-toplevel` when cwd is already a leadgenie checkout — confirm with
   `git -C "$REPO" remote get-url origin | grep apolloio/leadgenie`.
1. `$LEADGENIE_DIR` when it is set and passes the same remote check.
1. Ask the caller for the path.

Do not guess a conventional path such as `~/code/apolloio/leadgenie`. Checkout locations differ
per engineer, and a wrong path produces an "unknown revision" error that is easy to misread as
"the commit is not deployed".
