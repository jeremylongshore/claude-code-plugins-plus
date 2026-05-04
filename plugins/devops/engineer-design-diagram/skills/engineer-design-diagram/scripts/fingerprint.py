#!/usr/bin/env python3
"""
fingerprint.py — write, read, and diff structural fingerprints for engineer-design-diagram.

Usage:
    fingerprint.py write --input graph.json          # write new state
    fingerprint.py read                                # dump current state
    fingerprint.py diff --input graph.json            # diff current state against provided graph
    fingerprint.py path                                # print the resolved state file path

State file location (fallback chain):
    1. ${CLAUDE_PLUGIN_DATA}/arch-state.json
    2. ${XDG_STATE_HOME}/claude/arch/arch-state.json
    3. ~/.claude-state/arch/arch-state.json

Schema documented in references/fingerprint-spec.md. Current schema_version: "1".

Required packages: Python 3.9+ standard library only (hashlib, json, pathlib, os, sys, argparse).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1"
STATE_FILENAME = "arch-state.json"


def resolve_state_path() -> Path:
    """Return first writable location for the state file, creating parent dirs if needed."""
    candidates = []

    if "CLAUDE_PLUGIN_DATA" in os.environ:
        candidates.append(Path(os.environ["CLAUDE_PLUGIN_DATA"]) / STATE_FILENAME)

    xdg = os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local" / "state"))
    candidates.append(Path(xdg) / "claude" / "arch" / STATE_FILENAME)

    candidates.append(Path.home() / ".claude-state" / "arch" / STATE_FILENAME)

    for path in candidates:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            return path
        except OSError:
            continue

    raise RuntimeError("No writable state location found")


def node_stable_hash(node: dict[str, Any], neighbor_ids: list[str]) -> str:
    canonical = f"{node.get('role', '')}|{node.get('label', '')}|{'|'.join(sorted(neighbor_ids))}"
    return "sha256:" + hashlib.sha256(canonical.encode()).hexdigest()


def edge_stable_hash(edge: dict[str, Any]) -> str:
    canonical = f"{edge['from']}|{edge['to']}|{edge.get('kind', 'unknown')}"
    return "sha256:" + hashlib.sha256(canonical.encode()).hexdigest()


def graph_fingerprint(nodes: list[dict], edges: list[dict]) -> str:
    all_hashes = sorted([n["stable_hash"] for n in nodes] + [e["stable_hash"] for e in edges])
    return "sha256:" + hashlib.sha256("".join(all_hashes).encode()).hexdigest()


def enrich(graph: dict[str, Any]) -> dict[str, Any]:
    """Add stable_hash fields and graph_fingerprint to a bare graph."""
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    # Build neighbor map for stable node hashing
    neighbors: dict[str, set[str]] = {n["id"]: set() for n in nodes}
    for e in edges:
        if e["from"] in neighbors:
            neighbors[e["from"]].add(e["to"])
        if e["to"] in neighbors:
            neighbors[e["to"]].add(e["from"])

    for n in nodes:
        n["stable_hash"] = node_stable_hash(n, sorted(neighbors.get(n["id"], [])))
    for e in edges:
        e["stable_hash"] = edge_stable_hash(e)

    graph["graph_fingerprint"] = graph_fingerprint(nodes, edges)
    graph["schema_version"] = SCHEMA_VERSION
    graph["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    return graph


def cmd_write(input_path: str) -> int:
    with open(input_path) as f:
        graph = json.load(f)
    enriched = enrich(graph)
    state_path = resolve_state_path()
    with open(state_path, "w") as f:
        json.dump(enriched, f, indent=2)
        f.write("\n")
    print(f"Wrote fingerprint to {state_path}")
    print(f"graph_fingerprint: {enriched['graph_fingerprint']}")
    return 0


def cmd_read() -> int:
    state_path = resolve_state_path()
    if not state_path.exists():
        print(f"No state file at {state_path}", file=sys.stderr)
        return 2
    with open(state_path) as f:
        print(f.read())
    return 0


def cmd_diff(input_path: str) -> int:
    state_path = resolve_state_path()
    if not state_path.exists():
        print(f"No prior state at {state_path} — run `write` first to establish baseline.", file=sys.stderr)
        return 2

    with open(state_path) as f:
        old = json.load(f)
    with open(input_path) as f:
        new = json.load(f)
    new = enrich(new)

    if old.get("schema_version") != SCHEMA_VERSION:
        print(f"Schema mismatch: prior={old.get('schema_version')} current={SCHEMA_VERSION}", file=sys.stderr)
        print("Refusing to diff across schema versions. Re-baseline with `write`.", file=sys.stderr)
        return 3

    old_node_ids = {n["id"]: n for n in old.get("nodes", [])}
    new_node_ids = {n["id"]: n for n in new.get("nodes", [])}
    old_edge_hashes = {e["stable_hash"]: e for e in old.get("edges", [])}
    new_edge_hashes = {e["stable_hash"]: e for e in new.get("edges", [])}

    added_nodes = [n for nid, n in new_node_ids.items() if nid not in old_node_ids]
    removed_nodes = [n for nid, n in old_node_ids.items() if nid not in new_node_ids]
    changed_nodes = [
        n for nid, n in new_node_ids.items()
        if nid in old_node_ids and old_node_ids[nid]["stable_hash"] != n["stable_hash"]
    ]
    added_edges = [e for h, e in new_edge_hashes.items() if h not in old_edge_hashes]
    removed_edges = [e for h, e in old_edge_hashes.items() if h not in new_edge_hashes]

    diff = {
        "prior_fingerprint": old.get("graph_fingerprint"),
        "new_fingerprint": new["graph_fingerprint"],
        "changed": old.get("graph_fingerprint") != new["graph_fingerprint"],
        "added_nodes": added_nodes,
        "removed_nodes": removed_nodes,
        "changed_nodes": changed_nodes,
        "added_edges": added_edges,
        "removed_edges": removed_edges,
    }
    print(json.dumps(diff, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="fingerprint.py — structural state for engineer-design-diagram")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_write = sub.add_parser("write", help="Write new state from a graph JSON input")
    p_write.add_argument("--input", required=True, help="Path to graph JSON")

    sub.add_parser("read", help="Dump current state file to stdout")

    p_diff = sub.add_parser("diff", help="Diff current state against a new graph JSON")
    p_diff.add_argument("--input", required=True, help="Path to graph JSON")

    sub.add_parser("path", help="Print resolved state file path")

    args = parser.parse_args()

    if args.cmd == "write":
        return cmd_write(args.input)
    if args.cmd == "read":
        return cmd_read()
    if args.cmd == "diff":
        return cmd_diff(args.input)
    if args.cmd == "path":
        print(resolve_state_path())
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
