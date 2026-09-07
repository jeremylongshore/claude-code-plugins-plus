#!/usr/bin/env python3
"""Small, dependency-free Grammarly API contract library.

The library has no ambient network behavior. Callers must invoke the explicit
functions below and provide credentials through their process environment.
"""

from __future__ import annotations

import hashlib
import http.client
import ipaddress
import json
import os
import socket
import ssl
import stat
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


TOKEN_ENDPOINT = "https://auth.grammarly.com/v4/api/oauth2/token"
API_ORIGIN = "https://api.grammarly.com"
MAX_FILE_BYTES = 4_194_304
MAX_EXTRACTED_CHARACTERS = 100_000
MIN_WORDS = 30
UPLOAD_URL_LIFETIME_SECONDS = 120
DOCUMENT_RETENTION_MAX_HOURS = 24
SCORE_RETENTION_DAYS = 30
MAX_JSON_RESPONSE_BYTES = 1_048_576
UPLOAD_PROVIDER_SUFFIX = ("amazonaws", "com")

SUPPORTED_EXTENSIONS = frozenset({".doc", ".docx", ".odt", ".txt", ".rtf"})
TERMINAL_STATUSES = frozenset({"COMPLETED", "FAILED"})
ALL_STATUSES = frozenset({"PENDING", *TERMINAL_STATUSES})


@dataclass(frozen=True)
class DocumentContract:
    operation: str
    endpoint: str
    scopes: tuple[str, str]
    result_fields: tuple[str, ...]
    beta: bool


@dataclass(frozen=True)
class UploadDestination:
    """Validated upload authority plus the addresses allowed for connection."""

    hostname: str
    port: int
    origin: str
    request_target: str
    addresses: tuple[str, ...]


DOCUMENT_CONTRACTS: Mapping[str, DocumentContract] = {
    "writing-score": DocumentContract(
        operation="writing-score",
        endpoint=f"{API_ORIGIN}/ecosystem/api/v2/scores",
        scopes=("scores-api:read", "scores-api:write"),
        result_fields=("general_score", "engagement", "correctness", "delivery", "clarity"),
        beta=False,
    ),
    "ai-detection": DocumentContract(
        operation="ai-detection",
        endpoint=f"{API_ORIGIN}/ecosystem/api/v1/ai-detection",
        scopes=("ai-detection-api:read", "ai-detection-api:write"),
        result_fields=("average_confidence", "ai_generated_percentage"),
        beta=True,
    ),
    "plagiarism": DocumentContract(
        operation="plagiarism",
        endpoint=f"{API_ORIGIN}/ecosystem/api/v1/plagiarism",
        scopes=("plagiarism-api:read", "plagiarism-api:write"),
        result_fields=("originality",),
        beta=True,
    ),
}

KNOWN_SCOPES = frozenset(
    {scope for contract in DOCUMENT_CONTRACTS.values() for scope in contract.scopes}
    | {"analytics-api:read", "users-api:read"}
)


