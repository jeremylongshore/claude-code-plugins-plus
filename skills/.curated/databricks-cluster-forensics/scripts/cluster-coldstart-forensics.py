#!/usr/bin/env python3
"""cluster-coldstart-forensics.py — bucket a Databricks cluster's cold-start
(PENDING) time by lifecycle stage, deterministically (bead 4x0v / pain D01).

The pain: on VNet/VPC-injected workspaces a cluster that usually starts in 5-6
minutes randomly takes 20-35, and Databricks reports only the aggregate — it does
not tell you WHICH stage spiked (cloud-provider VM allocation, network/DNS setup,
or init-script + library install). This script reads a cluster's event stream
(from `clusters.events` / the databricks-workspace-mcp `clusters_events` tool) and
splits the PENDING window into named stages by the event boundaries Databricks
DOES emit, so the agent can say "the 22-minute start was 18 minutes stuck in
provisioning, not init scripts" instead of guessing.

The LLM never eyeballs timestamps — the arithmetic is here. The skill fetches the
events (MCP or CLI) and pipes them in; the script buckets and names the dominant
stage.

Stages (delimited by real cluster event types):
  provisioning     CREATING -> INIT_SCRIPTS_STARTED (or STARTING)
                   cloud-provider VM allocation + network/DNS/NPIP setup. These
                   two sub-causes are usually not separately evented, so they are
                   reported together; a long provisioning stage points the
                   investigation at the cloud/network layer, not init scripts.
  init_scripts     INIT_SCRIPTS_STARTED -> INIT_SCRIPTS_FINISHED
                   init-script execution (and much library install).
  spark_startup    INIT_SCRIPTS_FINISHED (or STARTING) -> RUNNING / DRIVER_HEALTHY
                   driver + executor spin-up and remaining library install.

Missing boundary events (not every cluster emits init scripts) are handled: the
stage is reported as "unmeasured" rather than folded silently into another.

Input: JSON on stdin or --input FILE. Either the raw `clusters.events` response
({"events": [...]}) or a bare list [...]. Each event needs `type` and a
millisecond `timestamp`.
Output: a human table (default) or --json for the machine record.
Exit codes: 0 ok · 2 bad usage/input.
"""

import argparse
import json
import sys

# Event types that open / close each stage. Ordered by cold-start progression.
CREATE_EVENTS = ("CREATING",)
INIT_START_EVENTS = ("INIT_SCRIPTS_STARTED",)
INIT_FINISH_EVENTS = ("INIT_SCRIPTS_FINISHED",)
# Terminal "cluster is up" markers, best first.
READY_EVENTS = ("DRIVER_HEALTHY", "RUNNING", "STARTING_DRIVER", "UPSIZE_COMPLETED")
# STARTING is a mid-provisioning marker on some clouds; used as a fallback split.
STARTING_EVENTS = ("STARTING",)

# Terminal failure markers — if the start ended in one of these, say so.
FAILURE_HINT_EVENTS = ("TERMINATING", "NODES_LOST", "DRIVER_NOT_RESPONDING")


def _norm(events):
    """Accept {'events':[...]} or [...]; return a list of {type,timestamp} sorted
    by timestamp, dropping malformed rows."""
    if isinstance(events, dict):
        events = events.get("events", [])
    out = []
    for e in events or []:
        if not isinstance(e, dict):
            continue
        t = e.get("type")
        ts = e.get("timestamp")
        if t is None or not isinstance(ts, (int, float)):
            continue
        out.append({"type": str(t), "timestamp": int(ts)})
    return sorted(out, key=lambda e: e["timestamp"])


def _first_ts(events, types, after=None):
    for e in events:
        if e["type"] in types and (after is None or e["timestamp"] >= after):
            return e["timestamp"]
    return None


