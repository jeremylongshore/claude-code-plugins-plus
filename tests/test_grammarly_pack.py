"""Offline production-contract tests for grammarly-pack v2."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "plugins" / "saas-packs" / "grammarly-pack"
CURATED = ROOT / "skills" / ".curated"
SHARED = PACK / "skills" / "grammarly-document-evaluator" / "scripts" / "grammarly_api.py"
EXPECTED_SKILLS = {
    "grammarly-access-readiness",
    "grammarly-api-reliability",
    "grammarly-data-safety-guardian",
    "grammarly-document-evaluator",
    "grammarly-license-governor",
}
RETIRED_SKILLS = {
    "grammarly-ci-integration",
    "grammarly-common-errors",
    "grammarly-core-workflow-a",
    "grammarly-core-workflow-b",
    "grammarly-cost-tuning",
    "grammarly-data-handling",
    "grammarly-debug-bundle",
    "grammarly-deploy-integration",
    "grammarly-enterprise-rbac",
    "grammarly-hello-world",
    "grammarly-incident-runbook",
    "grammarly-install-auth",
    "grammarly-local-dev-loop",
    "grammarly-migration-deep-dive",
    "grammarly-multi-env-setup",
    "grammarly-observability",
    "grammarly-performance-tuning",
    "grammarly-prod-checklist",
    "grammarly-rate-limits",
    "grammarly-reference-architecture",
    "grammarly-sdk-patterns",
    "grammarly-security-basics",
    "grammarly-upgrade-migration",
    "grammarly-webhooks-events",
}


def public_dns(*_args: Any, **_kwargs: Any) -> list[tuple[Any, ...]]:
    return [(0, 0, 0, "", ("8.8.8.8", 443))]


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


api = load_module(SHARED, "grammarly_api_test")
access = load_module(
    PACK / "skills" / "grammarly-access-readiness" / "scripts" / "audit_oauth_config.py",
    "grammarly_access_test",
)
reliability = load_module(
    PACK / "skills" / "grammarly-api-reliability" / "scripts" / "analyze_job_receipt.py",
    "grammarly_reliability_test",
)
safety = load_module(
    PACK / "skills" / "grammarly-data-safety-guardian" / "scripts" / "audit_submission_manifest.py",
    "grammarly_safety_test",
)
evaluator = load_module(
    PACK / "skills" / "grammarly-document-evaluator" / "scripts" / "run_document_evaluation.py",
    "grammarly_evaluator_test",
)
license_governor = load_module(
    PACK / "skills" / "grammarly-license-governor" / "scripts" / "analyze_license_snapshot.py",
    "grammarly_license_test",
)


class FakeResponse:
    def __init__(self, payload: dict[str, Any] | None = None, status: int = 200):
        self.payload = json.dumps(payload or {}).encode("utf-8")
        self.status = status

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args: Any) -> None:
        return None

    def read(self, size: int = -1) -> bytes:
        return self.payload if size < 0 else self.payload[:size]


class FakeUploadConnection:
    def __init__(
        self,
        destination: Any,
        address: str,
        *,
        timeout: float,
        captured: dict[str, Any],
        status: int = 204,
    ) -> None:
        captured.update(
            {
                "destination": destination,
                "address": address,
                "timeout": timeout,
            }
        )
        self.captured = captured
        self.status = status

    def request(self, method: str, target: str, *, body: bytes, headers: dict[str, str]) -> None:
        self.captured.update({"method": method, "target": target, "body": body, "headers": headers})

    def getresponse(self) -> FakeResponse:
        return FakeResponse(status=self.status)

    def close(self) -> None:
        self.captured["closed"] = True


class GrammarlyApiContractTests(unittest.TestCase):
    def test_pinned_endpoints_scopes_and_fields(self) -> None:
        writing = api.DOCUMENT_CONTRACTS["writing-score"]
        self.assertEqual(writing.endpoint, "https://api.grammarly.com/ecosystem/api/v2/scores")
        self.assertEqual(writing.scopes, ("scores-api:read", "scores-api:write"))
        self.assertEqual(
            writing.result_fields,
            ("general_score", "engagement", "correctness", "delivery", "clarity"),
        )
        self.assertEqual(api.DOCUMENT_CONTRACTS["ai-detection"].endpoint.rsplit("/", 1)[-1], "ai-detection")
        self.assertEqual(api.DOCUMENT_CONTRACTS["plagiarism"].result_fields, ("originality",))
        self.assertEqual(api.ALL_STATUSES, {"PENDING", "FAILED", "COMPLETED"})

    def test_valid_text_is_hashed_and_counted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "approved.txt"
            path.write_text(" ".join(f"word{i}" for i in range(30)), encoding="utf-8")
            data, metadata = api.read_document(str(path))
        self.assertEqual(metadata["word_count"], 30)
        self.assertEqual(metadata["content_sha256"], api.sha256_bytes(data))
        self.assertNotIn(data.decode(), json.dumps(metadata))

    def test_text_below_minimum_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "short.txt"
            path.write_text("too short", encoding="utf-8")
            with self.assertRaisesRegex(api.GrammarlyContractError, "30-word"):
                api.read_document(str(path))

    def test_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target.txt"
            target.write_text(" ".join(["safe"] * 30), encoding="utf-8")
            alias = Path(directory) / "alias.txt"
            alias.symlink_to(target)
            with self.assertRaisesRegex(api.GrammarlyContractError, "opened safely"):
                api.read_document(str(alias))

    def test_parent_directory_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            real = root / "real"
            real.mkdir()
            document = real / "document.txt"
            document.write_text(" ".join(["safe"] * 30), encoding="utf-8")
            alias = root / "alias"
            alias.symlink_to(real, target_is_directory=True)
            with self.assertRaisesRegex(api.GrammarlyContractError, "opened safely"):
                api.read_document(str(alias / "document.txt"))

    def test_oauth_request_is_exact_form_contract(self) -> None:
        captured: dict[str, Any] = {}

        def opener(request: Any, timeout: float) -> FakeResponse:
            captured.update({"request": request, "timeout": timeout})
            return FakeResponse({"access_token": "opaque"})

        environment = {
            "GRAMMARLY_CLIENT_ID": "client-id",
            "GRAMMARLY_CLIENT_SECRET": "secret-value",
        }
        original = os.environ.copy()
        try:
            os.environ.clear()
            os.environ.update(environment)
            token = api.obtain_access_token(["scores-api:read", "scores-api:write"], opener=opener)
        finally:
            os.environ.clear()
            os.environ.update(original)
        request = captured["request"]
        self.assertEqual(token, "opaque")
        self.assertEqual(request.full_url, api.TOKEN_ENDPOINT)
        self.assertEqual(request.method, "POST")
        self.assertEqual(request.headers["Content-type"], "application/x-www-form-urlencoded")
        self.assertEqual(
            request.data.decode("ascii"),
            "grant_type=client_credentials&client_id=client-id&client_secret=secret-value&scope=scores-api%3Aread%2Cscores-api%3Awrite",
        )

    def test_upload_does_not_send_bearer_or_content_type(self) -> None:
        captured: dict[str, Any] = {}

        def connection_factory(destination: Any, address: str, *, timeout: float) -> FakeUploadConnection:
            return FakeUploadConnection(destination, address, timeout=timeout, captured=captured)

        api.upload_document(
            "https://bucket.s3.amazonaws.com/object?signature=opaque",
            b"bytes",
            approved_origin="https://bucket.s3.amazonaws.com",
            connection_factory=connection_factory,
            resolver=public_dns,
        )
        self.assertEqual(captured["method"], "PUT")
        self.assertEqual(captured["target"], "/object?signature=opaque")
        self.assertEqual(captured["address"], "8.8.8.8")
        self.assertEqual(captured["headers"], {})
        self.assertTrue(captured["closed"])

    def test_upload_requires_matching_public_https_origin(self) -> None:
        with self.assertRaisesRegex(api.GrammarlyContractError, "unsafe upload URL"):
            api.upload_document(
                "http://127.0.0.1/object",
                b"bytes",
                approved_origin="http://127.0.0.1",
            )
        with self.assertRaisesRegex(api.GrammarlyContractError, "exact approved origin"):
            api.upload_document(
                "https://bucket.s3.amazonaws.com/object",
                b"bytes",
                approved_origin="https://1.1.1.1",
                resolver=public_dns,
            )

    def test_upload_rejects_non_s3_aws_hosts_and_nondefault_ports(self) -> None:
        for upload_url in (
            "https://ec2.amazonaws.com/object",
            "https://bucket.s3.amazonaws.com:8443/object",
            "https://bucket.s3.amazonaws.com/object\nHost:evil.example",
        ):
            with self.subTest(upload_url=upload_url):
                with self.assertRaises(api.GrammarlyContractError):
                    api.validated_upload_origin(upload_url, resolver=public_dns)

    def test_custom_contract_cannot_receive_bearer_token(self) -> None:
        custom = api.DocumentContract(
            operation="writing-score",
            endpoint="https://attacker.example/collect",
            scopes=("scores-api:read", "scores-api:write"),
            result_fields=("general_score",),
            beta=False,
        )
        with self.assertRaisesRegex(api.GrammarlyContractError, "exact official"):
            api.create_document_job(custom, filename="document.txt", token="opaque")

    def test_json_response_size_is_bounded(self) -> None:
        response = FakeResponse()
        response.payload = b"{" + b"x" * api.MAX_JSON_RESPONSE_BYTES + b"}"
        with self.assertRaisesRegex(api.GrammarlyContractError, "response-size"):
            api._decode_json_response(response, "test response")

    def test_shared_oauth_rejects_unowned_write_scope(self) -> None:
        with self.assertRaisesRegex(api.GrammarlyContractError, "undocumented"):
            api.obtain_access_token(["users-api:write"], opener=lambda *_args, **_kwargs: FakeResponse())

    def test_unknown_status_and_score_shape_fail_closed(self) -> None:
        request_id = "123e4567-e89b-12d3-a456-426614174000"

        def opener(_request: Any, timeout: float) -> FakeResponse:
            return FakeResponse({"score_request_id": request_id, "status": "done"})

        with self.assertRaisesRegex(api.GrammarlyContractError, "undocumented status"):
            api.get_document_job(
                api.DOCUMENT_CONTRACTS["writing-score"],
                request_id=request_id,
                token="opaque",
                opener=opener,
            )
        with self.assertRaisesRegex(api.GrammarlyContractError, "documented contract"):
            api.normalize_completed_score(
                api.DOCUMENT_CONTRACTS["writing-score"],
                {"status": "COMPLETED", "score": {"overallScore": 80}},
            )

    def test_private_upload_host_is_rejected(self) -> None:
        request_id = "123e4567-e89b-12d3-a456-426614174000"

        def opener(_request: Any, timeout: float) -> FakeResponse:
            return FakeResponse({"score_request_id": request_id, "file_upload_url": "https://127.0.0.1/object"})

        with self.assertRaisesRegex(api.GrammarlyContractError, "pinned S3 provider allowlist"):
            api.create_document_job(
                api.DOCUMENT_CONTRACTS["writing-score"],
                filename="document.txt",
                token="opaque",
                opener=opener,
            )


class GrammarlyOfflineAnalyzerTests(unittest.TestCase):
    def test_access_plan_owns_scope_catalog_and_enforces_least_privilege(self) -> None:
        plan = {
            "schema_version": "1",
            "access_tier": "enterprise",
            "oauth_client_configured": True,
            "configuration_source": "secret-manager-reference",
            "operations": ["writing-score"],
            "granted_scopes": ["scores-api:read", "scores-api:write"],
            "beta_scope_exception_approved": False,
        }
        self.assertEqual(access.audit(plan)["decision"], "READY")
        plan["granted_scopes"].append("analytics-api:read")
        result = access.audit(plan)
        self.assertEqual(result["decision"], "BLOCKED")
        self.assertIn("granted_scope_exceeds_least_privilege", result["reasons"])
        plan["granted_scopes"][-1] = "users-api:write"
        with self.assertRaisesRegex(access.AuditError, "undocumented"):
            access.audit(plan)

    def test_access_beta_scope_discrepancy_requires_explicit_review(self) -> None:
        plan = {
            "schema_version": "1",
            "access_tier": "education-institution-wide",
            "oauth_client_configured": True,
            "configuration_source": "environment-injected",
            "operations": ["ai-detection"],
            "granted_scopes": ["ai-detection-api:read", "ai-detection-api:write"],
            "beta_scope_exception_approved": False,
        }
        self.assertEqual(access.audit(plan)["decision"], "BLOCKED")
        plan["beta_scope_exception_approved"] = True
        reviewed = access.audit(plan)
        self.assertEqual(reviewed["decision"], "READY")
        self.assertEqual(
            reviewed["documentation_flags"],
            ["official_ai_plagiarism_oauth_catalog_inconsistency"],
        )

    def test_access_rejects_secret_bearing_fields(self) -> None:
        with self.assertRaisesRegex(access.AuditError, "secret-bearing key"):
            access.audit({"client_secret": "do-not-echo"})

    def test_submission_gate_requires_exact_origin_and_all_text_metrics(self) -> None:
        manifest = {
            "schema_version": "1",
            "operation": "writing-score",
            "content_sha256": "sha256:" + "a" * 64,
            "extension": ".txt",
            "byte_size": 100,
            "text_character_count": 100,
            "word_count": 30,
            "classification": "confidential",
            "data_owner_approved": True,
            "consent_confirmed": True,
            "transfer_approved": True,
            "provider_retention_acknowledged": True,
            "api_control_plane_origin": "https://api.grammarly.com",
            "presigned_upload_origin": "https://bucket.s3.amazonaws.com",
            "presigned_upload_origin_approved": True,
        }
        self.assertEqual(safety.audit(manifest)["decision"], "READY")
        manifest["api_control_plane_origin"] = "https://api.grammarly.com.example.test"
        self.assertEqual(safety.audit(manifest)["decision"], "BLOCKED")
        manifest["api_control_plane_origin"] = "https://api.grammarly.com"
        manifest["presigned_upload_origin"] = "https://127.0.0.1"
        self.assertEqual(safety.audit(manifest)["decision"], "BLOCKED")
        manifest["presigned_upload_origin"] = "https://bucket.s3.amazonaws.com"
        del manifest["word_count"]
        self.assertIn("text_metrics", safety.audit(manifest)["failed_checks"])

    def test_submission_gate_has_content_bound_preinspection_state(self) -> None:
        manifest = {
            "schema_version": "1",
            "operation": "writing-score",
            "content_sha256": "sha256:" + "a" * 64,
            "extension": ".txt",
            "byte_size": 100,
            "text_character_count": 100,
            "word_count": 30,
            "classification": "confidential",
            "data_owner_approved": True,
            "consent_confirmed": True,
            "transfer_approved": True,
            "provider_retention_acknowledged": True,
            "api_control_plane_origin": "https://api.grammarly.com",
            "presigned_upload_origin": None,
            "presigned_upload_origin_approved": False,
        }
        result = safety.audit(manifest)
        self.assertEqual(result["decision"], "INSPECTION_READY")
        self.assertEqual(
            result["pending_checks"],
            ["presigned_upload_origin", "presigned_upload_origin_approved"],
        )

    def test_submission_gate_blocks_restricted_and_raw_content(self) -> None:
        with self.assertRaisesRegex(safety.AuditError, "raw-content"):
            safety.audit({"raw_text": "sensitive document"})
        base = {
            "schema_version": "1",
            "operation": "plagiarism",
            "content_sha256": "sha256:" + "b" * 64,
            "extension": ".docx",
            "byte_size": 1,
            "classification": "restricted",
            "data_owner_approved": True,
            "consent_confirmed": True,
            "transfer_approved": True,
            "provider_retention_acknowledged": True,
            "api_control_plane_origin": "https://api.grammarly.com",
            "presigned_upload_origin": "https://bucket.s3.amazonaws.com",
            "presigned_upload_origin_approved": True,
        }
        self.assertIn("classification", safety.audit(base)["failed_checks"])

    def test_pending_receipt_at_cap_stops(self) -> None:
        result = reliability.classify({"status": "PENDING", "attempts": 3, "max_attempts": 3})
        self.assertEqual(result["classification"], "ATTEMPT_CAP_REACHED")

    def test_license_plan_requires_keyed_pseudonyms_and_snapshot_order(self) -> None:
        snapshot = {
            "snapshot_version": 1,
            "snapshot_generated_at": "2026-09-04T00:00:00Z",
            "inactive_before": "2026-09-01T00:00:00Z",
            "pseudonymization_attestation": {
                "scheme": "HMAC-SHA256",
                "key_reference": "org-license-audit",
                "key_version": "v1",
                "producer_attested": True,
            },
            "users": [
                {
                    "resource_id_hmac_sha256": "c" * 64,
                    "last_activity_at": "2026-08-01T00:00:00Z",
                    "is_admin": False,
                },
                {
                    "resource_id_hmac_sha256": "d" * 64,
                    "last_activity_at": "2026-01-01T00:00:00Z",
                    "is_admin": True,
                },
            ],
        }
        result = license_governor.analyze(snapshot)
        self.assertEqual(result["candidate_count"], 1)
        self.assertEqual(result["excluded_admin_count"], 1)
        self.assertIn("resource_id_hmac_sha256", result["candidates"][0])
        snapshot["inactive_before"] = "2026-09-05T00:00:00Z"
        with self.assertRaisesRegex(license_governor.SnapshotError, "cannot be later"):
            license_governor.analyze(snapshot)

    def test_license_plan_rejects_unattested_digest(self) -> None:
        snapshot = {
            "snapshot_version": 1,
            "snapshot_generated_at": "2026-09-04T00:00:00Z",
            "inactive_before": "2026-09-01T00:00:00Z",
            "pseudonymization_attestation": {
                "scheme": "SHA-256",
                "key_reference": "none",
                "key_version": "none",
                "producer_attested": False,
            },
            "users": [],
        }
        with self.assertRaisesRegex(license_governor.SnapshotError, "HMAC-SHA256"):
            license_governor.analyze(snapshot)


class GrammarlyPackShapeTests(unittest.TestCase):
    def test_curated_document_evaluator_is_self_contained(self) -> None:
        source_scripts = PACK / "skills" / "grammarly-document-evaluator" / "scripts"
        curated_scripts = CURATED / "grammarly-document-evaluator" / "scripts"
        safety_source = PACK / "skills" / "grammarly-data-safety-guardian" / "scripts" / "audit_submission_manifest.py"
        self.assertEqual(
            (source_scripts / "audit_submission_manifest.py").read_bytes(),
            safety_source.read_bytes(),
        )
        for filename in (
            "grammarly_api.py",
            "audit_submission_manifest.py",
            "run_document_evaluation.py",
        ):
            self.assertEqual(
                (curated_scripts / filename).read_bytes(),
                (source_scripts / filename).read_bytes(),
            )

        with tempfile.TemporaryDirectory() as directory:
            document = Path(directory) / "input.txt"
            document.write_text(" ".join(["approved"] * 30), encoding="utf-8")
            clean_env = {key: value for key, value in os.environ.items() if not key.startswith("GRAMMARLY_")}
            clean_env["PYTHONDONTWRITEBYTECODE"] = "1"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(curated_scripts / "run_document_evaluation.py"),
                    "--operation",
                    "writing-score",
                    "--file",
                    str(document),
                ],
                check=True,
                capture_output=True,
                text=True,
                env=clean_env,
            )
        self.assertEqual(json.loads(completed.stdout)["mode"], "dry-run")

    def test_exact_v2_skill_set_and_frontmatter_names(self) -> None:
        actual = {path.parent.name for path in (PACK / "skills").glob("*/SKILL.md")}
        self.assertEqual(actual, EXPECTED_SKILLS)
        for skill_id in actual:
            text = (PACK / "skills" / skill_id / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn(f"name: {skill_id}\n", text)
            self.assertIn("version: 2.0.0", text)
            self.assertNotIn("compatibility: Designed for Claude Code", text)

    def test_migration_map_covers_every_retired_id(self) -> None:
        migration = json.loads((PACK / "migration-map.json").read_text(encoding="utf-8"))
        self.assertEqual(set(migration["retired"]), RETIRED_SKILLS)
        destinations = {item for values in migration["retired"].values() for item in values}
        self.assertLessEqual(destinations, EXPECTED_SKILLS)
        self.assertTrue(RETIRED_SKILLS.isdisjoint(EXPECTED_SKILLS))

    def test_every_skill_has_script_references_and_eval(self) -> None:
        for skill_id in EXPECTED_SKILLS:
            directory = PACK / "skills" / skill_id
            self.assertTrue((directory / "eval-spec.yaml").is_file(), skill_id)
            self.assertTrue(any((directory / "scripts").glob("*.py")), skill_id)
            self.assertTrue(any((directory / "references").glob("*.md")), skill_id)

    def test_removed_unsafe_contracts_are_not_in_active_pack(self) -> None:
        active = "\n".join(
            path.read_text(encoding="utf-8", errors="replace")
            for root in (PACK / "shared", PACK / "skills")
            for path in root.rglob("*.py")
        )
        for unsupported in (
            "api.grammarly.com/oauth/token",
            "/v1/check",
            "/v1/usage",
            "/v1/account",
            "overallScore",
        ):
            self.assertNotIn(unsupported, active)

    def test_document_cli_is_dry_run_and_hash_gated(self) -> None:
        script = PACK / "skills" / "grammarly-document-evaluator" / "scripts" / "run_document_evaluation.py"
        with tempfile.TemporaryDirectory() as directory:
            document = Path(directory) / "input.txt"
            document.write_text(" ".join(["approved"] * 30), encoding="utf-8")
            clean_env = {key: value for key, value in os.environ.items() if not key.startswith("GRAMMARLY_")}
            dry = subprocess.run(
                [sys.executable, str(script), "--operation", "writing-score", "--file", str(document)],
                check=True,
                capture_output=True,
                text=True,
                env=clean_env,
            )
            payload = json.loads(dry.stdout)
            self.assertEqual(payload["mode"], "dry-run")
            attempted = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--operation",
                    "writing-score",
                    "--file",
                    str(document),
                    "--execute",
                    "--confirm-content-sha256",
                    "sha256:" + "0" * 64,
                ],
                check=False,
                capture_output=True,
                text=True,
                env=clean_env,
            )
        self.assertEqual(attempted.returncode, 2)
        self.assertIn("exact dry-run content digest", attempted.stderr)
        self.assertNotIn("approved approved", dry.stdout + attempted.stderr)

    def test_evaluator_inspects_origin_without_uploading(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            document = root / "input.txt"
            document.write_text(" ".join(["approved"] * 30), encoding="utf-8")
            metadata = api.read_document(str(document))[1]
            manifest = {
                "schema_version": "1",
                "operation": "writing-score",
                "content_sha256": metadata["content_sha256"],
                "extension": metadata["extension"],
                "byte_size": metadata["byte_size"],
                "text_character_count": metadata["character_count"],
                "word_count": metadata["word_count"],
                "classification": "confidential",
                "data_owner_approved": True,
                "consent_confirmed": True,
                "transfer_approved": True,
                "provider_retention_acknowledged": True,
                "api_control_plane_origin": "https://api.grammarly.com",
                "presigned_upload_origin": None,
                "presigned_upload_origin_approved": False,
            }
            manifest_path = root / "inspection-approval.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            args = evaluator.parser().parse_args(
                [
                    "--operation",
                    "writing-score",
                    "--file",
                    str(document),
                    "--inspect-upload-origin",
                    "--confirm-content-sha256",
                    metadata["content_sha256"],
                    "--approval-manifest",
                    str(manifest_path),
                ]
            )
            with (
                patch.object(evaluator, "obtain_access_token", return_value="opaque"),
                patch.object(
                    evaluator,
                    "create_document_job",
                    return_value=(
                        "123e4567-e89b-12d3-a456-426614174000",
                        "https://bucket.s3.amazonaws.com/object?sig=opaque",
                    ),
                ),
                patch.object(
                    evaluator,
                    "validated_upload_origin",
                    return_value="https://bucket.s3.amazonaws.com",
                ),
                patch.object(evaluator, "upload_document") as upload,
            ):
                result = evaluator.run(args)
        self.assertEqual(result["status"], "UPLOAD_ORIGIN_APPROVAL_REQUIRED")
        self.assertEqual(result["upload_origin"], "https://bucket.s3.amazonaws.com")
        self.assertTrue(result["presigned_upload_url_sha256"].startswith("sha256:"))
        self.assertFalse(result["document_uploaded"])
        upload.assert_not_called()

    def test_evaluator_requires_inspection_approval_before_oauth(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            document = Path(directory) / "input.txt"
            document.write_text(" ".join(["approved"] * 30), encoding="utf-8")
            metadata = api.read_document(str(document))[1]
            args = evaluator.parser().parse_args(
                [
                    "--operation",
                    "writing-score",
                    "--file",
                    str(document),
                    "--inspect-upload-origin",
                    "--confirm-content-sha256",
                    metadata["content_sha256"],
                ]
            )
            with patch.object(evaluator, "obtain_access_token") as oauth:
                with self.assertRaisesRegex(evaluator.GrammarlyContractError, "require a data-safety"):
                    evaluator.run(args)
            oauth.assert_not_called()

    def test_evaluator_requires_bound_ready_manifest_before_oauth(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            document = root / "input.txt"
            document.write_text(" ".join(["approved"] * 30), encoding="utf-8")
            metadata = api.read_document(str(document))[1]
            manifest = {
                "schema_version": "1",
                "operation": "plagiarism",
                "content_sha256": metadata["content_sha256"],
                "extension": metadata["extension"],
                "byte_size": metadata["byte_size"],
                "text_character_count": metadata["character_count"],
                "word_count": metadata["word_count"],
                "classification": "confidential",
                "data_owner_approved": True,
                "consent_confirmed": True,
                "transfer_approved": True,
                "provider_retention_acknowledged": True,
                "api_control_plane_origin": "https://api.grammarly.com",
                "presigned_upload_origin": "https://bucket.s3.amazonaws.com",
                "presigned_upload_origin_approved": True,
            }
            manifest_path = root / "approval.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            args = evaluator.parser().parse_args(
                [
                    "--operation",
                    "writing-score",
                    "--file",
                    str(document),
                    "--execute",
                    "--confirm-content-sha256",
                    metadata["content_sha256"],
                    "--approval-manifest",
                    str(manifest_path),
                ]
            )
            with patch.object(evaluator, "obtain_access_token") as oauth:
                with self.assertRaisesRegex(evaluator.GrammarlyContractError, "not bound"):
                    evaluator.run(args)
            oauth.assert_not_called()

    def test_evaluator_uploads_only_after_bound_origin_approval(self) -> None:
        request_id = "123e4567-e89b-12d3-a456-426614174000"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            document = root / "input.txt"
            document.write_text(" ".join(["approved"] * 30), encoding="utf-8")
            metadata = api.read_document(str(document))[1]
            manifest = {
                "schema_version": "1",
                "operation": "writing-score",
                "content_sha256": metadata["content_sha256"],
                "extension": metadata["extension"],
                "byte_size": metadata["byte_size"],
                "text_character_count": metadata["character_count"],
                "word_count": metadata["word_count"],
                "classification": "confidential",
                "data_owner_approved": True,
                "consent_confirmed": True,
                "transfer_approved": True,
                "provider_retention_acknowledged": True,
                "api_control_plane_origin": "https://api.grammarly.com",
                "presigned_upload_origin": "https://bucket.s3.amazonaws.com",
                "presigned_upload_origin_approved": True,
            }
            manifest_path = root / "approval.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            args = evaluator.parser().parse_args(
                [
                    "--operation",
                    "writing-score",
                    "--file",
                    str(document),
                    "--execute",
                    "--confirm-content-sha256",
                    metadata["content_sha256"],
                    "--approval-manifest",
                    str(manifest_path),
                ]
            )
            completed = {
                "score_request_id": request_id,
                "status": "COMPLETED",
                "score": {
                    "general_score": 0.9,
                    "engagement": 0.8,
                    "correctness": 0.7,
                    "delivery": 0.6,
                    "clarity": 0.5,
                },
            }
            with (
                patch.object(evaluator, "obtain_access_token", return_value="opaque"),
                patch.object(
                    evaluator,
                    "create_document_job",
                    return_value=(request_id, "https://bucket.s3.amazonaws.com/object?sig=opaque"),
                ),
                patch.object(
                    evaluator,
                    "validated_upload_origin",
                    return_value="https://bucket.s3.amazonaws.com",
                ),
                patch.object(evaluator, "upload_document") as upload,
                patch.object(evaluator, "get_document_job", return_value=completed),
            ):
                result = evaluator.run(args)
        self.assertEqual(result["status"], "COMPLETED")
        self.assertTrue(result["document_uploaded"])
        self.assertEqual(result["approved_upload_origin"], "https://bucket.s3.amazonaws.com")
        upload.assert_called_once()
        self.assertEqual(upload.call_args.kwargs["approved_origin"], "https://bucket.s3.amazonaws.com")

    def test_evaluator_aborts_if_provider_origin_changes_after_approval(self) -> None:
        request_id = "123e4567-e89b-12d3-a456-426614174000"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            document = root / "input.txt"
            document.write_text(" ".join(["approved"] * 30), encoding="utf-8")
            metadata = api.read_document(str(document))[1]
            manifest = {
                "schema_version": "1",
                "operation": "writing-score",
                "content_sha256": metadata["content_sha256"],
                "extension": metadata["extension"],
                "byte_size": metadata["byte_size"],
                "text_character_count": metadata["character_count"],
                "word_count": metadata["word_count"],
                "classification": "confidential",
                "data_owner_approved": True,
                "consent_confirmed": True,
                "transfer_approved": True,
                "provider_retention_acknowledged": True,
                "api_control_plane_origin": "https://api.grammarly.com",
                "presigned_upload_origin": "https://approved.s3.amazonaws.com",
                "presigned_upload_origin_approved": True,
            }
            manifest_path = root / "approval.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            args = evaluator.parser().parse_args(
                [
                    "--operation",
                    "writing-score",
                    "--file",
                    str(document),
                    "--execute",
                    "--confirm-content-sha256",
                    metadata["content_sha256"],
                    "--approval-manifest",
                    str(manifest_path),
                ]
            )
            with (
                patch.object(evaluator, "obtain_access_token", return_value="opaque"),
                patch.object(
                    evaluator,
                    "create_document_job",
                    return_value=(request_id, "https://changed.s3.amazonaws.com/object?sig=opaque"),
                ),
                patch.object(
                    evaluator,
                    "validated_upload_origin",
                    return_value="https://changed.s3.amazonaws.com",
                ),
                patch.object(evaluator, "upload_document") as upload,
            ):
                with self.assertRaisesRegex(evaluator.GrammarlyContractError, "did not match"):
                    evaluator.run(args)
            upload.assert_not_called()


if __name__ == "__main__":
    unittest.main()
