#!/usr/bin/env python3
"""
gantt_generator.py v2 — Quarterly engineering Gantt chart generator.

Features:
  - Per-project design days, experiment weeks, and dependencies
  - On-call rotation (all engineers, weekly round-robin, Mon–Sun)
  - Separate eng and design overhead multipliers
  - 2 parallel engineers for 10+ dev-day projects
  - Designer row in resource view
  - Capacity analysis with overflow detection and additional-eng estimate

Usage:
  python3 gantt_generator.py --csv projects.csv,resourcing.csv [options]
  python3 gantt_generator.py --sheet <google-sheets-url> [options]

Options:
  --start YYYY-MM-DD          Chart start date (default: 2026-05-01)
  --end   YYYY-MM-DD          Chart end date   (default: 2026-10-31)
  --eng-multiplier  FLOAT     Eng overhead multiplier  (default: 2.0)
  --design-multiplier FLOAT   Design overhead multiplier (default: 1.5)
  --output PATH               Output HTML path (default: gantt.html in CWD)
"""

import argparse, csv, io, json, math, html as html_lib, sys, urllib.request, re, heapq
from collections import defaultdict
from datetime import date, timedelta


# ─── CLI ──────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser()
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--csv")
    src.add_argument("--sheet")
    p.add_argument("--start", default="2026-05-01")
    p.add_argument("--end",   default="2026-10-31")
    p.add_argument("--eng-multiplier",    dest="eng_mult",    default=2.0, type=float)
    p.add_argument("--design-multiplier", dest="design_mult", default=1.5, type=float)
    p.add_argument("--output", default="gantt.html")
    p.add_argument("--debug", action="store_true", help="Print scheduling trace and gap analysis to stderr")
    return p.parse_args()


# ─── Data loading ─────────────────────────────────────────────────────────────

def read_file(path):
    with open(path.strip(), newline="", encoding="utf-8-sig") as f:
        return f.read()

def parse_csv_text(text):
    return list(csv.DictReader(io.StringIO(text.strip())))

def col(row, *names):
    lk = {k.strip().lower(): k for k in row}
    for n in names:
        if n.lower() in lk:
            return lk[n.lower()]
    return None

def is_projects_text(text):
    first = text.split("\n")[0].lower()
    return "project" in first and ("rank" in first or "effort" in first or "eng" in first)

def load_data(args):
    if args.sheet:
        m = re.search(r'/d/([a-zA-Z0-9_-]+)', args.sheet)
        if not m:
            sys.exit("Cannot extract sheet ID from URL")
        sid = m.group(1)
        texts = []
        for name, gid in [("Projects", "0"), ("Resourcing", "1")]:
            fetched = False
            for url in [
                f"https://docs.google.com/spreadsheets/d/{sid}/gviz/tq?tqx=out:csv&sheet={name}",
                f"https://docs.google.com/spreadsheets/d/{sid}/export?format=csv&gid={gid}",
            ]:
                try:
                    with urllib.request.urlopen(url, timeout=10) as r:
                        t = r.read().decode("utf-8")
                    if "<html" not in t.lower():
                        texts.append(t); fetched = True; break
                except Exception:
                    pass
            if not fetched:
                sys.exit(f"Could not fetch '{name}' sheet")
        return texts[0], texts[1]
    else:
        parts = [x.strip() for x in args.csv.split(",", 1)]
        if len(parts) != 2:
            sys.exit("--csv requires two paths: projects.csv,resourcing.csv")
        a, b = read_file(parts[0]), read_file(parts[1])
        return (a, b) if is_projects_text(a) else (b, a)

def load_projects(text):
    rows = [{k.strip(): v.strip() for k, v in r.items()} for r in parse_csv_text(text)]
    out = []
    for row in rows:
        nc  = col(row, "project")
        ec  = col(row, "eng effort (dev days)", "eng effort", "dev days")
        rc  = col(row, "stack rank", "rank")
        cc  = col(row, "category")
        sc  = col(row, "application surface", "surface")
        ddc = col(row, "design effort (design days)", "design effort", "design days")
        ewc = col(row, "experiment runtime (weeks)", "experiment runtime", "experiment weeks")
        dpc = col(row, "dependencies", "dependency", "deps")
        if not nc or not (row.get(nc) or "").strip():
            continue
        try:
            eng_days = int(float(row.get(ec, 0) or 0))
            rank     = int(float(row.get(rc, 999) or 999))
        except (ValueError, TypeError):
            continue
        def pi(c):
            try: return int(float(row.get(c, 0) or 0)) if c else 0
            except: return 0
        design_days = pi(ddc)
        exp_weeks   = pi(ewc)
        deps_raw    = (row.get(dpc) or "").strip() if dpc else ""
        deps        = [d.strip() for d in deps_raw.split(",") if d.strip()]
        out.append({
            "project":      row[nc],
            "category":     (row.get(cc) or "") if cc else "",
            "surface":      (row.get(sc) or "") if sc else "",
            "eng_days":     eng_days,
            "design_days":  design_days,
            "exp_weeks":    exp_weeks,
            "rank":         rank,
            "dependencies": deps,
        })
    return out

def _load_people(text, role_filter):
    """Load people from resourcing CSV, optionally filtering by Role column value."""
    rows = [{k.strip(): v.strip() for k, v in r.items()} for r in parse_csv_text(text)]
    out = []
    for row in rows:
        nc = col(row, "name", "dev", "engineer", "developer") or list(row.keys())[0]
        ac = col(row, "capacity", "% allocation", "allocation", "alloc")
        rc = col(row, "role", "type")
        name = (row.get(nc) or "").strip()
        if not name:
            continue
        if rc:
            role = (row.get(rc) or "").strip().lower()
            if role_filter == "engineer" and role not in ("engineer", "eng", "dev", ""):
                continue
            if role_filter == "designer" and role not in ("designer", "design"):
                continue
        elif role_filter == "designer":
            continue  # No role column means no designers
        raw = ((row.get(ac) or "100") if ac else "100").strip().rstrip("%")
        try:
            pct = float(raw)
            if pct > 1: pct /= 100
        except ValueError:
            pct = 1.0
        out.append({"name": name, "capacity": pct})
    return out

def load_engineers(text):
    return _load_people(text, "engineer")

def load_designers(text):
    return _load_people(text, "designer")


# ─── Calendar helpers ─────────────────────────────────────────────────────────

def build_working_days(start_date, end_date):
    days, d = [], start_date
    while d <= end_date:
        if d.weekday() < 5:
            days.append(d)
        d += timedelta(days=1)
    return days

