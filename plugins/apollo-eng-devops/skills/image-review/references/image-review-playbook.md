# Image Review Playbook

Exact commands and reference material for the `image-review` skill. Keep `SKILL.md` thin;
put procedural detail here.

## Safe slug generation

Used for temp tags (`image-review-tmp:<slug>-before` / `-after`) and report filenames.
Never `eval` the target string.

1. Take the Dockerfile basename, or the final path component of the image reference, as
   the readable component.
1. Lowercase ASCII uppercase letters.
1. Replace every run of characters outside `[a-z0-9_.-]` with a single `-`.
1. Trim leading/trailing `.`, `_`, `-`. If empty, use `image`.
1. Truncate the readable component to 48 characters.
1. Append `-` plus the first 12 hex characters of a SHA-256 hash of the full canonical
   Dockerfile path or complete image reference (`sha256sum`, or `shasum -a 256` if that's
   unavailable — stop rather than silently drop the collision suffix if neither exists).

```bash
raw="<dockerfile-basename-or-image-final-component>"
readable=$(printf '%s' "$raw" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9_.-]+/-/g; s/^[-_.]+//; s/[-_.]+$//')
[ -z "$readable" ] && readable="image"
readable="${readable:0:48}"
hash=$(printf '%s' "<full-canonical-source-string>" | sha256sum | cut -c1-12)
slug="${readable}-${hash}"
```

## Run directory

```bash
rundir=$(mktemp -d "${TMPDIR:-/tmp}/image-review.XXXXXX")
```

## Preflight

```bash
command -v docker && docker info
command -v dive && dive --version
command -v jq
```

If `dive` is missing, stop and show (do not run) the install path for the detected
platform:

