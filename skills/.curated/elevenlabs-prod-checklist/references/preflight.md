# ElevenLabs Pre-Flight Check Script

Run this script as the last gate before promoting a build to production. It
verifies API connectivity, remaining quota, voice availability, and a live TTS
smoke test, exiting non-zero on any hard failure so it can block a CI/CD deploy
step. Requires `ELEVENLABS_API_KEY` in the environment and `jq` on PATH.

```bash
#!/bin/bash
# pre-flight-check.sh — Run before deploying

echo "=== ElevenLabs Pre-Flight Check ==="

# 1. API connectivity
HTTP=$(curl -s -o /dev/null -w "%{http_code}" \
  https://api.elevenlabs.io/v1/user \
  -H "xi-api-key: ${ELEVENLABS_API_KEY}")
echo "API connectivity: HTTP $HTTP"
[ "$HTTP" != "200" ] && echo "FAIL: API not reachable" && exit 1

# 2. Quota check
QUOTA=$(curl -s https://api.elevenlabs.io/v1/user \
  -H "xi-api-key: ${ELEVENLABS_API_KEY}" | \
  jq '.subscription | (.character_limit - .character_count)')
echo "Characters remaining: $QUOTA"
[ "$QUOTA" -lt 10000 ] && echo "WARN: Low quota"

# 3. Voice availability
VOICE_COUNT=$(curl -s https://api.elevenlabs.io/v1/voices \
  -H "xi-api-key: ${ELEVENLABS_API_KEY}" | jq '.voices | length')
echo "Voices available: $VOICE_COUNT"

# 4. TTS smoke test
TTS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM" \
  -H "xi-api-key: ${ELEVENLABS_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"text":"Pre-flight check.","model_id":"eleven_flash_v2_5"}')
echo "TTS smoke test: HTTP $TTS_STATUS"
[ "$TTS_STATUS" != "200" ] && echo "FAIL: TTS not working" && exit 1

echo "=== All checks passed ==="
```

## Wiring it into CI/CD

Add the script as a required step immediately before your deploy job. A non-zero
exit (unreachable API or failing TTS smoke test) fails the pipeline and prevents a
broken build from shipping:

```yaml
# .github/workflows/deploy.yml (excerpt)
- name: ElevenLabs pre-flight
  env:
    ELEVENLABS_API_KEY: ${{ secrets.ELEVENLABS_API_KEY_PROD }}
  run: ./scripts/pre-flight-check.sh
```
