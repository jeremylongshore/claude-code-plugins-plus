#!/usr/bin/env python3
"""location_router.py — multi-location Podium dispatch with per-location credential
isolation, pre-flight ownership verification, structured audit log, idempotent
onboarding, and per-location rate-limit isolation.

Library entry point:
    router = LocationRouter.from_credentials_file(
        "./config/locations.json",
        audit_log_path="./audit-log/podium-router.jsonl",
    )
    client = router.get_client(location_uid="{your-location-uid}")
    r = await client.call("POST", "/v4/contacts", json={...})

This module is dependency-light: stdlib + httpx. PodiumAuth / TokenBucket are imported
from sibling skills (podium-auth, podium-rate-limit-survival). When those packages are
not installed, the small stub classes at the bottom of this file are used so the
router remains testable in isolation.
"""

from __future__ import annotations
import asyncio
import json
import os
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx

LOCATIONS_URL = "https://api.podium.com/v4/locations"
VERIFY_TTL_SECONDS = 3600


# ---------------------------------------------------------------------------
# Error types — kept here so callers do not need a separate import
# ---------------------------------------------------------------------------
class UnknownLocationError(KeyError):
    """Raised when get_client() receives a location_uid not in the credentials map."""

    def __init__(self, location_uid: str):
        super().__init__(
            f"No credentials for location_uid={location_uid}. "
            f"Run onboard_location.py to register, then reload the router."
        )
        self.location_uid = location_uid


class LocationNotInScopeError(Exception):
    """Raised when GET /v4/locations does not contain the requested location_uid."""

    def __init__(self, location_uid: str, scope_uids: list[str]):
        super().__init__(
            f"location_uid={location_uid} not in /v4/locations scope. "
            f"Token sees {len(scope_uids)} locations; this UID is not one of them."
        )
        self.location_uid = location_uid
        self.scope_uids = scope_uids


class LocationVerificationError(Exception):
    """Raised when GET /v4/locations returns a non-200."""


class OnboardingPartialFailure(Exception):
    """Raised when one or more locations in a bulk onboard failed."""


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class LocationCredential:
    location_uid: str
    org_slug: str
    client_id: str
    client_secret: str
    refresh_token_file: str
    verified_at: float = 0.0
    rate_limit_capacity: int = 30
    rate_limit_refill_per_second: float = 5.0


@dataclass
class OnboardingResult:
    location_uid: str
    status: str  # "onboarded" | "skipped_existing" | "failed"
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# The router
# ---------------------------------------------------------------------------
class LocationRouter:
    """Holds one PodiumAuth + TokenBucket per location_uid. Pre-flight-verifies every
    call. Emits one JSONL audit line per call. Idempotent bulk onboarding."""

    def __init__(self, audit_log_path: str):
        self._creds: dict[str, LocationCredential] = {}
        self._auths: dict[str, "PodiumAuth"] = {}
        self._buckets: dict[str, "TokenBucket"] = {}
        self._verify_locks: dict[str, asyncio.Lock] = {}
        self._audit_log_path = audit_log_path
        self._credentials_map_path: Optional[Path] = None

    # -- construction ------------------------------------------------------
    @classmethod
    def from_credentials_file(cls, path: str, audit_log_path: str) -> "LocationRouter":
        router = cls(audit_log_path=audit_log_path)
        router._credentials_map_path = Path(path)
        raw = json.loads(Path(path).read_text())
        for uid, entry in raw.items():
            cred = LocationCredential(
                location_uid=uid,
                org_slug=entry["org_slug"],
                client_id=entry["client_id"],
                client_secret=entry["client_secret"],
                refresh_token_file=entry["refresh_token_file"],
                rate_limit_capacity=entry.get("rate_limit", {}).get("capacity", 30),
                rate_limit_refill_per_second=entry.get("rate_limit", {}).get("refill_per_second", 5.0),
            )
            router._creds[uid] = cred
        return router

    # -- public API --------------------------------------------------------
    def get_client(self, location_uid: str) -> "PodiumLocationClient":
        cred = self._creds.get(location_uid)
        if not cred:
            raise UnknownLocationError(location_uid)
        if location_uid not in self._auths:
            self._auths[location_uid] = PodiumAuth(
                client_id=cred.client_id,
                client_secret=cred.client_secret,
                refresh_token=_load_refresh_token(cred.refresh_token_file),
            )
            self._buckets[location_uid] = TokenBucket(
                capacity=cred.rate_limit_capacity,
                refill_per_second=cred.rate_limit_refill_per_second,
            )
            self._verify_locks[location_uid] = asyncio.Lock()
        return PodiumLocationClient(location_uid=location_uid, router=self)

    async def ensure_location_verified(self, location_uid: str) -> None:
        cred = self._creds[location_uid]
        if time.time() - cred.verified_at < VERIFY_TTL_SECONDS:
            return
        async with self._verify_locks[location_uid]:
            if time.time() - cred.verified_at < VERIFY_TTL_SECONDS:
                return
            auth = self._auths[location_uid]
            token = await auth.get_token()
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.get(
                    LOCATIONS_URL,
                    headers={"Authorization": f"Bearer {token}"},
                )
            if r.status_code != 200:
                raise LocationVerificationError(f"GET /v4/locations failed status={r.status_code}")
            scope = [loc["uid"] for loc in r.json().get("locations", [])]
            if location_uid not in scope:
                raise LocationNotInScopeError(location_uid, scope)
            cred.verified_at = time.time()

    def emit_audit(
        self, *, location_uid: str, endpoint: str, method: str, status: int, latency_ms: float, request_id: str
    ) -> None:
        cred = self._creds[location_uid]
        record = {
            "ts": time.time(),
            "location_uid": location_uid,
            "org_slug": cred.org_slug,
            "endpoint": endpoint,
            "method": method,
            "status": status,
            "request_id": request_id,
            "latency_ms": round(latency_ms, 2),
        }
        os.makedirs(os.path.dirname(self._audit_log_path) or ".", exist_ok=True)
        with open(self._audit_log_path, "a") as f:
            f.write(json.dumps(record) + "\n")

    async def onboard_locations(self, new: list[LocationCredential]) -> list[OnboardingResult]:
        results: list[OnboardingResult] = []
        for cred in new:
            if cred.location_uid in self._creds:
                results.append(OnboardingResult(cred.location_uid, "skipped_existing"))
                continue
            try:
                self._persist_credential(cred)
                self._auths[cred.location_uid] = PodiumAuth(
                    client_id=cred.client_id,
                    client_secret=cred.client_secret,
                    refresh_token=_load_refresh_token(cred.refresh_token_file),
                )
                self._buckets[cred.location_uid] = TokenBucket(
                    capacity=cred.rate_limit_capacity,
                    refill_per_second=cred.rate_limit_refill_per_second,
                )
                self._verify_locks[cred.location_uid] = asyncio.Lock()
                self._creds[cred.location_uid] = cred
                await self.ensure_location_verified(cred.location_uid)
                results.append(OnboardingResult(cred.location_uid, "onboarded"))
            except Exception as e:
                self._creds.pop(cred.location_uid, None)
                self._auths.pop(cred.location_uid, None)
                self._buckets.pop(cred.location_uid, None)
                self._verify_locks.pop(cred.location_uid, None)
                results.append(OnboardingResult(cred.location_uid, "failed", str(e)))
        return results

    # -- internals ---------------------------------------------------------
    def _persist_credential(self, cred: LocationCredential) -> None:
        """Atomically write the new credential entry to the credentials-map file."""
        if not self._credentials_map_path:
            return
        path = self._credentials_map_path
        current = json.loads(path.read_text()) if path.exists() else {}
        current[cred.location_uid] = {
            "org_slug": cred.org_slug,
            "client_id": cred.client_id,
            "client_secret": cred.client_secret,
            "refresh_token_file": cred.refresh_token_file,
            "rate_limit": {
                "capacity": cred.rate_limit_capacity,
                "refill_per_second": cred.rate_limit_refill_per_second,
            },
        }
        fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".locations.")
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(current, f, indent=2)
            os.chmod(tmp, 0o600)
            os.replace(tmp, path)
        except Exception:
            try:
                os.unlink(tmp)
            except FileNotFoundError:
                pass
            raise

    def bucket_for(self, location_uid: str) -> "TokenBucket":
        return self._buckets[location_uid]

    def auth_for(self, location_uid: str) -> "PodiumAuth":
        return self._auths[location_uid]


