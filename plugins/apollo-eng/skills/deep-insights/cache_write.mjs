#!/usr/bin/env node
// cache_write.mjs — write side of the deep-insights leaf cache.
//
// The expensive part of the skill is the per-session reviewer fan-out. Each
// reviewer's finding ("leaf") is cached so an unchanged session is never analyzed
// twice: reviewers READ the cache themselves (in the workflow), and this script
// WRITES the leaves back after a run. Keyed by <session>__<fingerprint>.json, where
// the fingerprint changes when the session grows — so a grown session re-analyzes.
//
// Usage:
//   node cache_write.mjs <result.json> [--cache-dir DIR] [--fingerprints <compact.json>]
//   # result.json = the workflow return object (must contain fresh_findings[])
//   # fingerprints source: either the result's own .fingerprints, or a compact.json
//   #   ({fingerprints:{id:fp}}) passed via --fingerprints. A finding with no known
//   #   fingerprint is skipped (can't form a stable key) and reported on stderr.

import { readFileSync, writeFileSync, mkdirSync } from 'node:fs'
import path from 'node:path'
import os from 'node:os'

const argv = process.argv.slice(2)
function flag(name) {
  const i = argv.indexOf(name)
  return i >= 0 ? argv[i + 1] : undefined
}
const positional = argv.filter(
  (a, i) => !a.startsWith('--') && (i === 0 || !argv[i - 1].startsWith('--')),
)
const resultPath = positional[0]
if (!resultPath) {
  process.stderr.write('cache_write: need a result.json path\n')
  process.exit(1)
}
const cacheDir =
  flag('--cache-dir') ||
  path.join(os.homedir(), '.claude', 'deep-insights', 'cache')

const result = JSON.parse(readFileSync(resultPath, 'utf8'))
const findings = Array.isArray(result.fresh_findings) ? result.fresh_findings : []

// fingerprint map: prefer an explicit --fingerprints compact.json, else the
// result's own .fingerprints (the SKILL threads the enumerator's map through).
let fingerprints = result.fingerprints || {}
const fpPath = flag('--fingerprints')
if (fpPath) {
  try {
    const c = JSON.parse(readFileSync(fpPath, 'utf8'))
    fingerprints = c.fingerprints || fingerprints
  } catch {
    /* keep whatever we had */
  }
}

mkdirSync(cacheDir, { recursive: true })
let wrote = 0
const skipped = []
for (const f of findings) {
  const id = f && f.session
  const fp = id && fingerprints[id]
  if (!id || !fp) {
    if (id) skipped.push(id)
    continue
  }
  const out = path.join(cacheDir, `${id}__${fp}.json`)
  writeFileSync(out, JSON.stringify(f))
  wrote++
}

process.stderr.write(
  `cache_write: wrote ${wrote} leaf finding(s) to ${cacheDir}` +
    (skipped.length
      ? ` (skipped ${skipped.length} with no known fingerprint)\n`
      : '\n'),
)
process.stdout.write(String(wrote) + '\n')
