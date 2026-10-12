# Zip MCP Setup Reference

Use this reference when `/apollo-eng-devops:renewal-radar` needs the Zip MCP but it is missing, unauthorized, or not visible to the current Claude/Codex session — or when a Zip call comes back permission-denied.

## Preflight Checks

For Claude Code:

```bash
claude mcp get zip
```

For Codex:

```bash
codex mcp list
```

If the MCP is configured but the tool namespace is not visible inside the current session, restart Claude Code or Codex (for Claude Code, reconnecting via `/mcp` also works). MCP tool namespaces are loaded at session startup.

## Zip MCP

Zip is required for this skill. There is no cache and no offline mode; if Zip is unavailable, the skill stops. The expected MCP name is:

```text
zip
```

This is a user-scoped remote HTTP server at `https://mcp.zip.com/mcp`, deliberately **not** declared in the plugin manifest, so each engineer authenticates as themselves and sees only what their own Zip permissions allow. It uses OAuth (dynamic client registration + PKCE); the authorization server metadata is at `https://app.ziphq.com/.well-known/oauth-authorization-server`.

Setup:

```bash
claude mcp add --transport http --scope user zip https://mcp.zip.com/mcp
claude mcp login zip
```

`claude mcp login zip` opens the browser for Zip's OAuth flow. You can instead run `/mcp` inside Claude Code and authenticate `zip` there. Verify:

```bash
claude mcp get zip
```

A healthy result reports `Status: ✔ Connected`. Do not ask the user to paste tokens or secrets into the chat.

Tokens expire. If `claude mcp list` shows `zip` as `Needs authentication`, re-run `claude mcp login zip`. A session that was already running when you logged in from the CLI does not pick up the new token on its own; reconnect it via `/mcp`.

Confirm the session's identity and scope with `whoami`, which returns `user_guid`, `email`, and `organization_guid`.

## Permission-Denied Playbook

Zip permissions are granted per object type, and a token that can read agreements does not necessarily read departments. These are known current limitations of typical Apollo engineer access, **not bugs in this skill**. Do not treat them as errors to debug, and do not tell the user something is broken.

Note that `#zip-help-desk` membership itself grants nothing — it's Tyler Davis's team's support channel, open to anyone, for asking Zip questions. The permission grant is a separate Zip permission-group change that Procurement makes; the channel is only where you ask for it. Below, "ask in `#zip-help-desk`" always means the latter.

### Department read denied

`list_departments` fails with a message of this shape:

```text
Error calling tool 'list_departments': Permission(has_permission=False,
reasons={<PermissionResultReason.DEFAULT_NO_ACCESS: -3>}(, Missing department read permission))
```

This is the common case for engineer-level Zip access. Show the user this one line and continue:

```text
Department read unavailable for this token — falling back to unfiltered query with client-side matching.
```

Then follow step 2.3 of the skill: query `list_agreements` without `department_guid` and match the team name client-side against each hit's `department.name`, presenting matched and other-department rows in separate visible buckets.

To get the permission properly rather than living on the fallback, ask in `#zip-help-desk`. It is a Zip permission-group change, not an MCP or Claude Code problem.

### Agreement read scoped to creator

Agreement reads usually succeed but return only agreements the caller created or owns, rather than everything in the department. In practice a query that should show a whole team's contracts comes back with a handful of rows and a small `total`, all with the caller's own email in `creator.email`.

There is no error and nothing to fix in the skill. The correct response is the scope caveat the skill always prints: the result is a floor, not a complete inventory. Contracts filed by Procurement or by another engineer will not appear.

Two ways to widen it:

- Have other owners on the team run the skill themselves and compare.
- Ask `#zip-help-desk` for broader agreement read on the department.

### Vendor read denied

If `list_vendors` is also denied, the vendor sweep in step 3 cannot run. Say so in one line and continue with the agreement results. Do not silently omit the sweep — an absent sweep and an empty sweep mean different things.

## Fallback Behavior

If the `zip` tool namespace is entirely absent, stop before producing any digest. Print the setup commands above and say plainly that no renewal data was retrieved. Never reconstruct a digest from memory, prior sessions, or inference.
