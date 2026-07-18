#!/usr/bin/env python3
"""dolt-detect.py — universal Dolt flavor/mode auto-detection ("what kind of Dolt
database am I working with?").

The plugin's Step-0 answer for ANY consumer: point this at a directory (default
cwd) and/or an endpoint, and it returns ranked FINDINGS — each one a ready-to-use
connection descriptor (the §2 home: flavor/mode/endpoint/database/creds-ref/
maturity). Detection output IS a descriptor, so it composes with everything
downstream (descriptor-to-mcp-args.py -> dolt-mcp-client.py -> the verb-class
mutation gate). Nothing is guessed: every finding carries its evidence, and an
undetected dir gets a clean "not a Dolt database" with the list of what was
checked.

The taxonomy (every make and model DoltHub ships):

  flavor    mode      detected by                                   posture
  --------  --------  --------------------------------------------  ----------------
  dolt      repo      a `.dolt/` dir (classic repo layout)          full CLI verbs
  dolt      server    live `dolt sql-server` process (cwd matched,  MySQL wire via the
                      ACTUAL bound port read from /proc — never     pinned dolt-mcp-server
                      config.yaml) or a MySQL-wire greeting whose
                      version string contains "dolt"
  dolt      embedded  `.beads/embeddeddolt/<p>/.dolt` layout or     read-only CLI verbs
                      `.beads/metadata.json` dolt_mode:"embedded"   (single-writer .lock is
                                                                    owned by the embedding
                                                                    tool, e.g. bd)
  doltgres  server    Postgres-wire probe / version signature       Postgres wire via
                      containing "doltgres"                         --doltgres
  doltlite  file      single-file DB whose header starts with the   detect + report; local
                      chunk-store magic b"CTLD" (LE 0x444C5443,     doltlite CLI verbs;
                      verified against dolthub/doltlite             alpha => read-only;
                      src/chunk_store.h CHUNK_STORE_MAGIC)          no wire (decision 6)
  dumbo     server    `dumbo` process / Mongo-wire version string   detect + report only
                      containing "dumbo"                            (experimental,
                                                                    fail-closed)
  (none)    -         nothing matched                               honest negative

Mixed layouts (a workspace with BOTH `.beads/dolt/` and `.beads/embeddeddolt/`,
i.e. migrated state) return BOTH findings, ranked live-server > repo > embedded.
A plain-SQLite file (header "SQLite format 3\\0") is NOT a Dolt database, but when
it sits next to a Dolt repo sidecar (the sqlite-runtime + dolt-system-of-record
pattern, e.g. freshie) the pairing is recorded as evidence on the repo finding.

Pure functions (no dolt binary, no filesystem — unit-tested with fixtures):
  sniff_header, classify_dolt_dirs, interpret_metadata, flavor_from_version,
  parse_mysql_greeting, port_from_cmdline, parse_tcp_listen_ports,
  match_server_to_store, assemble_descriptor, rank_findings
Thin wrappers do the actual filesystem/pgrep//proc/socket probes.

Usage:
  dolt-detect.py [PATH] [--endpoint HOST:PORT] [--json]
                 [--emit-descriptor [PATH]] [--no-processes] [--depth N]
Exit: 0 findings returned · 1 nothing detected · 2 usage/probe error.
Read-only: never starts, stops, or writes to any database.
"""
import argparse
import json
import os
import re
import socket
import subprocess
import sys

# ---------------------------------------------------------------- constants

SQLITE_MAGIC = b"SQLite format 3\x00"
# dolthub/doltlite src/chunk_store.h: #define CHUNK_STORE_MAGIC 0x444C5443
# written little-endian by CS_WRITE_U32 -> on-disk bytes are b"CTLD".
DOLTLITE_MAGIC = b"CTLD"

# Default maturity per flavor (product family map, 000-docs/001). The descriptor
# maturity drives the sql_classifier gate: alpha/experimental => read-only.
FLAVOR_MATURITY = {"dolt": "ga", "doltgres": "beta",
                   "doltlite": "alpha", "dumbo": "experimental"}

