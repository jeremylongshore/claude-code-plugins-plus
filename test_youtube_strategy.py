"""
Tests for the youtube-strategy plugin structure.

Validates plugin.json, skills, commands, and agents follow the
Claude Code Plugins spec (2026). Discovered by CI's find . -name "test_*.py".
"""

import json
import os
import re

import pytest
import yaml

PLUGIN_ROOT = os.path.join(
    os.path.dirname(__file__),
    "plugins", "productivity", "youtube-strategy"
)

PLUGIN_JSON_PATH = os.path.join(PLUGIN_ROOT, ".claude-plugin", "plugin.json")

EXPECTED_SKILLS = ["yt-research", "yt-ideation", "yt-brief", "yt-packaging", "yt-outline"]

EXPECTED_COMMANDS = [
    "youtube-strategy.md",
    "yt-pipeline.md",
    "yt-research.md",
    "yt-ideate.md",
    "yt-brief.md",
    "yt-package.md",
    "yt-outline.md",
]

EXPECTED_AGENTS = ["yt-scraper.md", "channel-analyzer.md", "idea-validator.md"]

# Allowed fields per CLAUDE.md spec
ALLOWED_PLUGIN_JSON_FIELDS = {
    "name", "version", "description", "author",
    "repository", "homepage", "license", "keywords"
}

# Valid tool names per 2026 spec
VALID_TOOLS = {
    "Read", "Write", "Edit", "Bash", "Glob", "Grep",
    "WebFetch", "WebSearch", "Task", "TodoWrite",
    "NotebookEdit", "AskUserQuestion", "Skill"
}

VALID_MODELS = {"sonnet", "haiku", "opus"}


def _parse_frontmatter(filepath: str) -> dict:
    """Parse YAML frontmatter from a markdown file."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    assert match, f"No YAML frontmatter found in {filepath}"
    return yaml.safe_load(match.group(1))


# ───────────────────────────────────────────────────────────────────────
# TestPluginJson
# ───────────────────────────────────────────────────────────────────────

class TestPluginJson:
    def test_plugin_json_exists(self):
        assert os.path.exists(PLUGIN_JSON_PATH), (
            f"plugin.json not found at {PLUGIN_JSON_PATH}"
        )

    def test_plugin_json_valid_with_required_fields(self):
        with open(PLUGIN_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["name"] == "youtube-strategy"
        assert "version" in data, "Missing 'version' field"
        assert "description" in data, "Missing 'description' field"

    def test_no_extra_fields(self):
        with open(PLUGIN_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        extra = set(data.keys()) - ALLOWED_PLUGIN_JSON_FIELDS
        assert not extra, f"Disallowed fields in plugin.json: {extra}"


# ───────────────────────────────────────────────────────────────────────
# TestSkills
# ───────────────────────────────────────────────────────────────────────

class TestSkills:
    @pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
    def test_skill_directory_exists(self, skill_name):
        skill_dir = os.path.join(PLUGIN_ROOT, "skills", skill_name)
        assert os.path.isdir(skill_dir), f"Skill directory missing: {skill_dir}"

    @pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
    def test_skill_md_has_valid_frontmatter(self, skill_name):
        skill_path = os.path.join(PLUGIN_ROOT, "skills", skill_name, "SKILL.md")
        assert os.path.exists(skill_path), f"SKILL.md missing for {skill_name}"

        fm = _parse_frontmatter(skill_path)
        assert "name" in fm, f"Missing 'name' in {skill_name} SKILL.md"
        assert "description" in fm, f"Missing 'description' in {skill_name} SKILL.md"
        assert "allowed-tools" in fm, f"Missing 'allowed-tools' in {skill_name} SKILL.md"

    @pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
    def test_skill_allowed_tools_are_valid(self, skill_name):
        skill_path = os.path.join(PLUGIN_ROOT, "skills", skill_name, "SKILL.md")
        fm = _parse_frontmatter(skill_path)

        raw_tools = fm.get("allowed-tools", "")
        if isinstance(raw_tools, list):
            tools = raw_tools
        else:
            # Comma-separated string, may have Bash(pattern) syntax
            tools = [t.strip() for t in str(raw_tools).split(",")]

        for tool in tools:
            # Strip Bash(...) patterns to just "Bash"
            base_tool = re.sub(r"\(.*\)", "", tool).strip()
            assert base_tool in VALID_TOOLS, (
                f"Invalid tool '{tool}' in {skill_name} SKILL.md"
            )

    @pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
    def test_skill_name_matches_directory(self, skill_name):
        skill_path = os.path.join(PLUGIN_ROOT, "skills", skill_name, "SKILL.md")
        fm = _parse_frontmatter(skill_path)
        assert fm["name"] == skill_name, (
            f"Frontmatter name '{fm['name']}' != directory '{skill_name}'"
        )


# ───────────────────────────────────────────────────────────────────────
# TestCommands
# ───────────────────────────────────────────────────────────────────────

class TestCommands:
    def test_expected_command_files_exist(self):
        commands_dir = os.path.join(PLUGIN_ROOT, "commands")
        assert os.path.isdir(commands_dir), "commands/ directory missing"

        for cmd_file in EXPECTED_COMMANDS:
            path = os.path.join(commands_dir, cmd_file)
            assert os.path.exists(path), f"Command file missing: {cmd_file}"

    @pytest.mark.parametrize("cmd_file", EXPECTED_COMMANDS)
    def test_command_has_valid_frontmatter(self, cmd_file):
        path = os.path.join(PLUGIN_ROOT, "commands", cmd_file)
        fm = _parse_frontmatter(path)

        assert "name" in fm, f"Missing 'name' in {cmd_file}"
        assert "description" in fm, f"Missing 'description' in {cmd_file}"


# ───────────────────────────────────────────────────────────────────────
# TestAgents
# ───────────────────────────────────────────────────────────────────────

class TestAgents:
    @pytest.mark.parametrize("agent_file", EXPECTED_AGENTS)
    def test_agent_file_exists(self, agent_file):
        path = os.path.join(PLUGIN_ROOT, "agents", agent_file)
        assert os.path.exists(path), f"Agent file missing: {agent_file}"

    @pytest.mark.parametrize("agent_file", EXPECTED_AGENTS)
    def test_agent_has_valid_frontmatter(self, agent_file):
        path = os.path.join(PLUGIN_ROOT, "agents", agent_file)
        fm = _parse_frontmatter(path)

        assert "name" in fm, f"Missing 'name' in {agent_file}"
        assert "description" in fm, f"Missing 'description' in {agent_file}"

    @pytest.mark.parametrize("agent_file", EXPECTED_AGENTS)
    def test_agent_model_is_valid(self, agent_file):
        path = os.path.join(PLUGIN_ROOT, "agents", agent_file)
        fm = _parse_frontmatter(path)

        model = fm.get("model")
        if model is not None:
            assert model in VALID_MODELS, (
                f"Invalid model '{model}' in {agent_file} (expected one of {VALID_MODELS})"
            )
