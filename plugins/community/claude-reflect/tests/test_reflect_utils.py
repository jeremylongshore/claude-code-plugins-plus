#!/usr/bin/env python3
"""Tests for reflect_utils module."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lib.reflect_utils import (
    get_queue_path,
    get_backup_dir,
    get_claude_dir,
    load_queue,
    save_queue,
    append_to_queue,
    iso_timestamp,
    backup_timestamp,
    detect_patterns,
    create_queue_item,
    extract_user_messages,
    extract_tool_rejections,
    find_claude_files,
    suggest_claude_file,
    should_include_message,
    EXCLUDED_DIRS,
    _parse_rule_frontmatter,
    get_project_folder_name,
)


class TestPathUtilities(unittest.TestCase):
    """Tests for path utility functions."""

    def test_get_queue_path(self):
        """Test queue path returns correct per-project location."""
        path = get_queue_path()
        self.assertIsInstance(path, Path)
        self.assertEqual(path.name, "learnings-queue.json")
        # Queue is now per-project: ~/.claude/projects/<encoded>/learnings-queue.json
        self.assertIn("projects", path.parts)

    def test_get_queue_path_explicit_project(self):
        """Test queue path with explicit project directory."""
        path = get_queue_path("/tmp/test-project")
        self.assertIsInstance(path, Path)
        self.assertEqual(path.name, "learnings-queue.json")
        self.assertIn("projects", path.parts)
        self.assertIn("-tmp-test-project", str(path))

    def test_get_global_queue_path(self):
        """Test legacy global queue path."""
        from lib.reflect_utils import get_global_queue_path
        path = get_global_queue_path()
        self.assertIsInstance(path, Path)
        self.assertEqual(path.name, "learnings-queue.json")
        self.assertEqual(path.parent.name, ".claude")

    def test_get_backup_dir(self):
        """Test backup dir returns correct location."""
        path = get_backup_dir()
        self.assertIsInstance(path, Path)
        self.assertEqual(path.name, "learnings-backups")
        self.assertEqual(path.parent.name, ".claude")

    def test_get_claude_dir(self):
        """Test claude dir returns correct location."""
        path = get_claude_dir()
        self.assertIsInstance(path, Path)
        self.assertEqual(path.name, ".claude")


class TestQueueOperations(unittest.TestCase):
    """Tests for queue operations."""

    def setUp(self):
        """Create temporary directory for tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_queue_path = Path(self.temp_dir) / "learnings-queue.json"

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("lib.reflect_utils.get_queue_path")
    def test_load_queue_empty_file(self, mock_path):
        """Test loading empty queue."""
        mock_path.return_value = self.test_queue_path
        result = load_queue()
        self.assertEqual(result, [])

    @patch("lib.reflect_utils.get_queue_path")
    def test_load_queue_with_items(self, mock_path):
        """Test loading queue with items."""
        mock_path.return_value = self.test_queue_path
        test_items = [{"type": "auto", "message": "test"}]
        self.test_queue_path.write_text(json.dumps(test_items))

        result = load_queue()
        self.assertEqual(result, test_items)

    @patch("lib.reflect_utils.get_queue_path")
    def test_save_queue(self, mock_path):
        """Test saving queue."""
        mock_path.return_value = self.test_queue_path
        test_items = [{"type": "auto", "message": "test"}]

        save_queue(test_items)

        saved_data = json.loads(self.test_queue_path.read_text())
        self.assertEqual(saved_data, test_items)

    @patch("lib.reflect_utils.get_queue_path")
    def test_append_to_queue(self, mock_path):
        """Test appending to queue."""
        mock_path.return_value = self.test_queue_path
        self.test_queue_path.write_text("[]")

        item = {"type": "auto", "message": "new item"}
        append_to_queue(item)

        saved_data = json.loads(self.test_queue_path.read_text())
        self.assertEqual(len(saved_data), 1)
        self.assertEqual(saved_data[0]["message"], "new item")


