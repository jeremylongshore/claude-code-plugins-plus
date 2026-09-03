"""Behavioral security regressions for the remediated Mistral skills."""

from __future__ import annotations

import json
import os
import re
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MISTRAL_SKILLS = ROOT / "plugins" / "saas-packs" / "mistral-pack" / "skills"
COMMON_ERRORS = MISTRAL_SKILLS / "mistral-common-errors" / "SKILL.md"
INCIDENT_RUNBOOK = MISTRAL_SKILLS / "mistral-incident-runbook" / "SKILL.md"


def bash_block_after(document: Path, heading: str) -> str:
    """Return the first Bash fence after a stable Markdown heading."""

    text = document.read_text(encoding="utf-8")
    start = text.index(heading)
    match = re.search(r"```bash\n(?P<body>.*?)\n```", text[start:], re.DOTALL)
    if match is None:
        raise AssertionError(f"no Bash block found after {heading!r} in {document}")
    return match.group("body")


def write_executable(path: Path, contents: str) -> None:
    path.write_text(contents, encoding="utf-8")
    path.chmod(0o755)


class MistralCommonErrorsProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = bash_block_after(COMMON_ERRORS, "### Step 1: Quick Diagnostic")

    def run_probe(self, status: int, body: dict[str, object]) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            bin_directory = root / "bin"
            bin_directory.mkdir()
            write_executable(
                bin_directory / "curl",
                "#!/bin/sh\n"
                "set -eu\n"
                "printf '%s' \"$MOCK_HTTP_BODY\"\n"
                "printf '\\n%s' \"$MOCK_HTTP_STATUS\"\n",
            )
            environment = os.environ.copy()
            environment.update(
                {
                    "PATH": f"{bin_directory}:{environment['PATH']}",
                    "MISTRAL_API_KEY": "test-only-placeholder",
                    "MOCK_HTTP_STATUS": str(status),
                    "MOCK_HTTP_BODY": json.dumps(body),
                }
            )
            return subprocess.run(
                ["bash", "-c", self.script],
                cwd=root,
                env=environment,
                capture_output=True,
                text=True,
            )

    def test_valid_200_body_is_parsed_without_status_corrupting_json(self) -> None:
        result = self.run_probe(200, {"data": [{"id": "mistral-small-latest"}]})

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "mistral-small-latest")
        self.assertNotIn("HTTP", result.stdout)

    def test_401_and_429_fail_closed_without_echoing_response_body(self) -> None:
        for status, classification in ((401, "authentication failed"), (429, "rate limit reached")):
            with self.subTest(status=status):
                result = self.run_probe(status, {"secret": "RESPONSE_BODY_SENTINEL"})
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(classification, result.stderr)
                self.assertNotIn("RESPONSE_BODY_SENTINEL", result.stdout + result.stderr)


class MistralIncidentEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = bash_block_after(INCIDENT_RUNBOOK, "### Evidence Collection")

    def test_archive_excludes_raw_logs_and_secret_bearing_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            bin_directory = root / "bin"
            bin_directory.mkdir()
            calls = root / "kubectl-calls.txt"
            write_executable(
                bin_directory / "kubectl",
                """#!/bin/sh
set -eu
printf '%s\n' "$*" >> "$MOCK_KUBECTL_CALLS"
if [ "${1:-}" = "logs" ]; then
  printf '%s\n' 'RAW_LOG_SECRET_SENTINEL CUSTOMER_PROMPT_SENTINEL'
  exit 0
fi
cat <<'JSON'
{
  "metadata": {
    "generation": 42,
    "annotations": {"authorization": "SECRET_ANNOTATION_SENTINEL"}
  },
  "spec": {
    "replicas": 3,
    "template": {"spec": {"containers": [{"env": [{"value": "CONTAINER_SECRET_SENTINEL"}]}]}}
  },
  "status": {
    "replicas": 3,
    "updatedReplicas": 3,
    "readyReplicas": 2,
    "availableReplicas": 2,
    "unavailableReplicas": 1,
    "conditions": [
      {"type": "Available", "status": "True", "message": "CUSTOMER_PROMPT_SENTINEL"},
      {"type": "InjectedType", "status": "SECRET_STATUS_SENTINEL"}
    ]
  }
}
JSON
""",
            )
            environment = os.environ.copy()
            environment.update(
                {
                    "PATH": f"{bin_directory}:{environment['PATH']}",
                    "MOCK_KUBECTL_CALLS": str(calls),
                    "TMPDIR": str(root),
                }
            )

            result = subprocess.run(
                ["bash", "-c", self.script],
                cwd=root,
                env=environment,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn("logs", calls.read_text(encoding="utf-8").split())
            archives = list(root.glob("mistral-incident-evidence-*.tar.gz"))
            self.assertEqual(len(archives), 1)
            with tarfile.open(archives[0], "r:gz") as archive:
                self.assertEqual(archive.getnames(), ["deployment-summary.json"])
                extracted = archive.extractfile("deployment-summary.json")
                self.assertIsNotNone(extracted)
                payload_bytes = extracted.read()

            payload_text = payload_bytes.decode("utf-8")
            for forbidden in (
                "RAW_LOG_SECRET_SENTINEL",
                "CUSTOMER_PROMPT_SENTINEL",
                "SECRET_ANNOTATION_SENTINEL",
                "CONTAINER_SECRET_SENTINEL",
                "SECRET_STATUS_SENTINEL",
            ):
                self.assertNotIn(forbidden, payload_text)

            payload = json.loads(payload_text)
            self.assertEqual(
                set(payload),
                {"schema_version", "deployment_generation", "replicas", "rollout_conditions"},
            )
            self.assertEqual(payload["deployment_generation"], 42)
            self.assertEqual(payload["rollout_conditions"], [{"type": "Available", "status": "True"}])


if __name__ == "__main__":
    unittest.main(verbosity=2)