# Lower rank sorts first: a live wire beats a repo beats an embedded store.
MODE_RANK = {"server": 0, "repo": 1, "embedded": 2, "file": 3}

DOLTLITE_SUFFIXES = (".db", ".sqlite", ".sqlite3", ".doltlite")

CHECKS_DESCRIPTION = [
    ".dolt/ directory (classic Dolt repo), scanned to --depth",
    ".beads/dolt/<prefix>/.dolt (bd server-mode store)",
    ".beads/embeddeddolt/<prefix>/.dolt (bd embedded store)",
    ".beads/metadata.json dolt_mode marker",
    "live `dolt sql-server` processes (cwd + actual bound port via /proc)",
    "live `dumbo` processes",
    "single-file DB headers (DoltLite chunk-store magic b'CTLD'; "
    "plain SQLite noted, not claimed)",
    "--endpoint wire greeting (MySQL handshake version string)",
]


def eprint(*a):
    print(*a, file=sys.stderr)


# ---------------------------------------------------------------- pure logic

def sniff_header(header):
    """First bytes of a candidate file -> 'sqlite' | 'doltlite' | None."""
    if header[:16] == SQLITE_MAGIC:
        return "sqlite"
    if header[:4] == DOLTLITE_MAGIC:
        return "doltlite"
    return None


def classify_dolt_dirs(dolt_parents):
    """Relative paths of dirs CONTAINING a `.dolt/` -> layout findings.

    '' (the root itself) or any other parent => classic repo; a parent under
    .beads/embeddeddolt/ => embedded store; under .beads/dolt/ => server-mode
    store (mode 'server' is only claimed once a live process/port is matched —
    until then it is reported as a server-mode STORE with endpoint unknown).
    """
    findings = []
    for parent in sorted(dolt_parents):
        norm = parent.replace(os.sep, "/").strip("/")
        segs = norm.split("/") if norm else []
        name = segs[-1] if segs else ""
        if norm.endswith((".beads/dolt", ".beads/embeddeddolt")):
            # bd's data-dir root itself carries a .dolt marker; the databases are
            # its CHILDREN — the root is not a database, so it is never a finding.
            continue
        if ".beads/embeddeddolt/" in f"/{norm}/":
            findings.append({"flavor": "dolt", "mode": "embedded",
                             "database": name, "path": norm,
                             "evidence": f"{norm or '.'}/.dolt under .beads/embeddeddolt/ "
                                         "(single-writer embedded store)"})
        elif ".beads/dolt/" in f"/{norm}/":
            findings.append({"flavor": "dolt", "mode": "server",
                             "database": name, "path": norm, "live": False,
                             "evidence": f"{norm or '.'}/.dolt under .beads/dolt/ "
                                         "(bd server-mode store)"})
        else:
            findings.append({"flavor": "dolt", "mode": "repo",
                             "database": name, "path": norm,
                             "evidence": f"{norm or '.'}/.dolt (classic Dolt repo)"})
    return findings


def interpret_metadata(meta):
    """.beads/metadata.json dict -> partial finding or None (machine marker)."""
    if not isinstance(meta, dict):
        return None
    mode = str(meta.get("dolt_mode", "")).lower()
    if mode == "embedded":
        return {"flavor": "dolt", "mode": "embedded",
                "database": meta.get("dolt_database") or "",
                "evidence": '.beads/metadata.json dolt_mode:"embedded"'}
    if mode in ("server", "sql-server"):
        return {"flavor": "dolt", "mode": "server", "live": False,
                "database": meta.get("dolt_database") or "",
                "evidence": f'.beads/metadata.json dolt_mode:"{mode}"'}
    return None


def flavor_from_version(version_string):
    """A server version string (any wire) -> flavor or None. Case-insensitive;
    'dumbo' and 'doltgres' are checked before the 'dolt' substring they contain."""
    s = (version_string or "").lower()
    if "dumbo" in s:
        return "dumbo"
    if "doltgres" in s:
        return "doltgres"
    if "dolt" in s:
        return "dolt"
    return None


