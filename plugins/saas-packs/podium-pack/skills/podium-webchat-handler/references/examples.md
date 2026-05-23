# Examples — podium-webchat-handler

Ten complete worked examples. Each is runnable end-to-end with the env vars and prerequisites listed at the top of the snippet.

## 1. Normalize phones at the widget edge

```python
# pip install phonenumbers
import phonenumbers
from phonenumbers import NumberParseException, PhoneNumberFormat, is_valid_number

class PhoneValidationError(Exception):
    pass

def normalize_phone(raw: str, default_country: str = "AU") -> str:
    try:
        parsed = phonenumbers.parse(raw, default_country)
    except NumberParseException as e:
        raise PhoneValidationError(f"unparseable: {raw!r}: {e}")
    if not is_valid_number(parsed):
        raise PhoneValidationError(f"invalid for {default_country}: {raw!r}")
    return phonenumbers.format_number(parsed, PhoneNumberFormat.E164)

# Sanity checks
assert normalize_phone("0412 345 678", "AU") == "+61412345678"
assert normalize_phone("(415) 555-1234", "US") == "+14155551234"
assert normalize_phone("+61 412 345 678", "AU") == "+61412345678"
```

## 2. CLI: normalize one phone with carrier metadata

```bash
python3 scripts/phone_normalize.py --phone "0412 345 678" --default-country AU --output json
```

Output:

```json
{
  "input": "0412 345 678",
  "e164": "+61412345678",
  "country": "AU",
  "country_code": 61,
  "national_number": 412345678,
  "is_valid": true,
  "is_possible": true,
  "number_type": "MOBILE",
  "carrier": "Telstra"
}
```

## 3. Race-tolerant contact upsert

```python
# env: PODIUM_CLIENT_ID, PODIUM_CLIENT_SECRET, PODIUM_REFRESH_TOKEN_FILE
import httpx
from podium_auth import PodiumAuth

class WebchatError(Exception):
    pass

async def upsert_contact_by_phone(
    auth: PodiumAuth, phone_e164: str, location_uid: str,
    first_name: str | None = None, last_name: str | None = None,
) -> dict:
    token = await auth.get_token()
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(
            "https://api.podium.com/v4/contacts",
            headers=headers,
            params={"phone": phone_e164, "location_uid": location_uid},
        )
    if r.status_code == 200 and r.json().get("data"):
        return r.json()["data"][0]

    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.post(
            "https://api.podium.com/v4/contacts",
            headers=headers,
            json={"phone": phone_e164, "location_uid": location_uid,
                  "first_name": first_name, "last_name": last_name},
        )
    if r.status_code in (200, 201):
        return r.json()
    if r.status_code == 409:
        async with httpx.AsyncClient(timeout=10) as c:
            r2 = await c.get(
                "https://api.podium.com/v4/contacts",
                headers=headers,
                params={"phone": phone_e164, "location_uid": location_uid},
            )
        if r2.status_code == 200 and r2.json().get("data"):
            return r2.json()["data"][0]
    raise WebchatError(f"upsert failed: {r.status_code} {r.text}")
```

## 4. Load + validate the location allowlist

```python
import httpx
from podium_auth import PodiumAuth

VALID_LOCATION_UIDS: set[str] = set()

async def load_locations(auth: PodiumAuth) -> None:
    token = await auth.get_token()
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(
            "https://api.podium.com/v4/locations",
            headers={"Authorization": f"Bearer {token}"},
        )
    r.raise_for_status()
    VALID_LOCATION_UIDS.clear()
    VALID_LOCATION_UIDS.update(loc["uid"] for loc in r.json()["data"])

def validate_location(location_uid: str | None) -> str:
    if not location_uid:
        raise ValueError("ERR_WEBCHAT_002 location_uid is required (no default)")
    if location_uid not in VALID_LOCATION_UIDS:
        raise ValueError(f"ERR_WEBCHAT_003 unknown location_uid {location_uid!r}")
    return location_uid
```

## 5. Session timeout scan with partial-state buffer

```python
import asyncio, time, json
from dataclasses import dataclass, field
from pathlib import Path

SESSION_IDLE_WARN_SECONDS  = 20 * 60
SESSION_IDLE_CLOSE_SECONDS = 28 * 60
PARTIAL_STATE_DIR = Path("/var/lib/webchat-partial-state")

@dataclass
class WebchatSession:
    session_uid: str
    phone_e164: str
    location_uid: str
    last_message_at: float
    partial_state: dict = field(default_factory=dict)

    def status(self) -> str:
        idle = time.time() - self.last_message_at
        if idle >= SESSION_IDLE_CLOSE_SECONDS: return "close"
        if idle >= SESSION_IDLE_WARN_SECONDS:  return "warn"
        return "active"

def persist_partial_state(s: WebchatSession) -> None:
    key = f"{s.phone_e164}__{s.location_uid}.json"
    path = PARTIAL_STATE_DIR / key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "session_uid": s.session_uid,
        "phone_e164": s.phone_e164,
        "location_uid": s.location_uid,
        "partial_state": s.partial_state,
        "persisted_at": time.time(),
    }))

def hydrate_partial_state(phone_e164: str, location_uid: str) -> dict:
    key = f"{phone_e164}__{location_uid}.json"
    path = PARTIAL_STATE_DIR / key
    if not path.exists(): return {}
    return json.loads(path.read_text()).get("partial_state", {})

async def session_loop(sessions: dict[str, WebchatSession]):
    while True:
        for uid, s in list(sessions.items()):
            if s.status() == "warn":
                await send_keepalive_prompt(s.session_uid)
            elif s.status() == "close":
                persist_partial_state(s)
                await close_session_cleanly(s.session_uid)
                del sessions[uid]
        await asyncio.sleep(60)
```