class TestTimestampUtilities(unittest.TestCase):
    """Tests for timestamp functions."""

    def test_iso_timestamp_format(self):
        """Test ISO timestamp has correct format."""
        ts = iso_timestamp()
        # Should match YYYY-MM-DDTHH:MM:SSZ format
        self.assertRegex(ts, r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

    def test_backup_timestamp_format(self):
        """Test backup timestamp has correct format."""
        ts = backup_timestamp()
        # Should match YYYYMMDD-HHMMSS format
        self.assertRegex(ts, r"^\d{8}-\d{6}$")


class TestPatternDetection(unittest.TestCase):
    """Tests for pattern detection."""

    def test_explicit_remember_pattern(self):
        """Test detection of explicit remember: marker."""
        result = detect_patterns("remember: always use gpt-5.1")
        item_type, patterns, confidence, sentiment, decay = result

        self.assertEqual(item_type, "explicit")
        self.assertIn("remember:", patterns)
        self.assertEqual(confidence, 0.90)
        self.assertEqual(decay, 120)

    def test_positive_pattern_perfect(self):
        """Test detection of positive feedback."""
        result = detect_patterns("perfect! that's exactly what I wanted")
        item_type, patterns, confidence, sentiment, decay = result

        self.assertEqual(item_type, "positive")
        self.assertEqual(sentiment, "positive")
        self.assertGreaterEqual(confidence, 0.70)

    def test_correction_no_use(self):
        """Test detection of 'no, use' correction."""
        result = detect_patterns("no, use Python instead")
        item_type, patterns, confidence, sentiment, decay = result

        self.assertEqual(item_type, "auto")
        self.assertIn("no,", patterns)
        self.assertEqual(sentiment, "correction")

    def test_correction_dont_use(self):
        """Test detection of 'don't use' correction."""
        result = detect_patterns("don't use that library")
        item_type, patterns, confidence, sentiment, decay = result

        self.assertEqual(item_type, "auto")
        self.assertIn("don't", patterns)

    def test_correction_stop_using(self):
        """Test detection of 'stop using' correction."""
        result = detect_patterns("stop using that approach")
        item_type, patterns, confidence, sentiment, decay = result

        self.assertEqual(item_type, "auto")
        self.assertIn("stop/never", patterns)

    def test_correction_never_use(self):
        """Test detection of 'never use' correction."""
        result = detect_patterns("never use global variables")
        item_type, patterns, confidence, sentiment, decay = result

        self.assertEqual(item_type, "auto")
        self.assertIn("stop/never", patterns)

    def test_correction_thats_wrong(self):
        """Test detection of 'that's wrong' correction."""
        result = detect_patterns("that's wrong, the API returns JSON")
        item_type, patterns, confidence, sentiment, decay = result

        self.assertEqual(item_type, "auto")
        self.assertIn("that's-wrong", patterns)

    def test_correction_i_told_you_high_confidence(self):
        """Test that 'I told you' gets high confidence."""
        result = detect_patterns("I told you to use async")
        item_type, patterns, confidence, sentiment, decay = result

        self.assertEqual(item_type, "auto")
        self.assertIn("I-told-you", patterns)
        # Base 0.85 + 0.10 short message boost = 0.90 (capped)
        self.assertGreaterEqual(confidence, 0.85)
        self.assertEqual(decay, 120)

    def test_multiple_patterns_high_confidence(self):
        """Test multiple patterns increase confidence."""
        result = detect_patterns("no, don't use that, you should use Python")
        item_type, patterns, confidence, sentiment, decay = result

        self.assertEqual(item_type, "auto")
        self.assertGreaterEqual(confidence, 0.75)

    def test_guardrail_dont_add_unless(self):
        """Test detection of 'don't add X unless' guardrail pattern."""
        result = detect_patterns("don't add docstrings unless I explicitly ask")
        item_type, patterns, confidence, sentiment, decay = result

        self.assertEqual(item_type, "guardrail")
        self.assertIn("dont-unless-asked", patterns)
        self.assertGreaterEqual(confidence, 0.90)
        self.assertEqual(decay, 120)

    def test_guardrail_only_change_what_asked(self):
        """Test detection of 'only change what I asked' guardrail pattern."""
        result = detect_patterns("only change what I asked you to change")
        item_type, patterns, confidence, sentiment, decay = result

        self.assertEqual(item_type, "guardrail")
        self.assertIn("only-what-asked", patterns)
        self.assertGreaterEqual(confidence, 0.90)

    def test_guardrail_stop_refactoring(self):
        """Test detection of 'stop refactoring unrelated' guardrail pattern."""
        result = detect_patterns("stop refactoring unrelated code")
        item_type, patterns, confidence, sentiment, decay = result

        self.assertEqual(item_type, "guardrail")
        self.assertIn("stop-unrelated", patterns)

    def test_guardrail_dont_over_engineer(self):
        """Test detection of 'don't over-engineer' guardrail pattern."""
        result = detect_patterns("don't over-engineer this solution")
        item_type, patterns, confidence, sentiment, decay = result

        self.assertEqual(item_type, "guardrail")
        self.assertIn("dont-over-engineer", patterns)

    def test_guardrail_leave_alone(self):
        """Test detection of 'leave X alone' guardrail pattern."""
        result = detect_patterns("leave the existing code alone")
        item_type, patterns, confidence, sentiment, decay = result

        self.assertEqual(item_type, "guardrail")
        self.assertIn("leave-alone", patterns)

    def test_guardrail_minimal_changes(self):
        """Test detection of 'minimal changes' guardrail pattern."""
        result = detect_patterns("only make minimal changes please")
        item_type, patterns, confidence, sentiment, decay = result

        self.assertEqual(item_type, "guardrail")
        self.assertIn("minimal-changes", patterns)

    def test_no_pattern_match(self):
        """Test text without patterns returns None type."""
        result = detect_patterns("Hello, how are you?")
        item_type, patterns, confidence, sentiment, decay = result

        self.assertIsNone(item_type)
        self.assertEqual(patterns, "")

    def test_false_positive_question_rejected(self):
        """Test that questions (ending with ?) are rejected."""
        result = detect_patterns("can you figure out how to make this fit?")
        item_type, patterns, confidence, sentiment, decay = result

        self.assertIsNone(item_type)

    def test_false_positive_task_request_rejected(self):
        """Test that task requests are rejected."""
        result = detect_patterns("please help me fix this issue")
        item_type, patterns, confidence, sentiment, decay = result

        self.assertIsNone(item_type)

    def test_false_positive_error_description_rejected(self):
        """Test that error descriptions are rejected."""
        result = detect_patterns("the error is: could not connect to database")
        item_type, patterns, confidence, sentiment, decay = result

        self.assertIsNone(item_type)

    def test_false_positive_bug_report_rejected(self):
        """Test that bug reports are rejected."""
        result = detect_patterns("it just opens and closes, is not working")
        item_type, patterns, confidence, sentiment, decay = result

        self.assertIsNone(item_type)

    def test_short_message_confidence_boost(self):
        """Test that short messages get a confidence boost."""
        result = detect_patterns("no, use gpt-5.1")
        item_type, patterns, confidence, sentiment, decay = result

        self.assertEqual(item_type, "auto")
        self.assertGreaterEqual(confidence, 0.75)  # Boosted for short message

    def test_long_message_confidence_reduced(self):
        """Test that long messages get reduced confidence."""
        long_msg = "no, " + "this is a very long explanation " * 15
        result = detect_patterns(long_msg)
        item_type, patterns, confidence, sentiment, decay = result

        # Should still match but with lower confidence
        if item_type == "auto":
            self.assertLessEqual(confidence, 0.65)


class TestCJKPatternDetection(unittest.TestCase):
    """Tests for CJK (Chinese, Japanese, Korean) pattern detection."""

    # --- Short message rejection ---

    def test_short_message_rejected(self):
        """Test that very short messages are rejected as non-actionable."""
        result = detect_patterns("OK")
        self.assertIsNone(result[0])

    def test_short_cjk_message_rejected(self):
        """Test that very short CJK messages (<=2 chars) are rejected."""
        result = detect_patterns("好")
        self.assertIsNone(result[0])

        result = detect_patterns("うん")
        self.assertIsNone(result[0])

    def test_short_cjk_correction_not_rejected(self):
        """Test that short but meaningful CJK corrections are NOT rejected."""
        result = detect_patterns("やめて")
        self.assertEqual(result[0], "auto")

    # --- Full-width question mark ---

    def test_fullwidth_question_mark_rejected(self):
        """Test that full-width question marks are treated as questions."""
        result = detect_patterns("何ですか？")
        self.assertIsNone(result[0])

        result = detect_patterns("這是什麼？")
        self.assertIsNone(result[0])

    # --- CJK question particles ---

    def test_cjk_question_particle_ja(self):
        """Test Japanese question particle か."""
        result = detect_patterns("何ですか")
        self.assertIsNone(result[0])

    def test_cjk_question_particle_zh(self):
        """Test Chinese question particles 嗎/呢."""
        result = detect_patterns("這是什麼嗎")
        self.assertIsNone(result[0])

        result = detect_patterns("你在做什麼呢")
        self.assertIsNone(result[0])

    def test_cjk_question_particle_ko(self):
        """Test Korean question particle 까."""
        result = detect_patterns("이것은 뭐입니까")
        self.assertIsNone(result[0])

    # --- Non-correction English phrases ---

    def test_no_problem_not_correction(self):
        """Test 'No problem' in mixed CJK-English text is not a correction."""
        result = detect_patterns("No problem, 次に進もう")
        self.assertIsNone(result[0])

    def test_dont_worry_not_correction(self):
        """Test 'don't worry' in mixed text is not a correction."""
        result = detect_patterns("don't worry、大丈夫")
        self.assertIsNone(result[0])

    def test_no_worries_not_correction(self):
        """Test 'No worries' is not a correction."""
        result = detect_patterns("No worries, それでOK")
        self.assertIsNone(result[0])

    def test_never_mind_not_correction(self):
        """Test 'Never mind' is not a correction."""
        result = detect_patterns("Never mind、別の方法でやろう")
        self.assertIsNone(result[0])

    # --- Japanese correction patterns ---

    def test_ja_iya_correction(self):
        """Test Japanese いや、(no,) correction pattern."""
        result = detect_patterns("いや、そっちじゃなくてこっちを修正して")
        self.assertEqual(result[0], "auto")
        self.assertIn("iya", result[1])

    def test_ja_chigau_correction(self):
        """Test Japanese 違う、(wrong,) correction pattern."""
        result = detect_patterns("違う、useStateじゃなくてuseRefを使って")
        self.assertEqual(result[0], "auto")
        self.assertIn("chigau", result[1])

    def test_ja_machigatteru_correction(self):
        """Test Japanese 間違ってる (it's wrong) correction pattern."""
        result = detect_patterns("それ間違ってる、型が違う")
        self.assertEqual(result[0], "auto")
        self.assertIn("machigatte", result[1])

    def test_ja_souja_nakute_correction(self):
        """Test Japanese そうじゃなくて (not that) correction pattern."""
        result = detect_patterns("そうじゃなくて別のファイルを見て")
        self.assertEqual(result[0], "auto")
        self.assertIn("souja-nakute", result[1])

    def test_ja_janakute_nishite_correction(self):
        """Test Japanese じゃなくて〜にして (use X not Y) correction pattern."""
        result = detect_patterns("mapじゃなくてforEachにして")
        self.assertEqual(result[0], "auto")
        self.assertIn("janakute-nishite", result[1])

    def test_ja_souja_nai_correction(self):
        """Test Japanese そうじゃない (that's not right) correction pattern."""
        result = detect_patterns("そうじゃない、もう一度考えて")
        self.assertEqual(result[0], "auto")
        self.assertIn("souja-nai", result[1])

    def test_ja_tte_itta_correction(self):
        """Test Japanese って言ったのに (I told you) correction pattern."""
        result = detect_patterns("TypeScriptにしてって言ったのに")
        self.assertEqual(result[0], "auto")
        self.assertIn("tte-itta", result[1])

    # --- Chinese correction patterns ---

    def test_zh_bushi_correction(self):
        """Test Chinese 不是 (no) correction pattern."""
        result = detect_patterns("不是，应该用另一个方法")
        self.assertEqual(result[0], "auto")
        self.assertIn("bushi", result[1])

    def test_zh_cuole_correction(self):
        """Test Chinese 错了 (wrong) correction pattern."""
        result = detect_patterns("错了，这个逻辑有问题")
        self.assertEqual(result[0], "auto")
        self.assertIn("cuole", result[1])

    # --- Korean correction patterns ---

    def test_ko_ani_correction(self):
        """Test Korean 아니 (no) correction pattern."""
        result = detect_patterns("아니, 그게 아니라 이거를 수정해")
        self.assertEqual(result[0], "auto")
        self.assertIn("ani", result[1])

    # --- English patterns still work ---

    def test_english_patterns_unchanged(self):
        """Ensure existing English patterns are not broken."""
        # Corrections
        result = detect_patterns("No, use TypeScript not JavaScript")
        self.assertEqual(result[0], "auto")

        result = detect_patterns("actually, use the other method")
        self.assertEqual(result[0], "auto")

        result = detect_patterns("I told you to use npm")
        self.assertEqual(result[0], "auto")

        # Non-corrections
        result = detect_patterns("how do I install this?")
        self.assertIsNone(result[0])

        result = detect_patterns("please fix this bug")
        self.assertIsNone(result[0])

        # Explicit
        result = detect_patterns("remember: always use bun")
        self.assertEqual(result[0], "explicit")

        # Guardrail
        result = detect_patterns("don't add comments unless I ask")
        self.assertEqual(result[0], "guardrail")


class TestQueueItemCreation(unittest.TestCase):
    """Tests for queue item creation."""

    def test_create_queue_item_all_fields(self):
        """Test queue item has all required fields."""
        item = create_queue_item(
            message="test message",
            item_type="auto",
            patterns="no,use",
            confidence=0.75,
            sentiment="correction",
            decay_days=90,
            project="/test/project",
        )

        self.assertEqual(item["message"], "test message")
        self.assertEqual(item["type"], "auto")
        self.assertEqual(item["patterns"], "no,use")
        self.assertEqual(item["confidence"], 0.75)
        self.assertEqual(item["sentiment"], "correction")
        self.assertEqual(item["decay_days"], 90)
        self.assertEqual(item["project"], "/test/project")
        self.assertIn("timestamp", item)


class TestSessionExtraction(unittest.TestCase):
    """Tests for session file extraction."""

    def setUp(self):
        """Create temporary session file."""
        self.temp_dir = tempfile.mkdtemp()
        self.session_file = Path(self.temp_dir) / "test-session.jsonl"

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_extract_user_messages_basic(self):
        """Test extracting basic user messages."""
        session_data = [
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
            {
                "type": "user",
                "message": {
                    "content": [{"type": "text", "text": "no, use Python instead"}]
                }
            },
        ]

        with open(self.session_file, "w") as f:
            for entry in session_data:
                f.write(json.dumps(entry) + "\n")

        messages = extract_user_messages(self.session_file)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0], "Hello world")
        self.assertEqual(messages[1], "no, use Python instead")

    def test_extract_user_messages_string_content(self):
        """Test extracting user messages when content is a string (not list)."""
        session_data = [
            {
                "type": "user",
                "message": {
                    "content": "This is a string content message"
                }
            },
            {
                "type": "user",
                "message": {
                    "content": "no, use this approach instead"
                }
            },
        ]

        with open(self.session_file, "w") as f:
            for entry in session_data:
                f.write(json.dumps(entry) + "\n")

        messages = extract_user_messages(self.session_file)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0], "This is a string content message")
        self.assertEqual(messages[1], "no, use this approach instead")

    def test_extract_user_messages_skip_meta(self):
        """Test that isMeta messages are skipped."""
        session_data = [
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
        ]

        with open(self.session_file, "w") as f:
            for entry in session_data:
                f.write(json.dumps(entry) + "\n")

        messages = extract_user_messages(self.session_file)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0], "Regular message")

    def test_extract_corrections_only(self):
        """Test extracting only correction messages."""
        session_data = [
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
            {
                "type": "user",
                "message": {
                    "content": [{"type": "text", "text": "remember: always test"}]
                }
            },
        ]

        with open(self.session_file, "w") as f:
            for entry in session_data:
                f.write(json.dumps(entry) + "\n")

        messages = extract_user_messages(self.session_file, corrections_only=True)
        self.assertEqual(len(messages), 2)
        self.assertIn("no, use Python", messages)
        self.assertIn("remember: always test", messages)

    def test_extract_nonexistent_file(self):
        """Test extracting from nonexistent file returns empty list."""
        messages = extract_user_messages(Path("/nonexistent/file.jsonl"))
        self.assertEqual(messages, [])