def build_oncall(working_days, engineers, start_date):
    if not engineers or not working_days:
        return {}
    names = [e["name"] for e in engineers]
    oncall = {n: set() for n in names}
    d = start_date
    while d.weekday() != 0:   # advance to first Monday
        d += timedelta(days=1)
    idx = 0
    while d <= working_days[-1] + timedelta(days=6):
        week_end = d + timedelta(days=6)
        eng = names[idx % len(names)]
        for wd in working_days:
            if d <= wd <= week_end:
                oncall[eng].add(wd)
        idx += 1
        d += timedelta(days=7)
    return oncall

def wd_on_or_after(working_days, target):
    for d in working_days:
        if d >= target:
            return d
    return None

def _weekday_advance(start, n):
    """Return the date that is n weekdays after start (start inclusive if weekday)."""
    d = start
    while d.weekday() >= 5:
        d += timedelta(days=1)
    for _ in range(n - 1):
        d += timedelta(days=1)
        while d.weekday() >= 5:
            d += timedelta(days=1)
    return d

def advance_n(working_days, oncall_set, start_date, n):
    """Count n non-oncall working days from start_date.
    Returns (last_productive_date, next_available_date_or_None).
    None for next means overflow past quarter end; last is the actual end date."""
    si = next((i for i, d in enumerate(working_days) if d >= start_date), None)
    if si is None:
        return _weekday_advance(start_date, n), None
    productive, last = 0, None
    for i in range(si, len(working_days)):
        d = working_days[i]
        if d not in oncall_set:
            productive += 1
            last = d
            if productive >= n:
                nxt = working_days[i + 1] if i + 1 < len(working_days) else None
                return last, nxt
    # Ran out of quarter days — extrapolate remaining weekdays beyond the boundary
    remaining = n - productive
    return _weekday_advance(working_days[-1] + timedelta(days=1), remaining), None


# ─── Topological sort ─────────────────────────────────────────────────────────

def topo_sort(projects):
    by_name = {p["project"]: p for p in projects}
    dependents = defaultdict(list)
    in_degree  = {p["project"]: 0 for p in projects}
    for proj in projects:
        for dep in proj["dependencies"]:
            if dep in by_name:
                in_degree[proj["project"]] += 1
                dependents[dep].append(proj["project"])
    q = []
    for proj in projects:
        if in_degree[proj["project"]] == 0:
            heapq.heappush(q, (proj["rank"], proj["project"]))
    result = []
    while q:
        _, name = heapq.heappop(q)
        result.append(by_name[name])
        for dep in dependents[name]:
            in_degree[dep] -= 1
            if in_degree[dep] == 0:
                heapq.heappush(q, (by_name[dep]["rank"], dep))
    done = {p["project"] for p in result}
    result += sorted([p for p in projects if p["project"] not in done], key=lambda p: p["rank"])
    return result


# ─── Scheduler ────────────────────────────────────────────────────────────────