class GrammarlyContractError(RuntimeError):
    """A bounded contract or safety failure safe to show to an operator."""


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Reject redirects so credentials and upload bytes never change destinations."""

    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> None:
        return None


def open_without_redirects(request: urllib.request.Request, *, timeout: float) -> Any:
    return urllib.request.build_opener(_NoRedirectHandler).open(request, timeout=timeout)


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def _open_regular_without_symlinks(path: Path) -> int:
    """Open a regular file through pinned directory descriptors only."""

    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
        raise GrammarlyContractError("safe component-by-component file open is unavailable")
    absolute = Path(os.path.abspath(path))
    parts = absolute.parts
    directory_fd = os.open(parts[0], os.O_RDONLY | os.O_DIRECTORY)
    try:
        for component in parts[1:-1]:
            next_fd = os.open(
                component,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=directory_fd,
            )
            os.close(directory_fd)
            directory_fd = next_fd
        descriptor = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory_fd)
    except OSError as exc:
        raise GrammarlyContractError("document could not be opened safely") from exc
    finally:
        os.close(directory_fd)
    opened = os.fstat(descriptor)
    if not stat.S_ISREG(opened.st_mode):
        os.close(descriptor)
        raise GrammarlyContractError("input must be a regular non-symlink file")
    return descriptor


def read_small_regular_file(path_value: str, *, max_bytes: int, label: str) -> bytes:
    """Read one bounded regular file without following symlink components."""

    descriptor = _open_regular_without_symlinks(Path(path_value))
    try:
        opened = os.fstat(descriptor)
        if opened.st_size <= 0:
            raise GrammarlyContractError(f"{label} must not be empty")
        if opened.st_size > max_bytes:
            raise GrammarlyContractError(f"{label} exceeds the local size limit")
        chunks: list[bytes] = []
        remaining = max_bytes + 1
        while remaining > 0:
            chunk = os.read(descriptor, min(65_536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        data = b"".join(chunks)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)

    if len(data) > max_bytes:
        raise GrammarlyContractError(f"{label} exceeds the local size limit")
    if (after.st_size, after.st_mtime_ns) != (opened.st_size, opened.st_mtime_ns):
        raise GrammarlyContractError(f"{label} changed while it was read")
    return data


def read_document(path_value: str) -> tuple[bytes, dict[str, Any]]:
    """Read one regular document without following any symlink path component."""

    path = Path(path_value)
    extension = path.suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise GrammarlyContractError("unsupported document extension")
    data = read_small_regular_file(path_value, max_bytes=MAX_FILE_BYTES, label="document")

    metadata: dict[str, Any] = {
        "content_sha256": sha256_bytes(data),
        "byte_size": len(data),
        "extension": extension,
        "extracted_text_constraints": "UNVERIFIED_UNTIL_PROVIDER_EXTRACTION",
    }
    if extension == ".txt":
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise GrammarlyContractError("text documents must be valid UTF-8") from exc
        character_count = len(text)
        word_count = len(text.split())
        if character_count > MAX_EXTRACTED_CHARACTERS:
            raise GrammarlyContractError("text exceeds the documented 100,000 character limit")
        if word_count < MIN_WORDS:
            raise GrammarlyContractError("text is below the documented 30-word minimum")
        metadata.update(
            {
                "character_count": character_count,
                "word_count": word_count,
                "extracted_text_constraints": "LOCALLY_VERIFIED_FOR_UTF8_TEXT",
            }
        )
    return data, metadata


def _validate_scopes(scopes: Sequence[str]) -> tuple[str, ...]:
    normalized = tuple(dict.fromkeys(scopes))
    if not normalized or any(scope not in KNOWN_SCOPES for scope in normalized):
        raise GrammarlyContractError("requested OAuth scope is empty or undocumented")
    return normalized


def _validate_contract(contract: DocumentContract) -> DocumentContract:
    official = DOCUMENT_CONTRACTS.get(contract.operation)
    if official is None or contract != official:
        raise GrammarlyContractError("document contract is not an exact official pack contract")
    return official


def _decode_json_response(response: Any, label: str) -> dict[str, Any]:
    try:
        raw = response.read(MAX_JSON_RESPONSE_BYTES + 1)
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError) as exc:
        raise GrammarlyContractError(f"{label} returned invalid JSON") from exc
    if len(raw) > MAX_JSON_RESPONSE_BYTES:
        raise GrammarlyContractError(f"{label} exceeded the response-size limit")
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError) as exc:
        raise GrammarlyContractError(f"{label} returned invalid JSON") from exc
    if not isinstance(payload, dict):
        raise GrammarlyContractError(f"{label} returned a non-object response")
    return payload


def _open(
    request: urllib.request.Request,
    *,
    opener: Callable[..., Any],
    timeout: float,
    label: str,
) -> Any:
    try:
        return opener(request, timeout=timeout)
    except urllib.error.HTTPError as exc:
        raise GrammarlyContractError(f"{label} failed with HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise GrammarlyContractError(f"{label} failed at the network boundary") from exc


def obtain_access_token(
    scopes: Sequence[str],
    *,
    opener: Callable[..., Any] = open_without_redirects,
    timeout: float = 30.0,
) -> str:
    normalized = _validate_scopes(scopes)
    client_id = os.environ.get("GRAMMARLY_CLIENT_ID")
    client_secret = os.environ.get("GRAMMARLY_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise GrammarlyContractError(
            "GRAMMARLY_CLIENT_ID and GRAMMARLY_CLIENT_SECRET must be supplied by the environment"
        )
    body = urllib.parse.urlencode(
        {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": ",".join(normalized),
        }
    ).encode("ascii")
    request = urllib.request.Request(
        TOKEN_ENDPOINT,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with _open(request, opener=opener, timeout=timeout, label="OAuth token request") as response:
        payload = _decode_json_response(response, "OAuth token request")
    token = payload.get("access_token")
    if not isinstance(token, str) or not token or len(token) > 16_384:
        raise GrammarlyContractError("OAuth response did not include an access token")
    return token


def validated_upload_origin(
    upload_url: str,
    *,
    resolver: Callable[..., Any] = socket.getaddrinfo,
) -> str:
    """Validate a provider-issued upload URL and return its canonical origin."""

    return _validated_upload_destination(upload_url, resolver=resolver).origin


def _is_allowed_s3_hostname(hostname: str) -> bool:
    labels = hostname.split(".")
    return (
        len(labels) >= 3
        and tuple(labels[-2:]) == UPLOAD_PROVIDER_SUFFIX
        and any(label == "s3" or label.startswith("s3-") for label in labels[:-2])
    )


def _validated_upload_destination(
    upload_url: str,
    *,
    resolver: Callable[..., Any] = socket.getaddrinfo,
) -> UploadDestination:
    """Validate one S3 upload URL and retain its approved connection addresses."""

    if (
        not isinstance(upload_url, str)
        or not upload_url.isascii()
        or any(ord(character) < 0x20 or ord(character) == 0x7F for character in upload_url)
    ):
        raise GrammarlyContractError("creation response contained an unsafe upload URL")
    parsed = urllib.parse.urlsplit(upload_url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password or parsed.fragment:
        raise GrammarlyContractError("creation response contained an unsafe upload URL")
    hostname = parsed.hostname
    if not hostname or hostname.lower() == "localhost" or hostname.lower().endswith((".localhost", ".local")):
        raise GrammarlyContractError("creation response contained an unsafe upload host")
    normalized_hostname = hostname.lower()
    if not _is_allowed_s3_hostname(normalized_hostname):
        raise GrammarlyContractError("upload host is outside the pinned S3 provider allowlist")
    try:
        port = parsed.port
    except ValueError as exc:
        raise GrammarlyContractError("creation response contained an unsafe upload port") from exc
    if port not in (None, 443):
        raise GrammarlyContractError("upload URL must use the default HTTPS port")
    try:
        resolved = resolver(hostname, 443, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise GrammarlyContractError("upload host could not be resolved safely") from exc
    if not resolved:
        raise GrammarlyContractError("upload host did not resolve")
    addresses: list[str] = []
    for item in resolved:
        try:
            address = ipaddress.ip_address(item[4][0])
        except (IndexError, ValueError, TypeError) as exc:
            raise GrammarlyContractError("upload host returned an invalid address") from exc
        if not address.is_global:
            raise GrammarlyContractError("upload host resolved to a non-public address")
        rendered = str(address)
        if rendered not in addresses:
            addresses.append(rendered)
    request_target = urllib.parse.urlunsplit(("", "", parsed.path or "/", parsed.query, ""))
    return UploadDestination(
        hostname=normalized_hostname,
        port=443,
        origin=f"https://{normalized_hostname}",
        request_target=request_target,
        addresses=tuple(addresses),
    )


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    """Connect to one validated address while verifying TLS for the URL host."""

    def __init__(self, destination: UploadDestination, address: str, *, timeout: float) -> None:
        super().__init__(
            destination.hostname,
            port=destination.port,
            timeout=timeout,
            context=ssl.create_default_context(),
        )
        self._pinned_address = address

    def connect(self) -> None:
        try:
            raw_socket = socket.create_connection(
                (self._pinned_address, self.port),
                self.timeout,
                self.source_address,
            )
            self.sock = self._context.wrap_socket(raw_socket, server_hostname=self.host)
        except Exception:
            if "raw_socket" in locals():
                raw_socket.close()
            raise


def create_document_job(
    contract: DocumentContract,
    *,
    filename: str,
    token: str,
    opener: Callable[..., Any] = open_without_redirects,
    timeout: float = 30.0,
) -> tuple[str, str]:
    _validate_contract(contract)
    body = canonical_json({"filename": filename})
    request = urllib.request.Request(
        contract.endpoint,
        data=body,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "tons-of-skills-grammarly-pack/2.0",
        },
        method="POST",
    )
    with _open(request, opener=opener, timeout=timeout, label="document job creation") as response:
        payload = _decode_json_response(response, "document job creation")
    request_id = payload.get("score_request_id")
    upload_url = payload.get("file_upload_url")
    try:
        normalized_id = str(uuid.UUID(str(request_id)))
    except (ValueError, AttributeError) as exc:
        raise GrammarlyContractError("creation response contained an invalid request identifier") from exc
    if not isinstance(upload_url, str):
        raise GrammarlyContractError("creation response omitted the upload URL")
    validated_upload_origin(upload_url)
    return normalized_id, upload_url


def upload_document(
    upload_url: str,
    data: bytes,
    *,
    approved_origin: str,
    connection_factory: Callable[..., Any] = _PinnedHTTPSConnection,
    resolver: Callable[..., Any] = socket.getaddrinfo,
    timeout: float = 60.0,
) -> None:
    destination = _validated_upload_destination(upload_url, resolver=resolver)
    if approved_origin != destination.origin:
        raise GrammarlyContractError("upload origin did not match the exact approved origin")
    connection = connection_factory(destination, destination.addresses[0], timeout=timeout)
    try:
        connection.request("PUT", destination.request_target, body=data, headers={})
        response = connection.getresponse()
        status = response.status
    except (OSError, ssl.SSLError, http.client.HTTPException) as exc:
        raise GrammarlyContractError("document upload failed at the pinned TLS boundary") from exc
    finally:
        connection.close()
    if not 200 <= int(status) < 300:
        raise GrammarlyContractError(f"document upload failed with HTTP {status}")


def get_document_job(
    contract: DocumentContract,
    *,
    request_id: str,
    token: str,
    opener: Callable[..., Any] = open_without_redirects,
    timeout: float = 30.0,
) -> dict[str, Any]:
    _validate_contract(contract)
    try:
        normalized_id = str(uuid.UUID(request_id))
    except ValueError as exc:
        raise GrammarlyContractError("poll request identifier is invalid") from exc
    request = urllib.request.Request(
        f"{contract.endpoint}/{normalized_id}",
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "tons-of-skills-grammarly-pack/2.0",
        },
        method="GET",
    )
    with _open(request, opener=opener, timeout=timeout, label="document job poll") as response:
        payload = _decode_json_response(response, "document job poll")
    status_value = payload.get("status")
    if status_value not in ALL_STATUSES:
        raise GrammarlyContractError("poll response contained an undocumented status")
    if payload.get("score_request_id") != normalized_id:
        raise GrammarlyContractError("poll response identifier did not match the request")
    return payload


def normalize_completed_score(contract: DocumentContract, payload: Mapping[str, Any]) -> dict[str, float]:
    _validate_contract(contract)
    if payload.get("status") != "COMPLETED":
        raise GrammarlyContractError("only a completed job can be normalized")
    score = payload.get("score")
    if not isinstance(score, dict):
        raise GrammarlyContractError("completed job did not include a score object")
    if set(score) != set(contract.result_fields):
        raise GrammarlyContractError("score object did not match the documented contract")
    normalized: dict[str, float] = {}
    for field in contract.result_fields:
        value = score[field]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise GrammarlyContractError("score object contained a non-numeric value")
        number = float(value)
        if not 0.0 <= number <= 1.0:
            raise GrammarlyContractError("score value fell outside the documented 0-to-1 range")
        normalized[field] = number
    return normalized
