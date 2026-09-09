#!/usr/bin/env python3
"""Tests for tool error extraction functionality."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lib.reflect_utils import (
    extract_tool_errors,
    aggregate_tool_errors,
    TOOL_ERROR_EXCLUDE_PATTERNS,
    PROJECT_SPECIFIC_ERROR_PATTERNS,
)


class TestToolErrorPatterns(unittest.TestCase):
    """Tests for error pattern definitions."""

    def test_exclude_patterns_defined(self):
        """Test that exclusion patterns are defined."""
        self.assertIsInstance(TOOL_ERROR_EXCLUDE_PATTERNS, list)
        self.assertGreater(len(TOOL_ERROR_EXCLUDE_PATTERNS), 0)

    def test_project_specific_patterns_defined(self):
        """Test that project-specific patterns are defined."""
        self.assertIsInstance(PROJECT_SPECIFIC_ERROR_PATTERNS, list)
        self.assertGreater(len(PROJECT_SPECIFIC_ERROR_PATTERNS), 0)

    def test_pattern_structure(self):
        """Test that patterns have correct structure."""
        for pattern in PROJECT_SPECIFIC_ERROR_PATTERNS:
            self.assertIsInstance(pattern, tuple)
            self.assertEqual(len(pattern), 3)
            error_type, regex, guideline = pattern
            self.assertIsInstance(error_type, str)
            self.assertIsInstance(regex, str)
            self.assertIsInstance(guideline, str)


class TestExtractToolErrors(unittest.TestCase):
    """Tests for extract_tool_errors function."""

    def setUp(self):
        """Create temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_session_file(self, entries):
        """Create a test session JSONL file."""
        session_file = Path(self.temp_dir) / "test_session.jsonl"
        with open(session_file, "w") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")
        return session_file

    def test_extract_empty_file(self):
        """Test extraction from empty file."""
        session_file = Path(self.temp_dir) / "empty.jsonl"
        session_file.write_text("")

        result = extract_tool_errors(session_file)
        self.assertEqual(result, [])

    def test_extract_nonexistent_file(self):
        """Test extraction from nonexistent file."""
        session_file = Path(self.temp_dir) / "nonexistent.jsonl"

        result = extract_tool_errors(session_file)
        self.assertEqual(result, [])

    def test_extract_connection_refused_error(self):
        """Test extraction of connection refused errors."""
        entries = [{
            "type": "user",
            "message": {
                "content": [{
                    "type": "tool_result",
                    "is_error": True,
                    "content": "Connection refused to localhost:5432"
                }]
            }
        }]
        session_file = self._create_session_file(entries)

        result = extract_tool_errors(session_file, project_specific_only=True)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["error_type"], "connection_refused")
        self.assertIn("Connection refused", result[0]["content"])

    def test_exclude_guardrails(self):
        """Test that Claude Code guardrails are excluded."""
        entries = [{
            "type": "user",
            "message": {
                "content": [{
                    "type": "tool_result",
                    "is_error": True,
                    "content": "File has not been read yet. Read it first before writing to it."
                }]
            }
        }]
        session_file = self._create_session_file(entries)

        result = extract_tool_errors(session_file, project_specific_only=True)
        self.assertEqual(result, [])

    def test_exclude_user_rejections(self):
        """Test that user rejections are excluded (handled separately)."""
        entries = [{
            "type": "user",
            "message": {
                "content": [{
                    "type": "tool_result",
                    "is_error": True,
                    "content": "The user doesn't want to proceed with this tool use."
                }]
            }
        }]
        session_file = self._create_session_file(entries)

        result = extract_tool_errors(session_file, project_specific_only=True)
        self.assertEqual(result, [])

    def test_exclude_bash_quoting_errors(self):
        """Test that bash quoting errors are excluded (global Claude behavior)."""
        entries = [{
            "type": "user",
            "message": {
                "content": [{
                    "type": "tool_result",
                    "is_error": True,
                    "content": "unexpected EOF while looking for matching `'"
                }]
            }
        }]
        session_file = self._create_session_file(entries)

        result = extract_tool_errors(session_file, project_specific_only=True)
        self.assertEqual(result, [])

    def test_extract_supabase_error(self):
        """Test extraction of Supabase-related errors."""
        entries = [{
            "type": "user",
            "message": {
                "content": [{
                    "type": "tool_result",
                    "is_error": True,
                    "content": "Error: supabase connection failed - invalid URL"
                }]
            }
        }]
        session_file = self._create_session_file(entries)

        result = extract_tool_errors(session_file, project_specific_only=True)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["error_type"], "supabase_error")
        self.assertIn("SUPABASE", result[0]["suggested_guideline"])

    def test_extract_module_not_found(self):
        """Test extraction of module not found errors."""
        entries = [{
            "type": "user",
            "message": {
                "content": [{
                    "type": "tool_result",
                    "is_error": True,
                    "content": "ModuleNotFoundError: No module named 'myapp.utils'"
                }]
            }
        }]
        session_file = self._create_session_file(entries)

        result = extract_tool_errors(session_file, project_specific_only=True)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["error_type"], "module_not_found")

    def test_include_all_errors(self):
        """Test that project_specific_only=False includes unknown errors."""
        entries = [{
            "type": "user",
            "message": {
                "content": [{
                    "type": "tool_result",
                    "is_error": True,
                    "content": "Some random unknown error happened"
                }]
            }
        }]
        session_file = self._create_session_file(entries)

        # With project_specific_only=True, should be empty
        result_filtered = extract_tool_errors(session_file, project_specific_only=True)
        self.assertEqual(result_filtered, [])

        # With project_specific_only=False, should be included
        result_all = extract_tool_errors(session_file, project_specific_only=False)
        self.assertEqual(len(result_all), 1)
        self.assertEqual(result_all[0]["error_type"], "unknown")

    def test_skip_non_user_entries(self):
        """Test that non-user entries are skipped."""
        entries = [{
            "type": "assistant",
            "message": {
                "content": [{
                    "type": "tool_result",
                    "is_error": True,
                    "content": "Connection refused to localhost:5432"
                }]
            }
        }]
        session_file = self._create_session_file(entries)

        result = extract_tool_errors(session_file)
        self.assertEqual(result, [])

    def test_skip_non_error_results(self):
        """Test that non-error tool results are skipped."""
        entries = [{
            "type": "user",
            "message": {
                "content": [{
                    "type": "tool_result",
                    "is_error": False,
                    "content": "Command completed successfully"
                }]
            }
        }]
        session_file = self._create_session_file(entries)

        result = extract_tool_errors(session_file)
        self.assertEqual(result, [])


