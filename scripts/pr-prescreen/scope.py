#!/usr/bin/env python3
"""Resolve real plugin roots and supplement skill-only prescreen results.

The marketplace contains category-level support files such as
``plugins/mcp/destructive-policies.json``.  A path-prefix truncation cannot
distinguish those files from ``plugins/<category>/<plugin>`` directories, so
the prescreen must consult the checked-out trees before treating a prefix as
a plugin.

The skill validator also intentionally emits no record for a valid plugin
that contains only MCP/hooks/runtime components.  For those plugins this
module performs deterministic canonical structural checks and emits a neutral
component record (no score or grade). Structural failures are returned as
hard-block signals; they are never converted into a synthetic grade.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import stat
import sys
from pathlib import Path, PurePosixPath
from typing import Any


_CATALOG_PATH = Path(".claude-plugin/marketplace.extended.json")
_KEBAB_NAME = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")
_STRICT_SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)
_MCP_RESERVED_NAMES = {"skill", "claude", "anthropic", "mcp", "plugin", "agent"}
_MCP_UNSAFE_DESCRIPTION = re.compile(r"<[^>]+>|\$\{|\$\(|`")


def _safe_plugin_root(filename: str) -> str | None:
    """Return the lexical ``plugins/<category>/<plugin>`` prefix.

    A tracked file inside a plugin has at least four path components.  A
    three-component path is a category-root support file, not a plugin tree.
    Dot segments and absolute paths are rejected before any filesystem read.
    """

    path = PurePosixPath(filename)
    parts = path.parts
    if path.is_absolute() or len(parts) < 4 or parts[0] != "plugins":
        return None
    if any(part in ("", ".", "..") for part in parts):
        return None
    return "/".join(parts[:3])


def _direct_plugin_root(
    filename: str,
    *,
    pr_root: Path,
    base_root: Path,
    pr_catalog: set[str],
    base_catalog: set[str],
) -> str | None:
    """Resolve a three-part Git entry only with plugin-specific authority.

    Git represents a plugin-root symlink or non-directory replacement as the
    root path itself. Exact catalog membership, a real marked plugin tree, or
    a kebab-named symlink/non-directory establishes plugin scope. Ordinary
    category support files such as ``destructive-policies.json`` do not.
    """

    path = PurePosixPath(filename)
    if (
        path.is_absolute()
        or len(path.parts) != 3
        or path.parts[0] != "plugins"
        or any(part in ("", ".", "..") for part in path.parts)
    ):
        return None
    relative = path.as_posix()
    if relative in pr_catalog or relative in base_catalog:
        return relative
    if _scope_existing_root(pr_root, relative) or _scope_existing_root(base_root, relative):
        return relative
    if not _KEBAB_NAME.fullmatch(path.parts[2]):
        return None
    for checkout in (pr_root, base_root):
        candidate = checkout.joinpath(*path.parts)
        if not _lexists(candidate):
            continue
        try:
            metadata = candidate.lstat()
        except OSError:
            return relative
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            return relative
    return None


def _real_directory(checkout: Path, relative: str) -> bool:
    """True only for a non-symlink directory contained by ``checkout``."""

    root = checkout.resolve()
    candidate = root.joinpath(*PurePosixPath(relative).parts)
    if candidate.is_symlink() or not candidate.is_dir():
        return False
    try:
        return candidate.resolve().is_relative_to(root)
    except (OSError, RuntimeError):
        return False


def _lexists(path: Path) -> bool:
    return os.path.lexists(path)


def _plugin_has_marker(checkout: Path, relative: str) -> bool:
    """Return whether a directory has an actual plugin component marker.

    This excludes category support trees (for example ``mcp/.greptile`` and
    ``saas-packs/_templates``) without guessing from their names. Symlinked
    markers intentionally count here so the structural lane can reject them
    explicitly instead of silently dropping the plugin from scope.
    """

    root = checkout.joinpath(*PurePosixPath(relative).parts)
    direct_markers = (
        root / ".claude-plugin" / "plugin.json",
        root / ".mcp.json",
        root / "hooks" / "hooks.json",
        root / "SKILL.md",
    )
    if any(_lexists(marker) for marker in direct_markers):
        return True
    if any((root / name).is_symlink() for name in (".claude-plugin", "hooks", "skills", "agents", "commands")):
        return True
    for component_dir, pattern in (("skills", "SKILL.md"), ("agents", "*.md"), ("commands", "*.md")):
        directory = root / component_dir
        if _lexists(directory) and any(directory.rglob(pattern)):
            return True
    return False


def _scope_existing_root(checkout: Path, relative: str) -> bool:
    return _real_directory(checkout, relative) and _plugin_has_marker(checkout, relative)


def _normalize_catalog_source(source: Any) -> str | None:
    if not isinstance(source, str):
        return None
    normalized = source[2:] if source.startswith("./") else source
    path = PurePosixPath(normalized)
    if path.is_absolute() or len(path.parts) != 3 or path.parts[0] != "plugins":
        return None
    if any(part in ("", ".", "..") for part in path.parts):
        return None
    return path.as_posix()


def load_catalog_roots(checkout: Path, *, required: bool = False) -> set[str]:
    """Parse exact plugin sources from the canonical editable catalog."""

    catalog_path = checkout / _CATALOG_PATH
    if not _lexists(catalog_path):
        if required:
            raise ValueError(f"{_CATALOG_PATH} is missing")
        return set()
    if not _regular_contained_file(checkout, catalog_path):
        raise ValueError(f"{_CATALOG_PATH} must be a contained regular file")
    document, error = _load_object(catalog_path, str(_CATALOG_PATH))
    if error:
        raise ValueError(error)
    plugins = document.get("plugins") if document is not None else None
    if not isinstance(plugins, list):
        raise ValueError(f"{_CATALOG_PATH} must contain a plugins array")
    roots: set[str] = set()
    for index, entry in enumerate(plugins):
        if not isinstance(entry, dict):
            raise ValueError(f"{_CATALOG_PATH} plugins[{index}] must be an object")
        source = _normalize_catalog_source(entry.get("source"))
        if source is None:
            raise ValueError(
                f"{_CATALOG_PATH} plugins[{index}].source must be an exact "
                "plugins/<category>/<plugin> path"
            )
        roots.add(source)
    return roots


def _catalog_or_marker_root(checkout: Path, relative: str, catalog_roots: set[str]) -> bool:
    return _real_directory(checkout, relative) and (
        relative in catalog_roots or _plugin_has_marker(checkout, relative)
    )


def discover_plugin_dirs(
    entries: list[dict[str, Any]], *, pr_root: Path, base_root: Path
) -> tuple[list[str], list[str], int]:
    """Return changed dirs, deletion-touched dirs, and plugin-file count."""

    changed: set[str] = set()
    deleted: set[str] = set()
    plugin_file_count = 0
    pr_catalog = load_catalog_roots(pr_root)
    base_catalog = load_catalog_roots(base_root)

    for entry in entries:
        filename = entry.get("filename")
        status = entry.get("status")
        if not isinstance(filename, str) or not filename.startswith("plugins/"):
            continue
        plugin_file_count += 1
        plugin_root = _safe_plugin_root(filename) or _direct_plugin_root(
            filename,
            pr_root=pr_root,
            base_root=base_root,
            pr_catalog=pr_catalog,
            base_catalog=base_catalog,
        )
        if plugin_root is None:
            continue
        if status == "removed":
            # A file deletion from a plugin that still exists in the PR is a
            # plugin change, not a plugin deletion. Only a root absent from the
            # PR tree belongs in the deletion-integrity lane.
            if _catalog_or_marker_root(base_root, plugin_root, base_catalog):
                if _real_directory(pr_root, plugin_root):
                    changed.add(plugin_root)
                else:
                    deleted.add(plugin_root)
            elif _catalog_or_marker_root(pr_root, plugin_root, pr_catalog):
                changed.add(plugin_root)
        elif _catalog_or_marker_root(pr_root, plugin_root, pr_catalog):
            changed.add(plugin_root)
        elif _lexists(pr_root.joinpath(*PurePosixPath(plugin_root).parts)) and not _real_directory(
            pr_root, plugin_root
        ):
            # A plugin root added or replaced as a symlink/non-directory is
            # suspicious, not an ordinary removal. The deletion lane reports
            # the exact non-regular-root and stale-catalog violations.
            deleted.add(plugin_root)

        # GitHub exposes the old side of a rename as previous_filename. A
        # cross-plugin rename must scope both roots: the new root as changed,
        # and the old root as changed or deleted according to PR-tree reality.
        previous = entry.get("previous_filename")
        if status == "renamed" and isinstance(previous, str):
            old_root = _safe_plugin_root(previous)
            if old_root is not None and old_root != plugin_root:
                if _catalog_or_marker_root(base_root, old_root, base_catalog):
                    if _real_directory(pr_root, old_root):
                        changed.add(old_root)
                    else:
                        deleted.add(old_root)
                elif _catalog_or_marker_root(pr_root, old_root, pr_catalog):
                    changed.add(old_root)

    return sorted(changed), sorted(deleted), plugin_file_count


def _load_object(path: Path, label: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"{label} is not valid JSON: {exc}"
    if not isinstance(parsed, dict):
        return None, f"{label} must contain a JSON object"
    return parsed, None


def _regular_contained_file(plugin_dir: Path, path: Path) -> bool:
    """Require a regular file with no symlink in any path component."""

    try:
        relative = path.relative_to(plugin_dir)
    except ValueError:
        return False
    current = plugin_dir
    for index, segment in enumerate(relative.parts):
        current /= segment
        try:
            metadata = current.lstat()
        except OSError:
            return False
        if stat.S_ISLNK(metadata.st_mode):
            return False
        final = index == len(relative.parts) - 1
        if (final and not stat.S_ISREG(metadata.st_mode)) or (
            not final and not stat.S_ISDIR(metadata.st_mode)
        ):
            return False
    try:
        return path.resolve().is_relative_to(plugin_dir.resolve())
    except (OSError, RuntimeError):
        return False


_VALIDATOR_MODULE: Any | None = None


def _canonical_validator() -> Any:
    """Load the immutable base-authored canonical component validator."""

    global _VALIDATOR_MODULE  # noqa: PLW0603
    if _VALIDATOR_MODULE is None:
        validator_path = Path(__file__).resolve().parents[1] / "validate-skills-schema.py"
        spec = importlib.util.spec_from_file_location("_prescreen_base_validator", validator_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"canonical component validator unavailable at {validator_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        _VALIDATOR_MODULE = module
    return _VALIDATOR_MODULE


def _canonical_manifest_errors(path: Path, manifest: dict[str, Any]) -> list[str]:
    """Apply canonical manifest validation plus the strict marketplace name floor."""

    try:
        result = _canonical_validator().validate_plugin_json(path, strict=True)
    except RuntimeError as exc:
        return [str(exc)]
    errors = [str(value) for value in result.get("errors", []) + result.get("warnings", [])]
    name = manifest.get("name")
    if (
        not isinstance(name, str)
        or not _KEBAB_NAME.fullmatch(name)
        or len(name) > 64
    ):
        errors.append("Field 'name' must be a non-empty kebab-case name of at most 64 characters")
    return errors


def _validate_mcp_servers(servers: Any, label: str) -> list[str]:
    """Mirror the pinned kernel v2 + marketplace MCP server contract."""

    if not isinstance(servers, dict) or not servers:
        return [f"{label} must declare a non-empty mcpServers object"]
    errors: list[str] = []
    for server_name, config in servers.items():
        if (
            not isinstance(server_name, str)
            or not _KEBAB_NAME.fullmatch(server_name)
            or len(server_name) > 64
            or server_name in _MCP_RESERVED_NAMES
            or "claude" in server_name.lower()
            or "anthropic" in server_name.lower()
        ):
            errors.append(f"{label} contains an invalid kebab-case server name")
            continue
        if not isinstance(config, dict):
            errors.append(f"{label} server {server_name!r} must be an object")
            continue
        explicit_name = config.get("name", server_name)
        if explicit_name != server_name:
            errors.append(f"{label} server {server_name!r} name must match its map key")
        transport = config.get("type")
        if transport not in {"stdio", "http", "streamable-http", "sse", "ws"}:
            errors.append(
                f"{label} server {server_name!r} type must be one of "
                "stdio, http, streamable-http, sse, ws"
            )
        command = config.get("command")
        if not isinstance(command, str) or not command.strip():
            errors.append(f"{label} server {server_name!r} command must be a non-empty string")
        if transport in {"http", "streamable-http", "sse", "ws"}:
            if not isinstance(config.get("url"), str) or not config["url"].strip():
                errors.append(
                    f"{label} server {server_name!r} type {transport!r} requires a non-empty url"
                )
        if not isinstance(config.get("args"), list):
            errors.append(f"{label} server {server_name!r} args must be an array")
        elif not all(
            isinstance(value, str) for value in config["args"]
        ):
            errors.append(f"{label} server {server_name!r} args entries must be strings")
        if not isinstance(config.get("env"), dict):
            errors.append(f"{label} server {server_name!r} env must be an object")
        if "headers" in config and not isinstance(config["headers"], dict):
            errors.append(f"{label} server {server_name!r} headers must be an object")
        if "metadata" in config and not isinstance(config["metadata"], dict):
            errors.append(f"{label} server {server_name!r} metadata must be an object")
        description = config.get("description")
        if not isinstance(description, str) or not description.strip():
            errors.append(f"{label} server {server_name!r} description must be a non-empty string")
        elif len(description) > 1024:
            errors.append(f"{label} server {server_name!r} description exceeds 1024 characters")
        elif _MCP_UNSAFE_DESCRIPTION.search(description):
            errors.append(f"{label} server {server_name!r} description contains unsafe markup or substitution")
        version = config.get("version")
        if not isinstance(version, str) or not _STRICT_SEMVER.fullmatch(version):
            errors.append(f"{label} server {server_name!r} version must be strict SemVer")
        if not isinstance(config.get("enabled"), bool):
            errors.append(f"{label} server {server_name!r} enabled must be boolean")
        for deprecated in ("compatible-with", "when_to_use"):
            if deprecated in config:
                errors.append(f"{label} server {server_name!r} uses deprecated field {deprecated!r}")
    return errors


def _canonical_component_errors(path: Path, kind: str) -> list[str]:
    """Return canonical fatal/errors for an agent or command data file."""

    try:
        validator = _canonical_validator()
    except RuntimeError as exc:
        return [str(exc)]
    function = validator.validate_agent if kind == "agent" else validator.validate_command
    result = function(path)
    errors: list[str] = []
    if result.get("fatal"):
        errors.append(str(result["fatal"]))
    errors.extend(str(value) for value in result.get("errors", []))
    return errors


_HOOK_EVENTS = {
    "SessionStart",
    "Setup",
    "UserPromptSubmit",
    "UserPromptExpansion",
    "PreToolUse",
    "PermissionRequest",
    "PermissionDenied",
    "PostToolUse",
    "PostToolUseFailure",
    "PostToolBatch",
    "Notification",
    "MessageDisplay",
    "SubagentStart",
    "SubagentStop",
    "TaskCreated",
    "TaskCompleted",
    "Stop",
    "StopFailure",
    "TeammateIdle",
    "InstructionsLoaded",
    "ConfigChange",
    "CwdChanged",
    "FileChanged",
    "WorktreeCreate",
    "WorktreeRemove",
    "PreCompact",
    "PostCompact",
    "Elicitation",
    "ElicitationResult",
    "SessionEnd",
}


def _validate_hooks(
    document: Any, label: str, *, require_marketplace_fields: bool = True
) -> list[str]:
    """Validate the canonical event → matcher-group → handler shape."""

    if not isinstance(document, dict) or not isinstance(document.get("hooks"), dict):
        return [f"{label} must contain a hooks object"]
    errors: list[str] = []
    hooks = document["hooks"]
    if not hooks:
        errors.append(f"{label} hooks object must not be empty")
    for event, groups in hooks.items():
        if event not in _HOOK_EVENTS:
            errors.append(f"{label} uses unsupported hook event {event!r}")
            continue
        if not isinstance(groups, list) or not groups:
            errors.append(f"{label} event {event!r} must contain a non-empty array")
            continue
        for group_index, group in enumerate(groups):
            group_label = f"{label} event {event!r} group {group_index}"
            if not isinstance(group, dict):
                errors.append(f"{group_label} must be an object")
                continue
            matcher = group.get("matcher")
            if require_marketplace_fields and (not isinstance(matcher, str) or not matcher):
                errors.append(f"{group_label} matcher must be a non-empty string")
            elif matcher is not None and not isinstance(matcher, str):
                errors.append(f"{group_label} matcher must be a string when present")
            handlers = group.get("hooks")
            if not isinstance(handlers, list) or not handlers:
                errors.append(f"{group_label} hooks must be a non-empty array")
                continue
            for handler_index, handler in enumerate(handlers):
                handler_label = f"{group_label} handler {handler_index}"
                if not isinstance(handler, dict):
                    errors.append(f"{handler_label} must be an object")
                    continue
                kind = handler.get("type")
                required_field = {
                    "command": "command",
                    "http": "url",
                    "mcp_tool": "toolName",
                    "prompt": "prompt",
                    "agent": "prompt",
                }.get(kind)
                if required_field is None:
                    errors.append(f"{handler_label} has unsupported type {kind!r}")
                elif not isinstance(handler.get(required_field), str) or not handler[required_field].strip():
                    errors.append(f"{handler_label} requires a non-empty {required_field}")
                if require_marketplace_fields:
                    if not isinstance(handler.get("description"), str) or not handler["description"].strip():
                        errors.append(f"{handler_label} requires a non-empty description")
                    if not isinstance(handler.get("enabled"), bool):
                        errors.append(f"{handler_label} enabled must be boolean")
                    timeout = handler.get("timeout")
                    if isinstance(timeout, bool) or not isinstance(timeout, int) or timeout < 0:
                        errors.append(f"{handler_label} timeout must be a non-negative integer")
                    if not isinstance(handler.get("blocking"), bool):
                        errors.append(f"{handler_label} blocking must be boolean")
    return errors


def _load_regular_object(plugin_dir: Path, path: Path, label: str) -> tuple[dict[str, Any] | None, list[str]]:
    if not _regular_contained_file(plugin_dir, path):
        return None, [f"{label} must be a contained regular file with no symlink components"]
    document, error = _load_object(path, label)
    return document, [error] if error else []


def validate_plugin_structure(plugin_dir: Path, relative: str, *, has_skills: bool) -> list[str]:
    """Validate every structural artifact with canonical fail-closed rules."""

    errors: list[str] = []
    for component_dir in (".claude-plugin", "hooks", "skills", "agents", "commands"):
        candidate = plugin_dir / component_dir
        if candidate.is_symlink():
            errors.append(
                f"{relative}/{component_dir} must be a contained directory with no symlink components"
            )
    manifest_path = plugin_dir / ".claude-plugin" / "plugin.json"
    manifest: dict[str, Any] | None = None
    if _lexists(manifest_path):
        manifest, load_errors = _load_regular_object(
            plugin_dir, manifest_path, f"{relative}/.claude-plugin/plugin.json"
        )
        errors.extend(load_errors)
        if manifest is not None:
            errors.extend(
                f"{relative}/.claude-plugin/plugin.json: {error}"
                for error in _canonical_manifest_errors(manifest_path, manifest)
            )
    elif not has_skills:
        errors.append(f"Plugin dir {relative} has no SKILL.md or canonical .claude-plugin/plugin.json")

    mcp_documents: list[tuple[Path, str]] = []
    mcp_path = plugin_dir / ".mcp.json"
    if _lexists(mcp_path):
        mcp_documents.append((mcp_path, f"{relative}/.mcp.json"))

    if manifest is not None and "mcpServers" in manifest:
        declaration = manifest["mcpServers"]
        if isinstance(declaration, dict):
            errors.extend(
                _validate_mcp_servers(declaration, f"{relative}/.claude-plugin/plugin.json mcpServers")
            )
        elif isinstance(declaration, (str, list)):
            references = [declaration] if isinstance(declaration, str) else declaration
            for reference in references:
                if not isinstance(reference, str):
                    errors.append(f"{relative} mcpServers references must be strings")
                    continue
                ref_path = PurePosixPath(reference)
                if ref_path.is_absolute() or ".." in ref_path.parts:
                    errors.append(f"{relative} mcpServers reference escapes plugin: {reference}")
                    continue
                mcp_documents.append((plugin_dir.joinpath(*ref_path.parts), f"{relative}/{reference}"))

    hook_documents: list[tuple[Path, str]] = []
    if manifest is not None and "hooks" in manifest:
        declaration = manifest["hooks"]
        if isinstance(declaration, dict):
            errors.extend(
                _validate_hooks(
                    {"hooks": declaration},
                    f"{relative}/.claude-plugin/plugin.json hooks",
                    require_marketplace_fields=False,
                )
            )
        elif isinstance(declaration, (str, list)):
            references = [declaration] if isinstance(declaration, str) else declaration
            for reference in references:
                if not isinstance(reference, str):
                    errors.append(f"{relative} hooks references must be strings")
                    continue
                ref_path = PurePosixPath(reference)
                if ref_path.is_absolute() or ".." in ref_path.parts:
                    errors.append(f"{relative} hooks reference escapes plugin: {reference}")
                    continue
                hook_documents.append((plugin_dir.joinpath(*ref_path.parts), f"{relative}/{reference}"))

    seen_mcp: set[Path] = set()
    for path, label in mcp_documents:
        if path in seen_mcp:
            continue
        seen_mcp.add(path)
        document, load_errors = _load_regular_object(plugin_dir, path, label)
        errors.extend(load_errors)
        if document is not None:
            errors.extend(_validate_mcp_servers(document.get("mcpServers", document), label))

    hooks_path = plugin_dir / "hooks" / "hooks.json"
    if _lexists(hooks_path):
        hook_documents.append((hooks_path, f"{relative}/hooks/hooks.json"))
    seen_hooks: set[Path] = set()
    for path, label in hook_documents:
        if path in seen_hooks:
            continue
        seen_hooks.add(path)
        hooks, load_errors = _load_regular_object(plugin_dir, path, label)
        errors.extend(load_errors)
        if hooks is not None:
            errors.extend(_validate_hooks(hooks, label))

    for component_dir, kind in (("agents", "agent"), ("commands", "command")):
        directory = plugin_dir / component_dir
        if not _lexists(directory) or directory.is_symlink() or not directory.is_dir():
            continue
        for path in directory.rglob("*.md"):
            label = f"{relative}/{path.relative_to(plugin_dir).as_posix()}"
            if not _regular_contained_file(plugin_dir, path):
                errors.append(f"{label} must be a contained regular file with no symlink components")
                continue
            errors.extend(
                f"{label}: {error}" for error in _canonical_component_errors(path, kind)
            )

    return errors


def supplement_results(
    all_results: list[dict[str, Any]], changed_dirs: list[str], *, pr_root: Path
) -> tuple[list[dict[str, Any]], list[str]]:
    """Filter skill results and add neutral structural records for plugins."""

    filtered = [
        result
        for result in all_results
        if any((plugin + "/") in str(result.get("path", "")) for plugin in changed_dirs)
    ]
    signals: list[str] = []
    catalog_roots = load_catalog_roots(pr_root, required=True)

    for plugin in changed_dirs:
        plugin_dir = pr_root.joinpath(*PurePosixPath(plugin).parts)
        if plugin not in catalog_roots:
            signals.append(
                f"Missing exact catalog source './{plugin}' in {_CATALOG_PATH}"
            )
        has_skills = any(
            _regular_contained_file(plugin_dir, path) for path in plugin_dir.rglob("SKILL.md")
        )
        has_skill_result = any(
            (plugin + "/") in str(result.get("path", ""))
            and str(result.get("path", "")).endswith("SKILL.md")
            for result in filtered
        )
        errors = validate_plugin_structure(plugin_dir, plugin, has_skills=has_skills)
        if errors:
            signals.extend(errors)
            continue
        if has_skills and not has_skill_result:
            # A changed skill-bearing plugin with no validator record is an
            # internal failure, not a candidate for structural-only PASS.
            signals.append(f"prescreen-internal-error: validator produced no result for {plugin}")
            continue
        filtered.append(
            {
                "path": plugin,
                "score": None,
                "grade": None,
                "errors": 0,
                "warnings": 0,
                "error_messages": [],
                "warning_messages": [],
                "component_type": "plugin-structure",
            }
        )

    for result in filtered:
        path = str(result.get("path", ""))
        marker = "/plugins/"
        if marker in path:
            result["path"] = path[path.index(marker) + 1 :]

    return filtered, signals


def validate_deleted_plugins(
    deleted_dirs: list[str], *, pr_root: Path
) -> list[str]:
    """Validate full removals without following replacement symlinks."""

    catalog_roots = load_catalog_roots(pr_root, required=True)
    signals: list[str] = []
    for plugin in deleted_dirs:
        candidate = pr_root.joinpath(*PurePosixPath(plugin).parts)
        if _lexists(candidate):
            try:
                metadata = candidate.lstat()
            except OSError as exc:
                signals.append(f"Deleted plugin root {plugin} cannot be inspected: {exc}")
            else:
                if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
                    signals.append(
                        f"Deleted plugin root {plugin} still exists as a symlink or non-directory"
                    )
                else:
                    signals.append(f"prescreen-internal-error: deleted plugin root {plugin} still exists")
        if plugin in catalog_roots:
            signals.append(
                f"Deleted plugin {plugin} still has exact catalog source './{plugin}'"
            )
    return signals


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_lines(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_lines(path: Path, values: list[str]) -> None:
    path.write_text("".join(f"{value}\n" for value in values), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    subparsers = parser.add_subparsers(dest="command", required=True)

    discover = subparsers.add_parser("discover")
    discover.add_argument("--files-json", type=Path, required=True)
    discover.add_argument("--pr-root", type=Path, required=True)
    discover.add_argument("--base-root", type=Path, required=True)
    discover.add_argument("--changed-output", type=Path, required=True)
    discover.add_argument("--deleted-output", type=Path, required=True)

    supplement = subparsers.add_parser("supplement")
    supplement.add_argument("--validator-results", type=Path, required=True)
    supplement.add_argument("--changed-input", type=Path, required=True)
    supplement.add_argument("--pr-root", type=Path, required=True)
    supplement.add_argument("--results-output", type=Path, required=True)
    supplement.add_argument("--signals-output", type=Path, required=True)

    deletions = subparsers.add_parser("check-deletions")
    deletions.add_argument("--deleted-input", type=Path, required=True)
    deletions.add_argument("--pr-root", type=Path, required=True)
    deletions.add_argument("--signals-output", type=Path, required=True)

    args = parser.parse_args(argv)
    try:
        if args.command == "discover":
            entries = _read_json(args.files_json)
            if not isinstance(entries, list):
                raise ValueError("--files-json must contain a JSON array")
            changed, deleted, plugin_files = discover_plugin_dirs(
                entries, pr_root=args.pr_root, base_root=args.base_root
            )
            _write_lines(args.changed_output, changed)
            _write_lines(args.deleted_output, deleted)
            print(json.dumps({"changed": len(changed), "deleted": len(deleted), "plugin_files": plugin_files}))
        elif args.command == "supplement":
            results = _read_json(args.validator_results)
            if not isinstance(results, list):
                raise ValueError("--validator-results must contain a JSON array")
            filtered, signals = supplement_results(results, _read_lines(args.changed_input), pr_root=args.pr_root)
            args.results_output.write_text(json.dumps(filtered), encoding="utf-8")
            _write_lines(args.signals_output, signals)
            print(json.dumps({"filtered": len(filtered), "signals": len(signals)}))
        else:
            signals = validate_deleted_plugins(_read_lines(args.deleted_input), pr_root=args.pr_root)
            _write_lines(args.signals_output, signals)
            print(json.dumps({"deleted_signals": len(signals)}))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"prescreen scope error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