def parse_mysql_greeting(data):
    """Raw bytes of the MySQL initial handshake -> server version string or None.
    Layout: 3-byte length + 1-byte seq, then protocol version (0x0a), then a
    NUL-terminated human-readable version string."""
    if len(data) < 6 or data[4] != 0x0A:
        return None
    end = data.find(b"\x00", 5)
    if end < 0:
        return None
    try:
        return data[5:end].decode("utf-8", "replace")
    except Exception:
        return None


def port_from_cmdline(cmdline):
    """A process cmdline string -> declared port (int) or None. This is only the
    DECLARED port (-P/--port); the ACTUAL bound port comes from /proc/net/tcp —
    bd's live servers routinely bind an ephemeral port that differs from
    config.yaml, so a declared port is never trusted on its own."""
    m = re.search(r"(?:^|\s)(?:-P|--port(?:=|\s))\s*(\d+)", cmdline)
    return int(m.group(1)) if m else None


def parse_tcp_listen_ports(tcp_text, inodes):
    """/proc/net/tcp[6] content + the process's socket inodes -> sorted list of
    LISTEN local ports actually bound by that process."""
    ports = set()
    want = {str(i) for i in inodes}
    for line in tcp_text.splitlines()[1:]:
        parts = line.split()
        if len(parts) < 10:
            continue
        local, state, inode = parts[1], parts[3], parts[9]
        if state != "0A" or inode not in want:  # 0A = TCP_LISTEN
            continue
        try:
            ports.add(int(local.rsplit(":", 1)[1], 16))
        except (ValueError, IndexError):
            continue
    return sorted(ports)


def match_server_to_store(store_abs, proc_cwd):
    """Does a live dolt sql-server (cwd proc_cwd) serve the store at store_abs?
    True when one path contains the other (bd runs the server from the workspace
    or from the .beads data dir)."""
    if not store_abs or not proc_cwd:
        return False
    a = os.path.normpath(store_abs)
    c = os.path.normpath(proc_cwd)
    return a == c or a.startswith(c + os.sep) or c.startswith(a + os.sep)


def assemble_descriptor(finding, root_abs=""):
    """A finding -> a connection descriptor (the §2 contract + additive `mode`).
    Server findings get host:port; everything else gets a file: endpoint that the
    transform layer refuses to turn into a wire connection (CLI-verb posture)."""
    flavor = finding["flavor"]
    mode = finding["mode"]
    if mode == "server" and finding.get("live"):
        endpoint = f"{finding.get('host', '127.0.0.1')}:{finding['port']}"
    else:
        p = finding.get("path", "")
        endpoint = "file:" + (os.path.join(root_abs, p) if root_abs and not os.path.isabs(p) else p)
    return {
        "flavor": flavor,
        "mode": mode,
        "endpoint": endpoint,
        "database": finding.get("database") or "",
        "creds-ref": "env:DOLT_PASSWORD",
        "maturity": FLAVOR_MATURITY.get(flavor, "experimental"),
    }


def rank_findings(findings):
    """live-server first, then repo, then embedded, then files; stable by path."""
    return sorted(findings, key=lambda f: (
        MODE_RANK.get(f["mode"], 9),
        0 if f.get("live") else 1,
        f.get("path", "") or f.get("endpoint", ""),
    ))


# ------------------------------------------------------------- thin wrappers

