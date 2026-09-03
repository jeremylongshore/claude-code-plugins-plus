"""Behavioral and contract tests for the remediated Replit operator cohort."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "plugins/saas-packs/replit-pack/skills"
COHORT = (
    "replit-known-pitfalls",
    "replit-common-errors",
    "replit-reference-architecture",
    "replit-incident-runbook",
    "replit-prod-checklist",
)


def skill_text(skill: str) -> str:
    return (PACK / skill / "SKILL.md").read_text(encoding="utf-8")


def bash_block(skill: str, marker: str) -> str:
    for block in re.findall(r"```bash\n(.*?)\n```", skill_text(skill), flags=re.DOTALL):
        if marker in block:
            return block
    raise AssertionError(f"Bash block containing {marker!r} not found in {skill}")


def typescript_block(skill: str, marker: str) -> str:
    for block in re.findall(r"```typescript\n(.*?)\n```", skill_text(skill), flags=re.DOTALL):
        if marker in block:
            return block
    raise AssertionError(f"TypeScript block containing {marker!r} not found in {skill}")


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


def run_typescript(script: str) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmp:
        fixture = Path(tmp) / "fixture.ts"
        fixture.write_text(script, encoding="utf-8")
        compiler_path = Path(
            os.environ.get(
                "REPLIT_TEST_TYPESCRIPT_COMPILER",
                ROOT / "node_modules/typescript/lib/typescript.js",
            )
        )
        if compiler_path.is_file():
            runner = textwrap.dedent(
                f"""
                const fs = require("node:fs");
                const ts = require({json.dumps(str(compiler_path))});
                const source = fs.readFileSync(process.argv[1], "utf8");
                const result = ts.transpileModule(source, {{
                  compilerOptions: {{ target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.CommonJS }},
                  reportDiagnostics: true,
                }});
                const errors = (result.diagnostics || []).filter(
                  (item) => item.category === ts.DiagnosticCategory.Error,
                );
                if (errors.length) {{
                  console.error(errors.map((item) => ts.flattenDiagnosticMessageText(item.messageText, "\\n")).join("\\n"));
                  process.exit(2);
                }}
                eval("(async () => {{\\n" + result.outputText + "\\n}})().catch((error) => {{ console.error(error); process.exit(1); }});");
                """
            )
            command = ["node", "-e", runner, str(fixture)]
        else:
            node_version = subprocess.run(
                ["node", "-p", "process.versions.node.split('.')[0]"],
                text=True,
                capture_output=True,
                timeout=10,
                check=False,
            )
            if node_version.returncode != 0 or int(node_version.stdout.strip()) < 22:
                return subprocess.CompletedProcess(
                    args=["node"],
                    returncode=2,
                    stdout="",
                    stderr=(
                        "Replit TypeScript behavior tests require the repository "
                        "TypeScript compiler on Node <22; run pnpm install or set "
                        "REPLIT_TEST_TYPESCRIPT_COMPILER."
                    ),
                )
            command = ["node", "--experimental-strip-types", str(fixture)]
        return subprocess.run(
            command,
            cwd=tmp,
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )


def fake_curl(directory: Path) -> None:
    script = directory / "curl"
    script.write_text(
        textwrap.dedent(
            """\
            #!/usr/bin/env bash
            set -euo pipefail
            if [[ -n "${MOCK_CALL_LOG:-}" ]]; then
              printf '%s\n' "$*" >> "$MOCK_CALL_LOG"
            fi
            if [[ "$*" == *"status.replit.com/api/v2/summary.json"* ]]; then
              : "${MOCK_STATUS_JSON:?}"
              printf '%s' "$MOCK_STATUS_JSON"
              exit "${MOCK_STATUS_EXIT:-0}"
            fi
            printf '%s' "${MOCK_APP_PROBE:-200 0.125}"
            exit "${MOCK_APP_EXIT:-0}"
            """
        ),
        encoding="utf-8",
    )
    script.chmod(0o755)


class ReplitCohortContractTests(unittest.TestCase):
    def test_retired_and_unsafe_guidance_is_absent(self) -> None:
        combined = "\n".join(skill_text(skill) for skill in COHORT)
        for forbidden in (
            "@replit/database",
            "REPLIT_DB_URL",
            "X-Replit-User-Id",
            "kill -9",
            "rejectUnauthorized: false",
            "rejectUnauthorized:false",
            "every 4 min",
            "stable-24_05",
            "Hacker plan",
            "50 MiB",
            "one-click rollback",
            "DB snapshot",
            'deploymentTarget = "cloudrun"',
            "npm ci --production",
            "CNAME record pointing to",
            "1-5 minutes",
            "x-*",
            "raw health response",
            "sync into published apps by default",
            "Project Editor Secrets do not automatically carry over",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, combined)

    def test_count_only_audit_never_prints_matching_secret_or_source(self) -> None:
        script = bash_block("replit-known-pitfalls", "candidate_secret_assignments=")
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            source = cwd / "app.ts"
            source.write_text(
                'const api_key = "TOP_SECRET_SENTINEL";\nserver.listen(3000, "127.0.0.1");\n',
                encoding="utf-8",
            )
            result = run_bash(script, cwd)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout,
            "candidate_secret_assignments=1\nloopback_bind_candidates=1\n",
        )
        self.assertNotIn("TOP_SECRET_SENTINEL", result.stdout + result.stderr)
        self.assertNotIn("app.ts", result.stdout + result.stderr)

    def test_count_only_audit_fails_closed_on_scanner_error(self) -> None:
        script = bash_block("replit-known-pitfalls", "candidate_secret_assignments=")
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            fake_grep = cwd / "grep"
            fake_grep.write_text(
                "#!/usr/bin/env bash\nprintf 'TOP_SECRET_SENTINEL app.ts\\n' >&2\nexit 2\n",
                encoding="utf-8",
            )
            fake_grep.chmod(0o755)
            result = run_bash(script, cwd)

        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "Source audit failed\n")

    def test_count_only_audit_does_not_follow_project_symlinks(self) -> None:
        script = bash_block("replit-known-pitfalls", "candidate_secret_assignments=")
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            cwd = Path(tmp)
            outside_path = Path(outside)
            (outside_path / "secret.ts").write_text(
                'const api_key = "TOP_SECRET_SENTINEL";\nserver.listen(3000, "127.0.0.1");\n',
                encoding="utf-8",
            )
            (cwd / "outside-link").symlink_to(outside_path, target_is_directory=True)
            result = run_bash(script, cwd)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout,
            "candidate_secret_assignments=0\nloopback_bind_candidates=0\n",
        )
        self.assertNotIn("TOP_SECRET_SENTINEL", result.stdout + result.stderr)
        self.assertNotIn("outside-link", result.stdout + result.stderr)

    def test_incident_probe_emits_only_allowlisted_metadata(self) -> None:
        script = bash_block("replit-incident-runbook", "platform_indicator")
        for status in ("200", "401", "429", "500"):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as tmp:
                cwd = Path(tmp)
                fake_curl(cwd)
                call_log = cwd / "calls.log"
                result = run_bash(
                    script,
                    cwd,
                    REPLIT_DEPLOY_URL="https://safe-app.replit.app",
                    MOCK_STATUS_JSON=json.dumps(
                        {
                            "status": {"indicator": "none"},
                            "secret": "TOP_SECRET_SENTINEL",
                        }
                    ),
                    MOCK_APP_PROBE=f"{status} 0.125",
                    MOCK_CALL_LOG=str(call_log),
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(
                    json.loads(result.stdout),
                    {
                        "platform_indicator": "none",
                        "http_status": status,
                        "duration_seconds": "0.125",
                    },
                )
                self.assertNotIn("TOP_SECRET_SENTINEL", result.stdout + result.stderr)
                app_probe = call_log.read_text(encoding="utf-8").splitlines()[1]
                for required in (
                    "--output /dev/null",
                    "--connect-timeout 5",
                    "--max-time 10",
                    "--proto =https",
                ):
                    self.assertIn(required, app_probe)
                for forbidden in ("--header", "--cookie", "--location"):
                    self.assertNotIn(forbidden, app_probe)

        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            fake_curl(cwd)
            timeout = run_bash(
                script,
                cwd,
                REPLIT_DEPLOY_URL="https://safe-app.replit.app",
                MOCK_STATUS_JSON='{"status":{"indicator":"none"}}',
                MOCK_APP_PROBE="TOP_SECRET_SENTINEL",
                MOCK_APP_EXIT="28",
            )
        self.assertEqual(timeout.returncode, 1)
        self.assertEqual(timeout.stdout, "")
        self.assertEqual(timeout.stderr, "Published app probe failed\n")

    def test_incident_status_failure_and_invalid_indicator_fail_closed(self) -> None:
        script = bash_block("replit-incident-runbook", "platform_indicator")
        cases = (
            ('{"status":{"indicator":"none"}}', "22", "Unable to retrieve Replit status safely\n"),
            ('{"status":{"indicator":7}}', "0", "Invalid Replit status response\n"),
            (json.dumps({"status": {"indicator": "x" * 33}}), "0", "Invalid Replit status response\n"),
        )
        for status_json, status_exit, expected_error in cases:
            with self.subTest(status_exit=status_exit), tempfile.TemporaryDirectory() as tmp:
                cwd = Path(tmp)
                fake_curl(cwd)
                result = run_bash(
                    script,
                    cwd,
                    REPLIT_DEPLOY_URL="https://safe-app.replit.app",
                    MOCK_STATUS_JSON=status_json,
                    MOCK_STATUS_EXIT=status_exit,
                )
            self.assertEqual(result.returncode, 1)
            self.assertEqual(result.stdout, "")
            self.assertEqual(result.stderr, expected_error)

    def test_incident_probe_rejects_unapproved_origin_before_curl(self) -> None:
        script = bash_block("replit-incident-runbook", "platform_indicator")
        for origin in (
            "http://safe-app.replit.app",
            "https://safe-app.replit.app.evil.example",
            "https://user@safe-app.replit.app",
            "https://127.0.0.1",
            "https://safe.app.replit.app",
            "https://safe-app.replit.app/path",
            "https://safe-app.replit.app?token=secret",
            "https://custom.example",
            "-K/etc/passwd",
        ):
            with self.subTest(origin=origin), tempfile.TemporaryDirectory() as tmp:
                cwd = Path(tmp)
                fake_curl(cwd)
                call_log = cwd / "calls.log"
                result = run_bash(
                    script,
                    cwd,
                    REPLIT_DEPLOY_URL=origin,
                    MOCK_CALL_LOG=str(call_log),
                )
                self.assertEqual(result.returncode, 64)
                self.assertFalse(call_log.exists())

    def test_production_canary_accepts_2xx_and_fails_closed_otherwise(self) -> None:
        script = bash_block("replit-prod-checklist", "Published app is not healthy")
        cases = (
            ("204 0.075", "0", 0),
            ("401 0.075", "0", 1),
            ("429 0.075", "0", 1),
            ("500 0.075", "0", 1),
            ("200 injected", "0", 1),
            ("TOP_SECRET_SENTINEL", "28", 1),
        )
        for probe, curl_status, expected_status in cases:
            with self.subTest(probe=probe), tempfile.TemporaryDirectory() as tmp:
                cwd = Path(tmp)
                fake_curl(cwd)
                result = run_bash(
                    script,
                    cwd,
                    REPLIT_DEPLOY_URL="https://safe-app.replit.app",
                    MOCK_APP_PROBE=probe,
                    MOCK_APP_EXIT=curl_status,
                )
                self.assertEqual(result.returncode, expected_status, result.stderr)
                self.assertNotIn("TOP_SECRET_SENTINEL", result.stdout + result.stderr)
                if expected_status == 0:
                    self.assertEqual(
                        json.loads(result.stdout),
                        {"http_status": 204, "duration_seconds": 0.075},
                    )

    def test_production_canary_rejects_unapproved_origin_before_curl(self) -> None:
        script = bash_block("replit-prod-checklist", "Published app is not healthy")
        for origin in (
            "http://safe-app.replit.app",
            "https://safe-app.replit.app.evil.example",
            "https://user@safe-app.replit.app",
            "https://127.0.0.1",
            "https://safe.app.replit.app",
            "https://safe-app.replit.app/path",
            "https://safe-app.replit.app?token=secret",
            "https://custom.example",
            "-K/etc/passwd",
        ):
            with self.subTest(origin=origin), tempfile.TemporaryDirectory() as tmp:
                cwd = Path(tmp)
                fake_curl(cwd)
                call_log = cwd / "calls.log"
                result = run_bash(
                    script,
                    cwd,
                    REPLIT_DEPLOY_URL=origin,
                    MOCK_CALL_LOG=str(call_log),
                )
                self.assertEqual(result.returncode, 64)
                self.assertFalse(call_log.exists())

    def test_public_health_schema_is_exact_and_coarse(self) -> None:
        block = typescript_block("replit-reference-architecture", 'app.get("/healthz"')
        result = run_typescript(
            """
            let healthHandler;
            const app = {
              get(path, handler) {
                if (path === "/healthz") healthHandler = handler;
              },
            };
            """
            + block
            + """
            let statusCode;
            let payload;
            const response = {
              status(code) { statusCode = code; return this; },
              json(value) { payload = value; return this; },
            };
            healthHandler({}, response);
            console.log(JSON.stringify({ statusCode, payload }));
            """
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            json.loads(result.stdout),
            {"statusCode": 200, "payload": {"status": "ok"}},
        )
        for forbidden in ("database", "uptime", "memory", "secret", "path"):
            self.assertNotIn(forbidden, result.stdout.lower())

    def test_tenant_query_uses_only_verified_session_identity(self) -> None:
        block = typescript_block("replit-reference-architecture", "listOwnedProjects")
        result = run_typescript(
            block
            + """
            const rowsByOwner = {
              alice: [{ id: "a", name: "Alice project", ownerId: "alice" }],
              bob: [{ id: "b", name: "Bob project", ownerId: "bob" }],
            };
            const calls = [];
            const database = {
              async query(statement, parameters) {
                calls.push({ statement, parameters });
                return { rows: rowsByOwner[parameters[0]] ?? [] };
              },
            };
            const alice = await listOwnedProjects({ userId: "alice" }, database);
            const bob = await listOwnedProjects({ userId: "bob" }, database);
            let unauthenticated = "";
            try {
              await listOwnedProjects(null, database);
            } catch (error) {
              unauthenticated = error.message;
            }
            console.log(JSON.stringify({ alice, bob, calls, unauthenticated }));
            """
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual([row["ownerId"] for row in payload["alice"]], ["alice"])
        self.assertEqual([row["ownerId"] for row in payload["bob"]], ["bob"])
        self.assertEqual([call["parameters"] for call in payload["calls"]], [["alice"], ["bob"]])
        self.assertTrue(all("WHERE owner_id = $1" in call["statement"] for call in payload["calls"]))
        self.assertEqual(payload["unauthenticated"], "authentication required")


if __name__ == "__main__":
    unittest.main()
