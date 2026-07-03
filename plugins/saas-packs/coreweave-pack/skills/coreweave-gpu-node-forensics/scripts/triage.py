#!/usr/bin/env python3
"""Deterministic GPU-node failure triage for coreweave-gpu-node-forensics.

The LLM does NOT guess the verdict. This script maps a hardware signal — an
NVIDIA Xid code (optionally with row-remapper state) OR a pasted
dmesg / nvidia-smi blob — to a single, grounded triage decision:

    {classification, severity, action, why, next_command, ...}

`action` is one of the six operator moves:

    reschedule           restart the job; the node/GPU is healthy (Xid 94 CONTAINED)
    reset-gpu            drain + GPU reset; in-flight work is suspect (Xid 95 UNCONTAINED, 48, 74, 119/120)
    reboot-node          bare-metal reboot; the card is gone until then (Xid 79)
    rma                  terminal hardware fault; replace the card (row-remap FAILURE, Xid 64)
    watch                correctable / trending; not yet actionable (Xid 92, thermal)
    app-bug-not-hardware the app faulted, not the GPU; do NOT RMA (Xid 13/31/43/45)

The headline decision is the 94-vs-95 split: a CONTAINED error (94) only cost
you one job restart; an UNCONTAINED error (95) means the GPU could not isolate
the fault and everything it touched is suspect.

Grounding (see references/):
  - NVIDIA Xid error catalog: https://docs.nvidia.com/deploy/xid-errors/
  - references/xid-triage-table.md   (full code -> action table, cited)
  - references/row-remap-decision.md (Xid 63/64 + ROW_REMAPPER logic)
  - references/cordon-rules.md       (CoreWeave health-cordon hard rule)

HARD RULE embedded here and surfaced in every hardware verdict: never manually
uncordon a CoreWeave health cordon — the node-lifecycle controller owns it.

Usage:
    python3 triage.py --xid 94
    python3 triage.py --xid 63 --pending yes
    python3 triage.py --xid 48 --remap-failure yes
    python3 triage.py --blob dmesg.txt          # parse a pasted blob (file or - for stdin)
    cat dmesg.txt | python3 triage.py           # blob on stdin
    python3 triage.py --xid 95 --json           # machine-readable only
    python3 triage.py --self-test               # run bundled fixtures
"""

from __future__ import annotations

import argparse
import json
import re
import sys

# ---------------------------------------------------------------------------
# Severity ranking — used to pick the GOVERNING Xid when a blob carries several
# (the most severe fault dictates the triage move; the rest are noted).
# ---------------------------------------------------------------------------
SEVERITY_RANK = {"critical": 3, "high": 2, "medium": 1, "low": 0}

VALID_ACTIONS = (
    "reschedule",
    "reset-gpu",
    "reboot-node",
    "rma",
    "watch",
    "app-bug-not-hardware",
)

# The CoreWeave hard rule, attached to every verdict that touches the node/GPU
# at the hardware level. CoreWeave's node-lifecycle controller places a health
# cordon on a faulting node; a human uncordoning it re-schedules work onto known-
# bad hardware and races the controller. See references/cordon-rules.md.
CORDON_RULE = (
    "Do NOT manually uncordon a CoreWeave health cordon — the node-lifecycle "
    "controller owns cordon/uncordon. Let it drain and replace the node."
)

# CoreWeave does not publish exact auto-RMA thresholds (how many SBE/remap
# events trigger an automatic replacement) or the exact taint/label string of a
# health cordon. Anything depending on those is flagged [unverified].
UNVERIFIED_RMA_THRESHOLD = (
    "[unverified] CoreWeave's exact auto-RMA thresholds (SBE-rate / remaining "
    "remap-bank limits) are not publicly published — treat escalation counts as "
    "guidance, confirm the RMA trigger with CoreWeave support."
)