- macOS/Homebrew: `brew install dive`
- Debian/Ubuntu amd64: download the matching `dive_<version>_linux_amd64.deb` from the
  [latest release](https://github.com/wagoodman/dive/releases/latest), then
  `sudo apt install ./dive_<version>_linux_amd64.deb`
- Other platforms: pick the matching asset from the
  [releases page](https://github.com/wagoodman/dive/releases/latest), verify any published
  checksum, extract `dive` onto `PATH`, then confirm with `dive --version`

## Build or pull

```bash
# Dockerfile target — reuse identical context/platform/target/build-args for before+after
docker build -t "image-review-tmp:${slug}-before" \
  -f "<dockerfile-path>" \
  ${platform:+--platform "$platform"} \
  ${target:+--target "$target"} \
  "<build-context-dir>"

# Image reference target
docker pull "<image-ref>"
```

On a private-registry pull failure, tell the operator to run, themselves:

```bash
gcloud auth configure-docker <region>-docker.pkg.dev
```

Do not run it for them.

## Analyze with dive

```bash
dive "image-review-tmp:${slug}-before" --json "${rundir}/${slug}-before.json"

# CI policy check — use the repo's .dive-ci if present, else the fallback baseline below
dive "image-review-tmp:${slug}-before" --ci --ci-config "<path-to-.dive-ci-or-fallback>"
```

A `Result:FAIL` from `--ci` is a normal policy outcome — still produce the full review. A
missing report, invalid config, Docker failure, or JSON parse error is an execution
failure — stop and report it, do not guess at conclusions.

### `.dive-ci` schema (upstream contract)

```yaml
rules:
  lowestEfficiency: 0.95
  highestWastedBytes: 20MB
  highestUserWastedPercent: 0.20
```

- `lowestEfficiency`, `highestUserWastedPercent`: ratios from `0` to `1`.
- `highestWastedBytes`: accepts `B`, `KB`, `MB`, `GB`.
- `highestUserWastedPercent` excludes the base image layer.

Use this as the fallback baseline (label it `upstream-example baseline` in output, not a
repo policy) when the target repo has no `.dive-ci`.

## Extract evidence (fields dive actually exports)

The exact field name for the wasted-file list has changed across dive versions
(`fileReference` in some, `inefficientFiles` in others). Verify against the installed
`dive --version` before trusting either name, and use `try`/`//` so a schema mismatch
produces an empty result instead of a `jq` error:

```bash
jq '.image | {sizeBytes, efficiencyScore, inefficientBytes}' "${rundir}/${slug}-before.json"

jq '(try .image.fileReference catch []) + (try .image.inefficientFiles catch [])
    | sort_by(.sizeBytes) | reverse | .[:10]
    | map({file, count, sizeBytes})' "${rundir}/${slug}-before.json"

jq '.layer | sort_by(.sizeBytes) | reverse | .[:10]
    | map({index, sizeBytes, command})' "${rundir}/${slug}-before.json"
```

Dive's exporter defines `.image.{sizeBytes,efficiencyScore,inefficientBytes}` and
`.layer[].{index,sizeBytes,command}` consistently; the wasted-file list's key name is the
one field that has moved between versions — confirm it against the report itself
(`jq '.image | keys' <report>`) rather than assuming. There is no per-layer wasted-byte
field — do not invent one. Correlate layer `command` values to Dockerfile instructions
best-effort; label ambiguous BuildKit history as such.

## Before/after comparison

After an approved fix is rebuilt to `-after` and re-exported to
`${rundir}/${slug}-after.json`:

```bash
jq -s '
  .[0].image as $before |
  .[1].image as $after |
  {
    before: ($before | {sizeBytes, efficiencyScore, inefficientBytes}),
    after: ($after | {sizeBytes, efficiencyScore, inefficientBytes}),
    delta: {
      sizeBytes: ($after.sizeBytes - $before.sizeBytes),
      efficiencyScore: ($after.efficiencyScore - $before.efficiencyScore),
      inefficientBytes: ($after.inefficientBytes - $before.inefficientBytes)
    }
  }
' "${rundir}/${slug}-before.json" "${rundir}/${slug}-after.json"
```

## Cleanup

```bash
docker rmi "image-review-tmp:${slug}-before" "image-review-tmp:${slug}-after" 2>/dev/null
rm -rf "${rundir}"
```

Track the exact tags/paths this run created. Never remove the operator's original image or
any pre-existing tag. If cleanup fails, report the exact leftover names/paths — don't
retry with `--force` and don't silently move on.

## Anti-pattern → fix catalog

For every entry applied, state: the exact evidence supporting it (dive output, `docker history`, or Dockerfile inspection), whether the expected benefit is image size, wasted
bytes, build cache/context, or reproducibility, the functional risk, and why it applies
given the target's existing multi-stage/`.dockerignore` setup (don't recommend a pattern
that's already handled).

### Install and cleanup split across layers

Deletion in a later layer doesn't remove bytes added in an earlier one.

```dockerfile
# Before
RUN apt-get update
RUN apt-get install -y curl build-essential
RUN rm -rf /var/lib/apt/lists/*

# After
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl build-essential \
 && rm -rf /var/lib/apt/lists/*
```

If `build-essential` is only needed to compile, prefer a build stage instead of keeping it
in the runtime image.

### Temporary download removed in a later layer

```dockerfile
# Before
RUN curl -fsSL "$TOOL_URL" -o /tmp/tool.tar.gz
RUN tar -xzf /tmp/tool.tar.gz -C /usr/local/bin
RUN rm -f /tmp/tool.tar.gz

# After
RUN curl -fsSL "$TOOL_URL" -o /tmp/tool.tar.gz \
 && tar -xzf /tmp/tool.tar.gz -C /usr/local/bin \
 && rm -f /tmp/tool.tar.gz
```

Require checksum/signature verification if the target repo's supply-chain policy expects
it.

### Recursive ownership change after `COPY`

```dockerfile
# Before
COPY . /app
RUN chown -R app:app /app

# After
COPY --chown=app:app . /app
```

Confirm the builder supports `COPY --chown` and that ownership semantics are preserved.

### Dependency manifests copied after all source

Build-cache/context improvement — don't promise a dive score change from this alone.

```dockerfile
# Before
WORKDIR /app
COPY . .
RUN npm ci
RUN npm run build

# After
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build
```

Adapt to the actual package manager. Don't change lockfile behavior as part of this.

### Build toolchain retained in the runtime image

```dockerfile
# Before
FROM golang:1.24
WORKDIR /src
COPY . .
RUN CGO_ENABLED=0 go build -trimpath -o /server ./cmd/server
ENTRYPOINT ["/server"]

# After
FROM golang:1.24 AS build
WORKDIR /src
COPY . .
RUN CGO_ENABLED=0 go build -trimpath -o /out/server ./cmd/server

FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=build /out/server /server
USER nonroot:nonroot
ENTRYPOINT ["/server"]
```

Treat the runtime base as an example, not an Apollo-approved default. Preserve required
certs, libraries, and runtime compatibility. If the target already has stages, optimize
its existing final-stage boundary rather than adding another one.

### Package-manager cache retained

```dockerfile
# Before
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN rm -rf /root/.cache/pip

# After
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

Use the equivalent no-cache flag for the actual package manager in use.

### Missing or incomplete `.dockerignore`

Mostly a build-context/cache improvement — only changes final image size if ignored files
would otherwise have been copied in.

```dockerignore
.git
.gitignore
node_modules
coverage
tmp
*.log
.env*
```

Never replace an existing `.dockerignore` wholesale — propose the smallest additive edit
and preserve existing comments and `!` negations (e.g. `!fixtures/required.env`).

### Unpinned or overly broad base image

Reproducibility/supply-chain improvement, not inherently a dive efficiency fix.

```dockerfile
# Before
FROM node:latest

# After
FROM node:22-bookworm-slim@sha256:<verified-current-digest>
```

Resolve the real digest from the approved registry at implementation time — never invent
one. Validate architecture/runtime compatibility. Report expected dive impact as unknown
unless the replacement was actually measured.

## `.dive-ci` as a follow-up, not part of this run

If the target repo lacks `.dive-ci` and the review demonstrates stable, repeatable value,
propose adding it as a **separate**, owner-approved change that also wires `dive --ci`
into that repo's CI — thresholds calibrated against representative current images,
documented rationale, started as a regression guard rather than failing legacy images
outright. Don't bundle this into the Dockerfile optimization PR unless the repo owner
explicitly asks for it. Adding `.dive-ci` without a CI invocation enforces nothing.
