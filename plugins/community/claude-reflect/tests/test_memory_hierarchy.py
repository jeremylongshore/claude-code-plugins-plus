#!/usr/bin/env python3
"""Tests for memory hierarchy integration (v3.0.0).

Tests for: _parse_rule_frontmatter, find_claude_files (rules/local/user-rules),
suggest_claude_file (enhanced routing), auto memory utilities, read_all_memory_entries.
"""
import json
import os
import platform
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lib.reflect_utils import (
    _parse_rule_frontmatter,
    find_claude_files,
    suggest_claude_file,
    get_project_folder_name,
    get_auto_memory_path,
    read_auto_memory,
    suggest_auto_memory_topic,
    read_all_memory_entries,
)


class TestParseRuleFrontmatter(unittest.TestCase):
    """Tests for _parse_rule_frontmatter()."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_simple_paths(self):
        """Test parsing frontmatter with a simple paths list."""
        f = Path(self.temp_dir) / "rule.md"
        f.write_text("---\npaths:\n  - src/\n  - lib/\n---\n\n# Rule content\n")
        result = _parse_rule_frontmatter(f)
        self.assertIsNotNone(result)
        self.assertEqual(result["paths"], ["src/", "lib/"])

    def test_multi_paths_with_quotes(self):
        """Test parsing paths with quoted values."""
        f = Path(self.temp_dir) / "rule.md"
        f.write_text('---\npaths:\n  - "src/api/"\n  - \'lib/utils/\'\n---\n\nContent\n')
        result = _parse_rule_frontmatter(f)
        self.assertIsNotNone(result)
        self.assertEqual(result["paths"], ["src/api/", "lib/utils/"])

    def test_no_frontmatter(self):
        """Test file without frontmatter returns None."""
        f = Path(self.temp_dir) / "rule.md"
        f.write_text("# Just a regular markdown file\n\n- Some content\n")
        result = _parse_rule_frontmatter(f)
        self.assertIsNone(result)

    def test_malformed_frontmatter(self):
        """Test frontmatter without closing delimiter returns None."""
        f = Path(self.temp_dir) / "rule.md"
        f.write_text("---\npaths:\n  - src/\nSome content without closing\n")
        result = _parse_rule_frontmatter(f)
        self.assertIsNone(result)

    def test_empty_frontmatter(self):
        """Test empty frontmatter returns None."""
        f = Path(self.temp_dir) / "rule.md"
        f.write_text("---\n---\n\nContent\n")
        result = _parse_rule_frontmatter(f)
        self.assertIsNone(result)

    def test_scalar_value(self):
        """Test frontmatter with scalar key-value pair."""
        f = Path(self.temp_dir) / "rule.md"
        f.write_text("---\ndescription: My rule\n---\n\nContent\n")
        result = _parse_rule_frontmatter(f)
        self.assertIsNotNone(result)
        self.assertEqual(result["description"], "My rule")

    def test_nonexistent_file(self):
        """Test nonexistent file returns None."""
        result = _parse_rule_frontmatter(Path("/nonexistent/rule.md"))
        self.assertIsNone(result)


class TestFindClaudeFilesRules(unittest.TestCase):
    """Tests for find_claude_files() with rules, local, and user-rules."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()

    def tearDown(self):
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_discovers_project_rules(self):
        """Test that .claude/rules/*.md files are discovered."""
        rules_dir = Path(self.temp_dir) / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "guardrails.md").write_text("# Guardrails\n- Don't over-engineer\n")
        (rules_dir / "coding-style.md").write_text("# Style\n- Use 2-space indent\n")

        files = find_claude_files(self.temp_dir)
        rule_files = [f for f in files if f["type"] == "rule"]
        self.assertEqual(len(rule_files), 2)
        names = sorted(Path(f["path"]).name for f in rule_files)
        self.assertEqual(names, ["coding-style.md", "guardrails.md"])

    def test_rule_frontmatter_parsing(self):
        """Test that rule files have frontmatter parsed."""
        rules_dir = Path(self.temp_dir) / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "api.md").write_text("---\npaths:\n  - src/api/\n---\n\n# API Rules\n")

        files = find_claude_files(self.temp_dir)
        rule_files = [f for f in files if f["type"] == "rule"]
        self.assertEqual(len(rule_files), 1)
        self.assertIsNotNone(rule_files[0]["frontmatter"])
        self.assertEqual(rule_files[0]["frontmatter"]["paths"], ["src/api/"])

    @patch("lib.reflect_utils.get_claude_dir")
    def test_discovers_user_rules(self, mock_claude_dir):
        """Test that ~/.claude/rules/*.md files are discovered."""
        fake_claude_dir = Path(self.temp_dir) / "fake_claude"
        fake_claude_dir.mkdir()
        mock_claude_dir.return_value = fake_claude_dir

        user_rules = fake_claude_dir / "rules"
        user_rules.mkdir()
        (user_rules / "model-prefs.md").write_text("# Models\n- Use gpt-5.1\n")

        files = find_claude_files(self.temp_dir)
        user_rule_files = [f for f in files if f["type"] == "user-rule"]
        self.assertEqual(len(user_rule_files), 1)
        self.assertIn("model-prefs.md", user_rule_files[0]["relative_path"])

    def test_discovers_local_claude(self):
        """Test that CLAUDE.local.md is discovered."""
        (Path(self.temp_dir) / "CLAUDE.local.md").write_text("# Local\n- My setting\n")

        files = find_claude_files(self.temp_dir)
        local_files = [f for f in files if f["type"] == "local"]
        self.assertEqual(len(local_files), 1)
        self.assertEqual(local_files[0]["relative_path"], "./CLAUDE.local.md")

    @patch("lib.reflect_utils.get_claude_dir")
    def test_all_types_together(self, mock_claude_dir):
        """Test discovering all file types in one call."""
        fake_claude_dir = Path(self.temp_dir) / "fake_claude"
        fake_claude_dir.mkdir()
        mock_claude_dir.return_value = fake_claude_dir

        # Global CLAUDE.md
        (fake_claude_dir / "CLAUDE.md").write_text("# Global\n")
        # User rules
        (fake_claude_dir / "rules").mkdir()
        (fake_claude_dir / "rules" / "user-rule.md").write_text("# User Rule\n")

        # Project root
        (Path(self.temp_dir) / "CLAUDE.md").write_text("# Root\n")
        (Path(self.temp_dir) / "CLAUDE.local.md").write_text("# Local\n")

        # Project rules
        proj_rules = Path(self.temp_dir) / ".claude" / "rules"
        proj_rules.mkdir(parents=True)
        (proj_rules / "style.md").write_text("# Style\n")

        # Subdirectory
        sub = Path(self.temp_dir) / "src"
        sub.mkdir()
        (sub / "CLAUDE.md").write_text("# Src\n")

        files = find_claude_files(self.temp_dir)
        types = set(f["type"] for f in files)
        self.assertIn("global", types)
        self.assertIn("root", types)
        self.assertIn("local", types)
        self.assertIn("subdirectory", types)
        self.assertIn("rule", types)
        self.assertIn("user-rule", types)

    def test_excluded_dirs_still_work(self):
        """Test that excluded dirs are still excluded for new discovery."""
        nm = Path(self.temp_dir) / "node_modules"
        nm.mkdir()
        (nm / "CLAUDE.md").write_text("# Should be excluded\n")

        nm_rules = nm / ".claude" / "rules"
        nm_rules.mkdir(parents=True)
        (nm_rules / "bad.md").write_text("# Should not be found\n")

        files = find_claude_files(self.temp_dir)
        all_paths = [f["path"] for f in files]
        self.assertFalse(any("node_modules" in p for p in all_paths))

    def test_no_rules_dir_no_error(self):
        """Test that missing .claude/rules/ doesn't cause errors."""
        files = find_claude_files(self.temp_dir)
        rule_files = [f for f in files if f["type"] in ("rule", "user-rule")]
        # May find user rules depending on system, but should not error
        self.assertIsInstance(files, list)


