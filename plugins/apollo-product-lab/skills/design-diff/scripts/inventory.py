#!/usr/bin/env python3
"""Deterministic half of the design diff: what the Fabric Studio prototype and the production
package each contain, side by side, so the reviewer judges gaps instead of hunting for them.

usage: inventory.py <prototype-module-dir> <production-package-src>
                    [--exclude <path-relative-to-prototype>]... [--expect-branch <name>] [--out file.md]

- Both directories must exist; a missing one is an error, never an empty inventory.
- Nothing is excluded unless the caller names it with --exclude (the skill takes the list from the
  owning package's docs/base.md). Every exclusion is printed in the report.
- The header records each side's git branch, commit, and whether the tree was dirty, so the report
  can be tied to the revision that was actually compared (and --expect-branch fails on a mismatch).
- Pairing is by name and is a starting point: candidates are listed on both sides; no production
  file is dropped from the unmatched list until a human confirms the pairing.
- Copy extraction is a regex sample (JSX text, label/title/placeholder/aria-label props, react-intl
  defaultMessage). It is navigation for the reviewer, not proof of constrained-copy coverage.
No LLM, no network.
"""
import json, os, re, sys, pathlib, collections, subprocess

def die(msg): print(f"inventory: {msg}", file=sys.stderr); sys.exit(2)

def git_state(path):
    def g(*a):
        try: return subprocess.run(['git', '-C', str(path), *a], capture_output=True, text=True, check=True).stdout.strip()
        except Exception: return None
    top = g('rev-parse', '--show-toplevel')
    if not top: return {'repo': None}
    dirty = g('status', '--porcelain', '--', str(path)) or ''
    return {'repo': top, 'branch': g('rev-parse', '--abbrev-ref', 'HEAD'), 'commit': g('rev-parse', '--short=12', 'HEAD'),
            'dirty_files': len([l for l in dirty.splitlines() if l.strip()])}

def rel(p, root): return str(pathlib.Path(p).relative_to(root))

def tsx_files(root, excluded):
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d != 'node_modules' and str((pathlib.Path(dp)/d).relative_to(root)) not in excluded]
        for f in fn:
            if f.endswith(('.tsx', '.ts')) and not f.endswith(('.test.tsx', '.test.ts', '.stories.tsx', '.d.ts')):
                yield pathlib.Path(dp) / f

FABRIC_IMPORT = re.compile(r"import\s*\{([^}]*)\}\s*from\s*'@apolloio/fabric(?:-core)?(?:/[a-z]+)?'")
JSX_TEXT = re.compile(r">\s*([A-Z][^<>{}\n]{3,120}?)\s*<")
PROP_TEXT = re.compile(r"\b(?:label|title|placeholder|aria-label|description|content)=(?:\"([^\"]{3,160})\"|'([^']{3,160})')")
DEFINE_MESSAGES = re.compile(r"defaultMessage:\s*(?:\"((?:[^\"\\]|\\.)*)\"|'((?:[^'\\]|\\.)*)'|`([^`]*)`)")

def fabric_components(text):
    names = set()
    for m in FABRIC_IMPORT.finditer(text):
        for n in m.group(1).split(','):
            n = n.strip().split(' as ')[0].strip()
            if n and n[0].isupper(): names.add(n)
    return names

def scan(root, excluded=()):
    comps, strings, messages = {}, collections.Counter(), set()
    for f in tsx_files(root, set(excluded)):
        t = f.read_text(errors='ignore')
        comps[rel(f, root)] = sorted(fabric_components(t))
        if f.name.endswith('.messages.ts'):
            for m in DEFINE_MESSAGES.finditer(t): messages.add(next(g for g in m.groups() if g is not None))
        elif f.suffix == '.tsx':
            for s in JSX_TEXT.findall(t):
                s = s.strip()
                if not s.startswith(('{', '$')): strings[s] += 1
            for m in PROP_TEXT.finditer(t):
                strings[(m.group(1) or m.group(2)).strip()] += 1
    return comps, strings, messages

def stem(name):
    base = pathlib.Path(name).stem.replace('.module', '')
    return re.sub(r'(Route|Page|Modal|Dialog|Card|Panel|Button|Toast|List|Table|Flow|Wizard)$', '', base).lower()