class TestToolRejectionExtraction(unittest.TestCase):
    """Tests for tool rejection extraction."""

    def setUp(self):
        """Create temporary session file."""
        self.temp_dir = tempfile.mkdtemp()
        self.session_file = Path(self.temp_dir) / "test-session.jsonl"

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_extract_tool_rejection_with_feedback(self):
        """Test extracting tool rejection with user feedback."""
        # Schema matches actual Claude Code session files:
        # type=user, message.content[].type=tool_result, is_error=true
        session_data = [
            {
                "type": "user",
                "message": {
                    "content": [
                        {
                            "type": "tool_result",
                            "is_error": True,
                            "content": "The user doesn't want to proceed\nthe user said:\nDon't delete that file"
                        }
                    ]
                }
            },
        ]

        with open(self.session_file, "w") as f:
            for entry in session_data:
                f.write(json.dumps(entry) + "\n")

        rejections = extract_tool_rejections(self.session_file)
        self.assertEqual(len(rejections), 1)
        self.assertEqual(rejections[0], "Don't delete that file")

    def test_extract_tool_rejection_empty_feedback(self):
        """Test that empty feedback is skipped."""
        session_data = [
            {
                "type": "user",
                "message": {
                    "content": [
                        {
                            "type": "tool_result",
                            "is_error": True,
                            "content": "The user doesn't want to proceed\nthe user said:\n"
                        }
                    ]
                }
            },
        ]

        with open(self.session_file, "w") as f:
            for entry in session_data:
                f.write(json.dumps(entry) + "\n")

        rejections = extract_tool_rejections(self.session_file)
        self.assertEqual(len(rejections), 0)

    def test_extract_non_rejection_tool_result(self):
        """Test that normal tool results are ignored."""
        session_data = [
            {
                "type": "user",
                "message": {
                    "content": [
                        {
                            "type": "tool_result",
                            "is_error": False,
                            "content": "File created successfully"
                        }
                    ]
                }
            },
        ]

        with open(self.session_file, "w") as f:
            for entry in session_data:
                f.write(json.dumps(entry) + "\n")

        rejections = extract_tool_rejections(self.session_file)
        self.assertEqual(len(rejections), 0)


