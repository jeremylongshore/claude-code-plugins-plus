#!/usr/bin/env python3
"""Verify every 6767-h section citation in JSON Schema $comment fields exists.

Usage:
    python scripts/check-prose-anchors.py --doc PATH --schemas PATH [PATH ...]
    python scripts/check-prose-anchors.py --index PATH --schemas PATH [PATH ...]
    stdin: pipe parse-prose-anchors.py output | python scripts/check-prose-anchors.py --schemas ...

Citation pattern: "6767-h § <id>" where <id> is digits/dots or uppercase letter.
Exit 0 = valid, exit 1 = broken anchors found, exit 2 = I/O error.
"""

from __future__ import annotations

import argparse
import glob
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

_CITE_RE = re.compile(r"6767-h\s+§\s*(\d[\d.]*|[A-Z])\b")


def _citations(text: str) -> list[str]:
    return [m.group(1).strip() for m in _CITE_RE.finditer(text)]


def _walk(obj: Any, path: str = "") -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}/{k}" if path else k
            if k == "$comment" and isinstance(v, str):
                out.append((p, v))
            else:
                out.extend(_walk(v, p))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            out.extend(_walk(item, f"{path}[{i}]"))
    return out


def _load_index(path: Path) -> dict[str, dict]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {s["id"]: s for s in raw.get("sections", [])}


def _index_from_doc(doc_path: Path) -> dict[str, dict]:
    spec = importlib.util.spec_from_file_location(
        "parse_prose_anchors", Path(__file__).parent / "parse-prose-anchors.py"
    )
    if spec is None or spec.loader is None:
        raise ImportError("Cannot load parse-prose-anchors.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return {s["id"]: s for s in mod.parse_sections(doc_path.read_text(encoding="utf-8"))}


def _check_schema(path: Path, index: dict[str, dict]) -> list[dict]:
    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return [
            {"schema": str(path), "json_path": "<file>", "comment": "", "cited_id": "<parse-error>", "error": str(exc)}
        ]
    findings: list[dict] = []
    for jpath, text in _walk(schema):
        for cid in _citations(text):
            if cid not in index:
                findings.append(
                    {
                        "schema": str(path),
                        "json_path": jpath,
                        "comment": text,
                        "cited_id": cid,
                        "error": f"Section '{cid}' not found in 6767-h index",
                    }
                )
    return findings


def _expand(patterns: list[str]) -> list[Path]:
    paths: list[Path] = []
    seen: set[Path] = set()
    for pat in patterns:
        for p in glob.glob(pat, recursive=True) or [pat]:
            rp = Path(p).resolve()
            if rp not in seen:
                seen.add(rp)
                paths.append(Path(p))
    return paths


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Check JSON Schema $comment fields for broken 6767-h citations.")
    grp = ap.add_mutually_exclusive_group()
    grp.add_argument("--index", type=Path, default=None)
    grp.add_argument("--doc", type=Path, default=None)
    ap.add_argument("--schemas", nargs="+", required=True, metavar="PATH")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        if args.doc is not None:
            if not args.doc.is_file():
                print(f"ERROR: --doc not found: {args.doc}", file=sys.stderr)
                return 2
            index = _index_from_doc(args.doc.resolve())
        elif args.index is not None:
            if not args.index.is_file():
                print(f"ERROR: --index not found: {args.index}", file=sys.stderr)
                return 2
            index = _load_index(args.index)
        else:
            try:
                index = {s["id"]: s for s in json.load(sys.stdin).get("sections", [])}
            except (json.JSONDecodeError, KeyError) as exc:
                print(f"ERROR reading index from stdin: {exc}", file=sys.stderr)
                return 2
    except Exception as exc:
        print(f"ERROR building index: {exc}", file=sys.stderr)
        return 2
    schema_paths = _expand(args.schemas)
    if not schema_paths:
        print("ERROR: no schema files found.", file=sys.stderr)
        return 2
    all_findings: list[dict] = []
    cite_count = 0
    for sp in schema_paths:
        all_findings.extend(_check_schema(sp, index))
        try:
            for _, text in _walk(json.loads(sp.read_text(encoding="utf-8"))):
                cite_count += len(_citations(text))
        except Exception:
            pass
    report = {
        "index_section_count": len(index),
        "schemas_checked": len(schema_paths),
        "citations_found": cite_count,
        "broken_anchors": all_findings,
        "valid": len(all_findings) == 0,
    }
    if args.json:
        print(json.dumps(report, indent=2))
    elif all_findings:
        print(f"FAIL: {len(all_findings)} broken anchor(s) across {len(schema_paths)} schema(s):", file=sys.stderr)
        for f in all_findings:
            print(f"  {f['schema']} @ {f['json_path']}: cited '{f['cited_id']}' — {f['error']}", file=sys.stderr)
    else:
        print(
            f"OK: {cite_count} citation(s) in {len(schema_paths)} schema(s) all valid ({len(index)} sections in index)."
        )
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
