"""
Tests for deep_eval.llm_judge — LLM-as-Judge via Groq.

Uses AsyncMock/unittest.mock to mock Groq API calls.
No real API calls are made in tests.
"""

import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import pytest
from deep_eval.llm_judge import (
    judge_triggering_quality,
    judge_orchestration_fitness,
    judge_scope_calibration,
    judge_output_quality,
    run_llm_evaluation,
)


# Mock response factory
def _mock_groq_response(content_dict):
    """Create a mock Groq API response."""
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = json.dumps(content_dict)
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    return mock_response


@pytest.fixture
def mock_groq_client():
    """Mock the Groq client to avoid real API calls."""
    with patch("deep_eval.llm_judge._get_groq_client") as mock_get:
        client = MagicMock()
        mock_get.return_value = client
        yield client


class TestJudgeTriggeringQuality:
    def test_returns_none_without_api_key(self):
        """Should return None when Groq is unavailable."""
        with patch("deep_eval.llm_judge._get_groq_client", return_value=None):
            result = judge_triggering_quality("test", "A skill", "body")
            assert result is None

    def test_parses_response(self, mock_groq_client):
        mock_groq_client.chat.completions.create.return_value = _mock_groq_response(
            {
                "score": 85,
                "positive_prompts": ["deploy my app", "check deployment"],
                "negative_prompts": ["write a poem", "calculate taxes"],
                "precision_estimate": 0.9,
                "recall_estimate": 0.8,
                "reasoning": "Good triggering with specific use cases.",
            }
        )

        result = judge_triggering_quality("deploy-checker", "Check deployments", "## Instructions")
        assert result is not None
        assert result["score"] == 85
        assert len(result["positive_prompts"]) == 2

    def test_handles_api_error(self, mock_groq_client):
        mock_groq_client.chat.completions.create.side_effect = Exception("API error")
        result = judge_triggering_quality("test", "A skill", "body")
        assert result is None


class TestJudgeOrchestrationFitness:
    def test_pure_worker_high_score(self, mock_groq_client):
        mock_groq_client.chat.completions.create.return_value = _mock_groq_response(
            {
                "score": 95,
                "worker_signals": ["single focused task", "no delegation"],
                "orchestrator_signals": [],
                "recommendation": "Excellent pure worker.",
            }
        )

        result = judge_orchestration_fitness("linter", "Run eslint", "## Instructions\nRun eslint.")
        assert result["score"] == 95


class TestJudgeScopeCalibration:
    def test_well_scoped(self, mock_groq_client):
        mock_groq_client.chat.completions.create.return_value = _mock_groq_response(
            {
                "score": 80,
                "scope_assessment": "well-scoped",
                "split_recommendations": [],
                "expansion_recommendations": [],
                "reasoning": "Good scope.",
            }
        )

        result = judge_scope_calibration("test", "Test skill", "body", 300, True)
        assert result["scope_assessment"] == "well-scoped"


class TestJudgeOutputQuality:
    def test_simulated_tasks(self, mock_groq_client):
        mock_groq_client.chat.completions.create.return_value = _mock_groq_response(
            {
                "score": 75,
                "simulated_tasks": [
                    {"task": "Deploy to staging", "expected_quality": 80, "issues": []},
                    {"task": "Deploy to prod", "expected_quality": 70, "issues": ["missing rollback"]},
                    {"task": "Check config", "expected_quality": 85, "issues": []},
                ],
                "instruction_clarity": 0.8,
                "completeness": 0.7,
                "reasoning": "Good but missing rollback guidance.",
            }
        )

        result = judge_output_quality("deploy", "Deploy app", "## Instructions")
        assert result["score"] == 75
        assert len(result["simulated_tasks"]) == 3


class TestRunLLMEvaluation:
    def test_no_api_key(self):
        """Should report unavailable when no API key."""
        with patch.dict("os.environ", {}, clear=True):
            result = run_llm_evaluation("test", "A skill", "body")
            assert result["available"] is False

    def test_with_api_key(self, mock_groq_client):
        """Should attempt all 4 evaluations."""
        mock_groq_client.chat.completions.create.return_value = _mock_groq_response(
            {
                "score": 80,
                "positive_prompts": [],
                "negative_prompts": [],
                "precision_estimate": 0.8,
                "recall_estimate": 0.7,
                "reasoning": "Good.",
                "worker_signals": [],
                "orchestrator_signals": [],
                "recommendation": "OK.",
                "scope_assessment": "well-scoped",
                "split_recommendations": [],
                "expansion_recommendations": [],
                "simulated_tasks": [],
                "instruction_clarity": 0.8,
                "completeness": 0.7,
            }
        )

        # Mock both the env var check and the groq import in run_llm_evaluation
        mock_groq_module = MagicMock()
        with patch.dict("os.environ", {"GROQ_API_KEY": "test-key"}):
            with patch.dict("sys.modules", {"groq": mock_groq_module}):
                result = run_llm_evaluation("test", "A skill", "body")
                assert result["available"] is True
                # Should have attempted 4 LLM calls
                assert mock_groq_client.chat.completions.create.call_count == 4