class TestClaudeFileDiscovery(unittest.TestCase):
    """Tests for CLAUDE.md file discovery."""

    def setUp(self):
        """Create temporary directory structure."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()

    def tearDown(self):
        """Clean up temporary files and restore cwd."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_find_claude_files_root_only(self):
        """Test finding CLAUDE.md in root directory only."""
        # Create root CLAUDE.md
        root_claude = Path(self.temp_dir) / "CLAUDE.md"
        root_claude.write_text("# Test CLAUDE.md")

        files = find_claude_files(self.temp_dir)

        # Should find global and root (if global exists)
        root_files = [f for f in files if f["type"] == "root"]
        self.assertEqual(len(root_files), 1)
        self.assertEqual(root_files[0]["relative_path"], "./CLAUDE.md")

    def test_find_claude_files_subdirectory(self):
        """Test finding CLAUDE.md in subdirectories."""
        # Create root CLAUDE.md
        root_claude = Path(self.temp_dir) / "CLAUDE.md"
        root_claude.write_text("# Root")

        # Create subdirectory CLAUDE.md
        subdir = Path(self.temp_dir) / "src"
        subdir.mkdir()
        sub_claude = subdir / "CLAUDE.md"
        sub_claude.write_text("# Src")

        files = find_claude_files(self.temp_dir)

        subdir_files = [f for f in files if f["type"] == "subdirectory"]
        self.assertEqual(len(subdir_files), 1)
        self.assertIn("src/CLAUDE.md", subdir_files[0]["relative_path"])

    def test_find_claude_files_excludes_node_modules(self):
        """Test that node_modules is excluded from search."""
        # Create CLAUDE.md in node_modules (should be excluded)
        node_modules = Path(self.temp_dir) / "node_modules"
        node_modules.mkdir()
        excluded_claude = node_modules / "CLAUDE.md"
        excluded_claude.write_text("# Should be excluded")

        files = find_claude_files(self.temp_dir)

        # Should not find the node_modules CLAUDE.md
        all_paths = [f["path"] for f in files]
        self.assertFalse(any("node_modules" in p for p in all_paths))

    def test_find_claude_files_excludes_git(self):
        """Test that .git is excluded from search."""
        # Create CLAUDE.md in .git (should be excluded)
        git_dir = Path(self.temp_dir) / ".git"
        git_dir.mkdir()
        excluded_claude = git_dir / "CLAUDE.md"
        excluded_claude.write_text("# Should be excluded")

        files = find_claude_files(self.temp_dir)

        # Should not find the .git CLAUDE.md
        all_paths = [f["path"] for f in files]
        self.assertFalse(any(".git" in p for p in all_paths))

    def test_excluded_dirs_constant(self):
        """Test that EXCLUDED_DIRS contains expected directories."""
        self.assertIn("node_modules", EXCLUDED_DIRS)
        self.assertIn(".git", EXCLUDED_DIRS)
        self.assertIn("venv", EXCLUDED_DIRS)
        self.assertIn("__pycache__", EXCLUDED_DIRS)


