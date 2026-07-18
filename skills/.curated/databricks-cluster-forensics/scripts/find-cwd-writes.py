#!/usr/bin/env python3
"""find-cwd-writes.py — flag Python writes to the current working directory that
DBR 14.x's 500 MB workspace-filesystem cap silently breaks (bead c54a / pain D03).

DBR 14.x moved a cluster's default working directory onto the workspace filesystem,
which carries a ~500 MB quota. Any job that writes intermediate files to a
RELATIVE path (the CWD) — a common pattern in notebooks lifted from local dev —
keeps working until the data crosses 500 MB, then fails with a quota error that
names neither the cause nor the offending line. This scanner reads the source with
Python's AST (no execution) and reports every write whose destination is a
relative/CWD path, so the upgrade review sees them before the pipeline breaks in
prod.

It classifies each write destination:
  CWD        a relative path literal (or bare filename) → AT RISK under the cap
  SAFE       an absolute cloud / DBFS / Volumes / /tmp path → not on the WSFS quota
  DYNAMIC    a computed path (variable / f-string / os.path.join) → NEEDS REVIEW
             (the scanner cannot prove where it lands)

Write sinks recognized: builtin open(..., 'w'|'wb'|'a'|'x'); pandas
DataFrame.to_csv/to_parquet/to_json/to_pickle/to_feather/to_excel/to_hdf; Spark
`.write.save/csv/parquet/json/text/orc(path)` and `.save(path)`; numpy save/savetxt;
pickle.dump(to a path via open); plain Path(...).write_text/write_bytes.

Input: file/dir paths as args (recurses dirs for *.py), or stdin ('-').
Output: a table (default) or --json. --risk-only prints only CWD (at-risk) rows.
Exit codes: 0 ok (findings are data) · 2 bad usage · 1 a file failed to parse
            (syntax error) AND --strict was given.
"""

import argparse
import ast
import json
import os
import sys

WRITE_OPEN_MODES = ("w", "wb", "a", "ab", "x", "xb", "w+", "r+", "a+")
# method name -> index of the positional path argument
PANDAS_WRITERS = {
    "to_csv": 0,
    "to_parquet": 0,
    "to_json": 0,
    "to_pickle": 0,
    "to_feather": 0,
    "to_excel": 0,
    "to_hdf": 0,
    "to_orc": 0,
}
SPARK_WRITERS = {"save": 0, "csv": 0, "parquet": 0, "json": 0, "text": 0, "orc": 0}
NUMPY_WRITERS = {"save": 0, "savetxt": 0, "savez": 0}
PATH_WRITE_METHODS = ("write_text", "write_bytes")

CWD, SAFE, DYNAMIC = "CWD", "SAFE", "DYNAMIC"

# Prefixes that are NOT on the workspace-filesystem quota (safe destinations).
SAFE_PREFIXES = (
    "/dbfs/",
    "dbfs:/",
    "/Volumes/",
    "/tmp/",
    "/local_disk0/",
    "/mnt/",
    "s3://",
    "s3a://",
    "abfss://",
    "gs://",
    "wasbs://",
    "file:/",
)


