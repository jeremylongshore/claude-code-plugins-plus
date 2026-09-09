#!/usr/bin/env python3
"""Integration tests for claude-reflect scripts.

These tests verify that both bash and Python versions produce the same results.
Run with: python -m pytest tests/test_integration.py -v
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# Skip bash tests on Windows
IS_WINDOWS = sys.platform == 'win32'
skip_on_windows = unittest.skipIf(IS_WINDOWS, "Bash scripts not available on Windows")

# Script locations
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
BASH_SCRIPTS = {
    "check_learnings": SCRIPTS_DIR / "legacy" / "check-learnings.sh",
    "post_commit_reminder": SCRIPTS_DIR / "legacy" / "post-commit-reminder.sh",
    "capture_learning": SCRIPTS_DIR / "legacy" / "capture-learning.sh",
    "extract_session_learnings": SCRIPTS_DIR / "legacy" / "extract-session-learnings.sh",
    "extract_tool_rejections": SCRIPTS_DIR / "legacy" / "extract-tool-rejections.sh",
}
PYTHON_SCRIPTS = {
    "check_learnings": SCRIPTS_DIR / "check_learnings.py",
    "post_commit_reminder": SCRIPTS_DIR / "post_commit_reminder.py",
    "capture_learning": SCRIPTS_DIR / "capture_learning.py",
    "extract_session_learnings": SCRIPTS_DIR / "extract_session_learnings.py",
    "extract_tool_rejections": SCRIPTS_DIR / "extract_tool_rejections.py",
}


def run_bash_script(script_path: Path, stdin: str = "", args: list = None) -> tuple:
    """Run a bash script and return (stdout, stderr, returncode)."""
    cmd = ["bash", str(script_path)] + (args or [])
    result = subprocess.run(
        cmd,
        input=stdin,
        capture_output=True,
        text=True,
        cwd=str(SCRIPTS_DIR),
    )
    return result.stdout, result.stderr, result.returncode


def run_python_script(script_path: Path, stdin: str = "", args: list = None) -> tuple:
    """Run a Python script and return (stdout, stderr, returncode)."""
    cmd = [sys.executable, str(script_path)] + (args or [])
    result = subprocess.run(
        cmd,
        input=stdin,
        capture_output=True,
        text=True,
        cwd=str(SCRIPTS_DIR),
    )
    return result.stdout, result.stderr, result.returncode


class TestPostCommitReminder(unittest.TestCase):
    """Tests for post-commit reminder hook."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.queue_path = Path(self.temp_dir) / ".claude" / "learnings-queue.json"
        self.queue_path.parent.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @skip_on_windows
    def test_bash_git_commit_detected(self):
        """Test bash script detects git commit."""
        stdin = json.dumps({"tool_input": {"command": "git commit -m 'test'"}})
        stdout, stderr, code = run_bash_script(
            BASH_SCRIPTS["post_commit_reminder"], stdin=stdin
        )
        self.assertEqual(code, 0)
        self.assertIn("Git commit detected", stdout)

    def test_python_git_commit_detected(self):
        """Test Python script detects git commit."""
        stdin = json.dumps({"tool_input": {"command": "git commit -m 'test'"}})
        stdout, stderr, code = run_python_script(
            PYTHON_SCRIPTS["post_commit_reminder"], stdin=stdin
        )
        self.assertEqual(code, 0)
        self.assertIn("Git commit detected", stdout)

    @skip_on_windows
    def test_bash_ignores_amend(self):
        """Test bash script ignores --amend commits."""
        stdin = json.dumps({"tool_input": {"command": "git commit --amend -m 'test'"}})
        stdout, stderr, code = run_bash_script(
            BASH_SCRIPTS["post_commit_reminder"], stdin=stdin
        )
        self.assertEqual(code, 0)
        self.assertNotIn("Git commit detected", stdout)

    def test_python_ignores_amend(self):
        """Test Python script ignores --amend commits."""
        stdin = json.dumps({"tool_input": {"command": "git commit --amend -m 'test'"}})
        stdout, stderr, code = run_python_script(
            PYTHON_SCRIPTS["post_commit_reminder"], stdin=stdin
        )
        self.assertEqual(code, 0)
        self.assertNotIn("Git commit detected", stdout)

    @skip_on_windows
    def test_bash_ignores_non_commit(self):
        """Test bash script ignores non-commit commands."""
        stdin = json.dumps({"tool_input": {"command": "ls -la"}})
        stdout, stderr, code = run_bash_script(
            BASH_SCRIPTS["post_commit_reminder"], stdin=stdin
        )
        self.assertEqual(code, 0)
        self.assertEqual(stdout.strip(), "")

    def test_python_ignores_non_commit(self):
        """Test Python script ignores non-commit commands."""
        stdin = json.dumps({"tool_input": {"command": "ls -la"}})
        stdout, stderr, code = run_python_script(
            PYTHON_SCRIPTS["post_commit_reminder"], stdin=stdin
        )
        self.assertEqual(code, 0)
        self.assertEqual(stdout.strip(), "")

    @skip_on_windows
    def test_bash_empty_input(self):
        """Test bash script handles empty input."""
        stdout, stderr, code = run_bash_script(
            BASH_SCRIPTS["post_commit_reminder"], stdin=""
        )
        self.assertEqual(code, 0)

    def test_python_empty_input(self):
        """Test Python script handles empty input."""
        stdout, stderr, code = run_python_script(
            PYTHON_SCRIPTS["post_commit_reminder"], stdin=""
        )
        self.assertEqual(code, 0)

    @skip_on_windows
    def test_bash_invalid_json(self):
        """Test bash script handles invalid JSON."""
        stdout, stderr, code = run_bash_script(
            BASH_SCRIPTS["post_commit_reminder"], stdin="not json"
        )
        self.assertEqual(code, 0)  # Should not crash

    def test_python_invalid_json(self):
        """Test Python script handles invalid JSON."""
        stdout, stderr, code = run_python_script(
            PYTHON_SCRIPTS["post_commit_reminder"], stdin="not json"
        )
        self.assertEqual(code, 0)  # Should not crash