class TestSuggestClaudeFile(unittest.TestCase):
    """Tests for suggest_claude_file function."""

    def test_suggest_global_for_model_names(self):
        """Test that model names suggest global CLAUDE.md."""
        files = [
            {"path": "/home/.claude/CLAUDE.md", "relative_path": "~/.claude/CLAUDE.md", "type": "global"},
            {"path": "/project/CLAUDE.md", "relative_path": "./CLAUDE.md", "type": "root"},
        ]

        result = suggest_claude_file("Use gpt-5.1 for reasoning tasks", files)
        self.assertEqual(result, "~/.claude/CLAUDE.md")

        result = suggest_claude_file("claude-opus is better for coding", files)
        self.assertEqual(result, "~/.claude/CLAUDE.md")

    def test_suggest_global_for_always_never(self):
        """Test that 'always/never' patterns suggest global."""
        files = [
            {"path": "/home/.claude/CLAUDE.md", "relative_path": "~/.claude/CLAUDE.md", "type": "global"},
            {"path": "/project/CLAUDE.md", "relative_path": "./CLAUDE.md", "type": "root"},
        ]

        result = suggest_claude_file("always run tests before committing", files)
        self.assertEqual(result, "~/.claude/CLAUDE.md")

        result = suggest_claude_file("never use force push on main", files)
        self.assertEqual(result, "~/.claude/CLAUDE.md")

    def test_suggest_subdirectory_when_mentioned(self):
        """Test suggestion based on directory name in learning."""
        files = [
            {"path": "/home/.claude/CLAUDE.md", "relative_path": "~/.claude/CLAUDE.md", "type": "global"},
            {"path": "/project/CLAUDE.md", "relative_path": "./CLAUDE.md", "type": "root"},
            {"path": "/project/api/CLAUDE.md", "relative_path": "./api/CLAUDE.md", "type": "subdirectory"},
        ]

        result = suggest_claude_file("The api module uses REST conventions", files)
        self.assertEqual(result, "./api/CLAUDE.md")

    def test_suggest_none_for_ambiguous(self):
        """Test that ambiguous learnings return None (let Claude decide)."""
        files = [
            {"path": "/home/.claude/CLAUDE.md", "relative_path": "~/.claude/CLAUDE.md", "type": "global"},
            {"path": "/project/CLAUDE.md", "relative_path": "./CLAUDE.md", "type": "root"},
        ]

        result = suggest_claude_file("Use database connection pooling", files)
        self.assertIsNone(result)