def walk_dolt_layout(root, depth):
    """Find every `.dolt/` (parent paths, relative), the .beads metadata dict,
    and candidate single-file DBs — bounded depth, never following symlinks."""
    dolt_parents, db_files, meta = [], [], None
    root = os.path.abspath(root)
    base_depth = root.rstrip(os.sep).count(os.sep)
    for cur, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [d for d in dirs if d not in
                   {".git", "node_modules", "__pycache__", ".venv"}]
        if ".dolt" in dirs:
            dolt_parents.append(os.path.relpath(cur, root))
            dirs.remove(".dolt")  # never descend into the store itself
        for f in files:
            if f.lower().endswith(DOLTLITE_SUFFIXES):
                db_files.append(os.path.join(cur, f))
        # classify the CURRENT level first, then prune descent at the limit —
        # a store sitting exactly at --depth must still be found.
        if cur.rstrip(os.sep).count(os.sep) - base_depth >= depth:
            dirs[:] = []
    dolt_parents = ["" if p == "." else p for p in dolt_parents]
    meta_path = os.path.join(root, ".beads", "metadata.json")
    if os.path.isfile(meta_path):
        try:
            with open(meta_path) as fh:
                meta = json.load(fh)
        except (OSError, json.JSONDecodeError):
            meta = None
    return dolt_parents, db_files, meta


def sniff_db_files(paths):
    """Header-sniff candidate files -> (doltlite findings, plain-sqlite paths)."""
    doltlite, sqlite_paths = [], []
    for p in paths:
        try:
            with open(p, "rb") as fh:
                kind = sniff_header(fh.read(16))
        except OSError:
            continue
        if kind == "doltlite":
            doltlite.append({"flavor": "doltlite", "mode": "file",
                             "database": os.path.splitext(os.path.basename(p))[0],
                             "path": p,
                             "evidence": f"{p}: chunk-store magic b'CTLD' "
                                         "(DoltLite prolly-tree single-file DB)"})
        elif kind == "sqlite":
            sqlite_paths.append(p)
    return doltlite, sqlite_paths


def live_dolt_servers():
    """pgrep + /proc -> [{pid, cwd, ports, declared_port, cmdline}] for every
    running `dolt sql-server`. Ports are the ACTUAL bound LISTEN ports."""
    try:
        out = subprocess.run(["pgrep", "-f", "dolt sql-server"],
                             capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.TimeoutExpired):
        return []
    servers = []
    for pid in out.split():
        try:
            with open(f"/proc/{pid}/cmdline", "rb") as fh:
                cmdline = fh.read().replace(b"\x00", b" ").decode("utf-8", "replace")
            if "dolt sql-server" not in cmdline:
                continue
            cwd = os.readlink(f"/proc/{pid}/cwd")
            inodes = []
            for fd in os.listdir(f"/proc/{pid}/fd"):
                try:
                    tgt = os.readlink(f"/proc/{pid}/fd/{fd}")
                except OSError:
                    continue
                m = re.match(r"socket:\[(\d+)\]", tgt)
                if m:
                    inodes.append(m.group(1))
            ports = []
            for tbl in ("tcp", "tcp6"):
                try:
                    with open(f"/proc/{pid}/net/{tbl}") as fh:
                        ports += parse_tcp_listen_ports(fh.read(), inodes)
                except OSError:
                    continue
            servers.append({"pid": int(pid), "cwd": cwd,
                            "ports": sorted(set(ports)),
                            "declared_port": port_from_cmdline(cmdline),
                            "cmdline": cmdline.strip()})
        except (OSError, ValueError):
            continue
    return servers


def live_dumbo_servers():
    """pgrep for a DumboDB process (experimental; detect-and-tell only)."""
    try:
        out = subprocess.run(["pgrep", "-af", r"dumbo"],
                             capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.TimeoutExpired):
        return []
    hits = []
    for line in out.splitlines():
        pid, _, cmd = line.partition(" ")
        if re.search(r"(^|/)dumbo(db)?\b", cmd):
            hits.append({"pid": int(pid), "cmdline": cmd.strip()})
    return hits