def classify_path(node):
    """Classify a path AST node → (kind, literal_or_None)."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        p = node.value
        low = p.lower()
        if p.startswith("/") or any(low.startswith(sp) for sp in SAFE_PREFIXES):
            # Absolute — safe unless it is a bare "/" workspace-root relative write,
            # which does not happen for the safe prefixes above.
            if any(low.startswith(sp) for sp in SAFE_PREFIXES) or p.startswith(
                ("/dbfs", "/Volumes", "/tmp", "/local_disk0", "/mnt")
            ):
                return SAFE, p
            # Some other absolute path (e.g. /home/..., /root/...) — on the driver
            # local FS, not the WSFS quota, so also safe from THIS cap.
            return SAFE, p
        return CWD, p  # relative literal or bare filename → CWD
    return DYNAMIC, None  # variable, f-string, os.path.join, etc.


def _write_sink(call):
    """If this Call is a recognized write to a path, return (sink_label, path_node)."""
    fn = call.func
    # builtin open(path, mode) with a write mode
    if isinstance(fn, ast.Name) and fn.id == "open" and call.args:
        mode = None
        if len(call.args) >= 2 and isinstance(call.args[1], ast.Constant):
            mode = call.args[1].value
        for kw in call.keywords:
            if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                mode = kw.value.value
        if mode is None or (isinstance(mode, str) and mode in WRITE_OPEN_MODES):
            if isinstance(mode, str) and mode in WRITE_OPEN_MODES:
                return "open", call.args[0]
        return None
    if isinstance(fn, ast.Attribute):
        m = fn.attr
        table = None
        if m in PANDAS_WRITERS:
            table = PANDAS_WRITERS
        elif m in SPARK_WRITERS:
            table = SPARK_WRITERS
        elif m in NUMPY_WRITERS:
            table = NUMPY_WRITERS
        elif m in PATH_WRITE_METHODS:
            # Path(x).write_text(...) — the path is on the RECEIVER, not an arg.
            recv = fn.value
            if isinstance(recv, ast.Call) and _is_path_ctor(recv) and recv.args:
                return f".{m}", recv.args[0]
            return None
        if table is not None and call.args and len(call.args) > table[m]:
            return f".{m}", call.args[table[m]]
    return None


def _is_path_ctor(call):
    f = call.func
    return (isinstance(f, ast.Name) and f.id in ("Path", "PurePath")) or (
        isinstance(f, ast.Attribute) and f.attr in ("Path", "PurePath")
    )


def find_cwd_writes(source, filename="<src>"):
    """Return a list of write findings. Pure — parses, never executes."""
    tree = ast.parse(source, filename=filename)
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        sink = _write_sink(node)
        if sink is None:
            continue
        label, path_node = sink
        kind, literal = classify_path(path_node)
        out.append(
            {
                "file": filename,
                "line": getattr(node, "lineno", 0),
                "sink": label,
                "kind": kind,
                "path": literal,
            }
        )
    return out


def _iter_py(paths):
    for p in paths:
        if p == "-":
            yield "<stdin>", sys.stdin.read()
            continue
        if os.path.isdir(p):
            for root, _d, files in os.walk(p):
                for f in files:
                    if f.endswith(".py"):
                        fp = os.path.join(root, f)
                        yield fp, open(fp, encoding="utf-8", errors="replace").read()
        else:
            yield p, open(p, encoding="utf-8", errors="replace").read()


def main():
    ap = argparse.ArgumentParser(description="Flag DBR-14 CWD (500MB-cap) writes in Python")
    ap.add_argument("paths", nargs="+", help="python files/dirs (recurses), or '-' for stdin")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--risk-only", action="store_true", help="only CWD (at-risk) findings")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any file fails to parse")
    args = ap.parse_args()

    findings, parse_errors = [], 0
    for name, src in _iter_py(args.paths):
        try:
            findings.extend(find_cwd_writes(src, name))
        except SyntaxError as e:
            parse_errors += 1
            print(f"parse error in {name}: {e}", file=sys.stderr)

    if args.risk_only:
        findings = [f for f in findings if f["kind"] == CWD]

    if args.json:
        print(json.dumps(findings, indent=2))
    else:
        n_risk = sum(1 for f in findings if f["kind"] == CWD)
        n_dyn = sum(1 for f in findings if f["kind"] == DYNAMIC)
        print(f"{len(findings)} write(s): {n_risk} AT RISK (CWD), {n_dyn} needs-review (dynamic)")
        for f in findings:
            flag = "AT RISK" if f["kind"] == CWD else ("review" if f["kind"] == DYNAMIC else "safe")
            print(f"  {f['file']}:{f['line']}  {f['sink']:<12} [{flag}] {f['path'] or '(dynamic path)'}")
    return 1 if (parse_errors and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
