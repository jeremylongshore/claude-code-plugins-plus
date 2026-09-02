"""Hostile regression tests for PR prescreen plugin scoping."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


_SCRIPT = Path(__file__).with_name("scope.py")
_SPEC = importlib.util.spec_from_file_location("_pr_prescreen_scope", _SCRIPT)
_SCOPE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _SCOPE
_SPEC.loader.exec_module(_SCOPE)


def _manifest(plugin: Path, value: dict | None = None) -> Path:
    path = plugin / ".claude-plugin" / "plugin.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value or {"name": plugin.name}), encoding="utf-8")
    return path


def _mcp(plugin: Path, value: dict | None = None) -> Path:
    path = plugin / ".mcp.json"
    path.write_text(
        json.dumps(
            value
            or {
                "mcpServers": {
                    plugin.name: {
                        "name": plugin.name,
                        "type": "stdio",
                        "command": "node",
                        "args": [],
                        "env": {},
                        "description": "A canonical test MCP server",
                        "version": "1.0.0",
                        "enabled": True,
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    return path


def _catalog(root: Path, sources: list[str]) -> Path:
    path = root / ".claude-plugin/marketplace.extended.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"plugins": [{"source": f"./{source}"} for source in sources]}),
        encoding="utf-8",
    )
    return path


def _supplement(
    results: list[dict], changed_dirs: list[str], *, pr_root: Path
) -> tuple[list[dict], list[str]]:
    _catalog(pr_root, changed_dirs)
    return _SCOPE.supplement_results(results, changed_dirs, pr_root=pr_root)


class ScopeTests(unittest.TestCase):
    def test_workflow_uses_only_immutable_base_tooling(self) -> None:
        workflow = (_SCRIPT.parents[2] / ".github/workflows/pr-prescreen.yml").read_text()
        self.assertIn('"$SCOPE_SCRIPT" discover', workflow)
        self.assertIn('"$SCOPE_SCRIPT" supplement', workflow)
        self.assertIn("python3 base/scripts/validate-skills-schema.py --marketplace --json --repo-root pr", workflow)
        self.assertNotIn("SCOPE_SCRIPT=pr/", workflow)
        self.assertNotIn(".prescreen-validator.py", workflow)
        self.assertNotIn("install -m 0644", workflow)

    def test_workflow_resolves_dispatch_head_base_and_all_file_pages(self) -> None:
        workflow = (_SCRIPT.parents[2] / ".github/workflows/pr-prescreen.yml").read_text()
        self.assertIn("gh api \"repos/${{ github.repository }}/pulls/$PR_NUMBER\"", workflow)
        self.assertIn("ref: ${{ steps.pr.outputs.head_sha }}", workflow)
        self.assertIn("ref: ${{ steps.pr.outputs.base_sha }}", workflow)
        self.assertIn("gh api --paginate --slurp", workflow)
        self.assertIn("| jq 'add' > /tmp/pr-files.json", workflow)
        self.assertIn('if [ "$VALIDATOR_EXIT" -ne 0 ]', workflow)
        self.assertIn('"$SCOPE_SCRIPT" check-deletions', workflow)
        self.assertNotIn("grep -q", workflow)

    def test_category_support_file_is_not_a_plugin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pr/plugins/mcp").mkdir(parents=True)
            (root / "base/plugins/mcp").mkdir(parents=True)
            (root / "pr/plugins/mcp/destructive-policies.json").write_text("{}")
            changed, deleted, count = _SCOPE.discover_plugin_dirs(
                [{"filename": "plugins/mcp/destructive-policies.json", "status": "modified"}],
                pr_root=root / "pr",
                base_root=root / "base",
            )
        self.assertEqual((changed, deleted, count), ([], [], 1))

    def test_new_cataloged_plugin_root_symlink_is_scoped_for_hard_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "outside"
            target.mkdir()
            candidate = root / "pr/plugins/mcp/evil"
            candidate.parent.mkdir(parents=True)
            candidate.symlink_to(target, target_is_directory=True)
            _catalog(root / "pr", ["plugins/mcp/evil"])
            changed, deleted, _count = _SCOPE.discover_plugin_dirs(
                [{"filename": "plugins/mcp/evil", "status": "added"}],
                pr_root=root / "pr",
                base_root=root / "base",
            )
            signals = _SCOPE.validate_deleted_plugins(deleted, pr_root=root / "pr")
        self.assertEqual(changed, [])
        self.assertEqual(deleted, ["plugins/mcp/evil"])
        self.assertTrue(any("symlink or non-directory" in signal for signal in signals))
        self.assertTrue(any("still has exact catalog source" in signal for signal in signals))

    def test_three_part_regular_cataloged_plugin_root_is_changed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _manifest(root / "pr/plugins/mcp/regular-plugin")
            _catalog(root / "pr", ["plugins/mcp/regular-plugin"])
            changed, deleted, _count = _SCOPE.discover_plugin_dirs(
                [{"filename": "plugins/mcp/regular-plugin", "status": "added"}],
                pr_root=root / "pr",
                base_root=root / "base",
            )
        self.assertEqual(changed, ["plugins/mcp/regular-plugin"])
        self.assertEqual(deleted, [])

    def test_real_support_directories_are_excluded_by_missing_markers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entries = []
            for relative in (
                "plugins/mcp/.greptile/config.json",
                "plugins/saas-packs/scripts/generate-skill-db.py",
                "plugins/saas-packs/_templates/slots/S01.md.j2",
            ):
                path = root / "pr" / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("support")
                entries.append({"filename": relative, "status": "modified"})
            changed, deleted, _count = _SCOPE.discover_plugin_dirs(
                entries, pr_root=root / "pr", base_root=root / "base"
            )
        self.assertEqual(changed, [])
        self.assertEqual(deleted, [])

    def test_cataloged_axiom_without_root_marker_is_scoped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plugin = root / "pr/plugins/skill-enhancers/axiom"
            (plugin / "plugins/axiom/skills").mkdir(parents=True)
            (plugin / "plugins/axiom/skills/example.md").write_text("nested component")
            _catalog(root / "pr", ["plugins/skill-enhancers/axiom"])
            changed, deleted, _count = _SCOPE.discover_plugin_dirs(
                [{"filename": "plugins/skill-enhancers/axiom/README.md", "status": "modified"}],
                pr_root=root / "pr",
                base_root=root / "base",
            )
        self.assertEqual(changed, ["plugins/skill-enhancers/axiom"])
        self.assertEqual(deleted, [])

    def test_same_basename_catalog_source_does_not_spoof_exact_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plugin = root / "plugins/mcp/shared-name"
            _manifest(plugin)
            _mcp(plugin)
            _catalog(root, ["plugins/security/shared-name"])
            results, signals = _SCOPE.supplement_results(
                [], ["plugins/mcp/shared-name"], pr_root=root
            )
        self.assertEqual(len(results), 1)
        self.assertTrue(any("Missing exact catalog source" in signal for signal in signals))

    def test_real_mcp_plugin_and_support_file_yield_only_plugin_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plugin = root / "pr/plugins/mcp/a2a-client"
            _manifest(plugin)
            changed, deleted, _count = _SCOPE.discover_plugin_dirs(
                [
                    {"filename": "plugins/mcp/a2a-client/src/index.ts", "status": "added"},
                    {"filename": "plugins/mcp/destructive-policies.json", "status": "modified"},
                ],
                pr_root=root / "pr",
                base_root=root / "base",
            )
        self.assertEqual(changed, ["plugins/mcp/a2a-client"])
        self.assertEqual(deleted, [])

    def test_partial_deletion_inside_existing_plugin_remains_changed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _manifest(root / "pr/plugins/mcp/a2a-client")
            _manifest(root / "base/plugins/mcp/a2a-client")
            changed, deleted, _count = _SCOPE.discover_plugin_dirs(
                [{"filename": "plugins/mcp/a2a-client/old.ts", "status": "removed"}],
                pr_root=root / "pr",
                base_root=root / "base",
            )
        self.assertEqual(changed, ["plugins/mcp/a2a-client"])
        self.assertEqual(deleted, [])

    def test_deleted_manifest_with_remaining_plugin_root_is_not_full_deletion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plugin = root / "pr/plugins/mcp/a2a-client"
            plugin.mkdir(parents=True)
            (plugin / "README.md").write_text("still here")
            _manifest(root / "base/plugins/mcp/a2a-client")
            changed, deleted, _count = _SCOPE.discover_plugin_dirs(
                [{
                    "filename": "plugins/mcp/a2a-client/.claude-plugin/plugin.json",
                    "status": "removed",
                }],
                pr_root=root / "pr",
                base_root=root / "base",
            )
        self.assertEqual(changed, ["plugins/mcp/a2a-client"])
        self.assertEqual(deleted, [])

    def test_fully_absent_plugin_is_deleted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pr").mkdir()
            _manifest(root / "base/plugins/mcp/old-plugin")
            changed, deleted, _count = _SCOPE.discover_plugin_dirs(
                [{"filename": "plugins/mcp/old-plugin/README.md", "status": "removed"}],
                pr_root=root / "pr",
                base_root=root / "base",
            )
        self.assertEqual(changed, [])
        self.assertEqual(deleted, ["plugins/mcp/old-plugin"])

    def test_base_plugin_replaced_by_symlink_enters_deletion_integrity_lane(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _manifest(root / "base/plugins/mcp/old-plugin")
            _catalog(root / "base", ["plugins/mcp/old-plugin"])
            target = root / "outside"
            target.mkdir()
            candidate = root / "pr/plugins/mcp/old-plugin"
            candidate.parent.mkdir(parents=True)
            candidate.symlink_to(target, target_is_directory=True)
            _catalog(root / "pr", ["plugins/mcp/old-plugin"])
            changed, deleted, _count = _SCOPE.discover_plugin_dirs(
                [{"filename": "plugins/mcp/old-plugin/README.md", "status": "modified"}],
                pr_root=root / "pr",
                base_root=root / "base",
            )
        self.assertEqual(changed, [])
        self.assertEqual(deleted, ["plugins/mcp/old-plugin"])

    def test_cross_plugin_rename_scopes_new_and_deleted_old_roots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _manifest(root / "pr/plugins/mcp/new-plugin")
            _manifest(root / "base/plugins/mcp/old-plugin")
            changed, deleted, _count = _SCOPE.discover_plugin_dirs(
                [{
                    "filename": "plugins/mcp/new-plugin/src/index.ts",
                    "previous_filename": "plugins/mcp/old-plugin/src/index.ts",
                    "status": "renamed",
                }],
                pr_root=root / "pr",
                base_root=root / "base",
            )
        self.assertEqual(changed, ["plugins/mcp/new-plugin"])
        self.assertEqual(deleted, ["plugins/mcp/old-plugin"])

    def test_cross_plugin_rename_scopes_old_root_when_it_still_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _manifest(root / "pr/plugins/mcp/new-plugin")
            _manifest(root / "pr/plugins/mcp/old-plugin")
            _manifest(root / "base/plugins/mcp/old-plugin")
            changed, deleted, _count = _SCOPE.discover_plugin_dirs(
                [{
                    "filename": "plugins/mcp/new-plugin/src/index.ts",
                    "previous_filename": "plugins/mcp/old-plugin/src/index.ts",
                    "status": "renamed",
                }],
                pr_root=root / "pr",
                base_root=root / "base",
            )
        self.assertEqual(changed, ["plugins/mcp/new-plugin", "plugins/mcp/old-plugin"])
        self.assertEqual(deleted, [])

    def test_valid_non_skill_mcp_plugin_gets_neutral_structural_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plugin = root / "plugins/mcp/a2a-client"
            _manifest(plugin)
            _mcp(plugin)
            results, signals = _supplement(
                [], ["plugins/mcp/a2a-client"], pr_root=root
            )
        self.assertEqual(signals, [])
        self.assertEqual(len(results), 1)
        self.assertIsNone(results[0]["grade"])
        self.assertIsNone(results[0]["score"])
        self.assertEqual(results[0]["component_type"], "plugin-structure")

    def test_manifest_name_contract_fails_for_skill_and_non_skill_plugins(self) -> None:
        for name, with_skill in (("", False), ("Bad Name", False), ("", True), ("Bad Name", True)):
            with self.subTest(name=name, with_skill=with_skill), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                plugin = root / "plugins/mcp/name-contract"
                _manifest(plugin, {"name": name})
                validator_results: list[dict] = []
                if with_skill:
                    skill = plugin / "skills/check/SKILL.md"
                    skill.parent.mkdir(parents=True)
                    skill.write_text("---\nname: check\ndescription: Valid test skill description\n---\n")
                    validator_results.append(
                        {"path": str(skill), "score": 95, "grade": "A", "errors": 0, "warnings": 0}
                    )
                results, signals = _supplement(
                    validator_results, ["plugins/mcp/name-contract"], pr_root=root
                )
            self.assertTrue(any("non-empty kebab-case" in signal for signal in signals))

    def test_mcp_marketplace_required_fields_fail_closed(self) -> None:
        canonical = {
            "name": "server",
            "type": "stdio",
            "command": "node",
            "args": [],
            "env": {},
            "description": "Canonical MCP server",
            "version": "1.0.0",
            "enabled": True,
        }
        for field in ("type", "command", "args", "env", "description", "version", "enabled"):
            with self.subTest(field=field):
                config = dict(canonical)
                del config[field]
                errors = _SCOPE._validate_mcp_servers({"server": config}, "test MCP")
                self.assertTrue(any(field in error for error in errors), errors)
        self.assertTrue(
            _SCOPE._validate_mcp_servers(
                {"Bad Name": canonical}, "test MCP"
            )
        )
        invalid_version = dict(canonical, version="1.0")
        self.assertTrue(
            any(
                "strict SemVer" in error
                for error in _SCOPE._validate_mcp_servers({"server": invalid_version}, "test MCP")
            )
        )
        for mutation, expected in (
            ({"description": "${SECRET}"}, "unsafe"),
            ({"description": "x" * 1025}, "1024"),
            ({"version": "1.0.0-01"}, "SemVer"),
            ({"metadata": []}, "metadata"),
            ({"when_to_use": "legacy"}, "deprecated"),
        ):
            with self.subTest(mutation=mutation):
                errors = _SCOPE._validate_mcp_servers(
                    {"server": dict(canonical, **mutation)}, "test MCP"
                )
                self.assertTrue(any(expected in error for error in errors), errors)

    def test_invalid_manifest_version_type_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plugin = root / "plugins/mcp/broken-version"
            _manifest(plugin, {"name": "broken-version", "version": 7})
            results, signals = _supplement(
                [], ["plugins/mcp/broken-version"], pr_root=root
            )
        self.assertEqual(results, [])
        self.assertTrue(any("Field 'version' must be string" in signal for signal in signals))

    def test_inline_http_mcp_without_url_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plugin = root / "plugins/mcp/broken-inline"
            _manifest(plugin, {
                "name": "broken-inline",
                "mcpServers": {
                    "remote": {
                        "name": "remote",
                        "type": "http",
                        "command": "node",
                        "args": [],
                        "env": {},
                        "description": "Remote MCP server",
                        "version": "1.0.0",
                        "enabled": True,
                    }
                },
            })
            results, signals = _supplement(
                [], ["plugins/mcp/broken-inline"], pr_root=root
            )
        self.assertEqual(results, [])
        self.assertTrue(any("requires a non-empty url" in signal for signal in signals))

    def test_malformed_hooks_shape_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plugin = root / "plugins/mcp/broken-hooks"
            _manifest(plugin)
            hooks = plugin / "hooks/hooks.json"
            hooks.parent.mkdir()
            hooks.write_text(json.dumps({"hooks": {"PreToolUse": []}}))
            results, signals = _supplement(
                [], ["plugins/mcp/broken-hooks"], pr_root=root
            )
        self.assertEqual(results, [])
        self.assertTrue(any("must contain a non-empty array" in signal for signal in signals))

    def test_malformed_agent_and_command_fail_closed_without_skills(self) -> None:
        for component in ("agents", "commands"):
            with self.subTest(component=component), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                plugin = root / "plugins/mcp/broken-component"
                _manifest(plugin)
                _mcp(plugin)
                artifact = plugin / component / "broken.md"
                artifact.parent.mkdir(parents=True)
                artifact.write_text("No frontmatter here")
                results, signals = _supplement(
                    [], ["plugins/mcp/broken-component"], pr_root=root
                )
            self.assertEqual(results, [])
            self.assertTrue(any("No frontmatter found" in signal for signal in signals))

    def test_deleted_root_symlink_and_stale_exact_catalog_both_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "outside"
            target.mkdir()
            candidate = root / "plugins/mcp/old-plugin"
            candidate.parent.mkdir(parents=True)
            candidate.symlink_to(target, target_is_directory=True)
            _catalog(root, ["plugins/mcp/old-plugin"])
            signals = _SCOPE.validate_deleted_plugins(
                ["plugins/mcp/old-plugin"], pr_root=root
            )
        self.assertTrue(any("symlink or non-directory" in signal for signal in signals))
        self.assertTrue(any("still has exact catalog source" in signal for signal in signals))

    def test_malformed_inline_hooks_shape_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plugin = root / "plugins/mcp/broken-inline-hooks"
            _manifest(plugin, {
                "name": "broken-inline-hooks",
                "hooks": {"PreToolUse": [{"hooks": "not-an-array"}]},
            })
            results, signals = _supplement(
                [], ["plugins/mcp/broken-inline-hooks"], pr_root=root
            )
        self.assertEqual(results, [])
        self.assertTrue(any("hooks must be a non-empty array" in signal for signal in signals))

    def test_nested_symlink_artifacts_fail_closed(self) -> None:
        for case in ("manifest", "mcp", "hooks"):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                plugin = root / "plugins/mcp/symlinked"
                outside = root / "outside"
                outside.mkdir()
                if case == "manifest":
                    target = outside / "plugin.json"
                    target.write_text(json.dumps({"name": "symlinked"}))
                    link = plugin / ".claude-plugin/plugin.json"
                    link.parent.mkdir(parents=True)
                    link.symlink_to(target)
                else:
                    _manifest(plugin)
                    if case == "mcp":
                        target = outside / ".mcp.json"
                        target.write_text(json.dumps({"mcpServers": {"x": {"command": "node"}}}))
                        (plugin / ".mcp.json").symlink_to(target)
                    else:
                        target = outside / "hooks.json"
                        target.write_text(json.dumps({"hooks": {}}))
                        (plugin / "hooks").symlink_to(outside, target_is_directory=True)
                results, signals = _supplement(
                    [], ["plugins/mcp/symlinked"], pr_root=root
                )
                self.assertEqual(results, [])
                self.assertTrue(any("no symlink components" in signal for signal in signals))

    def test_dangling_manifest_parent_symlink_on_skill_plugin_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plugin = root / "plugins/security/symlinked"
            skill = plugin / "skills/check/SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("---\nname: check\n---\n")
            (plugin / ".claude-plugin").symlink_to(root / "missing", target_is_directory=True)
            validator_result = {
                "path": str(skill), "score": 95, "grade": "A", "errors": 0, "warnings": 0,
            }
            results, signals = _supplement(
                [validator_result], ["plugins/security/symlinked"], pr_root=root
            )
        self.assertEqual(len(results), 1)
        self.assertTrue(any(".claude-plugin" in signal and "no symlink" in signal for signal in signals))

    def test_a_skill_result_does_not_hide_invalid_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plugin = root / "plugins/security/example"
            _manifest(plugin, {"name": "example", "version": 4})
            skill = plugin / "skills/check/SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("---\nname: check\ndescription: example\n---\n")
            validator_result = {
                "path": str(skill), "score": 95, "grade": "A", "errors": 0, "warnings": 0,
            }
            results, signals = _supplement(
                [validator_result], ["plugins/security/example"], pr_root=root
            )
        self.assertEqual(len(results), 1)
        self.assertTrue(any("Field 'version' must be string" in signal for signal in signals))

    def test_skill_bearing_plugin_without_validator_result_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plugin = root / "plugins/security/example"
            _manifest(plugin)
            skill = plugin / "skills/check/SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("---\nname: check\n---\n")
            results, signals = _supplement(
                [], ["plugins/security/example"], pr_root=root
            )
        self.assertEqual(results, [])
        self.assertEqual(signals, [
            "prescreen-internal-error: validator produced no result for plugins/security/example"
        ])


if __name__ == "__main__":
    unittest.main()