class TestAggregateToolErrors(unittest.TestCase):
    """Tests for aggregate_tool_errors function."""

    def test_aggregate_empty_list(self):
        """Test aggregation of empty list."""
        result = aggregate_tool_errors([])
        self.assertEqual(result, [])

    def test_aggregate_below_threshold(self):
        """Test that errors below threshold are filtered out."""
        errors = [
            {"error_type": "connection_refused", "content": "error1", "suggested_guideline": "test"},
        ]

        result = aggregate_tool_errors(errors, min_occurrences=2)
        self.assertEqual(result, [])

    def test_aggregate_at_threshold(self):
        """Test that errors at threshold are included."""
        errors = [
            {"error_type": "connection_refused", "content": "error1", "suggested_guideline": "test"},
            {"error_type": "connection_refused", "content": "error2", "suggested_guideline": "test"},
        ]

        result = aggregate_tool_errors(errors, min_occurrences=2)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["error_type"], "connection_refused")
        self.assertEqual(result[0]["count"], 2)

    def test_aggregate_confidence_scaling(self):
        """Test that confidence scales with occurrence count."""
        errors_2 = [{"error_type": "test", "content": f"error{i}", "suggested_guideline": "test"}
                    for i in range(2)]
        errors_3 = [{"error_type": "test", "content": f"error{i}", "suggested_guideline": "test"}
                    for i in range(3)]
        errors_5 = [{"error_type": "test", "content": f"error{i}", "suggested_guideline": "test"}
                    for i in range(5)]

        result_2 = aggregate_tool_errors(errors_2, min_occurrences=2)
        result_3 = aggregate_tool_errors(errors_3, min_occurrences=2)
        result_5 = aggregate_tool_errors(errors_5, min_occurrences=2)

        self.assertEqual(result_2[0]["confidence"], 0.70)
        self.assertEqual(result_3[0]["confidence"], 0.85)
        self.assertEqual(result_5[0]["confidence"], 0.90)

    def test_aggregate_multiple_types(self):
        """Test aggregation of multiple error types."""
        errors = [
            {"error_type": "connection_refused", "content": "err1", "suggested_guideline": "fix1"},
            {"error_type": "connection_refused", "content": "err2", "suggested_guideline": "fix1"},
            {"error_type": "module_not_found", "content": "err3", "suggested_guideline": "fix2"},
            {"error_type": "module_not_found", "content": "err4", "suggested_guideline": "fix2"},
            {"error_type": "module_not_found", "content": "err5", "suggested_guideline": "fix2"},
            {"error_type": "single_error", "content": "err6", "suggested_guideline": "fix3"},
        ]

        result = aggregate_tool_errors(errors, min_occurrences=2)

        self.assertEqual(len(result), 2)
        # Should be sorted by count descending
        self.assertEqual(result[0]["error_type"], "module_not_found")
        self.assertEqual(result[0]["count"], 3)
        self.assertEqual(result[1]["error_type"], "connection_refused")
        self.assertEqual(result[1]["count"], 2)

    def test_aggregate_sample_errors_limit(self):
        """Test that sample_errors is limited to 3 items."""
        errors = [{"error_type": "test", "content": f"error{i}", "suggested_guideline": "test"}
                  for i in range(10)]

        result = aggregate_tool_errors(errors, min_occurrences=2)

        self.assertEqual(len(result), 1)
        self.assertLessEqual(len(result[0]["sample_errors"]), 3)


if __name__ == "__main__":
    unittest.main()
