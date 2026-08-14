#!/usr/bin/env python3
"""GKE cluster version + EOL report for the kubernetes-specialist skill.

Lists every known Apollo GKE cluster's Kubernetes version, flags clusters on a
past-EOL (or soon-EOL) minor version using live data from endoflife.date, and
can optionally run `kubent` (read-only deprecated-API scan) against flagged
clusters.

Design notes:
- All functions that shell out or hit the network take an injectable
  ``runner``/``fetcher`` callable so tests can feed canned data without real
  gcloud/kubent/network calls. Defaults shell out via subprocess / urllib.
- Pure helpers (EOL flagging, table rendering) live at module scope with no
  I/O so they can be imported and unit-tested directly.
- Read-only against GCP: `gcloud container clusters list`, `gcloud projects
  list`, `gcloud container clusters get-credentials` (local kubeconfig
  context switch only), and `kubent` (read-only scan). Never runs `apply`,
  `delete`, or `drain`.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Callable, Sequence

Runner = Callable[[Sequence[str]], str]
Fetcher = Callable[[str], bytes]

SCRIPT_DIR = Path(__file__).resolve().parent
CLUSTERS_FILE = SCRIPT_DIR / "gke_clusters.json"
EOL_API_URL = "https://endoflife.date/api/v1/products/kubernetes/"
EOL_CACHE_FILE = Path(os.environ.get("TMPDIR", "/tmp")) / "gke-versions-eol-cache.json"
EOL_CACHE_TTL_SECONDS = 24 * 60 * 60
EOL_SOON_WINDOW_DAYS = 60

PAST_EOL = "PAST_EOL"
EOL_SOON = "EOL_SOON"
FLAG_LABELS = {PAST_EOL: "\U0001f534 **PAST EOL**", EOL_SOON: "\U0001f7e1 EOL soon", None: ""}
FLAG_SORT_ORDER = {PAST_EOL: 0, EOL_SOON: 1, None: 2}


class GkeReportError(RuntimeError):
    """Raised when `gcloud`/`kubent` is missing or returns a nonzero exit code."""


def _subprocess_runner(argv: Sequence[str]) -> str:
    try:
        proc = subprocess.run(list(argv), capture_output=True, text=True, check=False)
    except FileNotFoundError as exc:
        raise GkeReportError(f"`{argv[0]}` not found on PATH.") from exc
    if proc.returncode != 0:
        raise GkeReportError(f"`{' '.join(argv)}` exited {proc.returncode}: {proc.stderr.strip()}")
    return proc.stdout


def _url_fetcher(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=10) as resp:  # noqa: S310 (fixed https URL)
        return resp.read()


# --- inventory ---------------------------------------------------------------------


def load_seed_projects(path: Path = CLUSTERS_FILE) -> list[dict]:
    data = json.loads(path.read_text())
    return data["projects"]


# --- gcloud wrappers -----------------------------------------------------------------


def list_clusters(project: str, runner: Runner | None = None) -> list[dict]:
    """Return parsed rows from `gcloud container clusters list --project P --format=json`.

    Projects without the GKE API enabled (403 "has not been used") are treated as
    having zero clusters rather than raising, since the seed/--refresh scan expects
    to hit plenty of non-GKE projects.
    """
    runner = runner or _subprocess_runner
    try:
        raw = runner(
            ["gcloud", "container", "clusters", "list", "--project", project, "--format=json"]
        )
    except GkeReportError as exc:
        if "has not been used" in str(exc) or "PERMISSION_DENIED" in str(exc):
            return []
        raise
    rows = json.loads(raw or "[]")
    return [
        {
            "project": project,
            "name": row["name"],
            "location": row.get("location") or row.get("zone"),
            "master_version": row["currentMasterVersion"],
            "node_version": row["currentNodeVersion"],
            "status": row["status"],
        }
        for row in rows
    ]


def list_all_projects(runner: Runner | None = None) -> list[str]:
    runner = runner or _subprocess_runner
    raw = runner(["gcloud", "projects", "list", "--format=value(projectId)"])
    return [line.strip() for line in raw.splitlines() if line.strip()]


# --- EOL data ------------------------------------------------------------------------


def fetch_eol_data(
    fetcher: Fetcher | None = None,
    cache_file: Path = EOL_CACHE_FILE,
    ttl_seconds: int = EOL_CACHE_TTL_SECONDS,
    now: float | None = None,
) -> dict:
    """Fetch Kubernetes release EOL data from endoflife.date, cached to disk.

    Returns the raw `result` dict from the API's v1 schema (a `releases` list); use
    `eol_lookup()` to turn it into a {minor_version: release} map.
    """
    now = time.time() if now is None else now
    if cache_file.exists():
        try:
            cached = json.loads(cache_file.read_text())
            if now - cached.get("_fetched_at", 0) < ttl_seconds:
                return cached["result"]
        except (json.JSONDecodeError, KeyError):
            pass  # fall through and refetch

    fetcher = fetcher or _url_fetcher
    result = json.loads(fetcher(EOL_API_URL))["result"]
    try:
        cache_file.write_text(json.dumps({"_fetched_at": now, "result": result}))
    except OSError:
        pass  # best-effort cache; not fatal if the cache dir isn't writable
    return result


def eol_lookup(eol_result: dict) -> dict[str, dict]:
    """Map minor version string (e.g. "1.34") -> release dict from the EOL API result."""
    return {release["name"]: release for release in eol_result.get("releases", [])}


# --- flagging (pure) -------------------------------------------------------------------


def minor_version(full_version: str) -> str:
    """"1.34.9-gke.1065000" -> "1.34" """
    return ".".join(full_version.split(".")[:2])


def flag_for_version(
    full_version: str,
    eol_by_minor: dict[str, dict],
    today: date,
    soon_window_days: int = EOL_SOON_WINDOW_DAYS,
) -> tuple[str | None, str | None]:
    """Return (flag, eol_date_str) for a cluster's master version.

    flag is PAST_EOL, EOL_SOON, or None (still supported, or the minor isn't in the
    EOL dataset yet — e.g. a brand-new release).
    """
    release = eol_by_minor.get(minor_version(full_version))
    eol_from = release.get("eolFrom") if release else None
    if not eol_from:
        return None, None
    eol_date = datetime.strptime(eol_from, "%Y-%m-%d").date()
    if eol_date <= today:
        return PAST_EOL, eol_from
    if eol_date - today <= timedelta(days=soon_window_days):
        return EOL_SOON, eol_from
    return None, eol_from


# --- rendering (pure) ------------------------------------------------------------------


def render_report(rows: list[dict]) -> str:
    """Render clusters as a markdown table, flagged rows (PAST_EOL, then EOL_SOON) first."""
    ordered = sorted(rows, key=lambda r: FLAG_SORT_ORDER.get(r.get("flag"), 2))
    lines = [
        "| Project | Cluster | Location | Master Version | Node Version | Status | EOL Date | Flag |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in ordered:
        lines.append(
            "| {project} | {name} | {location} | {master_version} | {node_version} | "
            "{status} | {eol_date} | {flag_label} |".format(
                project=r["project"],
                name=r["name"],
                location=r["location"],
                master_version=r["master_version"],
                node_version=r["node_version"],
                status=r["status"],
                eol_date=r.get("eol_date") or "—",
                flag_label=FLAG_LABELS.get(r.get("flag"), ""),
            )
        )
    return "\n".join(lines) + "\n"


# --- kubent --------------------------------------------------------------------------


def kubent_context_name(project: str, location: str, cluster: str) -> str:
    return f"gke_{project}_{location}_{cluster}"


def run_kubent(project: str, cluster: str, location: str, runner: Runner | None = None) -> str:
    """get-credentials then run kubent (both read-only) against one cluster."""
    runner = runner or _subprocess_runner
    try:
        runner(
            [
                "gcloud",
                "container",
                "clusters",
                "get-credentials",
                cluster,
                "--project",
                project,
                "--location",
                location,
            ]
        )
    except GkeReportError as exc:
        return f"Could not get credentials for {cluster} ({project}): {exc}"

    context = kubent_context_name(project, location, cluster)
    try:
        return runner(["kubent", "--context", context, "-o", "json", "-e"])
    except GkeReportError as exc:
        if "not found on PATH" in str(exc):
            return (
                "kubent is not installed. Install it with `brew install kubent` "
                "(see https://github.com/doitintl/kube-no-trouble for other platforms)."
            )
        return f"kubent scan failed for {cluster}: {exc}"


# --- report assembly -------------------------------------------------------------------


def build_report(
    projects: list[dict],
    runner: Runner | None = None,
    fetcher: Fetcher | None = None,
    today: date | None = None,
) -> tuple[str, list[dict]]:
    today = today or date.today()
    eol_by_minor = eol_lookup(fetch_eol_data(fetcher=fetcher))
    rows: list[dict] = []
    for p in projects:
        for cluster in list_clusters(p["project"], runner=runner):
            flag, eol_date = flag_for_version(cluster["master_version"], eol_by_minor, today)
            cluster["flag"] = flag
            cluster["eol_date"] = eol_date
            rows.append(cluster)
    return render_report(rows), rows


# --- CLI ---------------------------------------------------------------------------


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--versions", action="store_true", help="Print the GKE version/EOL report (default)."
    )
    parser.add_argument(
        "--project", help="Only report on this GCP project (skips the seed inventory)."
    )
    parser.add_argument(
        "--cluster", help="With --kubent, only scan this cluster (requires --project/--location)."
    )
    parser.add_argument("--location", help="Cluster location/zone, used with --cluster.")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Also probe every visible GCP project for clusters missing from gke_clusters.json.",
    )
    parser.add_argument(
        "--kubent", action="store_true", help="Run kubent against flagged clusters after the report."
    )
    args = parser.parse_args(argv)

    projects = [{"project": args.project, "env": "adhoc"}] if args.project else load_seed_projects()

    report, rows = build_report(projects)
    print(report)

    if args.refresh:
        known = {p["project"] for p in projects}
        print("\n## --refresh: projects with GKE clusters not in gke_clusters.json\n")
        found_new = False
        for project in list_all_projects():
            if project in known:
                continue
            clusters = list_clusters(project)
            if clusters:
                found_new = True
                names = ", ".join(c["name"] for c in clusters)
                print(f"- `{project}`: {names}")
        if not found_new:
            print("(none found)")

    if args.kubent:
        if args.cluster:
            if not args.project or not args.location:
                print("--kubent --cluster requires --project and --location", file=sys.stderr)
                return 2
            targets = [{"project": args.project, "name": args.cluster, "location": args.location}]
        else:
            targets = [r for r in rows if r.get("flag") in (PAST_EOL, EOL_SOON)]
        if not targets:
            print("\nNo flagged clusters to scan with kubent.")
        for r in targets:
            print(f"\n## kubent: {r['name']} ({r['project']})\n")
            print(run_kubent(r["project"], r["name"], r["location"]))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