def run_schedule(projects, engineers, designers, working_days, oncall, eng_mult, design_mult):
    if not working_days:
        return {}
    elig = [e for e in engineers if e["capacity"] > 0]
    sched_log = []  # one entry per project, always collected

    eng_budget    = {}
    for e in engineers:
        non_oc = sum(1 for d in working_days if d not in oncall.get(e["name"], set()))
        eng_budget[e["name"]] = math.floor(non_oc * e["capacity"])

    eng_alloc = {e["name"]: 0 for e in engineers}
    eng_next  = {e["name"]: working_days[0] for e in engineers}

    # Per-designer tracking (no on-call for designers)
    des_budget  = {d["name"]: math.floor(len(working_days) * d["capacity"]) for d in designers}
    des_alloc   = {d["name"]: 0 for d in designers}
    des_next    = {d["name"]: working_days[0] for d in designers}
    des_day_map = {d["name"]: {} for d in designers}
    eng_day_map = {e["name"]: {} for e in engineers}

    phases     = {}
    completion = {}

    for proj in topo_sort(projects):
        pname       = proj["project"]
        eng_days    = proj["eng_days"]
        design_days = proj["design_days"]
        exp_weeks   = proj["exp_weeks"]

        info = {"engineers": [], "overflow": False, "unscheduled": False}
        log = {"project": pname, "rank": proj["rank"], "gates": {}, "design": None, "eng": []}

        # Three separate dependency gates:
        #   dep_design_gate — blocks design start (waits for dep's design to finish)
        #   dep_eng_gate    — blocks eng start    (waits for dep's eng to finish)
        #   dep_exp_gate    — blocks experiment   (waits for dep's full completion)
        # Designers only need the dep's design direction; engineers need the dep built.
        dep_design_gate = working_days[0]
        dep_eng_gate    = working_days[0]
        dep_exp_gate    = working_days[0]
        for dep in proj["dependencies"]:
            dep_info = phases.get(dep, {})
            dep_design_end = dep_info.get("design_end")
            dep_eng_end    = dep_info.get("eng_end")
            dep_completion = dep_info.get("completion") or completion.get(dep)

            # Design gate: only blocked by dep's design phase ending.
            # If dep has no design phase, designers can start immediately (no gate).
            # Eng gate handles the "dep must be built" constraint separately.
            if dep_design_end:
                cand = wd_on_or_after(working_days, dep_design_end + timedelta(days=1))
                if cand and cand > dep_design_gate:
                    dep_design_gate = cand
                    log["gates"]["design"] = f"{dep}.design_end={dep_design_end} → gate={cand}"

            # Eng gate: after dep's eng phase (completion as fallback)
            eg_src = dep_eng_end if dep_eng_end else dep_completion
            eg_src_label = "eng_end" if dep_eng_end else "completion"
            if eg_src:
                cand = wd_on_or_after(working_days, eg_src + timedelta(days=1))
                if cand and cand > dep_eng_gate:
                    dep_eng_gate = cand
                    log["gates"]["eng"] = f"{dep}.{eg_src_label}={eg_src} → gate={cand}"

            # Experiment gate: after dep's full completion (incl. experiment)
            if dep_completion:
                cand = wd_on_or_after(working_days, dep_completion + timedelta(days=1))
                if cand and cand > dep_exp_gate:
                    dep_exp_gate = cand
                    log["gates"]["exp"] = f"{dep}.completion={dep_completion} → gate={cand}"

        # ── Design phase ──────────────────────────────────────────────────
        design_end = None
        if design_days > 0 and designers:
            dc = math.ceil(design_days * design_mult)
            eligible_des = sorted(
                [d for d in designers if des_alloc[d["name"]] + dc <= des_budget[d["name"]]],
                key=lambda d: (wd_on_or_after(working_days, max(des_next[d["name"]], dep_design_gate)) or working_days[-1],
                               -(des_budget[d["name"]] - des_alloc[d["name"]]))
            )
            log["design"] = {
                "dep_gate": str(dep_design_gate),
                "cal_need": dc,
                "designers": [
                    {"name": d["name"], "next_avail": str(des_next[d["name"]]),
                     "budget_remaining": des_budget[d["name"]] - des_alloc[d["name"]]}
                    for d in designers
                ],
                "eligible": len(eligible_des),
                "chosen": eligible_des[0]["name"] if eligible_des else None,
            }
            if not eligible_des:
                info["overflow"] = True
                phases[pname] = info
                completion[pname] = working_days[-1]
                log["overflow"] = True
                sched_log.append(log)
                continue
            chosen_des = eligible_des[0]
            ds = wd_on_or_after(working_days, max(des_next[chosen_des["name"]], dep_design_gate))
            if ds is None:
                info["overflow"] = True
                phases[pname] = info
                completion[pname] = working_days[-1]
                log["overflow"] = True
                sched_log.append(log)
                continue
            ds_last, ds_next = advance_n(working_days, set(), ds, dc)
            info["design_start"]    = ds
            info["design_end"]      = ds_last
            info["designer"]        = chosen_des["name"]
            design_end = ds_last
            if ds_next is None:
                info["overflow"] = True
            des_next[chosen_des["name"]]  = ds_next or (working_days[-1] + timedelta(days=1))
            des_alloc[chosen_des["name"]] += dc
            for d in working_days:
                if ds <= d <= ds_last:
                    des_day_map[chosen_des["name"]][d] = pname
            log["design"]["actual_start"] = str(ds)
            log["design"]["actual_end"]   = str(ds_last)

        # ── Eng phase ─────────────────────────────────────────────────────
        proj_eng_end = design_end

        if eng_days > 0:
            n_eng    = min(2 if eng_days >= 10 else 1, len(elig))
            days_per = math.ceil(eng_days / n_eng)
            cal_need = math.ceil(days_per * eng_mult)

            eng_early_base = (design_end + timedelta(days=1)) if design_end else working_days[0]
            eng_early = wd_on_or_after(working_days, max(eng_early_base, dep_eng_gate))
            if eng_early is None:
                info["overflow"] = True
                phases[pname] = info
                completion[pname] = working_days[-1]
                log["overflow"] = True
                sched_log.append(log)
                continue

            def sort_key(e):
                ea = wd_on_or_after(working_days, max(eng_next[e["name"]], eng_early))
                return (ea or working_days[-1], -(eng_budget[e["name"]] - eng_alloc[e["name"]]))

            cands = sorted(
                [e for e in elig if eng_alloc[e["name"]] + cal_need <= eng_budget[e["name"]]],
                key=sort_key
            )
            if len(cands) < n_eng and n_eng == 2:
                n_eng    = 1
                days_per = eng_days
                cal_need = math.ceil(days_per * eng_mult)
                cands = sorted(
                    [e for e in elig if eng_alloc[e["name"]] + cal_need <= eng_budget[e["name"]]],
                    key=sort_key
                )

            eng_log = {
                "dep_eng_gate":     str(dep_eng_gate),
                "eng_early":        str(eng_early),
                "n_eng":            n_eng,
                "days_per":         days_per,
                "cal_need":         cal_need,
                "budget_eligible":  len(cands),
                "overflow_forced":  False,
                "candidates": [
                    {"name": e["name"],
                     "next_avail": str(eng_next[e["name"]]),
                     "budget_remaining": eng_budget[e["name"]] - eng_alloc[e["name"]],
                     "effective_start": str(wd_on_or_after(working_days, max(eng_next[e["name"]], eng_early)) or "overflow")}
                    for e in elig
                ],
            }
            log["eng"].append(eng_log)

            if not cands:
                # Budget exhausted — assign anyway (project is already overflow).
                # Primary sort: highest capacity first (respect partial-capacity contracts).
                # Secondary sort: earliest estimated finish time (accounting for capacity).
                # This ensures a 50% engineer is only used for overflow when all
                # higher-capacity engineers would finish even later.
                info["overflow"] = True
                def sort_key_overflow(e):
                    ea = wd_on_or_after(working_days, max(eng_next[e["name"]], eng_early))
                    ea_idx = next((i for i, d in enumerate(working_days) if d >= ea), len(working_days)) if ea else len(working_days)
                    finish_idx = ea_idx + int(cal_need / e["capacity"])
                    return (-e["capacity"], finish_idx)
                cands = sorted(elig, key=sort_key_overflow)
                eng_log["overflow_forced"] = True
            if not cands:
                info["unscheduled"] = True
                phases[pname]       = info
                completion[pname]   = working_days[-1]
                log["overflow"] = True
                sched_log.append(log)
                continue

            assigned = cands[:n_eng]
            eng_log["assigned"] = [e["name"] for e in assigned]
            e_starts, e_ends = [], []

            for eng in assigned:
                e_start_base = max(eng_next[eng["name"]], eng_early)
                e_start = wd_on_or_after(working_days, e_start_base)
                if e_start is None:
                    # Eng starts entirely beyond quarter; extrapolate actual end date
                    info["overflow"] = True
                    actual_start = _weekday_advance(e_start_base, 1)
                    e_last = _weekday_advance(actual_start, cal_need)
                    e_starts.append(actual_start)
                    e_ends.append(e_last)
                    e_nxt = _weekday_advance(e_last + timedelta(days=1), 1)
                    eng_next[eng["name"]] = e_nxt
                    eng_alloc[eng["name"]] += cal_need
                    info["engineers"].append(eng["name"])
                    continue
                e_last, e_next = advance_n(
                    working_days, oncall.get(eng["name"], set()), e_start, cal_need
                )
                if e_next is None:
                    info["overflow"] = True
                e_starts.append(e_start)
                e_ends.append(e_last)
                eng_next[eng["name"]]  = e_next or (working_days[-1] + timedelta(days=1))
                eng_alloc[eng["name"]] += cal_need
                info["engineers"].append(eng["name"])
                for d in working_days:
                    if e_start <= d <= e_last:
                        eng_day_map[eng["name"]][d] = pname

            if e_ends:
                info["eng_start"]  = min(e_starts) if e_starts else eng_early
                info["eng_end"]    = max(e_ends)
                proj_eng_end       = info["eng_end"]
                eng_log["actual_eng_start"] = str(info["eng_start"])
                eng_log["actual_eng_end"]   = str(info["eng_end"])

        # ── Experiment phase ───────────────────────────────────────────────
        # Gated on both: own eng_end AND dependency's full completion (dep_exp_gate)
        if exp_weeks > 0 and proj_eng_end:
            exp_s_base = max(proj_eng_end, dep_exp_gate) + timedelta(days=1)
            exp_s = wd_on_or_after(working_days, exp_s_base)
            if exp_s is None:
                exp_s = _weekday_advance(exp_s_base, 1)
            needed = exp_weeks * 5
            # Count within-quarter days first, then extrapolate if needed
            cnt = 0
            exp_e = None
            for d in working_days:
                if d >= exp_s:
                    cnt += 1
                    if cnt >= needed:
                        exp_e = d
                        break
            if exp_e is None:
                remaining = needed - cnt
                exp_e = _weekday_advance(working_days[-1] + timedelta(days=1), remaining) if remaining > 0 else working_days[-1]
                info["overflow"] = True
            elif exp_e > working_days[-1]:
                info["overflow"] = True
            info["exp_start"] = exp_s
            info["exp_end"]   = exp_e
            proj_eng_end      = exp_e

        done = proj_eng_end or dep_eng_gate
        info["completion"] = done
        if done and done > working_days[-1]:
            info["overflow"] = True
        completion[pname] = done
        phases[pname]     = info
        log["completion"] = str(done) if done else None
        log["overflow"]   = info["overflow"]
        sched_log.append(log)

    return {
        "phases":       phases,
        "eng_day_map":  eng_day_map,
        "des_day_map":  des_day_map,
        "oncall":       oncall,
        "eng_budget":   eng_budget,
        "eng_alloc":    eng_alloc,
        "des_budget":   des_budget,
        "des_alloc":    des_alloc,
        "sched_log":    sched_log,
    }


