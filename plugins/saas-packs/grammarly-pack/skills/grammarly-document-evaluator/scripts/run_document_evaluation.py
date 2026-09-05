#!/usr/bin/env python3
"""Plan or explicitly execute one Grammarly document evaluation."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from grammarly_api import (  # noqa: E402
    DOCUMENT_CONTRACTS,
    SCORE_RETENTION_DAYS,
    DOCUMENT_RETENTION_MAX_HOURS,
    GrammarlyContractError,
    create_document_job,
    get_document_job,
    normalize_completed_score,
    obtain_access_token,
    read_document,
    read_small_regular_file,
    sha256_bytes,
    upload_document,
    validated_upload_origin,
)

from audit_submission_manifest import AuditError as SafetyAuditError  # noqa: E402
from audit_submission_manifest import audit as audit_submission  # noqa: E402
from audit_submission_manifest import parse_json as parse_submission_json  # noqa: E402


def validate_approval_manifest(
    path: str,
    *,
    operation: str,
    metadata: dict[str, object],
    expected_decision: str,
) -> str | None:
    """Require a content-bound safety decision before any OAuth request."""

    raw = read_small_regular_file(path, max_bytes=65_536, label="approval manifest")
    try:
        document = parse_submission_json(raw.decode("utf-8"))
        decision = audit_submission(document)
    except (UnicodeDecodeError, SafetyAuditError, RecursionError) as exc:
        raise GrammarlyContractError("approval manifest was invalid or unsafe") from exc
    if decision["decision"] != expected_decision:
        raise GrammarlyContractError(f"approval manifest did not produce {expected_decision}")
    expected: dict[str, object] = {
        "operation": operation,
        "content_sha256": metadata["content_sha256"],
        "extension": metadata["extension"],
        "byte_size": metadata["byte_size"],
    }
    if metadata.get("character_count") is not None:
        expected["text_character_count"] = metadata["character_count"]
        expected["word_count"] = metadata["word_count"]
    if any(document.get(key) != value for key, value in expected.items()):
        raise GrammarlyContractError("approval manifest was not bound to this operation and document")
    origin = document["presigned_upload_origin"]
    return origin if isinstance(origin, str) else None


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Validate a document locally, or explicitly submit it to a documented Grammarly API."
    )
    result.add_argument("--operation", choices=tuple(DOCUMENT_CONTRACTS), required=True)
    result.add_argument("--file", required=True)
    mode = result.add_mutually_exclusive_group()
    mode.add_argument(
        "--inspect-upload-origin",
        action="store_true",
        help="create a provider request and reveal only its upload origin; do not upload",
    )
    mode.add_argument("--execute", action="store_true", help="perform the approved OAuth/create/upload/poll flow")
    result.add_argument(
        "--confirm-content-sha256",
        help="exact sha256:... digest printed by dry-run; required for inspection and execution",
    )
    result.add_argument(
        "--approval-manifest",
        help="closed metadata-only manifest required for origin inspection and execution",
    )
    result.add_argument("--poll-interval-seconds", type=float, default=2.0)
    result.add_argument("--max-polls", type=int, default=60)
    return result


def run(args: argparse.Namespace) -> dict[str, object]:
    contract = DOCUMENT_CONTRACTS[args.operation]
    document, metadata = read_document(args.file)
    plan: dict[str, object] = {
        "schema_version": "1",
        "mode": "execute" if args.execute else "upload-origin-inspection" if args.inspect_upload_origin else "dry-run",
        "operation": contract.operation,
        "beta": contract.beta,
        "endpoint": contract.endpoint,
        "required_scopes": list(contract.scopes),
        "document": metadata,
        "provider_retention_boundary": {
            "document_max_hours": DOCUMENT_RETENTION_MAX_HOURS,
            "score_days": SCORE_RETENTION_DAYS,
        },
        "non_claims": [
            "no_public_sandbox_assumed",
            "no_processing-time_sla_assumed",
            "no_idempotent-create_retry_assumed",
        ],
    }
    if not args.execute and not args.inspect_upload_origin:
        if args.approval_manifest:
            raise GrammarlyContractError("--approval-manifest is valid only for inspection or execution")
        plan["next_action"] = "obtain INSPECTION_READY, then inspect the upload origin with the exact content digest"
        return plan

    if args.confirm_content_sha256 != metadata["content_sha256"]:
        raise GrammarlyContractError("execution requires the exact dry-run content digest")
    if not 0.5 <= args.poll_interval_seconds <= 60:
        raise GrammarlyContractError("poll interval must be between 0.5 and 60 seconds")
    if not 1 <= args.max_polls <= 300:
        raise GrammarlyContractError("max polls must be between 1 and 300")

    if not args.approval_manifest:
        raise GrammarlyContractError("inspection and execution require a data-safety approval manifest")
    expected_decision = "READY" if args.execute else "INSPECTION_READY"
    approved_upload_origin = validate_approval_manifest(
        args.approval_manifest,
        operation=contract.operation,
        metadata=metadata,
        expected_decision=expected_decision,
    )

    token = obtain_access_token(contract.scopes)
    request_id, upload_url = create_document_job(
        contract,
        filename=f"document{metadata['extension']}",
        token=token,
    )
    upload_origin = validated_upload_origin(upload_url)
    request_id_sha256 = sha256_bytes(request_id.encode("ascii"))
    if args.inspect_upload_origin:
        return {
            **plan,
            "mode": "upload-origin-inspection",
            "status": "UPLOAD_ORIGIN_APPROVAL_REQUIRED",
            "upload_origin": upload_origin,
            "presigned_upload_url_sha256": sha256_bytes(upload_url.encode("ascii")),
            "request_id_sha256": request_id_sha256,
            "document_uploaded": False,
            "next_action": "approve this exact origin in the data-safety manifest, then rerun execution",
        }
    if approved_upload_origin is None or approved_upload_origin != upload_origin:
        raise GrammarlyContractError("provider-issued upload origin did not match the exact approved origin")
    upload_document(upload_url, document, approved_origin=approved_upload_origin)

    final: dict[str, object] | None = None
    for _ in range(args.max_polls):
        payload = get_document_job(contract, request_id=request_id, token=token)
        if payload["status"] != "PENDING":
            final = payload
            break
        time.sleep(args.poll_interval_seconds)
    if final is None:
        raise GrammarlyContractError("local polling budget exhausted; provider processing limit is undocumented")

    result: dict[str, object] = {
        **plan,
        "request_id_sha256": request_id_sha256,
        "approved_upload_origin": upload_origin,
        "presigned_upload_url_sha256": sha256_bytes(upload_url.encode("ascii")),
        "document_uploaded": True,
        "status": final["status"],
    }
    if final["status"] == "COMPLETED":
        result["score"] = normalize_completed_score(contract, final)
    else:
        result["score"] = None
        result["failure_reason"] = "provider_reported_failed; inspect only through an approved redacted channel"
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        result = run(args)
    except GrammarlyContractError as exc:
        print(f"operator error: {exc}", file=sys.stderr)
        return 2
    json.dump(result, sys.stdout, sort_keys=True, indent=2)
    sys.stdout.write("\n")
    return 0 if result.get("status") != "FAILED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