class TestSuggestClaudeFileEnhanced(unittest.TestCase):
    """Tests for enhanced suggest_claude_file() with learning_type."""

    def setUp(self):
        self.files = [
            {"path": "/home/.claude/CLAUDE.md", "relative_path": "~/.claude/CLAUDE.md", "type": "global"},
            {"path": "/project/CLAUDE.md", "relative_path": "./CLAUDE.md", "type": "root"},
            {"path": "/project/.claude/rules/guardrails.md", "relative_path": "./.claude/rules/guardrails.md",
             "type": "rule", "frontmatter": None},
            {"path": "/project/.claude/rules/api.md", "relative_path": "./.claude/rules/api.md",
             "type": "rule", "frontmatter": {"paths": ["src/api/"]}},
        ]

    def test_guardrail_routes_to_rule_file(self):
        """Test guardrail learning routes to guardrails.md."""
        result = suggest_claude_file(
            "don't add docstrings unless asked",
            self.files,
            learning_type="guardrail",
        )
        self.assertEqual(result, "./.claude/rules/guardrails.md")

    def test_guardrail_creates_path_when_no_file(self):
        """Test guardrail suggests creating guardrails.md if not found."""
        files_no_guardrails = [f for f in self.files if "guardrails" not in f.get("path", "")]
        result = suggest_claude_file(
            "don't add docstrings unless asked",
            files_no_guardrails,
            learning_type="guardrail",
        )
        self.assertEqual(result, "./.claude/rules/guardrails.md")

    def test_model_routing_global(self):
        """Test model-related learning routes to global CLAUDE.md."""
        result = suggest_claude_file("use gpt-5.1 for reasoning", self.files)
        self.assertEqual(result, "~/.claude/CLAUDE.md")

    def test_backward_compat_no_learning_type(self):
        """Test backward compatibility — no learning_type still works."""
        result = suggest_claude_file("always use venv", self.files)
        self.assertEqual(result, "~/.claude/CLAUDE.md")

    def test_path_scoped_rule_match(self):
        """Test learning mentioning a directory matches path-scoped rule."""
        result = suggest_claude_file("In the src/api/ module, use REST", self.files)
        self.assertEqual(result, "./.claude/rules/api.md")

    def test_ambiguous_returns_none(self):
        """Test ambiguous learning returns None."""
        result = suggest_claude_file("use database pooling", self.files)
        self.assertIsNone(result)