# ---------------------------------------------------------------------------
# The Xid -> verdict table. Single source of truth for the code path; kept in
# lockstep with references/xid-triage-table.md. Each entry:
#   code: (classification, severity, action, why, next_command)
# ---------------------------------------------------------------------------
XID_TABLE: dict[int, tuple[str, str, str, str, str]] = {
    13: (
        "Graphics/compute engine exception",
        "low",
        "app-bug-not-hardware",
        "Engine exception — almost always an application or CUDA-kernel bug "
        "(illegal access, bad launch), not a hardware fault. Do NOT RMA.",
        "Reproduce under compute-sanitizer / cuda-memcheck and fix the failing kernel.",
    ),
    31: (
        "GPU memory page fault (MMU fault)",
        "low",
        "app-bug-not-hardware",
        "MMU page fault — an illegal / out-of-bounds memory access by the app, not hardware. Do NOT RMA.",
        "Run the job under compute-sanitizer to locate the out-of-bounds access.",
    ),
    43: (
        "GPU stopped processing (software-induced)",
        "low",
        "app-bug-not-hardware",
        "Software-induced channel fault in the running job — not a hardware failure. Do NOT RMA; fix the app.",
        "Debug the app; look earlier in dmesg for a preceding Xid 13/31 that triggered it.",
    ),
    45: (
        "Preemptive channel cleanup / robust channel recovery",
        "low",
        "app-bug-not-hardware",
        "Channel teardown after a kill, Ctrl-C, or a prior fault — usually a "
        "downstream symptom, not the root hardware cause. Do NOT RMA on this alone.",
        "Scan earlier dmesg for the preceding Xid that caused the teardown.",
    ),
    48: (
        "Double-Bit ECC error (DBE, uncorrectable)",
        "critical",
        "reset-gpu",
        "Uncorrectable double-bit ECC error — reset the GPU; a row-remap should "
        "follow. If the remap FAILS the card is terminal -> RMA.",
        "nvidia-smi -q -d ROW_REMAPPER on the GPU, drain + reset it; RMA if remapping failed.",
    ),
    63: (
        "ECC page retirement / row-remap recorded",
        "high",
        "reset-gpu",
        "A row-remap (or legacy page retirement) was recorded — routine ECC "
        "self-healing that applies on the next GPU reset, UNLESS the remap "
        "failed (terminal -> RMA).",
        "Read nvidia-smi -q -d ROW_REMAPPER: 'Pending: Yes' -> reset to apply; "
        "'Remapping Failure Occurred: Yes' -> RMA.",
    ),
    64: (
        "ECC row-remapper recording FAILURE",
        "critical",
        "rma",
        "The row-remapper could not record a remap — the sparing hardware itself "
        "failed. This is terminal; the GPU needs replacement -> RMA.",
        "Confirm nvidia-smi -q -d ROW_REMAPPER ('Remapping Failure Occurred: Yes'); cordon, drain, open an RMA.",
    ),
    74: (
        "NVLink error",
        "high",
        "reset-gpu",
        "NVLink / NVSwitch error between GPUs — reset the GPU and its NVLink "
        "domain. If it recurs on the same link, escalate to node reboot / RMA.",
        "nvidia-smi nvlink -e to read link errors; drain + GPU reset; escalate if it repeats.",
    ),
    79: (
        "GPU has fallen off the bus",
        "critical",
        "reboot-node",
        "The GPU dropped off the PCIe bus and is unreachable — it will NOT return "
        "until the node is rebooted (bare-metal power-cycle). All work on it is lost.",
        "Cordon + drain the node, then reboot it (RESTART_BM / power-cycle). If it recurs after reboot -> RMA.",
    ),
    92: (
        "High single-bit ECC (SBE) error rate",
        "medium",
        "watch",
        "Correctable single-bit ECC errors are trending high — the GPU is still "
        "healthy and self-correcting. Watch the trend; act only if it escalates "
        "to a DBE (Xid 48) or a remap failure.",
        "Track SBE counts (nvidia-smi -q -d ECC); RMA only on escalation to uncorrectable/remap-failure.",
    ),
    94: (
        "Contained ECC/memory error",
        "high",
        "reschedule",
        "The error was CONTAINED to the faulting application's context — the GPU "
        "and node are healthy. Just reschedule/restart the job; no reset or RMA needed.",
        "Restart or reschedule the failed rank; the node stays in service.",
    ),
    95: (
        "Uncontained ECC/memory error",
        "critical",
        "reset-gpu",
        "The error was UNCONTAINED — the GPU could not isolate it, so every "
        "context it touched is suspect. Drain the GPU and reset it; treat all "
        "in-flight work as corrupt.",
        "Cordon + drain, GPU-reset (nvidia-smi -r) or node reset; re-run any job that shared this GPU.",
    ),
    119: (
        "GSP RPC timeout",
        "high",
        "reset-gpu",
        "The GPU System Processor (GSP) RPC timed out — a GPU reset usually "
        "clears it. Reboot the node only if the reset does not.",
        "Drain + GPU reset; if it recurs, reboot the node.",
    ),
    120: (
        "GSP error",
        "high",
        "reset-gpu",
        "A GSP (GPU System Processor) error — a GPU reset usually clears it; reboot the node if reset does not.",
        "Drain + GPU reset; escalate to node reboot if it persists.",
    ),
}

