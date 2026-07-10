#!/usr/bin/env python3
"""
auto-bridge.py — session-start auto-bridge for the hyperflow CLAUDE.md doctrine block.

Called by hooks/session-start. Reads .hyperflow/.bridge-mode (default: auto), checks
whether the project's ./CLAUDE.md has the current doctrine block, and either:

  * mode=auto    → writes/refreshes the block silently, prints one-line notice
  * mode=manual  → leaves the file alone, prints an advisory when stale
  * mode=off     → does nothing

Idempotent. Preserves all other content in ./CLAUDE.md outside the
<!-- hyperflow:doctrine:start --> … <!-- hyperflow:doctrine:end --> markers.

Exits 0 on success or no-op. Exits 0 (not non-zero) on most error paths too,
because the hook is non-blocking by design — a bridge failure must not break
session start. Errors go to stderr; the hook captures them into
.hyperflow/.session-start.log.

Usage:
    auto-bridge.py <plugin-root> <project-root>
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import os
import re
import sys
from pathlib import Path

START_MARKER_RE = re.compile(
    r"<!--\s*hyperflow:doctrine:start"
    r"(?:\s+version=(?P<version>[^\s>]+))?"
    r"(?:\s+generated=(?P<generated>[^\s>]+))?"
    r"(?:\s+body-sha=(?P<body_sha>[0-9a-f]+))?"
    r"[^>]*-->",
)
END_MARKER = "<!-- hyperflow:doctrine:end -->"


def _body_hash(template: str) -> str:
    """Hash the template body (without per-render substitutions).

    Strips the start-marker line entirely from the hashed content so per-render
    version/timestamp/body-sha values never influence the hash itself.
    """
    body = START_MARKER_RE.sub("", template, count=1)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:12]


def _read_version(plugin_root: Path) -> str:
    """Resolve the current plugin version from skills/hyperflow/VERSION."""
    version_file = plugin_root / "skills" / "hyperflow" / "VERSION"
    try:
        return version_file.read_text(encoding="utf-8").strip() or "unknown"
    except OSError:
        return "unknown"


def _read_template(plugin_root: Path) -> str | None:
    """Read the doctrine template; return None if absent."""
    template = plugin_root / "templates" / "claude-md-doctrine.md"
    try:
        return template.read_text(encoding="utf-8")
    except OSError:
        return None


def _read_mode(project_root: Path) -> str:
    """Read .hyperflow/.bridge-mode. Default: auto."""
    path = project_root / ".hyperflow" / ".bridge-mode"
    try:
        value = path.read_text(encoding="utf-8").strip().lower()
        if value in {"auto", "manual", "off"}:
            return value
    except OSError:
        pass
    return "auto"


def _find_existing_block(
    content: str,
) -> tuple[int, int, str | None, str | None] | None:
    """Return (start_idx, end_idx_exclusive, version, body_sha) or None.

    Searches the file content for the doctrine markers. Returns character
    positions covering the entire block (start marker line through end marker
    line inclusive), the captured version, and the captured body-sha (if any).
    """
    match = START_MARKER_RE.search(content)
    if not match:
        return None
    start = content.rfind("\n", 0, match.start()) + 1
    end_marker_idx = content.find(END_MARKER, match.end())
    if end_marker_idx == -1:
        return None
    line_end = content.find("\n", end_marker_idx)
    end = line_end + 1 if line_end != -1 else len(content)
    return start, end, match.group("version"), match.group("body_sha")


def _render_block(template: str, version: str, generated_at: str, body_sha: str) -> str:
    """Substitute placeholders + add body-sha to the start marker."""
    rendered = template.replace("__HYPERFLOW_VERSION__", version).replace(
        "__GENERATED_AT__", generated_at
    )
    # Add or replace body-sha=<hash> attribute in the start marker.
    def _patch_marker(m: re.Match) -> str:
        # Always emit a marker that includes version, generated, and body-sha.
        v = m.group("version") or version
        g = m.group("generated") or generated_at
        return (
            f"<!-- hyperflow:doctrine:start version={v} generated={g} "
            f"body-sha={body_sha} source=https://github.com/Mohammed-Abdelhady/hyperflow -->"
        )

    return START_MARKER_RE.sub(_patch_marker, rendered, count=1)


def _write_claude_md(project_root: Path, new_block: str, mode: str) -> str:
    """Write or replace the doctrine block in ./CLAUDE.md. Returns action taken."""
    claude_md = project_root / "CLAUDE.md"
    if claude_md.exists():
        original = claude_md.read_text(encoding="utf-8")
    else:
        original = ""

    existing = _find_existing_block(original)
    if existing is None:
        # Append the block with a leading blank line if needed.
        sep = "" if original.endswith("\n\n") or not original else (
            "\n" if original.endswith("\n") else "\n\n"
        )
        new_content = original + sep + new_block
        if not new_content.endswith("\n"):
            new_content += "\n"
        action = "generated"
    else:
        start, end, _, _ = existing
        prefix = original[:start]
        suffix = original[end:]
        new_content = prefix + new_block
        if not new_content.endswith("\n"):
            new_content += "\n"
        new_content += suffix
        action = "refreshed"

    if not new_content.endswith("\n"):
        new_content += "\n"

    if mode == "manual":
        # In manual mode we never write; we just compute the would-be action
        # so the caller can print an advisory instead.
        return f"would-{action}"

    claude_md.write_text(new_content, encoding="utf-8")
    return action


def _print_body_sha(argv: list[str]) -> int:
    """Print the current template's body-sha — the value stamped into a block's marker.

    Exists so other tools (scripts/verify-downstreams.sh) can ask for the hash rather
    than reimplement it and silently disagree with auto-bridge about freshness.
    """
    if len(argv) < 3:
        print(
            "auto-bridge: usage: auto-bridge.py --body-sha <plugin-root>",
            file=sys.stderr,
        )
        return 2
    template = _read_template(Path(argv[2]))
    if template is None:
        print("auto-bridge: template not found", file=sys.stderr)
        return 2
    print(_body_hash(template))
    return 0


def main(argv: list[str]) -> int:
    if len(argv) >= 2 and argv[1] == "--body-sha":
        return _print_body_sha(argv)

    # --force re-stamps the marker even when the body is unchanged. Reserved for this
    # repo's own release commit, where the version label should track the release. User
    # projects must keep the content-keyed no-op so a version bump never churns their
    # CLAUDE.md.
    force = "--force" in argv[1:]
    argv = [a for a in argv if a != "--force"]

    if len(argv) < 3:
        print(
            "auto-bridge: usage: auto-bridge.py <plugin-root> <project-root> [--force]\n"
            "                    auto-bridge.py --body-sha <plugin-root>",
            file=sys.stderr,
        )
        return 0  # non-blocking

    plugin_root = Path(argv[1])
    project_root = Path(argv[2])

    if not (project_root / ".hyperflow").is_dir():
        # Project doesn't use hyperflow; nothing to bridge.
        return 0

    mode = _read_mode(project_root)
    if mode == "off":
        return 0

    version = _read_version(plugin_root)
    template = _read_template(plugin_root)
    if template is None:
        print(
            "auto-bridge: template not found at "
            f"{plugin_root}/templates/claude-md-doctrine.md — skipping",
            file=sys.stderr,
        )
        return 0

    generated_at = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    body_sha = _body_hash(template)
    new_block = _render_block(template, version, generated_at, body_sha)

    # Freshness check (S7 — content-hash invalidation):
    #   1. If the existing block's body-sha matches the new template body, skip
    #      the write entirely — content is unchanged across this plugin version,
    #      no need to touch the file even if the version label differs.
    #   2. Fall back to version-string matching when no body-sha is present in
    #      the marker (older blocks generated before S7 landed).
    #   3. --force bypasses both, so a release can re-stamp its own version label.
    claude_md = project_root / "CLAUDE.md"
    if claude_md.exists() and not force:
        try:
            existing = _find_existing_block(
                claude_md.read_text(encoding="utf-8")
            )
            if existing:
                _, _, existing_version, existing_body_sha = existing
                if existing_body_sha and existing_body_sha == body_sha:
                    return 0  # content unchanged → no-op
                if existing_body_sha is None and existing_version == version:
                    return 0  # legacy block, version matches → no-op
        except OSError:
            pass

    try:
        action = _write_claude_md(project_root, new_block, mode)
    except OSError as e:
        print(f"auto-bridge: failed to write CLAUDE.md — {e}", file=sys.stderr)
        return 0

    if action.startswith("would-"):
        # manual mode advisory
        real_action = action.replace("would-", "")
        print(
            f"hyperflow bridge: ./CLAUDE.md doctrine block would be {real_action} "
            f"(version {version}) — mode=manual, run /hyperflow:bridge refresh to apply"
        )
    else:
        print(
            f"hyperflow bridge: ./CLAUDE.md doctrine block {action} (version {version}) "
            f"— mode=auto · /hyperflow:bridge mode manual to require manual refreshes"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