# ─── Debug report ─────────────────────────────────────────────────────────────

def print_debug_report(sched, projects, engineers, designers, working_days):
    pr = lambda *a: print(*a, file=sys.stderr)
    proj_by_name = {p["project"]: p for p in projects}

    pr("=" * 80)
    pr("SCHEDULING TRACE")
    pr("=" * 80)

    for log in sched["sched_log"]:
        pname  = log["project"]
        rank   = log["rank"]
        proj   = proj_by_name.get(pname, {})
        over   = log.get("overflow", False)
        status = "OVERFLOW" if over else "ON TIME"
        pr(f"\n{'─' * 60}")
        pr(f"  [{rank:>2}] {pname}  [{status}]")
        pr(f"       eng={proj.get('eng_days',0)}d  design={proj.get('design_days',0)}d  "
           f"exp={proj.get('exp_weeks',0)}w  deps={proj.get('dependencies',[])}")
        pr(f"{'─' * 60}")

        gates = log.get("gates", {})
        if gates:
            pr("  Gates:")
            for gtype, gdesc in gates.items():
                pr(f"    {gtype}: {gdesc}")
        else:
            pr("  Gates: none (no dependencies)")

        des_log = log.get("design")
        if des_log:
            pr(f"  Design: dep_gate={des_log['dep_gate']}  cal_need={des_log['cal_need']}d  "
               f"eligible={des_log['eligible']}/{len(des_log['designers'])}")
            for d in des_log["designers"]:
                mark = "✓" if d["name"] == des_log.get("chosen") else " "
                pr(f"    [{mark}] {d['name']}  next_avail={d['next_avail']}  "
                   f"budget_remaining={d['budget_remaining']}")
            if des_log.get("actual_start"):
                pr(f"  → Design: {des_log['actual_start']} → {des_log['actual_end']}")
            elif des_log.get("chosen") is None:
                pr("  → No eligible designer (budget exhausted) — project marked overflow")
        elif proj.get("design_days", 0) > 0:
            pr("  Design: skipped (no designers configured)")
        else:
            pr("  Design: none (0 design days)")

        for eng_log in log.get("eng", []):
            pr(f"  Eng: dep_gate={eng_log['dep_eng_gate']}  eng_early={eng_log['eng_early']}  "
               f"n={eng_log['n_eng']}  days_per={eng_log['days_per']}  cal_need={eng_log['cal_need']}  "
               f"budget_eligible={eng_log['budget_eligible']}  overflow_forced={eng_log['overflow_forced']}")
            for c in eng_log.get("candidates", []):
                mark = "✓" if c["name"] in eng_log.get("assigned", []) else " "
                pr(f"    [{mark}] {c['name']}  next_avail={c['next_avail']}  "
                   f"budget_remaining={c['budget_remaining']}  effective_start={c['effective_start']}")
            if eng_log.get("actual_eng_start"):
                pr(f"  → Eng: {eng_log['actual_eng_start']} → {eng_log['actual_eng_end']}")

        if not log.get("eng"):
            pr("  Eng: none (0 eng days)")

        pr(f"  Completion: {log.get('completion')}")

    pr("\n" + "=" * 80)
    pr("GAP ANALYSIS (idle working-day blocks per person)")
    pr("=" * 80)

    oncall      = sched["oncall"]
    eng_day_map = sched["eng_day_map"]
    des_day_map = sched["des_day_map"]

    def idle_blocks(day_map, oc_set):
        blocks, start = [], None
        for d in working_days:
            busy = d in day_map or d in oc_set
            if not busy:
                if start is None:
                    start = d
            else:
                if start is not None:
                    blocks.append((start, d - timedelta(days=1)))
                    # walk back to actual last working day
                    last = d - timedelta(days=1)
                    while last >= start and last not in working_days:
                        last -= timedelta(days=1)
                    blocks[-1] = (start, last)
                    start = None
        if start is not None:
            blocks.append((start, working_days[-1]))
        return blocks

    pr("\nEngineers:")
    for eng in engineers:
        name  = eng["name"]
        pct   = int(eng["capacity"] * 100)
        dmap  = eng_day_map.get(name, {})
        oc    = oncall.get(name, set())
        idles = idle_blocks(dmap, oc)
        pr(f"\n  {name} ({pct}%):")
        if not idles:
            pr("    No idle gaps")
        else:
            total = sum(1 for d in working_days if d not in dmap and d not in oc)
            for s, e in idles:
                cnt = sum(1 for d in working_days if s <= d <= e)
                pr(f"    IDLE {s} → {e}  ({cnt} working days)")
            pr(f"    Total idle working days: {total}")

    pr("\nDesigners:")
    for des in designers:
        name  = des["name"]
        pct   = int(des["capacity"] * 100)
        dmap  = des_day_map.get(name, {})
        idles = idle_blocks(dmap, set())
        pr(f"\n  {name} ({pct}%):")
        if not idles:
            pr("    No idle gaps")
        else:
            total = sum(1 for d in working_days if d not in dmap)
            for s, e in idles:
                cnt = sum(1 for d in working_days if s <= d <= e)
                pr(f"    IDLE {s} → {e}  ({cnt} working days)")
            pr(f"    Total idle working days: {total}")

    pr("\n" + "=" * 80)


