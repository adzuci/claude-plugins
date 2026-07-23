# Vault Encryption with git-crypt

The `crypt` argument encrypts sensitive vault directories with
[git-crypt](https://github.com/AGWA/git-crypt): files matching `.gitattributes`
patterns are transparently encrypted in git objects (and on the remote) while
staying plaintext in the working tree. Obsidian, the SessionEnd hook, and
Claude Code keep working unchanged.

## What it protects — and what it doesn't

| | |
|---|---|
| File **contents** on GitHub / in git objects | ✅ encrypted |
| **Filenames and directory names** | ❌ visible (`coaching/2026-06-anja.md` stays readable as a path) |
| Commits made **before** enabling (migrate mode) | ❌ old plaintext stays in history; only new commits are encrypted |
| The **local working tree** | ❌ plaintext on disk — that's disk encryption's job (FileVault) |

The fresh-setup scaffold commit contains only empty templates, so nothing
sensitive lands in history on a brand-new vault.

## Key management

- `setup_crypt.py` exports the symmetric key to `<vault-parent>/<name>-vault.gitcrypt.key`
  (never inside the vault; the vault's `.gitignore` also blocks `*.gitcrypt.key`).
- **Store it in your password manager as a document**, e.g. 1Password item
  `"<name>-vault git-crypt key"`. With the 1Password CLI:
  `op document create <keyfile> --title "<name>-vault git-crypt key"`.
- Then **delete the local key file**. Never commit it. Without this key,
  encrypted files are unrecoverable — the key is the rollback artifact.

## Second machine (unlock)

```bash
git clone <remote> <vault>
# download the key from your password manager, then:
python3 scripts/setup_crypt.py --vault <vault> --unlock <keyfile> --apply
rm <keyfile>
```

Until `unlock` runs, encrypted files appear as binary blobs in the working
tree — Obsidian and Claude would read garbage, and the vault-sync script
refuses to commit in that state.

## Default encrypted paths

`memory/`, `sessions/`, `coaching/`, `meetings/`, `raw/`, `handoffs/` —
override with `--paths`. `index.md`, `wiki/`, and templates stay plaintext so
GitHub browsing and diffs keep working for non-sensitive notes.

## Everyday caveats

- GitHub shows encrypted files as binary blobs: no web preview, no readable
  diffs, no search on those paths.
- Merge conflicts in encrypted files can't be resolved in the GitHub UI —
  resolve locally (single-user vaults rarely hit this; the sync script pulls
  with `--rebase --autostash` to minimize divergence).
- `git-crypt status` shows the intended state of every file;
  `git show HEAD:<file> | head -c 9` printing `GITCRYPT` proves a committed
  blob is encrypted.

## Disable / rollback

```bash
# remove the managed block from .gitattributes, then:
git add --renormalize .
git commit -m "chore: disable git-crypt"
```

Files return to plaintext from that commit forward. The key is still needed
to read the older encrypted commits, so keep it in your password manager even
after disabling. No force-push is ever required or issued.
