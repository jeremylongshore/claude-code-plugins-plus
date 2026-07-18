#!/usr/bin/env python3
"""bundle-deploy-guard.py — PreToolUse guard that protects a Databricks Asset
Bundle's terraform state across a `databricks bundle deploy` (databricks-bundle-medic,
AP02 / pain D5).

Pain D5: on every redeploy after the first, the Terraform bundle engine can fail with
"unexpected EOF reading terraform.tfstate" (databricks/cli#4986) — a truncated-state
read that bricks the bundle until the team switches to DATABRICKS_BUNDLE_ENGINE=direct.
Once the state is corrupt, the fastest recovery is a known-good copy.

This hook runs BEFORE a `databricks bundle deploy` and, best-effort:
  * locates the CLI's local working state (.databricks/bundle/<target>/terraform/terraform.tfstate),
  * validates it parses as JSON (a truncated/EOF state does not),
  * if it is good, caches a timestamped known-good backup as a recovery escape hatch,
  * if it looks corrupt or has SHRUNK vs the last known-good, emits a loud advisory
    naming the #4986 workaround and the backup path.

DESIGN — advisory, never blocking (a deploy guard must never wall a deploy):
  * It ALWAYS allows. The value is the backup + the early warning, not a gate.
  * It FAILS OPEN: any error (no state file, unreadable, unknown layout) → allow,
    silently. It only speaks when it has something useful to say.

Protocol: reads the PreToolUse event JSON on stdin, writes a PreToolUse decision JSON
on stdout (allow, optionally with additionalContext), exits 0.
"""

import json
import os
import re
import sys

BUNDLE_DEPLOY = re.compile(r"\bdatabricks\s+bundle\s+deploy\b", re.IGNORECASE)
BACKUP_DIRNAME = ".medic-backups"
# A state that shrinks below this fraction of the last known-good is suspicious.
SHRINK_FRACTION = 0.5


def is_bundle_deploy(command):
    """True iff the command runs `databricks bundle deploy`."""
    return bool(command and isinstance(command, str) and BUNDLE_DEPLOY.search(command))


def classify_tfstate(text):
    """Classify raw terraform.tfstate text. Pure — the whole D5 detection contract.
    Returns {ok, resources, size, error}: ok=True only when it parses as JSON."""
    size = len(text or "")
    if not text or not text.strip():
        return {"ok": False, "resources": None, "size": size, "error": "empty state"}
    try:
        doc = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        # A truncated / EOF-corrupted state is exactly this — valid prefix, bad tail.
        return {"ok": False, "resources": None, "size": size, "error": "does not parse as JSON (truncated?)"}
    resources = doc.get("resources")
    n = len(resources) if isinstance(resources, list) else None
    return {"ok": True, "resources": n, "size": size, "error": None}


def deploy_advisory(current, last_good_size):
    """Given the classified current state and the last known-good byte size, return an
    advisory string (or None). Pure. Warns on corruption or a suspicious shrink."""
    if not current["ok"]:
        return (
            f"bundle-medic: the current terraform.tfstate {current['error']}. This is the "
            "databricks/cli#4986 signature ('unexpected EOF reading terraform.tfstate'). "
            "Recovery: restore the last known-good backup (see .databricks/bundle/**/"
            f"{BACKUP_DIRNAME}/), or redeploy with DATABRICKS_BUNDLE_ENGINE=direct."
        )
    if last_good_size and current["size"] < last_good_size * SHRINK_FRACTION:
        return (
            f"bundle-medic: terraform.tfstate shrank sharply ({current['size']} bytes vs a "
            f"prior {last_good_size}) — possible partial write (databricks/cli#4986). A "
            f"known-good backup is cached under {BACKUP_DIRNAME}/ before this deploy."
        )
    return None


def _find_state_files(root):
    """Best-effort: yield local bundle terraform.tfstate paths under root/.databricks."""
    base = os.path.join(root, ".databricks", "bundle")
    if not os.path.isdir(base):
        return []
    found = []
    for dirpath, _dirs, files in os.walk(base):
        if BACKUP_DIRNAME in dirpath:
            continue
        if "terraform.tfstate" in files:
            found.append(os.path.join(dirpath, "terraform.tfstate"))
    return found


def _latest_backup_size(state_path):
    """Byte size of the most recent cached backup for this state, or None."""
    backup_dir = os.path.join(os.path.dirname(state_path), BACKUP_DIRNAME)
    if not os.path.isdir(backup_dir):
        return None
    sizes = []
    for name in os.listdir(backup_dir):
        p = os.path.join(backup_dir, name)
        try:
            sizes.append((os.path.getmtime(p), os.path.getsize(p)))
        except OSError:
            continue
    if not sizes:
        return None
    sizes.sort()
    return sizes[-1][1]


def _cache_backup(state_path, text):
    """Write a known-good backup next to the state. Best-effort; never raises."""
    try:
        backup_dir = os.path.join(os.path.dirname(state_path), BACKUP_DIRNAME)
        os.makedirs(backup_dir, exist_ok=True)
        # mtime ordering gives us "latest"; a stable name keeps the dir bounded to a few.
        stamp = str(int(os.path.getmtime(state_path)))
        with open(os.path.join(backup_dir, f"terraform.tfstate.{stamp}.good"), "w") as fh:
            fh.write(text)
    except OSError:
        pass


def guard(command, root):
    """Best-effort guard. Returns an advisory string (or None). Never raises."""
    if not is_bundle_deploy(command):
        return None
    advisories = []
    for state_path in _find_state_files(root):
        try:
            with open(state_path) as fh:
                text = fh.read()
        except OSError:
            continue
        current = classify_tfstate(text)
        last_good = _latest_backup_size(state_path)
        msg = deploy_advisory(current, last_good)
        if current["ok"]:
            _cache_backup(state_path, text)
        if msg:
            advisories.append(msg)
    return "\n".join(advisories) if advisories else None


def _allow(context=None):
    out = {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow"}}
    if context:
        out["hookSpecificOutput"]["additionalContext"] = context
    return out


def main():
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    if event.get("tool_name") != "Bash":
        return 0
    command = (event.get("tool_input") or {}).get("command", "")
    try:
        advisory = guard(command, os.getcwd())
    except Exception:  # noqa: BLE001 — a guard must never block a deploy on its own bug.
        advisory = None
    if advisory:
        json.dump(_allow(advisory), sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