# ─── Colors ───────────────────────────────────────────────────────────────────

PALETTE = [
    "#4e79a7","#e15759","#59a14f","#f28e2b","#b07aa1",
    "#edc948","#76b7b2","#9c755f","#ff9da7","#59386f",
    "#1a7a4a","#1a4b8c","#c9a227","#8b0000","#2eb8b8",
]
DESIGN_COLOR  = "#FCD34D"  # amber — used for design phase in both project gantt and designer row
ENG_COLOR     = "#60A5FA"  # blue — used for eng phase in project gantt
EXP_COLOR     = "#A78BFA"
ONCALL_COLOR  = "#EE7733"
ONCALL_IN_PROJ= "#F5C89A"  # muted orange — on-call pause within eng phase
DESIGNER_COLOR= DESIGN_COLOR
IDLE_COLOR    = "#F5F5F5"
UNAVAIL_COLOR = "#DCDCDC"
EMPTY_COLOR   = "#FAFAFA"


# ─── HTML helpers ─────────────────────────────────────────────────────────────

def he(s):
    return html_lib.escape(str(s))

def header_cells(working_days):
    MONTHS = ["","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    spans, seen = {}, []
    for wd in working_days:
        k = (wd.year, wd.month)
        spans[k] = spans.get(k, 0) + 1
        if k not in seen: seen.append(k)
    month_row = "".join(
        f'<th class="mhdr" colspan="{spans[k]}">{MONTHS[k[1]]} {k[0]}</th>' for k in seen
    )
    day_row = "".join(
        f'<th class="dhdr{"  wk" if wd.weekday()==0 else ""}">{wd.day}</th>'
        for wd in working_days
    )
    return month_row, day_row


# ─── Project Gantt tab ────────────────────────────────────────────────────────

def project_tab(projects, sched, proj_colors, working_days):
    phases = sched["phases"]
    oncall = sched["oncall"]

    # Category filter buttons
    cats = []
    for p in projects:
        if p["category"] not in cats: cats.append(p["category"])
    filter_btns = '<button class="fbtn active" data-cat="__all__">All</button>'
    for c in cats:
        if c: filter_btns += f'<button class="fbtn active" data-cat="{he(c)}">{he(c)}</button>'

    # Legend (phase colors only — no per-project colors)
    legend = (
        f'<div class="li"><div class="sw" style="background:{DESIGN_COLOR}"></div><span>Design</span></div>'
        f'<div class="li"><div class="sw" style="background:{ENG_COLOR}"></div><span>Eng</span></div>'
        f'<div class="li"><div class="sw" style="background:{EXP_COLOR}"></div><span>Experiment</span></div>'
        f'<div class="li"><div class="sw" style="background:{ONCALL_IN_PROJ}"></div><span>On-Call Pause</span></div>'
    )

    mh, dh = header_cells(working_days)

    rows = ""
    for proj in projects:
        pname  = proj["project"]
        info   = phases.get(pname, {})
        color  = proj_colors[pname]
        rank   = proj["rank"]
        dev_d  = proj["eng_days"]
        des_d  = proj["design_days"]
        exp_w  = proj["exp_weeks"]
        engs   = info.get("engineers", [])
        over   = info.get("overflow", False)
        unsched = info.get("unscheduled", False)

        name_style = "color:#E53E3E;font-weight:600" if over else ""
        badges = ""
        if proj["category"]:
            badges += f' <span class="badge cat">{he(proj["category"])}</span>'
        meta = f'{dev_d}d eng'
        if des_d: meta += f' / {des_d}d design'
        if exp_w: meta += f' / {exp_w}w exp'
        _MONTHS = ["","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        if unsched:
            unsched_tag = ' <span class="badge red">unscheduled</span>'
        elif over:
            comp = info.get("completion")
            date_str = f"{_MONTHS[comp.month]} {comp.day}" if comp else "?"
            unsched_tag = f' <span class="badge orange">overflow · done {date_str}</span>'
        else:
            unsched_tag = ""

        label = (f'<span style="{name_style}">{he(pname)}</span>'
                 f'<span class="meta"> ({meta})</span>{badges}{unsched_tag}')

        # Pre-compute phase sets
        design_set = set()
        if "design_start" in info and "design_end" in info:
            for d in working_days:
                if info["design_start"] <= d <= info["design_end"]:
                    design_set.add(d)
        eng_set = set()
        if "eng_start" in info and "eng_end" in info:
            for d in working_days:
                if info["eng_start"] <= d <= info["eng_end"]:
                    eng_set.add(d)
        exp_set = set()
        if "exp_start" in info and "exp_end" in info:
            for d in working_days:
                if info["exp_start"] <= d <= info["exp_end"]:
                    exp_set.add(d)
        # Days when ALL assigned engineers are on-call (project paused)
        paused_set = set()
        if engs and eng_set:
            for d in eng_set:
                if all(d in oncall.get(e, set()) for e in engs):
                    paused_set.add(d)

        eng_label = ", ".join(engs) if engs else ""

        # Build contiguous phase segments for merged-cell rendering
        PHASE_CFG = {
            'design': (DESIGN_COLOR,   'Design',     40),
            'eng':    (ENG_COLOR,      'Eng',        25),
            'exp':    (EXP_COLOR,      'Experiment', 65),
            'paused': (ONCALL_IN_PROJ, 'On-Call',    50),
            'empty':  (EMPTY_COLOR,    '',            0),
        }
        def day_phase(d):
            if d in design_set: return 'design'
            if d in exp_set:    return 'exp'
            if d in paused_set: return 'paused'
            if d in eng_set:    return 'eng'
            return 'empty'

        segments = []
        i = 0
        while i < len(working_days):
            phase = day_phase(working_days[i])
            j = i + 1
            while j < len(working_days) and day_phase(working_days[j]) == phase:
                j += 1
            segments.append((phase, i, j - 1))
            i = j

        row = f'<tr data-cat="{he(proj["category"])}" style="height:34px">'
        row += f'<td class="rl">{label}</td>'
        for phase, si, ei in segments:
            colspan  = ei - si + 1
            wk       = " wk" if working_days[si].weekday() == 0 else ""
            color, lbl_text, min_px = PHASE_CFG[phase]
            if phase == 'design':
                tip = f"{pname} — Design\n{info['design_start']} → {info['design_end']}"
            elif phase == 'exp':
                tip = f"{pname} — Experiment ({exp_w}w)\n{info['exp_start']} → {info['exp_end']}"
            elif phase == 'paused':
                tip = f"{pname} — On-Call pause\n({', '.join(engs)} on-call)"
            elif phase == 'eng':
                tip = f"{pname} ({proj['category']} / {proj['surface']})\nEng: {eng_label}\n{info.get('eng_start','')} → {info.get('eng_end','')}"
            else:
                tip = ""
            tip_attr = f' title="{he(tip)}"' if tip else ''
            if lbl_text and colspan * 15 >= min_px:
                inner = f'<span style="font-size:10px;font-weight:600;color:rgba(0,0,0,0.55);white-space:nowrap">{lbl_text}</span>'
            else:
                inner = ''
            row += (f'<td class="dc{wk}" colspan="{colspan}"'
                    f' style="background:{color};overflow:hidden;vertical-align:middle;text-align:center"'
                    f'{tip_attr}>{inner}</td>')
        row += "</tr>"
        rows += row

    on_time = sum(1 for p in projects if not phases.get(p["project"], {}).get("overflow", False))
    overflow = len(projects) - on_time

    summary = f'<p class="sum"><strong>{on_time}/{len(projects)}</strong> projects complete within quarter'
    if overflow:
        summary += f' · <span style="color:#E53E3E"><strong>{overflow}</strong> overflow</span>'
    summary += "</p>"

    return f"""
<div id="tab-project" class="tab-panel">
  <div class="legend">{legend}</div>
  <div class="fbar"><span class="flabel">Category:</span>{filter_btns}</div>
  <div class="gw"><table>
    <thead>
      <tr><th class="rl corner"></th>{mh}</tr>
      <tr><th class="rl corner"></th>{dh}</tr>
    </thead>
    <tbody>{rows}</tbody>
  </table></div>
  {summary}
</div>"""


# ─── Resource tab ─────────────────────────────────────────────────────────────

def resource_tab(engineers, designers, sched, proj_colors, working_days):
    oncall      = sched["oncall"]
    eng_day_map = sched["eng_day_map"]
    des_day_map = sched["des_day_map"]

    legend = ""
    for pname, color in proj_colors.items():
        label = pname[:40] + ("…" if len(pname) > 40 else "")
        legend += f'<div class="li"><div class="sw" style="background:{color}"></div><span>{he(label)}</span></div>'
    legend += f'<div class="li"><div class="sw" style="background:{ONCALL_COLOR}"></div><span>On-Call</span></div>'
    legend += f'<div class="li"><div class="sw" style="background:{DESIGNER_COLOR}"></div><span>Design Work</span></div>'
    legend += f'<div class="li"><div class="sw" style="background:{IDLE_COLOR};border:1px solid #ccc"></div><span>Available</span></div>'

    mh, dh = header_cells(working_days)

    rows = ""
    for eng in engineers:
        name   = eng["name"]
        pct    = int(eng["capacity"] * 100)
        dmap   = eng_day_map.get(name, {})
        oc_set = oncall.get(name, set())

        label = f'{he(name)} <span class="meta">(Eng · {pct}%)</span>'
        if eng["capacity"] == 0:
            label += ' <span class="badge grey">no capacity</span>'

        row = f'<tr style="height:30px"><td class="rl">{label}</td>'
        for wd in working_days:
            wk = " wk" if wd.weekday() == 0 else ""
            if wd in oc_set:
                row += f'<td class="dc{wk}" style="background:{ONCALL_COLOR}" title="{he(name)} — On-Call"></td>'
            elif wd in dmap:
                pname = dmap[wd]
                c = proj_colors.get(pname, IDLE_COLOR)
                row += f'<td class="dc{wk}" style="background:{c}" title="{he(name)} — {he(pname)}"></td>'
            else:
                row += f'<td class="dc{wk}" style="background:{IDLE_COLOR}"></td>'
        row += "</tr>"
        rows += row

    # One row per designer
    for des in designers:
        name  = des["name"]
        pct   = int(des["capacity"] * 100)
        dmap  = des_day_map.get(name, {})
        label = f'{he(name)} <span class="meta">(Design · {pct}%)</span>'
        row   = f'<tr style="height:30px"><td class="rl">{label}</td>'
        for wd in working_days:
            wk = " wk" if wd.weekday() == 0 else ""
            if wd in dmap:
                pname = dmap[wd]
                tip = f"{name} — {pname}"
                row += f'<td class="dc{wk}" style="background:{DESIGNER_COLOR}" title="{he(tip)}"></td>'
            else:
                row += f'<td class="dc{wk}" style="background:{IDLE_COLOR}"></td>'
        row += "</tr>"
        rows += row

    return f"""
<div id="tab-resource" class="tab-panel" style="display:none">
  <div class="legend">{legend}</div>
  <div class="gw"><table>
    <thead>
      <tr><th class="rl corner"></th>{mh}</tr>
      <tr><th class="rl corner"></th>{dh}</tr>
    </thead>
    <tbody>{rows}</tbody>
  </table></div>
</div>"""


# ─── Capacity tab ─────────────────────────────────────────────────────────────

def capacity_tab(projects, engineers, designers, sched, working_days, eng_mult, end_date):
    phases     = sched["phases"]
    eng_budget = sched["eng_budget"]
    eng_alloc  = sched["eng_alloc"]
    des_budget = sched["des_budget"]
    des_alloc  = sched["des_alloc"]
    oncall     = sched["oncall"]
    total_wd   = len(working_days)

    def util_style(u):
        if u > 100: return "color:#E53E3E;font-weight:600"
        if u > 80:  return "color:#D97706"
        return "color:#059669"

    # Engineers
    rows = ""
    for eng in engineers:
        name     = eng["name"]
        pct      = int(eng["capacity"] * 100)
        oc_days  = len(oncall.get(name, set()))
        avail_wd = total_wd - oc_days
        budget   = eng_budget[name]
        alloc    = eng_alloc[name]
        u        = round(alloc / budget * 100) if budget > 0 else 0
        rows += (
            f"<tr>"
            f"<td>{he(name)}</td><td>Engineer</td><td>{pct}%</td>"
            f"<td>{oc_days}</td><td>{avail_wd}</td>"
            f"<td>{budget}</td><td>{alloc}</td>"
            f'<td style="{util_style(u)}">{u}%</td>'
            f"</tr>"
        )

    # Designers (no on-call)
    if designers:
        rows += "<tr><td colspan='8' style='padding:4px 8px;background:#f7fafc;font-weight:600;font-size:11px;color:#718096;border-top:2px solid #e2e8f0'>DESIGN</td></tr>"
    for des in designers:
        name   = des["name"]
        pct    = int(des["capacity"] * 100)
        budget = des_budget[name]
        alloc  = des_alloc[name]
        u      = round(alloc / budget * 100) if budget > 0 else 0
        rows += (
            f"<tr>"
            f"<td>{he(name)}</td><td>Designer</td><td>{pct}%</td>"
            f"<td>—</td><td>{budget}</td>"
            f"<td>{budget}</td><td>{alloc}</td>"
            f'<td style="{util_style(u)}">{u}%</td>'
            f"</tr>"
        )

    # Overflow analysis
    overflowed = [p for p in projects if phases.get(p["project"], {}).get("overflow") or phases.get(p["project"], {}).get("unscheduled")]
    on_time    = [p for p in projects if p not in overflowed]

    total_eng_req  = sum(p["eng_days"] for p in projects)
    total_eng_cap  = sum(eng_budget[e["name"]] for e in engineers)
    overall_util   = round(total_eng_req / total_eng_cap * 100) if total_eng_cap > 0 else 0

    if overflowed:
        overflow_raw  = sum(p["eng_days"] for p in overflowed)
        days_per_new  = total_wd / eng_mult
        add_engs      = math.ceil(overflow_raw / days_per_new)
        overflow_names = ', '.join(he(p['project']) for p in overflowed)
        conclusion_html = f"""
<div class="conclusion overflow">
  <strong>⚠ {len(overflowed)} of {len(projects)} projects cannot be completed this quarter.</strong><br>
  Overflow projects: {overflow_names}<br><br>
  An estimated <strong>{add_engs} additional engineer(s)</strong> at 100% capacity would be needed to complete all projects within the quarter.<br>
  <span style="font-size:12px;opacity:0.85;display:block;margin-top:8px;line-height:1.7">
    <strong>How this is calculated:</strong><br>
    Overflow eng work: <strong>{overflow_raw} raw dev days</strong> ({' + '.join(str(p['eng_days']) for p in overflowed)} across {len(overflowed)} projects)<br>
    Productive days per new 100% engineer: <strong>{days_per_new:.1f} days</strong> ({total_wd} working days ÷ {eng_mult}x overhead)<br>
    Additional engineers needed: <strong>ceil({overflow_raw} ÷ {days_per_new:.1f}) = {add_engs}</strong>
  </span>
</div>"""
    else:
        conclusion_html = f"""
<div class="conclusion ok">
  <strong>✓ All {len(projects)} projects can be completed this quarter with current resourcing.</strong>
</div>"""

    return f"""
<div id="tab-capacity" class="tab-panel" style="display:none">
  <div class="cards">
    <div class="card"><div class="cv">{len(projects)}</div><div class="cl">Total Projects</div></div>
    <div class="card ok"><div class="cv">{len(on_time)}</div><div class="cl">On Time</div></div>
    <div class="card {"overflow" if overflowed else "ok"}"><div class="cv">{len(overflowed)}</div><div class="cl">Overflow</div></div>
    <div class="card"><div class="cv">{total_eng_cap}</div><div class="cl">Eng Capacity (dev days)</div></div>
    <div class="card"><div class="cv">{total_eng_req}</div><div class="cl">Eng Effort Required</div></div>
    <div class="card {"overflow" if overall_util > 100 else "ok"}"><div class="cv">{overall_util}%</div><div class="cl">Overall Utilization</div></div>
  </div>
  <h3>Team Breakdown</h3>
  <table class="cap-table">
    <thead>
      <tr>
        <th>Name</th><th>Role</th><th>Capacity</th><th>On-Call Days</th>
        <th>Avail Working Days</th><th>Productive Budget</th>
        <th>Days Allocated</th><th>Utilization</th>
      </tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>
  {conclusion_html}
</div>"""


# ─── HTML assembler ───────────────────────────────────────────────────────────

def render_html(projects, engineers, designers, sched, working_days, start_date, end_date, eng_mult, design_mult):
    proj_colors = {p["project"]: PALETTE[i % len(PALETTE)] for i, p in enumerate(projects)}

    tab_proj = project_tab(projects, sched, proj_colors, working_days)
    tab_res  = resource_tab(engineers, designers, sched, proj_colors, working_days)
    tab_cap  = capacity_tab(projects, engineers, designers, sched, working_days, eng_mult, end_date)

    phases = sched["phases"]
    overflowed = sum(1 for p in projects if phases.get(p["project"], {}).get("overflow"))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Gantt — {start_date} to {end_date}</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ font-family: system-ui, -apple-system, sans-serif; margin: 0; padding: 16px 20px; background:#fff; color:#1a202c; }}
  h1 {{ font-size:20px; margin:0 0 2px; }}
  h3 {{ font-size:15px; margin:16px 0 8px; }}
  .sub {{ font-size:12px; color:#718096; margin-bottom:14px; }}
  .tab-bar {{ display:flex; gap:0; margin-bottom:16px; border-bottom:2px solid #e2e8f0; }}
  .tb {{ padding:8px 20px; border:none; background:none; font-size:14px; cursor:pointer;
         border-bottom:3px solid transparent; margin-bottom:-2px; color:#718096; font-family:inherit; }}
  .tb.active {{ color:#1a202c; border-bottom-color:#1a202c; font-weight:600; }}
  .tb:hover:not(.active) {{ color:#4a5568; background:#f7fafc; }}
  .legend {{ display:flex; flex-wrap:wrap; gap:10px; margin-bottom:12px; align-items:center; }}
  .li {{ display:flex; align-items:center; gap:5px; font-size:12px; }}
  .sw {{ width:14px; height:14px; border-radius:3px; flex-shrink:0; border:1px solid rgba(0,0,0,.08); }}
  .fbar {{ display:flex; flex-wrap:wrap; gap:6px; align-items:center; margin-bottom:10px; }}
  .flabel {{ font-size:12px; color:#718096; font-weight:500; }}
  .fbtn {{ padding:3px 10px; border-radius:999px; border:1px solid #cbd5e0;
           background:#f7fafc; color:#4a5568; font-size:11px; cursor:pointer; }}
  .fbtn.active {{ background:#2d3748; color:#fff; border-color:#2d3748; }}
  .gw {{ overflow-x:auto; border:1px solid #e2e8f0; border-radius:6px; }}
  table {{ border-collapse:collapse; table-layout:fixed; }}
  th, td {{ border:1px solid #e2e8f0; padding:0; }}
  .rl {{ min-width:280px; width:280px; position:sticky; left:0; background:#fff; z-index:2;
         font-size:12px; padding:0 8px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
         border-right:2px solid #cbd5e0; vertical-align:middle; }}
  .corner {{ background:#f7fafc; z-index:3; }}
  .meta {{ font-weight:400; color:#a0aec0; font-size:11px; }}
  .badge {{ font-size:10px; font-weight:600; padding:1px 5px; border-radius:3px; margin-left:3px; }}
  .badge.cat {{ background:#ebf4ff; color:#3182ce; }}
  .badge.red {{ background:#fff5f5; color:#e53e3e; }}
  .badge.orange {{ background:#fffaf0; color:#c05621; }}
  .badge.grey {{ background:#f7fafc; color:#718096; }}
  .mhdr {{ text-align:center; font-weight:700; font-size:11px; background:#f7fafc; height:22px; vertical-align:middle; }}
  .dhdr {{ text-align:center; font-size:10px; color:#a0aec0; height:18px; vertical-align:middle;
           background:#fafafa; width:15px; min-width:15px; }}
  .dc {{ width:15px; min-width:15px; cursor:default; }}
  .wk {{ border-left:1px solid #a0aec0 !important; }}
  .sum {{ margin-top:10px; font-size:13px; }}
  /* Capacity tab */
  .cards {{ display:flex; flex-wrap:wrap; gap:12px; margin-bottom:20px; }}
  .card {{ background:#f7fafc; border:1px solid #e2e8f0; border-radius:8px; padding:12px 18px; min-width:120px; }}
  .card.ok {{ border-color:#68d391; background:#f0fff4; }}
  .card.overflow {{ border-color:#fc8181; background:#fff5f5; }}
  .cv {{ font-size:24px; font-weight:700; }}
  .cl {{ font-size:11px; color:#718096; margin-top:2px; }}
  .cap-table {{ border-collapse:collapse; font-size:13px; width:100%; max-width:860px; }}
  .cap-table th {{ background:#f7fafc; font-weight:600; padding:6px 10px; border:1px solid #e2e8f0; text-align:left; }}
  .cap-table td {{ padding:5px 10px; border:1px solid #e2e8f0; }}
  .cap-table tr:hover {{ background:#f7fafc; }}
  .conclusion {{ margin-top:16px; padding:14px 18px; border-radius:8px; font-size:14px; line-height:1.6; }}
  .conclusion.ok {{ background:#f0fff4; border:1px solid #68d391; color:#276749; }}
  .conclusion.overflow {{ background:#fff5f5; border:1px solid #fc8181; color:#822727; }}
</style>
</head>
<body>
<h1>Engineering Planning — {start_date} to {end_date}</h1>
<p class="sub">{len(working_days)} working days &nbsp;·&nbsp; {len(engineers)} engineers &nbsp;·&nbsp; Eng {eng_mult}x multiplier &nbsp;·&nbsp; Design {design_mult}x multiplier</p>

<div class="tab-bar">
  <button class="tb active" data-tab="project">Project Gantt</button>
  <button class="tb" data-tab="resource">Resources</button>
  <button class="tb" data-tab="capacity">Capacity Analysis</button>
</div>

{tab_proj}
{tab_res}
{tab_cap}

<script>
document.querySelectorAll('.tb').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('.tb').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.style.display = 'none');
    btn.classList.add('active');
    document.getElementById('tab-' + btn.dataset.tab).style.display = '';
  }});
}});
(function() {{
  const btns = document.querySelectorAll('.fbtn');
  const rows = document.querySelectorAll('#tab-project tbody tr[data-cat]');
  function getActive() {{
    return new Set([...btns].filter(b => b.classList.contains('active') && b.dataset.cat !== '__all__').map(b => b.dataset.cat));
  }}
  function apply() {{
    const a = getActive();
    rows.forEach(r => r.style.display = (a.has(r.dataset.cat) ? '' : 'none'));
  }}
  btns.forEach(btn => {{
    btn.addEventListener('click', () => {{
      if (btn.dataset.cat === '__all__') {{
        btns.forEach(b => b.classList.add('active'));
      }} else {{
        const allBtn = document.querySelector('.fbtn[data-cat="__all__"]');
        allBtn.classList.remove('active');
        const others = [...btns].filter(b => b.dataset.cat !== '__all__' && b.classList.contains('active'));
        if (btn.classList.contains('active') && others.length === 1) return;
        btn.classList.toggle('active');
      }}
      apply();
    }});
  }});
}})();
</script>
</body>
</html>"""


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()
    proj_text, res_text = load_data(args)
    projects   = load_projects(proj_text)
    engineers  = load_engineers(res_text)
    designers  = load_designers(res_text)

    if not projects:  sys.exit("No projects found in CSV")
    if not engineers: sys.exit("No engineers found in CSV")

    start_date   = date.fromisoformat(args.start)
    end_date     = date.fromisoformat(args.end)
    working_days = build_working_days(start_date, end_date)
    oncall       = build_oncall(working_days, engineers, start_date)
    sched        = run_schedule(projects, engineers, designers, working_days, oncall, args.eng_mult, args.design_mult)

    html = render_html(projects, engineers, designers, sched, working_days, start_date, end_date,
                       args.eng_mult, args.design_mult)

    import os
    out = os.path.expanduser(args.output)
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)

    phases    = sched["phases"]
    on_time   = [p for p in projects if not phases.get(p["project"], {}).get("overflow")]
    overflow  = [p for p in projects if phases.get(p["project"], {}).get("overflow")]
    unsched   = [p for p in projects if phases.get(p["project"], {}).get("unscheduled")]

    if args.debug:
        print_debug_report(sched, projects, engineers, designers, working_days)

    summary = {
        "output":       out,
        "working_days": len(working_days),
        "projects":     len(projects),
        "on_time":      len(on_time),
        "overflow":     len(overflow),
        "unscheduled":  len(unsched),
        "overflow_list":  [p["project"] for p in overflow],
        "unsched_list":   [p["project"] for p in unsched],
    }
    print(json.dumps(summary, indent=2))
    print(f"\nGenerated: {out}")

if __name__ == "__main__":
    main()