## 6. Attachment size validation (client + server)

```python
PODIUM_ATTACHMENT_MAX_BYTES = 25 * 1024 * 1024   # 25 MiB

class AttachmentTooLargeError(Exception):
    pass

def validate_attachment_size(size_bytes: int) -> None:
    if size_bytes > PODIUM_ATTACHMENT_MAX_BYTES:
        raise AttachmentTooLargeError(
            f"attachment {size_bytes/1024/1024:.1f} MiB > "
            f"{PODIUM_ATTACHMENT_MAX_BYTES/1024/1024:.0f} MiB limit"
        )

# FastAPI server-side double-check
from fastapi import Request, HTTPException

async def reject_oversized(request: Request):
    cl = int(request.headers.get("content-length") or 0)
    try:
        validate_attachment_size(cl)
    except AttachmentTooLargeError as e:
        raise HTTPException(status_code=413, detail=str(e))
```

## 7. Unified opt-out store consulted across SMS + webchat

```python
import time
from typing import Optional

OPTOUT_KEYWORDS = {"STOP", "UNSUBSCRIBE", "QUIT", "END", "CANCEL", "OPTOUT"}

class OptoutStore:
    """Single store keyed on phone_e164. Backed by Postgres in prod; in-memory for tests."""
    def __init__(self):
        self._data: dict[str, dict] = {}     # phone_e164 → {source, recorded_at}

    async def is_opted_out(self, phone_e164: str) -> bool:
        return phone_e164 in self._data

    async def set_opted_out(self, phone_e164: str, source_channel: str) -> None:
        self._data[phone_e164] = {"source": source_channel, "recorded_at": time.time()}

optout_store = OptoutStore()

async def handle_inbound_webchat(message: dict) -> None:
    phone = normalize_phone(message["from"], message.get("country") or "AU")
    text = (message.get("body") or "").strip().upper()
    if text in OPTOUT_KEYWORDS:
        await optout_store.set_opted_out(phone, "webchat")
        return                                # acknowledge silently
    if await optout_store.is_opted_out(phone):
        log_optout_blocked(phone, channel="webchat")
        return                                # do NOT reply
    await process_webchat_message(message)

async def handle_inbound_sms(message: dict) -> None:
    phone = normalize_phone(message["from"], message.get("country") or "AU")
    text = (message.get("body") or "").strip().upper()
    if text in OPTOUT_KEYWORDS:
        await optout_store.set_opted_out(phone, "sms")
        return
    if await optout_store.is_opted_out(phone):
        return
    await process_sms_message(message)
```

## 8. FastAPI webhook handler wiring

```python
# Consumes verified events from podium-webhook-reliability
from fastapi import FastAPI, Request, HTTPException
from podium_auth import PodiumAuth

app = FastAPI()
auth = PodiumAuth(client_id=..., client_secret=..., refresh_token=...)

@app.on_event("startup")
async def startup():
    await load_locations(auth)

@app.post("/podium/webchat")
async def webchat_webhook(req: Request):
    # podium-webhook-reliability has already verified HMAC + dedup'd
    payload = await req.json()
    if payload.get("event_type") != "webchat.message.received":
        return {"status": "ignored"}

    message = payload["data"]
    try:
        phone = normalize_phone(message["from"], message.get("country") or "AU")
        loc = validate_location(message.get("location_uid"))
        await handle_inbound_webchat({**message, "from": phone, "location_uid": loc})
    except (PhoneValidationError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "ok"}
```

## 9. CLI: scan in-flight sessions and prompt or close

```bash
python3 scripts/session_timeout_monitor.py \
  --sessions-file /var/run/webchat/active-sessions.json \
  --warn-after 1200 \
  --close-after 1680 \
  --output json
```

Output:

```json
{
  "scanned": 247,
  "active": 198,
  "warned": 41,
  "closed": 8,
  "errors": 0
}
```

## 10. CLI: audit opt-out across all integration layers for one phone

```bash
python3 scripts/optout_audit.py --phone "+61412345678"
```

Output:

```json
{
  "phone": "+61412345678",
  "optout_store": {
    "opted_out": true,
    "source": "sms",
    "recorded_at_iso": "2026-05-09T14:23:11Z"
  },
  "podium_contact": {
    "uid": "{your-contact-uid}",
    "opted_out": true,
    "last_updated_iso": "2026-05-09T14:23:14Z"
  },
  "consistent": true
}
```

Exit code 0 = all layers agree (opted-out or not). Exit code 1 = drift detected and printed to stderr (typical cause: opt-out store has the record but Podium does not, or vice versa — both must be reconciled).
