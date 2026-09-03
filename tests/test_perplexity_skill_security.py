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


def typescript_block(skill: str, marker: str) -> str:
    text = (PACK / skill / "SKILL.md").read_text(encoding="utf-8")
    for block in re.findall(r"```typescript\n(.*?)\n```", text, flags=re.DOTALL):
        if marker in block:
            return block
    raise AssertionError(f"TypeScript block containing {marker!r} not found in {skill}")


def reference_typescript_block(skill: str, reference: str, marker: str) -> str:
    text = (PACK / skill / "references" / reference).read_text(encoding="utf-8")
    for block in re.findall(r"```typescript\n(.*?)\n```", text, flags=re.DOTALL):
        if marker in block:
            return block
    raise AssertionError(
        f"TypeScript block containing {marker!r} not found in {skill}/{reference}"
    )


def run_typescript(blocks: list[str], harness: str) -> subprocess.CompletedProcess[str]:
    source = "\n\n".join(blocks)
    source = re.sub(r'import OpenAI from "openai";\n', "", source)
    source = re.sub(
        r"const perplexity = new OpenAI\(\{.*?\n\}\);",
        "const perplexity = (globalThis as any).__perplexity;",
        source,
        flags=re.DOTALL,
    )
    source = source.replace('import { LRUCache } from "lru-cache";\n', "")
    source = source.replace('import { createHash } from "crypto";\n', "")
    source = source.replace('import { isIP } from "node:net";\n', "")
    support = textwrap.dedent(
        """
        const { createHash } = require("node:crypto");
        const { isIP } = require("node:net");
        class LRUCache<K, V> {
          private values = new Map<K, V>();
          constructor(_options: unknown) {}
          set(key: K, value: V): void { this.values.set(key, value); }
          get(key: K): V | undefined { return this.values.get(key); }
        }
        """
    )
    typescript = support + source + "\n" + harness

    with tempfile.TemporaryDirectory() as tmp:
        cwd = Path(tmp)
        source_path = cwd / "fixture.ts"
        source_path.write_text(typescript, encoding="utf-8")
        compiler_path = Path(
            os.environ.get(
                "PERPLEXITY_TEST_TYPESCRIPT_COMPILER",
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
                eval(result.outputText);
                """
            )
            command = ["node", "-e", runner, str(source_path)]
        else:
            command = ["node", "--experimental-strip-types", str(source_path)]
        return subprocess.run(
            command,
            cwd=cwd,
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )


def last_json_line(result: subprocess.CompletedProcess[str]) -> object:
    if result.returncode != 0:
        raise AssertionError(f"TypeScript fixture failed:\n{result.stdout}\n{result.stderr}")
    return json.loads(result.stdout.strip().splitlines()[-1])


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
    skill = "perplexity-reliability-patterns"
    reference = "reliability-test-matrix.md"

    def test_terminal_failures_never_serve_stale_cache(self) -> None:
        model_fallback = typescript_block(self.skill, "async function resilientSearch")
        classifiers = reference_typescript_block(
            self.skill, self.reference, "function isRetryablePerplexityError"
        )
        cache_fallback = typescript_block(self.skill, "async function searchWithCacheFallback")
        harness = textwrap.dedent(
            """
            void (async () => {
              const failures = [
                ...[400, 401, 402, 403, 422].map((status) =>
                  Object.assign(new Error(`terminal ${status}`), { status }),
                ),
                new Error("unclassified statusless defect"),
              ];
              const results: Array<Record<string, unknown>> = [];
              for (const failure of failures) {
                let calls = 0;
                (globalThis as any).__perplexity.chat.completions.create = async () => {
                  calls++;
                  if (calls === 1) return {
                    choices: [{ message: { content: "cached answer" } }],
                    citations: [],
                    model: "sonar",
                  };
                  throw failure;
                };
                await searchWithCacheFallback("tenant-a", "same query", "sonar", true);
                let caught: unknown;
                try {
                  await searchWithCacheFallback("tenant-a", "same query", "sonar", true);
                } catch (error) {
                  caught = error;
                }
                results.push({ sameError: caught === failure, calls });
              }
              console.log(JSON.stringify(results));
            })().catch((error) => { console.error(error); process.exitCode = 1; });
            """
        )
        prefix = "(globalThis as any).__perplexity = { chat: { completions: { create: async () => ({}) } } };"
        result = run_typescript(
            [prefix, classifiers, model_fallback, cache_fallback], harness
        )
        self.assertEqual(
            last_json_line(result),
            [
                {"sameError": True, "calls": 2},
                {"sameError": True, "calls": 2},
                {"sameError": True, "calls": 2},
                {"sameError": True, "calls": 2},
                {"sameError": True, "calls": 2},
                {"sameError": True, "calls": 2},
            ],
        )

    def test_retry_policy_waits_for_429_dedupes_sonar_and_classifies_transport(self) -> None:
        model_fallback = typescript_block(self.skill, "async function resilientSearch")
        classifiers = reference_typescript_block(
            self.skill, self.reference, "function isRetryablePerplexityError"
        )
        harness = textwrap.dedent(
            """
            void (async () => {
              const rateLimit = Object.assign(new Error("rate limited"), {
                status: 429,
                headers: { "retry-after": "0.001" },
              });
              const rateModels: string[] = [];
              const sleeps: number[] = [];
              (globalThis as any).__perplexity.chat.completions.create = async (request: any) => {
                rateModels.push(request.model);
                throw rateLimit;
              };
              let preserved = false;
              try {
                await resilientSearch("q", "sonar", {
                  maxElapsedMs: 100,
                  maxRateLimitRetriesPerModel: 1,
                  sleep: async (ms) => { sleeps.push(ms); },
                  now: () => 0,
                });
              } catch (error) {
                preserved = error === rateLimit;
              }

              const deadlineLimit = Object.assign(new Error("deadline rate limit"), {
                status: 429,
                headers: { "retry-after": "999" },
              });
              const deadlineModels: string[] = [];
              const deadlineSleeps: number[] = [];
              (globalThis as any).__perplexity.chat.completions.create = async (request: any) => {
                deadlineModels.push(request.model);
                throw deadlineLimit;
              };
              let deadlinePreserved = false;
              try {
                await resilientSearch("q", "sonar", {
                  maxElapsedMs: 100,
                  sleep: async (ms) => { deadlineSleeps.push(ms); },
                  now: () => 0,
                });
              } catch (error) {
                deadlinePreserved = error === deadlineLimit;
              }

              const transportModels: string[] = [];
              (globalThis as any).__perplexity.chat.completions.create = async (request: any) => {
                transportModels.push(request.model);
                if (transportModels.length === 1) {
                  throw Object.assign(new Error("connect timeout"), { name: "APIConnectionTimeoutError" });
                }
                return { choices: [{ message: { content: "ok" } }], citations: [], model: request.model };
              };
              const recovered = await resilientSearch("q", "sonar-pro", { now: () => 0 });
              console.log(JSON.stringify({
                rateModels, sleeps, preserved, deadlineModels, deadlineSleeps,
                deadlinePreserved, transportModels, recoveredModel: recovered.model,
              }));
            })().catch((error) => { console.error(error); process.exitCode = 1; });
            """
        )
        prefix = "(globalThis as any).__perplexity = { chat: { completions: { create: async () => ({}) } } };"
        result = run_typescript([prefix, classifiers, model_fallback], harness)
        self.assertEqual(
            last_json_line(result),
            {
                "rateModels": ["sonar", "sonar"],
                "sleeps": [1],
                "preserved": True,
                "deadlineModels": ["sonar"],
                "deadlineSleeps": [],
                "deadlinePreserved": True,
                "transportModels": ["sonar-pro", "sonar"],
                "recoveredModel": "sonar",
            },
        )

    def test_never_resolving_stream_establishment_aborts_and_times_out(self) -> None:
        stream = typescript_block(self.skill, "async function* streamWithTimeout").split(
            "// Usage", 1
        )[0]
        harness = textwrap.dedent(
            """
            void (async () => {
              let signal: AbortSignal | undefined;
              let abortEvents = 0;
              (globalThis as any).__perplexity.chat.completions.create = async (_request: any, options: any) => {
                signal = options.signal;
                signal?.addEventListener("abort", () => { abortEvents++; });
                return await new Promise(() => {});
              };
              const events: any[] = [];
              for await (const event of streamWithTimeout("q", "sonar", 50, 5)) events.push(event);
              console.log(JSON.stringify({ events, aborted: signal?.aborted, abortEvents }));
            })().catch((error) => { console.error(error); process.exitCode = 1; });
            """
        )
        prefix = "const perplexity = (globalThis as any).__perplexity = { chat: { completions: { create: async () => ({}) } } };"
        result = run_typescript([prefix, stream], harness)
        self.assertEqual(
            last_json_line(result),
            {
                "events": [
                    {"type": "timeout", "data": "Stream establishment timed out."}
                ],
                "aborted": True,
                "abortEvents": 1,
            },
        )

    def test_stream_timeout_handles_the_losing_provider_rejection(self) -> None:
        stream = typescript_block(self.skill, "async function* streamWithTimeout").split(
            "// Usage", 1
        )[0]
        harness = textwrap.dedent(
            """
            void (async () => {
              let unhandled = 0;
              process.on("unhandledRejection", () => { unhandled++; });
              (globalThis as any).__perplexity.chat.completions.create = async (_request: any, options: any) => {
                return await new Promise((_resolve, reject) => {
                  options.signal.addEventListener("abort", () => reject(new Error("provider aborted")));
                });
              };
              const events: any[] = [];
              for await (const event of streamWithTimeout("q", "sonar", 50, 5)) events.push(event);
              await new Promise((resolve) => setTimeout(resolve, 10));
              console.log(JSON.stringify({ events, unhandled }));
            })().catch((error) => { console.error(error); process.exitCode = 1; });
            """
        )
        prefix = "const perplexity = (globalThis as any).__perplexity = { chat: { completions: { create: async () => ({}) } } };"
        result = run_typescript([prefix, stream], harness)
        self.assertEqual(
            last_json_line(result),
            {
                "events": [
                    {"type": "timeout", "data": "Stream establishment timed out."}
                ],
                "unhandled": 0,
            },
        )

    def test_bracketed_ipv6_citations_are_rejected_even_when_allowlisted(self) -> None:
        citations = reference_typescript_block(
            self.skill, self.reference, "function validateCitations"
        )
        harness = textwrap.dedent(
            """
            const urls = ["https://[::1]/admin", "https://[::ffff:7f00:1]/admin"];
            const allowed = new Set(["::1", "::ffff:7f00:1", "[::1]", "[::ffff:7f00:1]"]);
            console.log(JSON.stringify(validateCitations(urls, allowed)));
            """
        )
        result = run_typescript([citations], harness)
        self.assertEqual(
            last_json_line(result),
            [
                {
                    "url": "https://[::1]/admin",
                    "valid": False,
                    "reason": "local-or-ip-host",
                },
                {
                    "url": "https://[::ffff:7f00:1]/admin",
                    "valid": False,
                    "reason": "local-or-ip-host",
                },
            ],
        )

    def test_citation_validation_never_fetches_model_supplied_urls(self) -> None:
        citations = reference_typescript_block(
            self.skill, self.reference, "function validateCitations"
        )
        self.assertNotIn("fetch(", citations)


if __name__ == "__main__":
    unittest.main()
