"""Behavioral and contract tests for the remediated Perplexity operator cohort."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "plugins/saas-packs/perplexity-pack/skills"


def bash_block(skill: str, marker: str) -> str:
    text = (PACK / skill / "SKILL.md").read_text(encoding="utf-8")
    for block in re.findall(r"```bash\n(.*?)\n```", text, flags=re.DOTALL):
        if marker in block:
            return block
    raise AssertionError(f"Bash block containing {marker!r} not found in {skill}")


def fake_curl(directory: Path) -> None:
    script = directory / "curl"
    script.write_text(
        textwrap.dedent(
            """\
            #!/usr/bin/env bash
            set -euo pipefail
            printf '%s\\n' "${MOCK_BODY:?}"
            printf '%s\\n' "${MOCK_STATUS:-200}"
            if [[ "$*" == *"%{time_total}"* ]]; then
              printf '%s\\n' "${MOCK_LATENCY:-0.125}"
            fi
            """
        ),
        encoding="utf-8",
    )
    script.chmod(0o755)


def run_bash(script: str, cwd: Path, **extra_env: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(extra_env)
    env["PATH"] = f"{cwd}{os.pathsep}{env['PATH']}"
    return subprocess.run(
        ["bash", "-c", script],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        timeout=10,
        check=False,
    )


class PerplexityProbeTests(unittest.TestCase):
    safe_body = json.dumps(
        {
            "id": "req-test",
            "model": "sonar",
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {"content": "CUSTOMER_PROMPT_SENTINEL"},
                }
            ],
            "citations": ["https://SECRET_CITATION_SENTINEL.example/path"],
            "usage": {
                "prompt_tokens": 3,
                "completion_tokens": 1,
                "total_tokens": 4,
            },
            "debug": "RAW_RESPONSE_SENTINEL",
        }
    )

    def test_common_error_probe_accepts_valid_200_without_leaking_body(self) -> None:
        script = bash_block("perplexity-common-errors", "Perplexity probe OK")
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            fake_curl(cwd)
            result = run_bash(
                script,
                cwd,
                PERPLEXITY_API_KEY="fixture-key",
                MOCK_BODY=self.safe_body,
                MOCK_STATUS="200",
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "Perplexity probe OK (HTTP 200)\n")
        self.assertNotIn("SENTINEL", result.stdout + result.stderr)

    def test_common_error_probe_fails_closed_for_401_and_429(self) -> None:
        script = bash_block("perplexity-common-errors", "Perplexity probe OK")
        for status in ("401", "429"):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as tmp:
                cwd = Path(tmp)
                fake_curl(cwd)
                result = run_bash(
                    script,
                    cwd,
                    PERPLEXITY_API_KEY="fixture-key",
                    MOCK_BODY='{"error":"RAW_RESPONSE_SENTINEL"}',
                    MOCK_STATUS=status,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn("RAW_RESPONSE_SENTINEL", result.stdout + result.stderr)

    def test_advanced_probe_emits_only_allowlisted_metadata(self) -> None:
        script = bash_block("perplexity-advanced-troubleshooting", "citation_count")
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            fake_curl(cwd)
            result = run_bash(
                script,
                cwd,
                PERPLEXITY_API_KEY="fixture-key",
                MOCK_BODY=self.safe_body,
                MOCK_STATUS="200",
                MOCK_LATENCY="0.125",
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        self.assertEqual(
            set(output),
            {
                "http_status",
                "latency_seconds",
                "model",
                "finish_reason",
                "citation_count",
                "total_tokens",
            },
        )
        self.assertNotIn("SENTINEL", result.stdout + result.stderr)


class PerplexityIncidentEvidenceTests(unittest.TestCase):
    def test_archive_contains_only_allowlisted_summary(self) -> None:
        script = bash_block("perplexity-incident-runbook", "evidence_dir=")
        body = PerplexityProbeTests.safe_body
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            fake_curl(cwd)
            result = run_bash(
                script,
                cwd,
                PERPLEXITY_API_KEY="fixture-key",
                PERPLEXITY_INCIDENT_ID="INC-2026-0042",
                MOCK_BODY=body,
                MOCK_STATUS="200",
                MOCK_LATENCY="0.250",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            archive = cwd / "perplexity-incident-INC-2026-0042.tar.gz"
            self.assertTrue(archive.is_file())
            with tarfile.open(archive, "r:gz") as bundle:
                self.assertEqual(bundle.getnames(), ["summary.json"])
                extracted = bundle.extractfile("summary.json")
                self.assertIsNotNone(extracted)
                summary_bytes = extracted.read()

        summary_text = summary_bytes.decode("utf-8")
        self.assertNotIn("SENTINEL", summary_text)
        summary = json.loads(summary_text)
        self.assertEqual(
            set(summary),
            {
                "schema_version",
                "incident_id",
                "provider",
                "http_status",
                "latency_seconds",
                "model",
                "finish_reason",
                "citation_count",
                "usage",
            },
        )
        self.assertEqual(
            set(summary["usage"]),
            {"prompt_tokens", "completion_tokens", "total_tokens"},
        )


class PerplexityReliabilityContractTests(unittest.TestCase):
    def test_citation_validation_never_fetches_model_supplied_urls(self) -> None:
        text = (PACK / "perplexity-reliability-patterns" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        section = text.split("### Step 5: Citation URL Validation", 1)[1].split(
            "## Error Handling", 1
        )[0]
        self.assertNotIn("fetch(", section)
        self.assertIn('url.protocol !== "https:"', section)
        self.assertIn('host === "localhost"', section)
        self.assertIn("isIP(host)", section)
        self.assertIn("host-not-allowlisted", section)

    def test_stream_timeout_aborts_the_inflight_iterator(self) -> None:
        text = (PACK / "perplexity-reliability-patterns" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        section = text.split("### Step 3: Streaming with Timeout Protection", 1)[1].split(
            "### Step 4:", 1
        )[0]
        self.assertIn("Promise.race", section)
        self.assertIn("controller.abort()", section)
        self.assertIn("iterator.next()", section)


if __name__ == "__main__":
    unittest.main()