class TestShouldIncludeMessage(unittest.TestCase):
    """Tests for should_include_message() — filters system content from user prompts."""

    def test_normal_user_message_included(self):
        """Normal user text should be included."""
        self.assertTrue(should_include_message("no, use gpt-5.1 not gpt-5"))

    def test_normal_correction_included(self):
        """Corrections should be included."""
        self.assertTrue(should_include_message("don't use sqlite, use postgres"))

    def test_remember_marker_included(self):
        """Explicit remember: markers should be included."""
        self.assertTrue(should_include_message("remember: always use venv"))

    def test_empty_string_excluded(self):
        """Empty strings should be excluded."""
        self.assertFalse(should_include_message(""))
        self.assertFalse(should_include_message("   "))

    def test_xml_tag_excluded(self):
        """Messages starting with XML tags should be excluded."""
        self.assertFalse(should_include_message("<task-notification>some content</task-notification>"))
        self.assertFalse(should_include_message("<system-reminder>use X not Y</system-reminder>"))

    def test_json_excluded(self):
        """Messages starting with JSON should be excluded."""
        self.assertFalse(should_include_message('{"prompt": "no, use X"}'))

    def test_tool_result_excluded(self):
        """Messages containing tool_result should be excluded."""
        self.assertFalse(should_include_message("tool_result content here"))

    def test_session_continuation_excluded(self):
        """Session continuation markers should be excluded."""
        self.assertFalse(should_include_message(
            "This session is being continued from a previous conversation"
        ))

    def test_system_reminder_with_correction_pattern(self):
        """System reminders containing correction-like text should still be excluded."""
        msg = '<system-reminder>use context7 mcp every time, don\'t use old API</system-reminder>'
        self.assertFalse(should_include_message(msg))

    def test_task_notification_with_correction_pattern(self):
        """Task notifications with correction patterns should be excluded."""
        msg = (
            '<task-notification>Skill "superpowers:using-superpowers" '
            'loaded. Don\'t use deprecated patterns.</task-notification>'
        )
        self.assertFalse(should_include_message(msg))

    def test_bracket_start_excluded(self):
        """Messages starting with brackets should be excluded."""
        self.assertFalse(should_include_message("[tool_use_id: abc123]"))

    def test_analysis_start_excluded(self):
        """Messages starting with 'Analysis:' should be excluded."""
        self.assertFalse(should_include_message("Analysis: the code uses X not Y"))

    def test_bold_text_excluded(self):
        """Messages starting with bold markdown should be excluded."""
        self.assertFalse(should_include_message("**Note:** don't use this pattern"))


