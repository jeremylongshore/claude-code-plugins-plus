"""Pins the invariant that makes sync-external.yml's PR gating safe (#1164).

BACKGROUND

The weekly external-plugin sync failed on every run from 2026-07-27 to
2026-08-09. One source (`slack-channel`) drifted from its sources.lock.json
baseline, and the commit/PR steps were gated on `quarantined == '0'`, so a
single drifted source halted mirroring for all 63. UIZZE (#1104) was accepted
2026-07-25 and still did not exist on the site two weeks later.

That gate was removed. It is safe to remove ONLY because of one property of
the sync engine: a drifted source writes nothing at all. The engine
short-circuits at the top of the per-source body and returns `changes: []`
before reaching any copy/write call, so drifted bytes never enter the working
tree and therefore cannot ride into the auto-PR.

WHY THIS FILE EXISTS

That property is an implicit contract between two files that are edited
independently. Nothing enforced it. If someone moves a write above the early
return — or deletes the early return — the workflow would silently begin
shipping drifted upstream content into an auto-PR, which is a supply-chain
regression that no existing gate would catch.

The reviewer of #1165 asked for exactly this: "the only durable fix for that
class of bug is an automated assertion, not a Slack ping." These are static
assertions rather than a live sync, so they need no network, no clone, and no
credentials, and they fail in CI the moment the contract is broken.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "sync-external.yml"
ENGINE = REPO_ROOT / "scripts" / "sync-external.mjs"

# Calls that mutate the filesystem. Deletions and permission changes count:
# pruning an orphaned file is as much a working-tree mutation as writing one.
#
# The first version of this pattern listed six sync APIs and missed
# `fs.appendFileSync` — which the engine uses TEN times, more than any other
# write call — along with every `fs.promises.*` async form. A detector that
# cannot see the most common write in the file it guards is not a guard, which
# is the same "gate that gates nothing" defect this whole PR exists to fix.
# Caught in review of #1165.
#
# Enumerated deliberately rather than inferred: an allowlist of read-only APIs
# would silently pass any newly-introduced mutator, whereas a missing entry here
# is caught by test_write_detector_recognizes_known_write_forms below.
_MUTATORS = (
    "writeFile|appendFile|copyFile|cp|mkdir|mkdtemp|rm|rmdir|unlink|rename|"
    "chmod|chown|truncate|symlink|link|utimes|writev|open"
)
RE_WRITE_CALL = re.compile(
    # fs.writeFileSync(...) / fs.appendFileSync(...) / fs.rmSync(...)
    rf"\bfs\.(?:{_MUTATORS})Sync\s*\("
    # fs.promises.writeFile(...) / fsp.copyFile(...) / fs.promises.rm(...)
    rf"|\bfs(?:\.promises|p)?\.(?:{_MUTATORS})\s*\("
    # createWriteStream in either form
    r"|\bfs(?:\.promises|p)?\.createWriteStream\s*\("
    # bare destructured imports: writeFileSync(...), appendFileSync(...)
    rf"|(?<![.\w])(?:{_MUTATORS})Sync\s*\("
)

# Write forms that MUST be detectable. If someone narrows RE_WRITE_CALL, this
# fails immediately rather than the narrowing going unnoticed until a real
# regression slips past the drift guard.
KNOWN_WRITE_FORMS = [
    "fs.writeFileSync(target, body)",
    "fs.appendFileSync(logPath, line)",
    "fs.copyFileSync(src, dest)",
    "fs.cpSync(src, dest, { recursive: true })",
    "fs.mkdirSync(dir, { recursive: true })",
    "fs.mkdtempSync(prefix)",
    "fs.rmSync(dir, { recursive: true, force: true })",
    "fs.renameSync(a, b)",
    "fs.chmodSync(p, 0o755)",
    "await fs.promises.writeFile(target, body)",
    "await fs.promises.copyFile(src, dest)",
    "await fs.promises.rm(dir, { recursive: true })",
    "await fsp.appendFile(logPath, line)",
    "const out = fs.createWriteStream(target)",
    "writeFileSync(target, body)",
]

# Read-only calls that must NOT trip the detector, or the test becomes noise
# and gets deleted.
KNOWN_SAFE_FORMS = [
    "fs.existsSync(p)",
    "fs.readFileSync(p, 'utf8')",
    "fs.statSync(p)",
    "fs.readdirSync(dir)",
    "const changes = [];",
    "log('nothing mirrored this run')",
]


def test_write_detector_recognizes_known_write_forms() -> None:
    """The detector must actually detect. A guard is only as good as its pattern."""
    missed = [f for f in KNOWN_WRITE_FORMS if not RE_WRITE_CALL.search(f)]
    assert not missed, (
        "RE_WRITE_CALL no longer matches these filesystem writes, so "
        "test_drift_short_circuit_returns_before_any_write would not catch them "
        f"inside the quarantine branch: {missed}"
    )

    false_positives = [f for f in KNOWN_SAFE_FORMS if RE_WRITE_CALL.search(f)]
    assert not false_positives, (
        f"RE_WRITE_CALL matches read-only calls, which makes the guard noisy "
        f"and likely to be disabled: {false_positives}"
    )


def _engine_source() -> str:
    return ENGINE.read_text(encoding="utf-8")


def test_drift_short_circuit_returns_before_any_write() -> None:
    """The drift guard must return before the first write call in its function.

    Located by finding the drift guard, then the `return` that closes it, and
    asserting no write call appears between the two. A write inside the guard
    body would mean drifted content reaches disk despite the quarantine.
    """
    src = _engine_source()

    guard = src.find("lockDiff.status === 'drifted' && !relockRequested")
    assert guard != -1, (
        "Could not find the drift quarantine guard in scripts/sync-external.mjs. "
        "If it was renamed, update this test deliberately — do not delete it. "
        "sync-external.yml's PR gating depends on this short-circuit."
    )

    ret = src.find("lockStatus: 'quarantined'", guard)
    assert ret != -1, "Drift guard no longer returns a 'quarantined' result."

    body = src[guard:ret]
    offenders = RE_WRITE_CALL.findall(body)
    assert not offenders, (
        "A filesystem write appears inside the drift-quarantine branch of "
        "scripts/sync-external.mjs. A quarantined source must write NOTHING — "
        "sync-external.yml no longer gates its commit/PR steps on the "
        "quarantine count, so any byte written here would be committed into "
        f"the automated sync PR unreviewed. Offending calls: {offenders}"
    )


def test_quarantined_result_reports_no_changes() -> None:
    """The quarantine branch must report an empty change set.

    The workflow's `Check for changes` step keys off the working tree, but the
    summary and downstream reporting key off `changes`. A non-empty value here
    would mean the quarantine is claiming to have mirrored something.
    """
    src = _engine_source()
    guard = src.find("lockDiff.status === 'drifted' && !relockRequested")
    ret = src.find("lockStatus: 'quarantined'", guard)
    body = src[guard:ret]
    assert "changes: []" in body, (
        "The drift-quarantine branch must return `changes: []`. A quarantined "
        "source mirrors nothing by definition."
    )


def test_commit_and_pr_steps_are_not_gated_on_quarantine_count() -> None:
    """Drift must quarantine one source, not halt the whole run.

    This is the regression that caused the 2026-07-27..08-09 outage. Restoring
    a `quarantined == '0'` gate would make one drifted source block all 63
    mirrors again. Drift is deliberately aligned with the REFUSE path, which
    already quarantines only the offending source.
    """
    doc = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = doc["jobs"]["sync"]["steps"]

    offenders = [
        s.get("name", "<unnamed>")
        for s in steps
        if "quarantined ==" in str(s.get("if", ""))
    ]
    assert not offenders, (
        "Steps are gated on the quarantine COUNT again: "
        f"{offenders}. One drifted source would halt mirroring for every other "
        "source (see #1164 — this caused a two-week outage). Drifted content "
        "cannot reach the working tree anyway, which the tests above pin, so "
        "the gate blocks only clean sources. Use the `Flag quarantined drift` "
        "step to fail the run instead."
    )


def test_drift_is_still_flagged_loudly() -> None:
    """Removing the gate must not make drift silent.

    The quarantine still has to red-fail the run and name the drifted sources;
    only the collateral damage to other sources was removed.
    """
    doc = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = doc["jobs"]["sync"]["steps"]

    flag = next((s for s in steps if s.get("name") == "Flag quarantined drift"), None)
    assert flag is not None, "The drift-flagging step was removed."
    assert "quarantined !=" in str(flag.get("if", "")), (
        "The drift-flagging step must still trigger on a non-zero quarantine count."
    )
    assert "exit 1" in flag.get("run", ""), (
        "The drift-flagging step must still fail the run — a quarantine that "
        "reports success is indistinguishable from a clean run."
    )


def test_scheduled_workflow_alerts_on_failure() -> None:
    """A cron job that cannot report its own failure is the root cause here.

    sync-external.yml red-failed weekly for two weeks with no alerting, and was
    found only while triaging an unrelated issue. See #1166 for the other
    scheduled workflows still missing this.
    """
    doc = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    on = doc.get("on") or doc.get(True) or {}
    assert "schedule" in on, "Expected sync-external.yml to still be scheduled."

    steps = doc["jobs"]["sync"]["steps"]
    alerts = [s for s in steps if str(s.get("if", "")).strip() == "failure()"]
    assert alerts, (
        "sync-external.yml runs on a schedule but has no `if: failure()` step. "
        "A scheduled job with no failure alerting is indistinguishable from one "
        "that is not running at all — that is precisely how #1164 went unnoticed "
        "for two weeks."
    )