def probe_endpoint(host, port, timeout=3.0):
    """Best-effort wire greeting read. MySQL sends its handshake unprompted;
    the version string names the flavor. Anything else is reported honestly as
    unconfirmed — never guessed."""
    try:
        with socket.create_connection((host, port), timeout=timeout) as s:
            s.settimeout(timeout)
            try:
                data = s.recv(256)
            except socket.timeout:
                data = b""
    except OSError as e:
        return {"error": f"connect {host}:{port} failed: {e}"}
    version = parse_mysql_greeting(data)
    if version:
        flavor = flavor_from_version(version)
        result = {"wire": "mysql", "version": version, "flavor": flavor}
        if not flavor:
            # dolt sql-server greets with a plain MySQL version (e.g. "8.0.33")
            # — the greeting alone cannot confirm Dolt. The caller cross-checks
            # the port against live dolt processes; failing that, only an
            # authenticated `SELECT dolt_version()` settles it. Never guessed.
            result["note"] = ("MySQL wire confirmed but the greeting does not "
                              "name the flavor; verify with SELECT dolt_version()")
        return result
    return {"wire": "unknown",
            "note": "endpoint is open but sent no MySQL greeting; if this is "
                    "Doltgres (Postgres wire), verify with credentials — "
                    "flavor NOT confirmed, not guessed"}


# --------------------------------------------------------------------- main

def detect(root, depth=4, with_processes=True):
    root_abs = os.path.abspath(root)
    dolt_parents, db_files, meta = walk_dolt_layout(root_abs, depth)
    findings = classify_dolt_dirs(dolt_parents)

    # metadata.json marker: corroborates or adds an embedded finding
    meta_f = interpret_metadata(meta) if meta else None
    if meta_f:
        dup = [f for f in findings if f["mode"] == meta_f["mode"]
               and (not meta_f["database"] or f["database"] == meta_f["database"])]
        if dup:
            dup[0]["evidence"] += " + " + meta_f["evidence"]
        else:
            meta_f["path"] = ".beads"
            findings.append(meta_f)

    doltlite_f, sqlite_paths = sniff_db_files(db_files)
    findings += doltlite_f
    # sqlite runtime + dolt sidecar pairing (system-of-record pattern): only a
    # repo under a `dolt/` folder pairs, and only with SQLite files sitting in
    # the directory that CONTAINS that folder — never any .db anywhere.
    for f in findings:
        if f["mode"] != "repo":
            continue
        segs = (f.get("path") or "").split("/")
        if "dolt" not in segs[:-1]:
            continue
        project_rel = "/".join(segs[:segs.index("dolt")])
        project_abs = os.path.normpath(os.path.join(root_abs, project_rel))
        paired = [p for p in sqlite_paths
                  if os.path.normpath(os.path.dirname(p)) == project_abs]
        if paired:
            f["evidence"] += ("; paired plain-SQLite runtime file(s) "
                              f"({', '.join(os.path.basename(p) for p in paired[:3])}) — "
                              "sqlite-runtime + Dolt-system-of-record pattern")

    if with_processes:
        for srv in live_dolt_servers():
            for f in findings:
                if f["mode"] != "server" or f.get("live"):
                    continue
                store_abs = os.path.join(root_abs, f.get("path", ""))
                if match_server_to_store(store_abs, srv["cwd"]) and srv["ports"]:
                    f["live"] = True
                    f["host"], f["port"] = "127.0.0.1", srv["ports"][0]
                    note = ""
                    if srv["declared_port"] and srv["declared_port"] not in srv["ports"]:
                        note = (f" (declared -P {srv['declared_port']} but actually "
                                f"bound {srv['ports']} — trust /proc, not config.yaml)")
                    f["evidence"] += (f" + live dolt sql-server pid {srv['pid']} "
                                      f"bound port {srv['ports'][0]}{note}")
        for d in live_dumbo_servers():
            findings.append({"flavor": "dumbo", "mode": "server", "live": True,
                             "database": "", "path": "",
                             "evidence": f"dumbo process pid {d['pid']}: {d['cmdline']} "
                                         "(experimental — detect-and-report only)"})

    # a server-mode store with no live server stays honest: it degrades to the
    # embedded rank (it is a .dolt on disk you can read with CLI verbs).
    for f in findings:
        if f["mode"] == "server" and not f.get("live"):
            f["evidence"] += "; no live server matched — treat as at-rest store"
    return rank_findings(findings), sqlite_paths