# ---------------------------------------------------------------------------
# The client wrapper
# ---------------------------------------------------------------------------
class PodiumLocationClient:
    """Single-location dispatch. Pre-flight-verifies, acquires the bucket, fetches the
    token, makes the call, and emits the audit line — in that exact order."""

    def __init__(self, location_uid: str, router: LocationRouter):
        self._location_uid = location_uid
        self._router = router

    async def call(self, method: str, path: str, **kwargs) -> httpx.Response:
        await self._router.ensure_location_verified(self._location_uid)
        bucket = self._router.bucket_for(self._location_uid)
        await bucket.acquire()

        request_id = uuid.uuid4().hex
        auth = self._router.auth_for(self._location_uid)
        token = await auth.get_token()

        start = time.monotonic()
        status = 0
        try:
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.request(
                    method,
                    f"https://api.podium.com{path}",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "X-Request-ID": request_id,
                        **kwargs.pop("headers", {}),
                    },
                    **kwargs,
                )
                status = r.status_code
                return r
        finally:
            self._router.emit_audit(
                location_uid=self._location_uid,
                endpoint=path,
                method=method,
                status=status,
                latency_ms=(time.monotonic() - start) * 1000,
                request_id=request_id,
            )


# ---------------------------------------------------------------------------
# Helpers + stubs
# ---------------------------------------------------------------------------
def _load_refresh_token(path: str) -> str:
    return json.loads(Path(path).read_text())["refresh_token"]


# Importing the real upstream classes if available; otherwise small stubs so this
# module is runnable in isolation for tests.
try:
    from podium_auth import PodiumAuth  # type: ignore
except Exception:

    class PodiumAuth:
        def __init__(self, client_id: str, client_secret: str, refresh_token: str):
            self.client_id = client_id
            self.client_secret = client_secret
            self.refresh_token = refresh_token

        async def get_token(self) -> str:
            # Stub — production deployments install podium-auth.
            return "stub-access-token"


try:
    from podium_rate_limit import TokenBucket  # type: ignore
except Exception:

    class TokenBucket:
        def __init__(self, capacity: int, refill_per_second: float):
            self.capacity = capacity
            self.refill_per_second = refill_per_second
            self._tokens = capacity
            self._last_refill = time.monotonic()
            self._lock = asyncio.Lock()

        async def acquire(self, n: int = 1) -> None:
            async with self._lock:
                now = time.monotonic()
                elapsed = now - self._last_refill
                self._tokens = min(
                    self.capacity,
                    self._tokens + elapsed * self.refill_per_second,
                )
                self._last_refill = now
                if self._tokens < n:
                    needed = (n - self._tokens) / self.refill_per_second
                    await asyncio.sleep(needed)
                    self._tokens = 0
                else:
                    self._tokens -= n
