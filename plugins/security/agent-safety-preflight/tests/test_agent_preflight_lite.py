import tempfile
import unittest
from pathlib import Path
import importlib.util
import subprocess

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "agent_preflight_lite.py"
spec = importlib.util.spec_from_file_location("agent_preflight_lite", MODULE)
scanner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scanner)


class AgentPreflightLiteTest(unittest.TestCase):
    def test_green_empty_repo(self):
        with tempfile.TemporaryDirectory() as td:
            subprocess.run(["git", "init"], cwd=td, check=True, capture_output=True)
            result = scanner.scan(Path(td))
            self.assertEqual(result["decision"], "Green")

    def test_non_git_directory_is_yellow(self):
        with tempfile.TemporaryDirectory() as td:
            result = scanner.scan(Path(td))
            self.assertEqual(result["git_state"], "unavailable")
            self.assertEqual(result["decision"], "Yellow")

    def test_generic_permissions_docs_do_not_trigger_agent_authority(self):
        with tempfile.TemporaryDirectory() as td:
            subprocess.run(["git", "init"], cwd=td, check=True, capture_output=True)
            p = Path(td) / "README.md"
            p.write_text("Document normal Linux file permissions and OAuth scopes.\n", encoding="utf-8")
            result = scanner.scan(Path(td))
            self.assertNotIn("agent-authority", result["risk_buckets"])

    def test_browser_permissions_array_does_not_trigger_agent_authority(self):
        with tempfile.TemporaryDirectory() as td:
            subprocess.run(["git", "init"], cwd=td, check=True, capture_output=True)
            p = Path(td) / "manifest.json"
            p.write_text('{"permissions": ["storage", "activeTab", "clipboardRead"]}\n', encoding="utf-8")
            result = scanner.scan(Path(td))
            self.assertNotIn("agent-authority", result["risk_buckets"])

    def test_risky_permissions_array_triggers_agent_authority(self):
        with tempfile.TemporaryDirectory() as td:
            subprocess.run(["git", "init"], cwd=td, check=True, capture_output=True)
            p = Path(td) / ".claude" / "settings.json"
            p.parent.mkdir()
            p.write_text('{"permissions": ["write"]}\n', encoding="utf-8")
            result = scanner.scan(Path(td))
            self.assertIn("agent-authority", result["risk_buckets"])

    def test_paypal_brand_docs_do_not_trigger_credential_write(self):
        with tempfile.TemporaryDirectory() as td:
            subprocess.run(["git", "init"], cwd=td, check=True, capture_output=True)
            p = Path(td) / "README.md"
            p.write_text("This e-commerce app accepts PayPal and card checkout.\n", encoding="utf-8")
            result = scanner.scan(Path(td))
            self.assertNotIn("credential-write", result["risk_buckets"])
            self.assertNotEqual(result["decision"], "Red")

    def test_git_hooks_docs_do_not_trigger_agent_authority(self):
        with tempfile.TemporaryDirectory() as td:
            subprocess.run(["git", "init"], cwd=td, check=True, capture_output=True)
            p = Path(td) / "README.md"
            p.write_text("Document pre-commit hooks and GitHub Actions release hooks.\n", encoding="utf-8")
            result = scanner.scan(Path(td))
            self.assertNotIn("agent-authority", result["risk_buckets"])

    def test_red_destructive_command(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "danger.sh"
            p.write_text("rm -" + "rf /tmp/example\n", encoding="utf-8")
            result = scanner.scan(Path(td))
            self.assertEqual(result["decision"], "Red")
            self.assertIn("destructive-recursive-delete", result["risk_buckets"])

    def test_env_mention_in_docs_is_not_credential_write(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "README.md"
            p.write_text("Copy .env.example to .env before running locally.\n", encoding="utf-8")
            result = scanner.scan(Path(td))
            self.assertNotIn("credential-write", result["risk_buckets"])
            self.assertNotEqual(result["decision"], "Red")

    def test_github_actions_secret_reference_is_not_credential_write(self):
        with tempfile.TemporaryDirectory() as td:
            workflow = Path(td) / ".github" / "workflows" / "ci.yml"
            workflow.parent.mkdir(parents=True)
            workflow.write_text(
                "env:\n  TOKEN: ${{ secrets.GITHUB_TOKEN }}\n  OPENAI: ${{ secrets.OPENAI_API_KEY }}\n",
                encoding="utf-8",
            )
            result = scanner.scan(Path(td))
            self.assertNotIn("credential-write", result["risk_buckets"])
            self.assertNotEqual(result["decision"], "Red")

    def test_api_key_assignment_is_credential_write(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "config.yml"
            p.write_text("OPENAI_API_KEY: sk-example\n", encoding="utf-8")
            result = scanner.scan(Path(td))
            self.assertEqual(result["decision"], "Red")
            self.assertIn("credential-write", result["risk_buckets"])

    def test_actual_env_file_is_credential_write(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / ".env.local"
            p.write_text("LOCAL_ONLY=1\n", encoding="utf-8")
            result = scanner.scan(Path(td))
            self.assertEqual(result["decision"], "Red")
            self.assertIn("credential-write", result["risk_buckets"])

    def test_large_file_uses_prefix_sample(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "README.md"
            p.write_text("safe\n" * (scanner.MAX_SCAN_BYTES // 5 + 2) + "rm -" + "rf /tmp/example\n", encoding="utf-8")
            result = scanner.scan(Path(td))
            self.assertNotIn("destructive-recursive-delete", result["risk_buckets"])


if __name__ == "__main__":
    unittest.main()
