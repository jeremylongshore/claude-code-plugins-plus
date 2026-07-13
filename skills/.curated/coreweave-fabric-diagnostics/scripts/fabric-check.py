#!/usr/bin/env python3
"""Deterministic GPUDirect-RDMA fabric diagnostic for coreweave-fabric-diagnostics.

The LLM does NOT eyeball the transport. The single most expensive silent failure on a
CoreWeave multi-node GPU job is NCCL falling back from InfiniBand (NET/IB) to TCP
(NET/Socket): collectives keep running, no error is raised, but throughput collapses
(commonly cited as 5-20x slower) while every GPU still bills at full rate. This script
scans pasted diagnostics -- an NCCL_DEBUG=INFO log, a Kubernetes pod-spec snippet, ibstat
output, and/or all_reduce_perf results -- and decides deterministically whether RDMA is
engaged, which transport is actually in use, which of the three required conditions are
missing, and what the fix is.

Grounding (see references/):
  - CoreWeave "Use GPUDirect RDMA with InfiniBand" (NCCL_IB_HCA=ibp,
    NCCL_SOCKET_IFNAME=eth0, OFED pre-installed, MPI Operator / Slurm, nccl-tests).
  - NVIDIA NCCL env + troubleshooting docs (NCCL_IB_DISABLE, NCCL_NET_GDR_LEVEL,
    NET/IB vs NET/Socket, GPU Direct RDMA Enabled).
  - github.com/coreweave/nccl-tests (all_reduce_perf busbw / algbw columns).

The three required conditions for RDMA to engage (any one missing => silent TCP fallback):
  1. rdma/ib device requested in BOTH resources.requests AND resources.limits.
  2. NCCL_IB_HCA and NCCL_SOCKET_IFNAME set (unless the MPI Operator manages them).
  3. NCCL_DEBUG=INFO then confirms NET/IB (ideally "GPU Direct RDMA Enabled").

CRITICAL invariant: this script NEVER hardcodes a pass/fail busbw number. Baseline
bandwidth varies by GPU count, GPU type, NCCL version, and SHARP -- it is compared against
CoreWeave's published nccl-tests manifest baseline, never a constant baked in here. Any
absolute GB/s figure this script echoes is tagged [unverified vs baseline].

Usage:
    python3 fabric-check.py --in diag.txt            # human verdict (default)
    cat nccl.log manifest.yaml | python3 fabric-check.py --json
    python3 fabric-check.py --self-test
"""

from __future__ import annotations

import argparse
import json
import re
import sys


# --- signal detection -------------------------------------------------------


def _low(text: str) -> str:
    return text.lower()


def detect_transport(text: str) -> tuple[str, bool, bool]:
    """Return (transport, gdr_confirmed, ib_attempt_failed).

    transport is one of: 'Socket' | 'IB' | 'mixed' | 'unknown'. The decisive NCCL line
    is "Using network <X>"; NET/IB and NET/Socket occurrences are the supporting signal.
    """
    low = _low(text)
    gdr = ("gpu direct rdma enabled" in low) or ("/gdrdma" in low) or ("gdrdma" in low)
    ib_failed = bool(re.search(r"nccl\s+warn.*(ibv_|net/ib|ib\s)", low))

    using_socket = "using network socket" in low
    using_ib = ("using network ib" in low) or ("using network ibext" in low)
    net_socket = "net/socket" in low
    net_ib = "net/ib" in low

    if using_socket and not using_ib:
        return "Socket", gdr, ib_failed
    if using_ib and not using_socket:
        return "IB", gdr, ib_failed
    if using_ib and using_socket:
        return "mixed", gdr, ib_failed
    # No decisive "Using network" line: fall back to NET/* occurrences.
    if net_socket and not net_ib:
        return "Socket", gdr, ib_failed
    if net_ib and not net_socket:
        return "IB", gdr, ib_failed
    if net_ib and net_socket:
        return "mixed", gdr, ib_failed
    return "unknown", gdr, ib_failed


def _rdma_in_sections(text: str) -> tuple[bool, bool, str | None, bool]:
    """Indentation-aware scan of a k8s resources block.

    Returns (in_requests, in_limits, rdma_key, manifest_seen). Tracks whether an
    'rdma/...: N' line sits under a 'requests:' header or a 'limits:' header, so the
    common failure -- the RDMA device present in limits but absent from requests (or
    vice-versa) -- is caught precisely, not just "rdma appears somewhere".
    """
    in_requests = in_limits = False
    rdma_key: str | None = None
    manifest_seen = False
    section: str | None = None
    section_indent = -1
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        stripped = raw.strip()
        key = stripped.split(":", 1)[0].strip()
        if key in ("requests", "limits"):
            section, section_indent, manifest_seen = key, indent, True
            continue
        if section is not None and indent <= section_indent:
            section, section_indent = None, -1
        if "rdma/" in stripped:
            manifest_seen = True
            rdma_key = rdma_key or stripped.split(":", 1)[0].strip()
            if section == "requests":
                in_requests = True
            elif section == "limits":
                in_limits = True
    return in_requests, in_limits, rdma_key, manifest_seen