class TestAutoMemoryPath(unittest.TestCase):
    """Tests for auto memory path utilities."""

    @unittest.skipIf(platform.system() == "Windows", "Unix-specific path encoding")
    def test_folder_name_encoding_unix(self):
        """Test project folder name encoding for Unix paths."""
        result = get_project_folder_name("/Users/bob/myapp")
        self.assertEqual(result, "-Users-bob-myapp")

    @unittest.skipIf(platform.system() == "Windows", "Unix-specific path encoding")
    def test_folder_name_encoding_deep(self):
        """Test project folder name encoding for deep paths."""
        result = get_project_folder_name("/Users/bob/code/projects/myapp")
        self.assertEqual(result, "-Users-bob-code-projects-myapp")

    def test_folder_name_encoding_structure(self):
        """Test folder name encoding produces valid structure on any platform."""
        result = get_project_folder_name(tempfile.gettempdir())
        self.assertTrue(result.startswith("-"))
        self.assertNotIn("/", result)
        self.assertNotIn("\\", result)

    @unittest.skipIf(platform.system() == "Windows", "Unix-specific path encoding")
    @patch("lib.reflect_utils.get_claude_dir")
    def test_auto_memory_path_resolution(self, mock_claude_dir):
        """Test auto memory path is correctly resolved."""
        mock_claude_dir.return_value = Path("/home/user/.claude")
        path = get_auto_memory_path("/Users/bob/myapp")
        self.assertEqual(path, Path("/home/user/.claude/projects/-Users-bob-myapp/memory"))

    def test_read_auto_memory_empty(self):
        """Test reading auto memory from nonexistent directory."""
        result = read_auto_memory("/nonexistent/path")
        self.assertEqual(result, [])

    def test_read_auto_memory_with_files(self):
        """Test reading auto memory with actual files."""
        temp_dir = tempfile.mkdtemp()
        try:
            with patch("lib.reflect_utils.get_auto_memory_path") as mock_path:
                memory_dir = Path(temp_dir) / "memory"
                memory_dir.mkdir()
                (memory_dir / "general.md").write_text("# General\n- Entry one\n- Entry two\n")
                (memory_dir / "tools.md").write_text("# Tools\n- Use MCP\n")
                mock_path.return_value = memory_dir

                result = read_auto_memory()
                self.assertEqual(len(result), 2)
                names = sorted(r["name"] for r in result)
                self.assertEqual(names, ["general", "tools"])
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_suggest_topic_model(self):
        """Test topic suggestion for model-related learning."""
        topic = suggest_auto_memory_topic("use gpt-5.1 for reasoning")
        self.assertEqual(topic, "model-preferences")

    def test_suggest_topic_tool(self):
        """Test topic suggestion for tool-related learning."""
        topic = suggest_auto_memory_topic("configure the MCP server plugin")
        self.assertEqual(topic, "tool-usage")

    def test_suggest_topic_general(self):
        """Test topic suggestion falls back to general."""
        topic = suggest_auto_memory_topic("something very generic")
        self.assertEqual(topic, "general")

    def test_suggest_topic_environment(self):
        """Test topic suggestion for environment-related learning."""
        topic = suggest_auto_memory_topic("always use venv for Python projects")
        self.assertEqual(topic, "environment")

    def test_suggest_topic_workflow(self):
        """Test topic suggestion for workflow-related learning."""
        topic = suggest_auto_memory_topic("run tests before deploying")
        self.assertEqual(topic, "workflow")


