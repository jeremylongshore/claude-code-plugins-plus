# ElevenLabs Debug Bundle — Worked Examples

Concrete end-to-end runs showing what the collector produces and how to read
it. Use these to confirm your bundle looks right before attaching it to a
support ticket.

## Example 1: Healthy account, shell bundle

```console
$ export ELEVENLABS_API_KEY=sk_...   # already set in your environment
$ bash elevenlabs-debug-bundle.sh
Bundle created: elevenlabs-debug-20260717-143022.tar.gz
Review for sensitive data before sharing with support.
```

Inspect the archive before sharing:

```console
$ tar -tzf elevenlabs-debug-20260717-143022.tar.gz
elevenlabs-debug-20260717-143022/summary.txt
elevenlabs-debug-20260717-143022/config-redacted.txt
elevenlabs-debug-20260717-143022/errors.txt
```

Representative `summary.txt` from a working account (secrets already masked):

```text
=== ElevenLabs Debug Bundle ===
Generated: 2026-07-17T14:30:22Z

--- Runtime Environment ---
v22.21.0
Python 3.12.3
OS: Linux 6.8.0-110-generic
API Key: SET (51 chars)

--- API Connectivity ---
GET /v1/user: HTTP 200
DNS api.elevenlabs.io: 104.18.x.x
TLS valid: yes

--- Subscription ---
{ "tier": "creator", "character_count": 48210, "character_limit": 100000, "next_reset": 1750000000 }
```

The key signals a support engineer looks for: `HTTP 200` (auth good), `TLS
valid: yes` (transport good), and `character_count` well under
`character_limit` (not a quota problem).

## Example 2: Bad API key (401)

When the key is wrong or revoked, connectivity fails and the subscription/voice/
model sections are skipped (the `if [ "$HTTP_CODE" = "200" ]` guard):

```text
--- API Connectivity ---
GET /v1/user: HTTP 401
DNS api.elevenlabs.io: 104.18.x.x
TLS valid: yes
```

`HTTP 401` with `TLS valid: yes` isolates the fault to authentication, not the
network — regenerate the key at elevenlabs.io.

## Example 3: Programmatic collector output

Running the TypeScript collector from `references/implementation.md`:

```console
npx tsx src/elevenlabs/debug.ts
```

```json
{
  "timestamp": "2026-07-17T14:30:22.101Z",
  "sdk": { "package": "@elevenlabs/elevenlabs-js", "version": "unknown" },
  "connectivity": { "status": 200, "latencyMs": 214 },
  "subscription": { "tier": "creator", "used": 48210, "limit": 100000, "resetAt": "2026-08-01T00:00:00.000Z" },
  "voices": { "total": 12, "cloned": 3, "premade": 9 },
  "models": ["eleven_multilingual_v2", "eleven_turbo_v2_5", "eleven_flash_v2_5"],
  "errors": []
}
```

A non-empty `errors` array with a populated `connectivity` block is the useful
diagnostic shape — for example `"errors": ["Voices: 429 Too Many Requests"]`
with `connectivity.status: 200` means auth works but you are being rate limited
on the voices endpoint specifically.