# Non-Xid signal: thermal throttling parsed from nvidia-smi PERFORMANCE output.
THERMAL_VERDICT = (
    "Thermal throttling (not a hardware failure)",
    "medium",
    "watch",
    "The GPU is clock-throttling due to heat — it is healthy but running hot. "
    "Investigate cooling / airflow / inlet temp, not the card. Reschedule off it "
    "only if throttling is tanking throughput.",
    "nvidia-smi -q -d PERFORMANCE to read the throttle reasons; check node airflow / datacenter cooling.",
)

# Actions that operate at the hardware/node level -> carry the cordon rule.
_HARDWARE_ACTIONS = {"reset-gpu", "reboot-node", "rma"}


def _verdict(
    *,
    xid: int | None,
    classification: str,
    severity: str,
    action: str,
    why: str,
    next_command: str,
    co_occurring: list[int] | None = None,
    unverified: list[str] | None = None,
) -> dict:
    """Assemble a verdict dict, attaching the cordon rule + unverified hedges."""
    v: dict = {
        "xid": xid,
        "classification": classification,
        "severity": severity,
        "action": action,
        "why": why,
        "next_command": next_command,
    }
    if co_occurring:
        v["co_occurring_xids"] = co_occurring
    hedges = list(unverified or [])
    if action in _HARDWARE_ACTIONS:
        v["cordon_rule"] = CORDON_RULE
    if action == "rma":
        hedges.append(UNVERIFIED_RMA_THRESHOLD)
    if hedges:
        v["unverified"] = hedges
    return v


def classify_xid(xid: int) -> dict:
    """Map a bare Xid code to its base verdict (no row-remap override)."""
    if xid in XID_TABLE:
        classification, severity, action, why, nxt = XID_TABLE[xid]
        return _verdict(
            xid=xid,
            classification=classification,
            severity=severity,
            action=action,
            why=why,
            next_command=nxt,
        )
    return _verdict(
        xid=xid,
        classification=f"Unmapped Xid {xid}",
        severity="high",
        action="reset-gpu",
        why=(
            f"Xid {xid} is not in the triage table. Unmapped Xids default to a "
            "conservative drain + GPU reset; consult the NVIDIA Xid catalog before "
            "deciding on RMA."
        ),
        next_command="See https://docs.nvidia.com/deploy/xid-errors/ for Xid "
        f"{xid}; drain the node and reset the GPU, then observe.",
        unverified=[f"[unverified] Xid {xid} has no entry in xid-triage-table.md — verdict is a conservative default."],
    )


def apply_remap_override(base: dict, pending: bool | None, remap_failure: bool | None) -> dict:
    """Row-remapper state is authoritative for the ECC/DBE family.

    - Remapping Failure Occurred: Yes  -> terminal, RMA (overrides any base).
    - Pending: Yes (no failure)         -> reset-gpu (the remap applies on reset).
    Anything else leaves the base verdict untouched.

    An override builds a FRESH verdict, so it must carry forward the forensic
    context the base accumulated — the co-occurring Xids and any [unverified]
    hedges — rather than silently dropping them.
    """
    xid = base.get("xid")
    if remap_failure:
        v = _verdict(
            xid=xid,
            classification="ECC row-remapper FAILURE (terminal)",
            severity="critical",
            action="rma",
            why=(
                "nvidia-smi reports 'Remapping Failure Occurred: Yes' — the GPU's "
                "spare-row sparing failed. This is terminal hardware; no reset "
                "recovers it. Replace the card -> RMA."
            ),
            next_command="Cordon + drain the node and open a CoreWeave RMA for the GPU.",
        )
    elif pending:
        v = _verdict(
            xid=xid,
            classification="ECC row-remap PENDING (routine)",
            severity="high",
            action="reset-gpu",
            why=(
                "nvidia-smi reports 'Pending: Yes' with no remap failure — a row-remap "
                "is queued and applies on the next GPU reset. Routine ECC self-healing, "
                "not an RMA."
            ),
            next_command="Drain the GPU and reset it (nvidia-smi -r or node reset) to apply the pending remap.",
        )
    else:
        return base

    # The override verdict is fresh — carry forward the base's forensic context
    # so a remap-driven RMA/reset still shows the ALSO-SEEN co-occurring Xids and
    # preserves the base's [unverified] hedges.
    if base.get("co_occurring_xids"):
        v["co_occurring_xids"] = base["co_occurring_xids"]
    base_hedges = base.get("unverified") or []
    if base_hedges:
        # union, dedup — do NOT double-append _verdict's own standard hedges
        v["unverified"] = list(dict.fromkeys([*base_hedges, *v.get("unverified", [])]))
    return v


