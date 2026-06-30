#!/usr/bin/env python3
"""descriptor-to-mcp-args.py — the connection-descriptor -> .mcp.json transform,
plus the descriptor validator rule (blueprint §2 / the creds-ref MAJOR).

Reads a `connection.descriptor.json` (the committed per-workspace home), VALIDATES
it, and emits the `dolt-mcp-server` args + env the .mcp.json wires — turning
`flavor`/`endpoint`/`database`/`maturity` from frozen literals into data.

Validator rule (fail-closed): the run is rejected (exit 2) if
  * a required field is missing (flavor, endpoint, database, creds-ref, maturity);
  * `flavor` is not a known flavor;
  * `maturity` is not ga|beta|alpha|experimental;
  * `creds-ref` does not start with a known `scheme:` (env:/sops:/pass:) — a
    creds-ref is a pointer, never a literal, so anything without a known scheme is
    refused rather than silently treated as a password.
Alpha/experimental flavors are emitted with DOLT_MATURITY set so the client gate
(sql_classifier.gate_decision) holds them to read-only.

Usage:
  descriptor-to-mcp-args.py [--descriptor connection.descriptor.json] [--format json|args]
    --format json  (default) -> {"args": [...], "env": {...}}  (machine-readable)
    --format args             -> the args, space-joined (for eyeballing)
Exit: 0 ok · 2 invalid descriptor / unknown scheme.
"""
import argparse
import json
import os
import sys

REQUIRED = ("flavor", "endpoint", "database", "creds-ref", "maturity")
FLAVOR_CONNECT = {"dolt": "--dolt", "doltgres": "--doltgres"}
# alpha/experimental flavors have no wired connect flag yet (descriptor-stub only,
# decision 6) — they validate but cannot be transformed into a live connection.
FLAVOR_STUB = {"doltlite", "dumbo"}
MATURITIES = {"ga", "beta", "alpha", "experimental"}
KNOWN_CREDS_SCHEMES = ("env:", "sops:", "pass:")


def eprint(*a):
    print(*a, file=sys.stderr)


def validate(d):
    errs = []
    for f in REQUIRED:
        if not d.get(f):
            errs.append(f"missing required field '{f}'")
    flavor = d.get("flavor")
    if flavor and flavor not in FLAVOR_CONNECT and flavor not in FLAVOR_STUB:
        errs.append(f"unknown flavor '{flavor}' (known: "
                    f"{', '.join(sorted(set(FLAVOR_CONNECT) | FLAVOR_STUB))})")
    maturity = (d.get("maturity") or "").lower()
    if maturity and maturity not in MATURITIES:
        errs.append(f"unknown maturity '{maturity}' (known: {', '.join(sorted(MATURITIES))})")
    cref = d.get("creds-ref")
    if cref and not str(cref).startswith(KNOWN_CREDS_SCHEMES):
        errs.append(f"creds-ref '{cref}' has no known scheme prefix "
                    f"({', '.join(KNOWN_CREDS_SCHEMES)}); a creds-ref must be a pointer, "
                    "never a literal secret")
    return errs


def split_endpoint(endpoint):
    host, _, port = endpoint.partition(":")
    return host or "127.0.0.1", port or "3308"


def transform(d):
    flavor = d["flavor"]
    if flavor in FLAVOR_STUB:
        raise ValueError(f"flavor '{flavor}' is a descriptor-stub (pre-beta) — no live "
                         "connection flag is wired yet (decision 6). It validates but "
                         "cannot be transformed until dolt-watch reports it has reached beta.")
    host, port = split_endpoint(d["endpoint"])
    user = os.environ.get("DOLT_USER", "root")
    args = ["--stdio", FLAVOR_CONNECT[flavor],
            "--host", host, "--port", port,
            "--user", user, "--database", d["database"]]
    env = {
        # the secret is resolved at runtime from the creds-ref pointer (never inlined)
        "DOLT_PASSWORD": "${DOLT_PASSWORD:-}",
        "DOLT_MATURITY": d["maturity"].lower(),
    }
    return {"args": args, "env": env, "creds-ref": d["creds-ref"]}


def main():
    ap = argparse.ArgumentParser(description="connection-descriptor -> .mcp.json args (validated)")
    ap.add_argument("--descriptor", default="connection.descriptor.json")
    ap.add_argument("--format", choices=["json", "args"], default="json")
    args = ap.parse_args()

    try:
        with open(args.descriptor) as fh:
            d = json.load(fh)
    except (OSError, json.JSONDecodeError) as e:
        eprint(f"error: cannot read descriptor '{args.descriptor}': {e}")
        return 2

    errs = validate(d)
    if errs:
        eprint(f"invalid descriptor '{args.descriptor}':")
        for e in errs:
            eprint(f"  - {e}")
        return 2

    try:
        out = transform(d)
    except ValueError as e:
        eprint(f"error: {e}")
        return 2

    if args.format == "args":
        print(" ".join(out["args"]))
    else:
        print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