class TestClaudeFileDiscoveryBackwardCompat(unittest.TestCase):
    """Backward-compatibility tests: new find_claude_files() still returns old types."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_old_types_still_returned(self):
        """Existing callers expecting 'root', 'subdirectory', 'global' still work."""
        root_claude = Path(self.temp_dir) / "CLAUDE.md"
        root_claude.write_text("# Root")
        sub = Path(self.temp_dir) / "src"
        sub.mkdir()
        (sub / "CLAUDE.md").write_text("# Src")

        files = find_claude_files(self.temp_dir)
        types = [f["type"] for f in files]
        self.assertIn("root", types)
        self.assertIn("subdirectory", types)

    def test_no_frontmatter_field_on_old_types(self):
        """Old types (root, subdirectory, global) don't have frontmatter field."""
        root_claude = Path(self.temp_dir) / "CLAUDE.md"
        root_claude.write_text("# Root")

        files = find_claude_files(self.temp_dir)
        root_files = [f for f in files if f["type"] == "root"]
        self.assertEqual(len(root_files), 1)
        self.assertNotIn("frontmatter", root_files[0])


class TestSuggestClaudeFileBackwardCompat(unittest.TestCase):
    """Backward-compatibility: suggest_claude_file() without learning_type."""

    def test_works_without_learning_type(self):
        """Calling without learning_type still works (default None)."""
        files = [
            {"path": "/home/.claude/CLAUDE.md", "relative_path": "~/.claude/CLAUDE.md", "type": "global"},
            {"path": "/project/CLAUDE.md", "relative_path": "./CLAUDE.md", "type": "root"},
        ]
        # Should work exactly as before
        result = suggest_claude_file("use gpt-5.1 for reasoning", files)
        self.assertEqual(result, "~/.claude/CLAUDE.md")

        result = suggest_claude_file("something ambiguous", files)
        self.assertIsNone(result)

    def test_two_arg_call_still_works(self):
        """Positional two-arg call (old API) still works."""
        files = [
            {"path": "/home/.claude/CLAUDE.md", "relative_path": "~/.claude/CLAUDE.md", "type": "global"},
        ]
        result = suggest_claude_file("always use venv", files)
        self.assertEqual(result, "~/.claude/CLAUDE.md")