# ---------------------------------------------------------------------------
# Blob parsing — pull Xid codes + row-remapper state + thermal flags out of a
# pasted dmesg / nvidia-smi dump.
# ---------------------------------------------------------------------------
# Matches:  "NVRM: Xid (PCI:0000:3b:00): 79, pid=..."  and  "[Xid 48]"  and  "Xid: 94"
_XID_RE = re.compile(r"Xid\s*(?:\([^)]*\))?\s*[:,]?\s*(\d{1,4})\b")
_REMAP_FAIL_RE = re.compile(r"Remapping\s+Failure\s+Occurred\s*:\s*(Yes|No)", re.IGNORECASE)
_PENDING_RE = re.compile(r"\bPending\s*:\s*(Yes|No)", re.IGNORECASE)
_THERMAL_RE = re.compile(r"(HW|SW)\s+Thermal\s+Slowdown\s*:\s*Active", re.IGNORECASE)


def parse_blob(text: str) -> dict:
    """Extract structured signals from a pasted dmesg / nvidia-smi blob."""
    xids = [int(m) for m in _XID_RE.findall(text)]
    remap_fail_m = _REMAP_FAIL_RE.search(text)
    pending_m = _PENDING_RE.search(text)
    return {
        "xids": xids,
        "remap_failure": (remap_fail_m.group(1).lower() == "yes") if remap_fail_m else None,
        "pending": (pending_m.group(1).lower() == "yes") if pending_m else None,
        "thermal": bool(_THERMAL_RE.search(text)),
    }


def triage_from_blob(text: str) -> dict:
    """End-to-end: parse a blob, pick the governing signal, return one verdict."""
    parsed = parse_blob(text)
    xids = parsed["xids"]

    if xids:
        # The most severe Xid governs the triage move; the rest are noted.
        governing = max(xids, key=lambda x: SEVERITY_RANK.get(_severity_of(x), 1))
        base = classify_xid(governing)
        others = sorted({x for x in xids if x != governing})
        if others:
            base["co_occurring_xids"] = others
        return apply_remap_override(base, parsed["pending"], parsed["remap_failure"])

    # No Xid — fall back to row-remap state, then thermal.
    if parsed["remap_failure"] or parsed["pending"]:
        return apply_remap_override(
            _verdict(
                xid=None,
                classification="Row-remapper state (no Xid in blob)",
                severity="high",
                action="watch",
                why="Row-remapper fields found without an Xid; the remap state governs.",
                next_command="nvidia-smi -q -d ROW_REMAPPER",
            ),
            parsed["pending"],
            parsed["remap_failure"],
        )
    if parsed["thermal"]:
        classification, severity, action, why, nxt = THERMAL_VERDICT
        return _verdict(
            xid=None,
            classification=classification,
            severity=severity,
            action=action,
            why=why,
            next_command=nxt,
        )

    return _verdict(
        xid=None,
        classification="No GPU fault signal found",
        severity="low",
        action="watch",
        why="No Xid, row-remapper failure, or thermal-throttle signal was found in the input.",
        next_command="Collect fresh evidence: dmesg -T | grep -i xid ; nvidia-smi -q -d ROW_REMAPPER,ECC,PERFORMANCE",
    )