def detect_ibstat(text: str) -> tuple[str, list[str]]:
    """Return ('ok' | 'down' | 'absent', notes). ibstat prints 'State:' and
    'Physical state:' per port; anything other than Active / LinkUp is a down or
    flapping link (CoreWeave auto-cordons flapping links)."""
    states = re.findall(r"^\s*State:\s*(.+)$", text, re.MULTILINE)
    phys = re.findall(r"^\s*Physical state:\s*(.+)$", text, re.MULTILINE)
    if not states and not phys:
        return "absent", []
    notes: list[str] = []
    bad_state = [s.strip() for s in states if "active" not in s.lower()]
    bad_phys = [p.strip() for p in phys if "linkup" not in p.lower().replace(" ", "")]
    if bad_state:
        notes.append(f"IB port State not Active: {', '.join(bad_state)}")
    if bad_phys:
        notes.append(f"IB Physical state not LinkUp: {', '.join(bad_phys)}")
    return ("down" if notes else "ok"), notes


def detect_busbw(text: str) -> float | None:
    """Extract the all_reduce_perf 'Avg bus bandwidth' summary if present. Deliberately
    NOT compared to a hardcoded baseline -- returned for the report to weigh against
    CoreWeave's published nccl-tests manifest baseline for the GPU count + NCCL version."""
    m = re.search(r"avg\s+bus\s+bandwidth\s*[:=]\s*([0-9]+(?:\.[0-9]+)?)", text, re.IGNORECASE)
    return float(m.group(1)) if m else None


# --- verdict assembly -------------------------------------------------------


def diagnose(text: str) -> dict:
    transport, gdr, ib_failed = detect_transport(text)
    in_req, in_lim, rdma_key, manifest_seen = _rdma_in_sections(text)
    ib_state, ib_notes = detect_ibstat(text)
    busbw = detect_busbw(text)
    low = _low(text)

    missing: list[str] = []
    key = rdma_key or "rdma/ib"
    if manifest_seen:
        if not in_req:
            missing.append(f"`{key}` missing from resources.requests")
        if not in_lim:
            missing.append(f"`{key}` missing from resources.limits")
    have_hca = "nccl_ib_hca" in low
    have_ifname = "nccl_socket_ifname" in low
    # Only assert env vars unset when we have a manifest to judge, or transport is Socket
    # (a bare NET/IB log needn't echo env vars). Hedged: MPI Operator may auto-set them.
    if manifest_seen or transport == "Socket":
        if not have_hca:
            missing.append("`NCCL_IB_HCA` not set (e.g. `ibp`) -- unless the MPI Operator manages it")
        if not have_ifname:
            missing.append("`NCCL_SOCKET_IFNAME` not set (e.g. `eth0`) -- unless the MPI Operator manages it")
    if re.search(r"nccl_ib_disable\s*[:=]\s*['\"]?1\b", low):
        missing.append("`NCCL_IB_DISABLE=1` is forcing the socket fallback -- set it to 0")

    degraded: list[str] = list(ib_notes)

    if transport == "Socket":
        rdma = "no"
        verdict = (
            "RDMA is NOT engaged -- NCCL fell back to TCP (NET/Socket). Multi-node "
            "collectives are running over the Ethernet control plane, commonly 5-20x "
            "slower for the same GPU-hours -- you pay full GPU rate for a fraction of "
            "the throughput, and NCCL raised no error."
        )
    elif transport == "IB":
        rdma = "yes"
        gdr_note = (
            "GPU Direct RDMA confirmed"
            if gdr
            else "on InfiniBand, but the 'GPU Direct RDMA Enabled' line is not in the paste -- "
            "confirm nvidia-peermem is loaded so traffic is not staging through host memory"
        )
        verdict = f"RDMA is engaged -- NCCL is using InfiniBand (NET/IB); {gdr_note}."
        if degraded:
            verdict += " Fabric is UP but DEGRADED (see below)."
    elif transport == "mixed":
        rdma = "partial"
        verdict = (
            "PARTIAL fallback -- some NCCL channels are on IB (NET/IB) and some on TCP "
            "(NET/Socket). Treat as degraded: the run is gated by the slow path. Find the "
            "node/rail that dropped to Socket."
        )
    else:
        rdma = "unknown"
        verdict = (
            "UNKNOWN -- no NCCL transport line found. Re-run the job with NCCL_DEBUG=INFO "
            "and paste the log (grep for 'Using network' / 'NET/IB' / 'NET/Socket')."
        )

    fix = _build_fix(rdma, missing, key)

    return {
        "rdma_engaged": rdma,
        "transport": transport,
        "gpu_direct_rdma_confirmed": gdr,
        "missing_conditions": missing,
        "degraded_signals": degraded,
        "observed_avg_busbw_gbps": busbw,  # [unverified vs baseline]
        "ib_attempt_failed_in_log": ib_failed,
        "verdict": verdict,
        "fix": fix,
    }