class TestCaptureLearningFiltering(unittest.TestCase):
    """Integration tests for capture_learning.py filtering logic.

    These tests verify that the two-layer filter (should_include_message +
    MAX_CAPTURE_PROMPT_LENGTH) correctly blocks false positives from system
    content while allowing real user corrections through.
    """

    def test_system_content_blocked_before_detect_patterns(self):
        """System content should be filtered BEFORE reaching detect_patterns."""
        # This is the key false-positive scenario: system-reminder contains
        # correction-like text ("use X not Y") but should never be captured.
        system_msg = '<system-reminder>use context7 mcp every time</system-reminder>'
        self.assertFalse(should_include_message(system_msg))

        # In contrast, a real user correction should pass the filter
        real_correction = "no, use gpt-5.1 not gpt-5"
        self.assertTrue(should_include_message(real_correction))

    def test_long_prompt_blocked(self):
        """Prompts longer than MAX_CAPTURE_PROMPT_LENGTH should be blocked."""
        from lib.reflect_utils import MAX_CAPTURE_PROMPT_LENGTH

        long_prompt = "a" * (MAX_CAPTURE_PROMPT_LENGTH + 1)
        # Simulates the check in capture_learning.py
        should_skip = len(long_prompt) > MAX_CAPTURE_PROMPT_LENGTH and "remember:" not in long_prompt.lower()
        self.assertTrue(should_skip)

    def test_long_prompt_with_remember_allowed(self):
        """Long prompts with 'remember:' should still be processed."""
        from lib.reflect_utils import MAX_CAPTURE_PROMPT_LENGTH

        long_remember = "remember: " + "a" * MAX_CAPTURE_PROMPT_LENGTH
        should_skip = len(long_remember) > MAX_CAPTURE_PROMPT_LENGTH and "remember:" not in long_remember.lower()
        self.assertFalse(should_skip)

    def test_short_real_correction_passes_both_filters(self):
        """A real, short user correction should pass both filters."""
        from lib.reflect_utils import MAX_CAPTURE_PROMPT_LENGTH

        msg = "no, use postgres not sqlite"
        self.assertTrue(should_include_message(msg))
        self.assertLessEqual(len(msg), MAX_CAPTURE_PROMPT_LENGTH)

    def test_task_notification_false_positive(self):
        """Reproduce the exact false positive: task-notification with 'use' pattern."""
        msg = (
            '<task-notification>Skill "superpowers:using-superpowers" '
            "has been loaded and added to the conversation. "
            "Use the skill in your next response.</task-notification>"
        )
        # This must be filtered out — it's system content, not a user correction
        self.assertFalse(should_include_message(msg))

    def test_session_continuation_false_positive(self):
        """Reproduce false positive: session continuation with correction patterns."""
        msg = (
            "This session is being continued from a previous conversation. "
            "Don't use the old API, use the new one instead."
        )
        self.assertFalse(should_include_message(msg))


if __name__ == "__main__":
    unittest.main()