def _severity_of(xid: int) -> str:
    return XID_TABLE[xid][1] if xid in XID_TABLE else "high"


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------
def render_verdict(v: dict) -> str:
    """Human-readable VERDICT block (the SKILL reasons over the JSON, humans read this)."""
    xid = v.get("xid")
    head = f"Xid {xid} — {v['classification']}" if xid is not None else v["classification"]
    lines = [
        f"VERDICT: {head} [severity: {v['severity'].upper()}]",
        f"ACTION:  {v['action']}",
        f"WHY:     {v['why']}",
        f"NEXT:    {v['next_command']}",
    ]
    if v.get("co_occurring_xids"):
        lines.append(
            f"ALSO SEEN: Xid {', '.join(str(x) for x in v['co_occurring_xids'])} (governed by the most severe above)"
        )
    if v.get("cordon_rule"):
        lines.append(f"CORDON:  {v['cordon_rule']}")
    for hedge in v.get("unverified", []):
        lines.append(f"NOTE:    {hedge}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Self-test — bundled fixtures, exit 0 on all-pass
# ---------------------------------------------------------------------------
def _run_self_test() -> int:
    cases = [
        # (label, verdict-producing thunk, expected_action)
        ("xid 94 CONTAINED -> reschedule", lambda: classify_xid(94), "reschedule"),
        ("xid 95 UNCONTAINED -> reset-gpu", lambda: classify_xid(95), "reset-gpu"),
        ("xid 79 fell-off-bus -> reboot-node", lambda: classify_xid(79), "reboot-node"),
        ("xid 43 software -> app-bug-not-hardware", lambda: classify_xid(43), "app-bug-not-hardware"),
        ("xid 13 engine-exception -> app-bug-not-hardware", lambda: classify_xid(13), "app-bug-not-hardware"),
        ("xid 31 page-fault -> app-bug-not-hardware", lambda: classify_xid(31), "app-bug-not-hardware"),
        ("xid 92 SBE-trend -> watch", lambda: classify_xid(92), "watch"),
        ("xid 64 remap-record-failure -> rma", lambda: classify_xid(64), "rma"),
        (
            "xid 63 + Pending:Yes -> reset-gpu",
            lambda: apply_remap_override(classify_xid(63), pending=True, remap_failure=False),
            "reset-gpu",
        ),
        (
            "remap-failure override -> rma",
            lambda: apply_remap_override(classify_xid(63), pending=False, remap_failure=True),
            "rma",
        ),
        (
            "xid 48 DBE + remap-failure -> rma",
            lambda: apply_remap_override(classify_xid(48), pending=False, remap_failure=True),
            "rma",
        ),
        (
            "blob: contained 94 -> reschedule",
            lambda: triage_from_blob("NVRM: Xid (PCI:0000:3b:00): 94, pid=1234, Contained: ECC error"),
            "reschedule",
        ),
        (
            "blob: uncontained 95 -> reset-gpu",
            lambda: triage_from_blob("kernel: NVRM: Xid (PCI:0000:65:00): 95, Uncontained ECC error"),
            "reset-gpu",
        ),
        (
            "blob: 79 fell off bus -> reboot-node",
            lambda: triage_from_blob("NVRM: Xid (PCI:0000:04:00): 79, GPU has fallen off the bus."),
            "reboot-node",
        ),
        (
            "blob: nvidia-smi remap FAILURE -> rma",
            lambda: triage_from_blob("    Remapping Failure Occurred          : Yes\n    Pending: No"),
            "rma",
        ),
        (
            "blob: nvidia-smi remap Pending -> reset-gpu",
            lambda: triage_from_blob(
                "  Row Remapper\n    Pending                             : Yes\n    Remapping Failure Occurred : No"
            ),
            "reset-gpu",
        ),
        (
            "blob: thermal throttle -> watch",
            lambda: triage_from_blob("Clocks Throttle Reasons\n    HW Thermal Slowdown : Active"),
            "watch",
        ),
        (
            "blob: co-occurring 43+79, 79 governs -> reboot-node",
            lambda: triage_from_blob("Xid 43, software fault\nlater: NVRM: Xid (PCI:0000:04:00): 79, fell off bus"),
            "reboot-node",
        ),
    ]

    passed = 0
    failed = 0
    for label, thunk, expected in cases:
        v = thunk()
        got = v.get("action")
        ok = got == expected and got in VALID_ACTIONS
        # Invariant: every hardware action carries the cordon rule.
        if v.get("action") in _HARDWARE_ACTIONS and not v.get("cordon_rule"):
            ok = False
            note = " (MISSING cordon_rule)"
        else:
            note = ""
        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        else:
            failed += 1
        print(f"[{status}] {label}: expected={expected} got={got}{note}")

    # ---- context-preservation checks for the remap override ----------------
    # A remap override builds a FRESH verdict; it must still carry forward the
    # base verdict's forensic context — co-occurring Xids AND [unverified]
    # hedges — deduping against _verdict's own standard hedges.
    ctx_checks = []

    # remap FAILURE (-> RMA): preserve co-occurring Xids + base hedges, and dedup
    # against _verdict's own standard RMA hedge (seeded into the base to prove it).
    base_fail = classify_xid(48)
    base_fail["co_occurring_xids"] = [79, 94]
    base_fail["unverified"] = ["[unverified] base-only forensic hedge", UNVERIFIED_RMA_THRESHOLD]
    v_fail = apply_remap_override(base_fail, pending=None, remap_failure=True)
    ctx_checks.append(
        (
            "remap-failure override preserves co_occurring_xids + base hedge (no dupes)",
            v_fail.get("action") == "rma"
            and v_fail.get("co_occurring_xids") == [79, 94]
            and "[unverified] base-only forensic hedge" in v_fail.get("unverified", [])
            and UNVERIFIED_RMA_THRESHOLD in v_fail.get("unverified", [])
            and len(v_fail.get("unverified", [])) == len(set(v_fail.get("unverified", []))),
        )
    )

    # pending (-> reset-gpu): likewise preserve the base's forensic context.
    base_pending = classify_xid(48)
    base_pending["co_occurring_xids"] = [92]
    base_pending["unverified"] = ["[unverified] base-only pending hedge"]
    v_pending = apply_remap_override(base_pending, pending=True, remap_failure=False)
    ctx_checks.append(
        (
            "pending override preserves co_occurring_xids + base hedge (no dupes)",
            v_pending.get("action") == "reset-gpu"
            and v_pending.get("co_occurring_xids") == [92]
            and "[unverified] base-only pending hedge" in v_pending.get("unverified", [])
            and len(v_pending.get("unverified", [])) == len(set(v_pending.get("unverified", []))),
        )
    )

    for label, ok in ctx_checks:
        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        else:
            failed += 1
        print(f"[{status}] {label}")

    print(f"\nself-test: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _yesno(val: str | None) -> bool | None:
    if val is None:
        return None
    return str(val).strip().lower() in ("yes", "y", "true", "1")


def main() -> int:
    ap = argparse.ArgumentParser(description="Deterministic CoreWeave GPU-node failure triage.")
    ap.add_argument("--xid", type=int, help="NVIDIA Xid code to classify.")
    ap.add_argument("--pending", help="Row-remapper 'Pending' state: yes|no.")
    ap.add_argument("--remap-failure", dest="remap_failure", help="'Remapping Failure Occurred' state: yes|no.")
    ap.add_argument("--blob", help="Path to a pasted dmesg/nvidia-smi blob ('-' for stdin).")
    ap.add_argument("--json", action="store_true", help="Emit machine-readable JSON only.")
    ap.add_argument("--self-test", action="store_true", help="Run bundled fixtures and exit.")
    args = ap.parse_args()

    if args.self_test:
        return _run_self_test()

    if args.xid is not None:
        base = classify_xid(args.xid)
        verdict = apply_remap_override(base, _yesno(args.pending), _yesno(args.remap_failure))
    else:
        # Blob mode: explicit --blob, else read stdin if piped.
        if args.blob:
            if args.blob == "-":
                text = sys.stdin.read()
            else:
                with open(args.blob, encoding="utf-8") as fh:
                    text = fh.read()
        elif not sys.stdin.isatty():
            text = sys.stdin.read()
        else:
            print(
                "error: provide --xid N, or --blob <file|->, or pipe a dmesg/nvidia-smi blob on stdin", file=sys.stderr
            )
            ap.print_help(sys.stderr)
            return 1
        if not text.strip():
            print("error: empty input blob", file=sys.stderr)
            return 1
        verdict = triage_from_blob(text)
        # A standalone row-remap override may still apply when the user pastes an
        # Xid AND supplies remap flags on the CLI alongside --blob (rare) — blob
        # parsing already folded remap state in, so nothing more to do here.

    if args.json:
        print(json.dumps(verdict, indent=2))
    else:
        print(render_verdict(verdict))
        print()
        print(json.dumps(verdict, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