def bucket_coldstart(events):
    """Split the cold-start window into named stages. Pure — no I/O.

    Returns a dict:
      { total_ms, stages: {name: {ms|None, measured}}, dominant, notes[] }
    A stage whose boundary events are missing has ms=None / measured=False and is
    NOT summed into another stage (so a partial event stream never lies)."""
    ev = _norm(events)
    notes = []
    if not ev:
        return {
            "total_ms": None,
            "stages": {},
            "dominant": None,
            "notes": ["no usable events (need type + millisecond timestamp)"],
        }

    t_create = _first_ts(ev, CREATE_EVENTS)
    t_init_start = _first_ts(ev, INIT_START_EVENTS, after=t_create)
    t_init_finish = _first_ts(ev, INIT_FINISH_EVENTS, after=t_init_start or t_create)
    t_ready = _first_ts(ev, READY_EVENTS, after=t_create)
    t_starting = _first_ts(ev, STARTING_EVENTS, after=t_create)

    if t_create is None:
        notes.append("no CREATING event — using the earliest event as the start boundary")
        t_create = ev[0]["timestamp"]
    if t_ready is None:
        # Cold start never completed in this window; use the last event as the end.
        last = ev[-1]
        t_ready = last["timestamp"]
        if last["type"] in FAILURE_HINT_EVENTS:
            notes.append(
                f"start did NOT reach a ready state — ended in {last['type']} (a failed start, not a slow one)"
            )
        else:
            notes.append(
                "no DRIVER_HEALTHY/RUNNING in this window — end boundary is the last event; start may be ongoing"
            )

    stages = {}

    # provisioning: CREATING -> INIT_SCRIPTS_STARTED (fallback STARTING, then ready)
    prov_end = t_init_start or t_starting or t_ready
    stages["provisioning"] = _stage(t_create, prov_end, measured=prov_end is not None)

    # init_scripts: INIT_SCRIPTS_STARTED -> INIT_SCRIPTS_FINISHED
    if t_init_start is not None and t_init_finish is not None:
        stages["init_scripts"] = _stage(t_init_start, t_init_finish, measured=True)
    else:
        stages["init_scripts"] = {"ms": None, "measured": False}
        notes.append(
            "no INIT_SCRIPTS_STARTED/FINISHED pair — this cluster has no init scripts, or the events were pruned"
        )

    # spark_startup: (init finish | starting | init start) -> ready
    ss_start = t_init_finish or t_starting or t_init_start
    if ss_start is not None and t_ready is not None and t_ready >= ss_start:
        stages["spark_startup"] = _stage(ss_start, t_ready, measured=True)
    else:
        stages["spark_startup"] = {"ms": None, "measured": False}

    total = t_ready - t_create if (t_ready is not None and t_create is not None) else None
    measured = {k: v["ms"] for k, v in stages.items() if v.get("measured") and v.get("ms") is not None}
    dominant = max(measured, key=measured.get) if measured else None
    return {"total_ms": total, "stages": stages, "dominant": dominant, "notes": notes}


def _stage(start, end, measured):
    if not measured or start is None or end is None or end < start:
        return {"ms": None, "measured": False}
    return {"ms": end - start, "measured": True}


def _fmt_ms(ms):
    if ms is None:
        return "unmeasured"
    s = ms / 1000.0
    return f"{int(s // 60)}m{int(s % 60):02d}s" if s >= 60 else f"{s:.1f}s"


def render(result):
    lines = []
    total = result["total_ms"]
    lines.append(f"Cold-start total (PENDING): {_fmt_ms(total)}")
    lines.append("stage           duration     share")
    for name in ("provisioning", "init_scripts", "spark_startup"):
        st = result["stages"].get(name, {})
        ms = st.get("ms")
        share = f"{100 * ms / total:.0f}%" if (ms is not None and total) else "  —"
        marker = "  <== dominant" if name == result["dominant"] else ""
        lines.append(f"  {name:<13} {_fmt_ms(ms):<11} {share:>5}{marker}")
    if result["dominant"] == "provisioning":
        lines.append(
            "\nDominant stage is PROVISIONING → cloud-provider VM allocation or "
            "network/DNS/NPIP setup. Check subnet IP capacity, custom DNS, and "
            "cloud capacity/throttling (see references/termination-codes.md)."
        )
    elif result["dominant"] == "init_scripts":
        lines.append(
            "\nDominant stage is INIT_SCRIPTS → an init script or library install is "
            "slow. Audit the init scripts and the cluster library list."
        )
    elif result["dominant"] == "spark_startup":
        lines.append(
            "\nDominant stage is SPARK_STARTUP → driver/executor spin-up or remaining "
            "library install. Check driver node type and heavy library installs."
        )
    for n in result["notes"]:
        lines.append(f"note: {n}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Bucket a cluster's cold-start time by stage")
    ap.add_argument("--input", help="clusters.events JSON (default: stdin)")
    ap.add_argument("--json", action="store_true", help="emit the machine record instead of a table")
    args = ap.parse_args()
    raw = open(args.input).read() if args.input else sys.stdin.read()
    if not raw.strip():
        sys.exit("error: no input — pipe clusters.events JSON on stdin or pass --input FILE")
    try:
        events = json.loads(raw)
    except json.JSONDecodeError as e:
        sys.exit(f"error: input is not valid JSON: {e}")
    result = bucket_coldstart(events)
    print(json.dumps(result, indent=2) if args.json else render(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