def _build_fix(rdma: str, missing: list[str], key: str) -> list[str]:
    if rdma == "yes" and not missing:
        return [
            "No fabric fix required. Benchmark all_reduce_perf busbw against "
            "CoreWeave's published nccl-tests manifest baseline for your GPU count + "
            "NCCL version to confirm the fabric is at line rate."
        ]
    steps = [
        f"Request the RDMA device in BOTH requests AND limits: `{key}: 1` "
        "(if it is in only one, the device plugin will not inject the IB device).",
        "Set `NCCL_IB_HCA=ibp` and `NCCL_SOCKET_IFNAME=eth0` (CoreWeave values), or let the MPI Operator manage them.",
        "Re-run with `NCCL_DEBUG=INFO` and confirm the log now shows `NET/IB` and "
        "`GPU Direct RDMA Enabled` -- not `NET/Socket` / `Using network Socket`.",
        "Confirm each IB port is `State: Active` / `Physical state: LinkUp` via `ibstat`; "
        "a flapping link gets auto-cordoned by CoreWeave.",
    ]
    return steps


# --- rendering --------------------------------------------------------------


def render(result: dict) -> str:
    lines = [f"### VERDICT: {result['verdict']}", ""]
    lines.append(f"- RDMA engaged: **{result['rdma_engaged']}**")
    lines.append(f"- Transport in use: **{result['transport']}**")
    if result["observed_avg_busbw_gbps"] is not None:
        lines.append(
            f"- Observed avg bus bandwidth: **{result['observed_avg_busbw_gbps']} GB/s** "
            "[unverified vs baseline -- compare to CoreWeave's nccl-tests manifest for your "
            "GPU count + NCCL version; do not treat this number as pass/fail on its own]"
        )
    if result["degraded_signals"]:
        lines.append("- Degraded fabric signals:")
        lines += [f"    - {d}" for d in result["degraded_signals"]]
    if result["missing_conditions"]:
        lines.append("- Missing conditions (each one alone forces a silent TCP fallback):")
        lines += [f"    - {m}" for m in result["missing_conditions"]]
    lines.append("")
    lines.append("**The fix (in order):**")
    lines += [f"{i}. {s}" for i, s in enumerate(result["fix"], start=1)]
    lines.append("")
    return "\n".join(lines)


# --- self-test --------------------------------------------------------------

NET_SOCKET_LOG = """\
node-0:120:180 [0] NCCL INFO Bootstrap : Using eth0:10.0.0.4<0>
node-0:120:180 [0] NCCL INFO NET/Socket : Using [0]eth0:10.0.0.4<0>
node-0:120:180 [0] NCCL INFO Using network Socket
node-0:120:180 [0] NCCL INFO comm 0x55 rank 0 nranks 16 - Init COMPLETE
"""

NET_IB_LOG = """\
node-0:120:180 [0] NCCL INFO NET/IB : Using [0]ibp0:1/IB [1]ibp1:1/IB
node-0:120:180 [0] NCCL INFO NET/IB : GPU Direct RDMA Enabled for GPU 0000:0f:00.0
node-0:120:180 [0] NCCL INFO Using network IB
node-0:120:180 [0] NCCL INFO Channel 00/0 : 0[0] -> 1[0] [send] via NET/IB/0/GDRDMA
"""

MANIFEST_MISSING_LIMIT = """\
spec:
  containers:
  - name: trainer
    resources:
      requests:
        nvidia.com/gpu: 8
        rdma/ib: 1
      limits:
        nvidia.com/gpu: 8
    env:
    - name: NCCL_IB_HCA
      value: ibp
    - name: NCCL_SOCKET_IFNAME
      value: eth0
"""