def main():
    ap = argparse.ArgumentParser(
        description="universal Dolt flavor/mode auto-detection (read-only)")
    ap.add_argument("path", nargs="?", default=".",
                    help="directory to inspect (default: cwd)")
    ap.add_argument("--endpoint", help="also probe HOST:PORT on the wire")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--emit-descriptor", nargs="?", const="connection.descriptor.json",
                    metavar="PATH", help="write the top-ranked finding as a "
                    "connection descriptor (default: connection.descriptor.json)")
    ap.add_argument("--no-processes", action="store_true",
                    help="skip pgrep//proc process probes")
    ap.add_argument("--depth", type=int, default=4, help="directory scan depth")
    args = ap.parse_args()

    if not os.path.isdir(args.path):
        eprint(f"error: '{args.path}' is not a directory")
        return 2

    findings, sqlite_paths = detect(args.path, depth=args.depth,
                                    with_processes=not args.no_processes)

    endpoint_result = None
    if args.endpoint:
        host, _, port = args.endpoint.partition(":")
        if not port.isdigit():
            eprint("error: --endpoint must be HOST:PORT")
            return 2
        endpoint_result = probe_endpoint(host or "127.0.0.1", int(port))
        if (endpoint_result.get("wire") == "mysql"
                and not endpoint_result.get("flavor")
                and not args.no_processes):
            # evidence-based confirmation: does a live dolt sql-server own this
            # port? (the greeting is a plain MySQL version for real Dolt servers)
            for srv in live_dolt_servers():
                if int(port) in srv["ports"]:
                    endpoint_result["flavor"] = "dolt"
                    endpoint_result["confirmed_by"] = (
                        f"live dolt sql-server pid {srv['pid']} is bound to port {port}")
                    break
        flavor = endpoint_result.get("flavor")
        if flavor:
            ev = f"wire greeting at {args.endpoint}: '{endpoint_result['version']}'"
            if endpoint_result.get("confirmed_by"):
                ev += f" + {endpoint_result['confirmed_by']}"
            findings.insert(0, {
                "flavor": flavor, "mode": "server", "live": True,
                "host": host or "127.0.0.1", "port": int(port), "database": "",
                "path": "", "evidence": ev})

    root_abs = os.path.abspath(args.path)
    descriptors = [assemble_descriptor(f, root_abs) for f in findings]

    if args.json:
        print(json.dumps({"root": root_abs, "findings": [
            {**f, "descriptor": d} for f, d in zip(findings, descriptors)],
            "endpoint_probe": endpoint_result,
            "plain_sqlite": sqlite_paths,
            "checked": CHECKS_DESCRIPTION}, indent=2))
    else:
        if findings:
            print(f"# {len(findings)} Dolt finding(s) under {root_abs} "
                  "(ranked live-server > repo > embedded > file):")
            for f, d in zip(findings, descriptors):
                live = " [LIVE]" if f.get("live") else ""
                print(f"  {f['flavor']}/{f['mode']}{live}  db={d['database'] or '?'}  "
                      f"endpoint={d['endpoint']}")
                print(f"    evidence: {f['evidence']}")
        if endpoint_result and not endpoint_result.get("flavor"):
            print(f"# endpoint probe: {json.dumps(endpoint_result)}")
        if sqlite_paths and not findings:
            print("# plain SQLite file(s) found (NOT a Dolt database): "
                  + ", ".join(sqlite_paths))

    if args.emit_descriptor and findings:
        top = descriptors[0]
        with open(args.emit_descriptor, "w") as fh:
            json.dump(top, fh, indent=2)
            fh.write("\n")
        eprint(f"# wrote top-ranked descriptor -> {args.emit_descriptor} "
               f"({top['flavor']}/{top['mode']} @ {top['endpoint']})")

    if not findings:
        print(f"# This is not a Dolt database (checked under {root_abs}):")
        for c in CHECKS_DESCRIPTION:
            print(f"#   - {c}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
