# ElevenLabs Security — Worked Examples

End-to-end scenarios exercising the code from
[implementation.md](implementation.md). Each example is a concrete situation an
operator hits when hardening an ElevenLabs integration.

## Example 1: Block a key commit before it happens

Install the pre-commit hook from Step 1, then attempt to commit a file
containing a key:

```bash
$ echo 'const KEY = "sk_abc123def456ghi789jkl";' > leak.ts
$ git add leak.ts && git commit -m "add config"
ERROR: ElevenLabs API key detected in staged changes!
Remove the key and use environment variables instead.
# commit aborted with exit code 1
```

The hook greps staged changes for the `sk_[a-zA-Z0-9]{20,}` pattern and blocks
the commit, so the key never reaches history.

## Example 2: Reject a replayed webhook

A valid-looking request arrives, but its timestamp is 6 minutes old:

```typescript
const header = "t=1700000000,v1=<computed-hmac>";
const ok = verifyWebhookSignature(rawBody, header, process.env.ELEVENLABS_WEBHOOK_SECRET!);
// age = now - 1700000000 > 300  →  logs "Webhook timestamp too old"  →  returns false
// Express handler responds 401 Invalid signature
```

Even with a correct HMAC, the 5-minute replay window closes the attack.

## Example 3: Rotate a leaked production key with zero downtime

You discover a key was exposed. Follow the Step 5 rotation runbook:

```bash
# Validate the replacement BEFORE cutting over
$ curl -s https://api.elevenlabs.io/v1/user \
    -H "xi-api-key: sk_new_key_here" | jq '.subscription.tier'
"creator"

# Push to every environment, deploy, verify prod, THEN revoke the old key
$ fly secrets set ELEVENLABS_API_KEY=sk_new_key_here
$ gh secret set ELEVENLABS_API_KEY --body "sk_new_key_here"
```

The old key stays live until production is confirmed on the new key — no
request fails mid-rotation.

## Example 4: Audit a voice-clone operation

Every clone/delete/use is logged as structured JSON for later review:

```typescript
logVoiceOperation("clone", "voice_9f3a", "user_42");
// {"timestamp":"2026-07-17T12:00:00.000Z","type":"elevenlabs.voice.audit",
//  "operation":"clone","voiceId":"voice_9f3a","userId":"user_42"}
```

Because cloned voices are biometric PII, this audit trail is what proves who
created a voice and whether consent was on file.