def main():
    argv = sys.argv[1:]
    excludes, out, expect = [], None, None
    pos = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == '--exclude': excludes.append(argv[i+1].strip('/')); i += 2
        elif a == '--out': out = argv[i+1]; i += 2
        elif a == '--expect-branch': expect = argv[i+1]; i += 2
        else: pos.append(a); i += 1
    if len(pos) != 2: die(__doc__.strip().splitlines()[3])
    proto, prod = pathlib.Path(pos[0]).resolve(), pathlib.Path(pos[1]).resolve()
    for p, what in ((proto, 'prototype module'), (prod, 'production source')):
        if not p.is_dir(): die(f"{what} does not exist: {p}")
    for e in excludes:
        if not (proto / e).exists(): die(f"--exclude {e} does not exist under the prototype; refusing to record a phantom exclusion")
    pg, dg = git_state(proto), git_state(prod)
    if expect and pg.get('branch') != expect: die(f"prototype checkout is on {pg.get('branch')!r}, expected {expect!r}")

    L = ["# Design diff inventory", ""]
    for label, p, g in (("Prototype", proto, pg), ("Production", prod, dg)):
        if g.get('repo'):
            L.append(f"- {label}: `{p}` — branch `{g['branch']}` @ `{g['commit']}`" + (f", **{g['dirty_files']} uncommitted file(s) under this path**" if g['dirty_files'] else ", clean"))
        else: L.append(f"- {label}: `{p}` — not a git checkout (revision unknown)")
    L += ["- Exclusions (declared by the caller, none inferred): " + (", ".join(f"`{e}`" for e in excludes) if excludes else "none"), ""]
    manifest = proto / 'prototype.manifest.json'
    if manifest.exists():
        m = json.loads(manifest.read_text())
        L += [f"## Prototype routes ({m.get('label','')})", "", "| Route | Group | Surface | Entry |", "|---|---|---|---|"]
        for r in m.get('routes', []): L.append(f"| `{r['path']}` | {r.get('group')} | {r.get('surface')} | `{r.get('entry')}` |")
        L.append("")
    else: L += ["## Prototype routes", "", "No `prototype.manifest.json` found; routes unknown.", ""]
    pc, ps, _ = scan(proto, excludes)
    dc, _, dm = scan(prod)
    for title, comps in (("Prototype components", pc), ("Production components", dc)):
        L += [f"## {title} ({len(comps)} files)", "", "| File | fabric-core imports |", "|---|---|"]
        for f in sorted(comps): L.append(f"| `{f}` | {', '.join(comps[f]) or '—'} |")
        L.append("")
    prod_by_stem = collections.defaultdict(list)
    for f in dc: prod_by_stem[stem(f)].append(f)
    L += ["## Name-based pairing (candidates only; a human confirms each row)", "", "| Prototype | Production candidate(s) |", "|---|---|"]
    for f in sorted(pc):
        c = prod_by_stem.get(stem(f), [])
        L.append(f"| `{f}` | {', '.join(f'`{x}`' for x in c) or '**none**'} |")
    L += ["", "Production files (all; those also listed as a candidate above are marked):", ""]
    cands = {x for f in pc for x in prod_by_stem.get(stem(f), [])}
    for f in sorted(dc): L.append(f"- `{f}`" + (" — candidate pair above" if f in cands else ""))
    L += ["", "## Copy (regex sample, not coverage)", "",
          f"Prototype strings found: {sum(ps.values())} ({len(ps)} distinct). Production react-intl defaultMessages: {len(dm)}.", "",
          "Prototype strings with no exact production message (i18n port list; also where constrained copy may have been softened, to be checked verbatim in the component):", ""]
    for s, n in sorted(ps.items(), key=lambda kv: -kv[1]):
        if s not in dm: L.append(f"- {s!r}{' ×'+str(n) if n>1 else ''}")
    L += ["", "## Not covered here", "", "Required-state coverage (empty, loading, error, permission-denied, disconnected, keyboard paths), SCSS, and copy passed through helpers are outside this scan. The skill's state matrix is the completion criterion; this file is navigation.", ""]
    text = "\n".join(L) + "\n"
    if out: pathlib.Path(out).write_text(text); print(f"wrote {out}")
    else: print(text)

if __name__ == '__main__': main()