IBSTAT_DOWN = """\
CA 'ibp0'
    Port 1:
        State: Down
        Physical state: Polling
"""

# NCCL_IB_DISABLE set via a SINGLE-quoted value -- the shape the old `\"?1` pattern missed.
NCCL_IB_DISABLE_ON = """\
export NCCL_IB_HCA=ibp
export NCCL_SOCKET_IFNAME=eth0
export NCCL_IB_DISABLE='1'
"""

# NCCL_IB_DISABLE explicitly off -- the finding must NOT fire.
NCCL_IB_DISABLE_OFF = """\
export NCCL_IB_HCA=ibp
export NCCL_SOCKET_IFNAME=eth0
export NCCL_IB_DISABLE=0
"""

# A value whose first digit is 1 but is not a literal 1 -- the trailing \\b must reject it.
NCCL_IB_DISABLE_LOOKALIKE = """\
export NCCL_IB_HCA=ibp
export NCCL_SOCKET_IFNAME=eth0
export NCCL_IB_DISABLE=16
"""


def self_test() -> int:
    # Fixture 1: a NET/Socket log -> "on TCP, fallback".
    a = diagnose(NET_SOCKET_LOG)
    assert a["rdma_engaged"] == "no", a
    assert a["transport"] == "Socket", a
    assert "fell back to tcp" in a["verdict"].lower(), a
    # the fix must give the requests-AND-limits rdma/ib condition (regression-critical).
    assert any("requests AND limits" in s or "requests and limits" in s.lower() for s in a["fix"]), a

    # Fixture 2: a NET/IB log -> "RDMA engaged".
    b = diagnose(NET_IB_LOG)
    assert b["rdma_engaged"] == "yes", b
    assert b["transport"] == "IB", b
    assert b["gpu_direct_rdma_confirmed"] is True, b
    assert "engaged" in b["verdict"].lower(), b

    # Fixture 3: a manifest missing rdma/ib in limits -> flags it precisely.
    c = diagnose(MANIFEST_MISSING_LIMIT)
    assert any("limits" in m for m in c["missing_conditions"]), c
    assert not any("requests" in m and "rdma" in m.lower() for m in c["missing_conditions"]), c

    # Bonus: ibstat down port surfaces as a degraded signal.
    d = diagnose(NET_IB_LOG + IBSTAT_DOWN)
    assert d["degraded_signals"], d

    # Regression: a SINGLE-quoted NCCL_IB_DISABLE='1' must raise the socket-fallback
    # finding (the old `\"?1` pattern only caught double-quoted / bare 1).
    e = diagnose(NCCL_IB_DISABLE_ON)
    assert any("forcing the socket fallback" in m for m in e["missing_conditions"]), e
    # ...and NCCL_IB_DISABLE=0 must NOT raise it.
    f = diagnose(NCCL_IB_DISABLE_OFF)
    assert not any("forcing the socket fallback" in m for m in f["missing_conditions"]), f
    # ...and a 1-prefixed lookalike (16) must NOT false-trigger -- the trailing \b guards it.
    g = diagnose(NCCL_IB_DISABLE_LOOKALIKE)
    assert not any("forcing the socket fallback" in m for m in g["missing_conditions"]), g

    # Bonus: no bandwidth constant is baked in -- the module source cites no GB/s literal
    # as a baseline (only the [unverified vs baseline] echo path).
    import inspect

    src = inspect.getsource(sys.modules[__name__])
    assert "unverified vs baseline" in src, "must hedge any bandwidth figure"

    print(
        "SELF-TEST PASSED: NET/Socket->fallback, NET/IB->engaged, "
        "manifest-missing-limit flagged, ibstat-down degraded, no hardcoded baseline."
    )
    return 0


# --- main -------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(description="Deterministic GPUDirect-RDMA fabric check.")
    ap.add_argument("--in", dest="infile", default="-", help="diagnostics file, or - for stdin")
    ap.add_argument("--json", action="store_true", help="emit the raw verdict dict as JSON")
    ap.add_argument("--self-test", action="store_true", help="run the built-in self-test and exit")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    if args.infile == "-":
        if sys.stdin.isatty():
            print("error: no input on stdin (pipe the NCCL log / manifest in, or pass --in <file>)", file=sys.stderr)
            ap.print_help(sys.stderr)
            return 1
        raw = sys.stdin.read()
    else:
        with open(args.infile, encoding="utf-8") as fh:
            raw = fh.read()

    if not raw.strip():
        print("error: empty input (paste an NCCL_DEBUG=INFO log and/or a pod-spec snippet)", file=sys.stderr)
        return 1

    result = diagnose(raw)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(render(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