class TestReadAllMemoryEntries(unittest.TestCase):
    """Tests for read_all_memory_entries()."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("lib.reflect_utils.get_claude_dir")
    def test_multi_tier_reads(self, mock_claude_dir):
        """Test reading entries from multiple tiers."""
        fake_claude = Path(self.temp_dir) / "fake_claude"
        fake_claude.mkdir()
        mock_claude_dir.return_value = fake_claude

        # Global CLAUDE.md
        (fake_claude / "CLAUDE.md").write_text("# Global\n- Use gpt-5.1\n- Always test\n")

        # Project CLAUDE.md
        (Path(self.temp_dir) / "CLAUDE.md").write_text("# Project\n- Use postgres\n")

        entries = read_all_memory_entries(self.temp_dir)
        texts = [e["text"] for e in entries]
        self.assertIn("Use gpt-5.1", texts)
        self.assertIn("Always test", texts)
        self.assertIn("Use postgres", texts)

    @patch("lib.reflect_utils.get_claude_dir")
    def test_source_tracking(self, mock_claude_dir):
        """Test that entries track their source file and type."""
        fake_claude = Path(self.temp_dir) / "fake_claude"
        fake_claude.mkdir()
        mock_claude_dir.return_value = fake_claude

        (fake_claude / "CLAUDE.md").write_text("# Global\n- Use gpt-5.1\n")
        (Path(self.temp_dir) / "CLAUDE.md").write_text("# Project\n- Use postgres\n")

        entries = read_all_memory_entries(self.temp_dir)
        global_entries = [e for e in entries if e["source_type"] == "global"]
        root_entries = [e for e in entries if e["source_type"] == "root"]
        self.assertTrue(len(global_entries) > 0)
        self.assertTrue(len(root_entries) > 0)
        self.assertEqual(global_entries[0]["source_file"], "~/.claude/CLAUDE.md")

    @patch("lib.reflect_utils.get_claude_dir")
    def test_missing_files_no_error(self, mock_claude_dir):
        """Test that missing files don't cause errors."""
        fake_claude = Path(self.temp_dir) / "fake_claude"
        fake_claude.mkdir()
        mock_claude_dir.return_value = fake_claude

        # No files exist
        entries = read_all_memory_entries(self.temp_dir)
        self.assertEqual(entries, [])


if __name__ == "__main__":
    unittest.main()
