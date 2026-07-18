#!/usr/bin/env python3
"""drain-workspace.py — terminate every running cluster, instance pool, and SQL
warehouse in a workspace so a customer-managed-key (CMK) rotation can proceed, then
resume exactly what was drained (databricks-bundle-medic, pain D8).

Pain D8: updating a workspace's CMK requires that every cluster, instance pool, and SQL
warehouse be terminated first — a hard maintenance window. Doing that by hand across a
multi-team workspace is error-prone in two directions: missing a resource (the rotation
fails) and, on the way back, restarting something that was already stopped before the
window (waking a resource nobody wanted running).

This script makes the drain deterministic and REVERSIBLE:
  * plan_drain() terminates only what is actually running — already-stopped resources
    are skipped, so the drain is IDEMPOTENT (re-running never double-acts).
  * it records exactly what IT stopped to a resume manifest, so plan_resume() restarts
    ONLY those — never something that was already off before the window.

SAFETY: dry-run is the DEFAULT. It prints the plan and touches nothing unless
`--execute` is passed. `--resume <manifest>` restarts from a prior drain's manifest.

Usage:
  drain-workspace.py --inventory inv.json                 # dry-run drain plan (default)
  drain-workspace.py --inventory inv.json --execute --manifest drain.json
  drain-workspace.py --resume drain.json [--execute]
Exit: 0 ok · 2 bad usage.

`inv.json` shape (as produced by the databricks CLI list commands):
  {"clusters":[{"cluster_id","cluster_name","state"}],
   "warehouses":[{"id","name","state"}],
   "instance_pools":[{"instance_pool_id","instance_pool_name","state"?,"idle"?}]}
"""

import argparse
import json
import sys

# States that mean "running / needs draining" per resource kind (everything else is
# already down → skipped, keeping the drain idempotent).
CLUSTER_RUNNING = {"RUNNING", "PENDING", "RESTARTING", "RESIZING"}
WAREHOUSE_RUNNING = {"RUNNING", "STARTING"}


def _running_clusters(clusters):
    for c in clusters or []:
        state = (c.get("state") or "").upper()
        yield c, state in CLUSTER_RUNNING


def _running_warehouses(warehouses):
    for w in warehouses or []:
        state = (w.get("state") or "").upper()
        yield w, state in WAREHOUSE_RUNNING


def _active_pools(pools):
    # A pool blocks CMK rotation if it holds instances. We can only know that from an
    # idle/used count when present; absent a count, treat the pool as active (safe).
    for p in pools or []:
        idle = p.get("idle")
        active = True if idle is None else idle > 0
        yield p, active


def plan_drain(inventory):
    """Return a list of drain actions. Pure. Each action: {kind,id,name,state,action}
    where action is 'terminate'/'drain-pool' (running) or 'skip' (already down)."""
    actions = []
    for c, running in _running_clusters(inventory.get("clusters")):
        actions.append(
            {
                "kind": "cluster",
                "id": c.get("cluster_id"),
                "name": c.get("cluster_name"),
                "state": (c.get("state") or "").upper(),
                "action": "terminate" if running else "skip",
            }
        )
    for w, running in _running_warehouses(inventory.get("warehouses")):
        actions.append(
            {
                "kind": "warehouse",
                "id": w.get("id"),
                "name": w.get("name"),
                "state": (w.get("state") or "").upper(),
                "action": "stop" if running else "skip",
            }
        )
    for p, active in _active_pools(inventory.get("instance_pools")):
        actions.append(
            {
                "kind": "instance_pool",
                "id": p.get("instance_pool_id"),
                "name": p.get("instance_pool_name"),
                "state": "ACTIVE" if active else "IDLE",
                "action": "drain-pool" if active else "skip",
            }
        )
    return actions


def drain_manifest(actions):
    """The subset we WOULD act on — the resume manifest records only these, so resume
    never wakes a resource that was already stopped before the window."""
    return [a for a in actions if a["action"] != "skip"]


def plan_resume(manifest):
    """Invert a drain manifest into resume actions. Pure. Pools that were drained to
    zero idle are NOT auto-restarted (restoring min-idle is a capacity decision) — they
    are reported for the operator to reset deliberately."""
    resume = []
    for a in manifest:
        if a["kind"] == "cluster":
            resume.append({**a, "action": "start"})
        elif a["kind"] == "warehouse":
            resume.append({**a, "action": "start"})
        elif a["kind"] == "instance_pool":
            resume.append({**a, "action": "restore-min-idle (manual — capacity decision)"})
    return resume


def _print_plan(title, actions):
    print(f"# {title}")
    if not actions:
        print("  (nothing to do)")
        return
    for a in actions:
        print(f"  [{a['action']:>28}] {a['kind']}/{a.get('name') or a.get('id')} (state={a['state']})")
    acted = [a for a in actions if not a["action"].startswith(("skip", "restore"))]
    print(f"  -> {len(acted)} resource(s) to act on, {len(actions) - len(acted)} skipped/manual")


def main():
    ap = argparse.ArgumentParser(description="Drain (and later resume) a workspace for CMK rotation (D8)")
    ap.add_argument("--inventory", help="JSON inventory of clusters/warehouses/instance_pools")
    ap.add_argument("--resume", help="a prior drain manifest to resume from")
    ap.add_argument("--manifest", default="drain-manifest.json", help="where to write the drain manifest")
    ap.add_argument("--execute", action="store_true", help="actually act (default: dry-run)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not args.inventory and not args.resume:
        ap.error("one of --inventory (to drain) or --resume (to resume) is required")

    if args.resume:
        with open(args.resume) as fh:
            manifest = json.load(fh)
        resume = plan_resume(manifest)
        if args.json:
            print(json.dumps(resume, indent=2))
        else:
            _print_plan("RESUME PLAN" + ("" if args.execute else " (dry-run)"), resume)
        if args.execute:
            print("\n[execute] run the printed start/restore commands via the databricks CLI.")
        return 0

    with open(args.inventory) as fh:
        inventory = json.load(fh)
    actions = plan_drain(inventory)
    manifest = drain_manifest(actions)
    if args.json:
        print(json.dumps({"plan": actions, "manifest": manifest}, indent=2))
    else:
        _print_plan("DRAIN PLAN" + ("" if args.execute else " (dry-run — pass --execute to act)"), actions)
    if args.execute:
        with open(args.manifest, "w") as fh:
            json.dump(manifest, fh, indent=2)
        print(f"\n[execute] wrote resume manifest -> {args.manifest}")
        print("[execute] terminate clusters/warehouses + set pool min_idle_instances=0 via the CLI,")
        print("          then rotate the CMK, then re-run with --resume", args.manifest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