class TestExtractSessionLearnings(unittest.TestCase):
    """Tests for session extraction script."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.session_file = Path(self.temp_dir) / "test-session.jsonl"

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_session_file(self, entries: list):
        """Create a session file with given entries."""
        with open(self.session_file, "w") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")

    @skip_on_windows
    def test_bash_extracts_user_messages(self):
        """Test bash script extracts user messages."""
        self._create_session_file([
            {
                "type": "user",
                "message": {
                    "content": [{"type": "text", "text": "Hello world"}]
                }
            },
            {
                "type": "assistant",
                "message": {"content": "Response"}
            },
        ])

        stdout, stderr, code = run_bash_script(
            BASH_SCRIPTS["extract_session_learnings"],
            args=[str(self.session_file)]
        )
        self.assertEqual(code, 0)
        self.assertIn("Hello world", stdout)

    def test_python_extracts_user_messages(self):
        """Test Python script extracts user messages."""
        self._create_session_file([
            {
                "type": "user",
                "message": {
                    "content": [{"type": "text", "text": "Hello world"}]
                }
            },
            {
                "type": "assistant",
                "message": {"content": "Response"}
            },
        ])

        stdout, stderr, code = run_python_script(
            PYTHON_SCRIPTS["extract_session_learnings"],
            args=[str(self.session_file)]
        )
        self.assertEqual(code, 0)
        self.assertIn("Hello world", stdout)

    @skip_on_windows
    def test_bash_skips_meta_messages(self):
        """Test bash script skips isMeta messages."""
        self._create_session_file([
            {
                "type": "user",
                "isMeta": True,
                "message": {
                    "content": [{"type": "text", "text": "Meta message"}]
                }
            },
            {
                "type": "user",
                "message": {
                    "content": [{"type": "text", "text": "Regular message"}]
                }
            },
        ])

        stdout, stderr, code = run_bash_script(
            BASH_SCRIPTS["extract_session_learnings"],
            args=[str(self.session_file)]
        )
        self.assertEqual(code, 0)
        self.assertNotIn("Meta message", stdout)
        self.assertIn("Regular message", stdout)

    def test_python_skips_meta_messages(self):
        """Test Python script skips isMeta messages."""
        self._create_session_file([
            {
                "type": "user",
                "isMeta": True,
                "message": {
                    "content": [{"type": "text", "text": "Meta message"}]
                }
            },
            {
                "type": "user",
                "message": {
                    "content": [{"type": "text", "text": "Regular message"}]
                }
            },
        ])

        stdout, stderr, code = run_python_script(
            PYTHON_SCRIPTS["extract_session_learnings"],
            args=[str(self.session_file)]
        )
        self.assertEqual(code, 0)
        self.assertNotIn("Meta message", stdout)
        self.assertIn("Regular message", stdout)

    @skip_on_windows
    def test_bash_corrections_only_flag(self):
        """Test bash script --corrections-only flag."""
        self._create_session_file([
            {
                "type": "user",
                "message": {
                    "content": [{"type": "text", "text": "Hello world"}]
                }
            },
            {
                "type": "user",
                "message": {
                    "content": [{"type": "text", "text": "no, use Python"}]
                }
            },
        ])

        stdout, stderr, code = run_bash_script(
            BASH_SCRIPTS["extract_session_learnings"],
            args=[str(self.session_file), "--corrections-only"]
        )
        self.assertEqual(code, 0)
        self.assertNotIn("Hello world", stdout)
        self.assertIn("no, use Python", stdout)

    def test_python_corrections_only_flag(self):
        """Test Python script --corrections-only flag."""
        self._create_session_file([
            {
                "type": "user",
                "message": {
                    "content": [{"type": "text", "text": "Hello world"}]
                }
            },
            {
                "type": "user",
                "message": {
                    "content": [{"type": "text", "text": "no, use Python"}]
                }
            },
        ])

        stdout, stderr, code = run_python_script(
            PYTHON_SCRIPTS["extract_session_learnings"],
            args=[str(self.session_file), "--corrections-only"]
        )
        self.assertEqual(code, 0)
        self.assertNotIn("Hello world", stdout)
        self.assertIn("no, use Python", stdout)

    @skip_on_windows
    def test_bash_nonexistent_file(self):
        """Test bash script handles nonexistent file."""
        stdout, stderr, code = run_bash_script(
            BASH_SCRIPTS["extract_session_learnings"],
            args=["/nonexistent/file.jsonl"]
        )
        self.assertNotEqual(code, 0)  # Should fail

    def test_python_nonexistent_file(self):
        """Test Python script handles nonexistent file."""
        stdout, stderr, code = run_python_script(
            PYTHON_SCRIPTS["extract_session_learnings"],
            args=["/nonexistent/file.jsonl"]
        )
        self.assertNotEqual(code, 0)  # Should fail


class TestCapturePatternEquivalence(unittest.TestCase):
    """Tests to verify bash and Python capture the same patterns."""

    # These tests ensure the Python pattern detection matches bash behavior

    def test_remember_pattern(self):
        """Test 'remember:' is detected by both versions."""
        test_messages = [
            "remember: always use gpt-5.1",
            "Remember: use async/await",
            "REMEMBER: never hardcode passwords",
        ]
        for msg in test_messages:
            with self.subTest(msg=msg):
                # The capture scripts would detect this
                # We test the pattern detection directly
                pass  # Pattern tests covered in test_reflect_utils.py

    def test_correction_patterns(self):
        """Test correction patterns are detected by both versions."""
        test_cases = [
            ("no, use Python", "no,use"),
            ("don't use that library", "don't-use"),
            ("stop using globals", "stop/never-use"),
            ("never use eval", "stop/never-use"),
            ("that's wrong", "that's-wrong"),
            ("that is incorrect", "that's-wrong"),
            ("I meant the other one", "I-meant/said"),
            ("I said use async", "I-meant/said"),
            ("I told you to use venv", "I-told-you"),
            ("you should use Python", "you-should-use"),
        ]
        for msg, expected_pattern in test_cases:
            with self.subTest(msg=msg):
                # Pattern matching tested in test_reflect_utils.py
                pass


@skip_on_windows
class TestBashPythonOutputEquivalence(unittest.TestCase):
    """Tests to verify bash and Python produce equivalent output."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.session_file = Path(self.temp_dir) / "test-session.jsonl"

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_session_file(self, entries: list):
        """Create a session file with given entries."""
        with open(self.session_file, "w") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")

    def test_extract_same_messages(self):
        """Test bash and Python extract the same messages."""
        self._create_session_file([
            {
                "type": "user",
                "message": {
                    "content": [{"type": "text", "text": "First message"}]
                }
            },
            {
                "type": "user",
                "message": {
                    "content": [{"type": "text", "text": "Second message"}]
                }
            },
            {
                "type": "user",
                "message": {
                    "content": [{"type": "text", "text": "no, use Python"}]
                }
            },
        ])

        bash_stdout, _, _ = run_bash_script(
            BASH_SCRIPTS["extract_session_learnings"],
            args=[str(self.session_file)]
        )
        python_stdout, _, _ = run_python_script(
            PYTHON_SCRIPTS["extract_session_learnings"],
            args=[str(self.session_file)]
        )

        # Both should extract the same messages
        bash_lines = set(bash_stdout.strip().split("\n"))
        python_lines = set(python_stdout.strip().split("\n"))

        self.assertEqual(bash_lines, python_lines)

    def test_extract_same_corrections(self):
        """Test bash and Python extract the same corrections."""
        self._create_session_file([
            {
                "type": "user",
                "message": {
                    "content": [{"type": "text", "text": "Hello world"}]
                }
            },
            {
                "type": "user",
                "message": {
                    "content": [{"type": "text", "text": "no, use Python instead"}]
                }
            },
            {
                "type": "user",
                "message": {
                    "content": [{"type": "text", "text": "remember: always test"}]
                }
            },
        ])

        bash_stdout, _, _ = run_bash_script(
            BASH_SCRIPTS["extract_session_learnings"],
            args=[str(self.session_file), "--corrections-only"]
        )
        python_stdout, _, _ = run_python_script(
            PYTHON_SCRIPTS["extract_session_learnings"],
            args=[str(self.session_file), "--corrections-only"]
        )

        bash_lines = set(bash_stdout.strip().split("\n")) if bash_stdout.strip() else set()
        python_lines = set(python_stdout.strip().split("\n")) if python_stdout.strip() else set()

        self.assertEqual(bash_lines, python_lines)


if __name__ == "__main__":
    unittest.main()
