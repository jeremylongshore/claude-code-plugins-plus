---
name: elevenlabs-upgrade-migration
description: |
  Upgrade ElevenLabs SDK versions and migrate between API model generations.
  Use when upgrading the elevenlabs-js or elevenlabs Python SDK,
  migrating from v1 to v2 models, or handling deprecations.
  Trigger: "upgrade elevenlabs", "elevenlabs migration",
  "elevenlabs breaking changes", "update elevenlabs SDK",
  "migrate elevenlabs model", "eleven_v3 migration".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, voice, ai, elevenlabs, migration, upgrade]
compatible-with: claude-code
---

# ElevenLabs Upgrade & Migration

## Overview

Guide for upgrading the ElevenLabs SDK and migrating between model generations. Covers the JS SDK package rename, model ID changes, and API endpoint evolution.

## Prerequisites

- Current ElevenLabs SDK installed
- Git for version control
- Test suite available
- Staging environment for validation

## Instructions

### Step 1: Check Current Versions

```bash
# Node.js SDK
npm list @elevenlabs/elevenlabs-js 2>/dev/null || npm list elevenlabs 2>/dev/null
npm view @elevenlabs/elevenlabs-js version

# Python SDK
pip show elevenlabs | grep -E "^(Name|Version)"

# Check what models your account has access to
curl -s https://api.elevenlabs.io/v1/models \
  -H "xi-api-key: ${ELEVENLABS_API_KEY}" | \
  jq '[.[] | {model_id, name}]'
```

### Step 2: JS SDK Package Migration

The official Node.js package changed names:

| Era | Package | Import |
|-----|---------|--------|
| Legacy | `elevenlabs` (community) | `import ElevenLabs from "elevenlabs"` |
| Current | `@elevenlabs/elevenlabs-js` | `import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js"` |

**Migration steps:**
```bash
# Remove old package
npm uninstall elevenlabs

# Install current official SDK
npm install @elevenlabs/elevenlabs-js

# Create upgrade branch
git checkout -b upgrade/elevenlabs-sdk
```

**Update imports:**
```typescript
// BEFORE (legacy community package)
import ElevenLabs from "elevenlabs";
const client = new ElevenLabs({ apiKey: "..." });

// AFTER (official SDK)
import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";
const client = new ElevenLabsClient({
  apiKey: process.env.ELEVENLABS_API_KEY,
  maxRetries: 3,
  timeoutInSeconds: 60,
});
```

### Step 3: Model Migration Guide

ElevenLabs models evolve across generations. Migration paths:

| Old Model | New Model | Migration Notes |
|-----------|-----------|-----------------|
| `eleven_monolingual_v1` | `eleven_multilingual_v2` | Supports 29 languages; same voice IDs work |
| `eleven_multilingual_v1` | `eleven_multilingual_v2` | Better emotional range; same API |
| `eleven_english_v1` | `eleven_turbo_v2_5` | Lower latency; same voice_settings |
| `eleven_turbo_v2` | `eleven_flash_v2_5` | Same quality, lower latency (~75ms) |
| `eleven_multilingual_v2` | `eleven_v3` | Most expressive; 70+ languages; NO WebSocket support |

**Model migration code:**
```typescript
// config/models.ts
type ModelPreference = "quality" | "balanced" | "speed";

const MODEL_MAP: Record<ModelPreference, string> = {
  quality: "eleven_v3",             // Best expressiveness, 70+ languages
  balanced: "eleven_multilingual_v2", // Good quality, WebSocket support
  speed: "eleven_flash_v2_5",       // ~75ms latency, 0.5x cost
};

function selectModel(preference: ModelPreference, needsWebSocket = false): string {
  if (needsWebSocket && preference === "quality") {
    // eleven_v3 doesn't support WebSocket — fall back
    console.warn("eleven_v3 does not support WebSocket streaming; using multilingual_v2");
    return "eleven_multilingual_v2";
  }
  return MODEL_MAP[preference];
}
```

### Step 4: Voice Settings Migration

Voice settings parameters have remained stable, but defaults and ranges have evolved:

```typescript
// Voice settings are consistent across models
const voiceSettings = {
  stability: 0.5,           // 0-1 (unchanged across versions)
  similarity_boost: 0.75,   // 0-1 (unchanged)
  style: 0.0,               // 0-1 (added in v2 models)
  speed: 1.0,               // 0.7-1.2 (added recently)
};

// The `speed` parameter may not be available on older models
// Always check model capabilities:
const models = await client.models.getAll();
for (const model of models) {
  console.log(`${model.model_id}:`);
  console.log(`  TTS: ${model.can_do_text_to_speech}`);
  console.log(`  STS: ${model.can_do_voice_conversion}`);
}
```

### Step 5: API Endpoint Changes

```typescript
// Endpoint paths have remained stable at /v1/
// Key endpoints and their stability:

const STABLE_ENDPOINTS = {
  tts:         "POST /v1/text-to-speech/{voice_id}",
  ttsStream:   "POST /v1/text-to-speech/{voice_id}/stream",
  sts:         "POST /v1/speech-to-speech/{voice_id}",
  voices:      "GET  /v1/voices",
  voiceGet:    "GET  /v1/voices/{voice_id}",
  voiceAdd:    "POST /v1/voices/add",
  user:        "GET  /v1/user",
  models:      "GET  /v1/models",
  soundGen:    "POST /v1/sound-generation",
  audioIso:    "POST /v1/audio-isolation",
  stt:         "POST /v1/speech-to-text",
};

// Newer endpoints (v2):
const V2_ENDPOINTS = {
  voiceSearch: "GET /v2/voices",  // Enhanced search/filter
};
```

### Step 6: Python SDK Upgrade

```bash
# Check current version
pip show elevenlabs

# Upgrade
pip install --upgrade elevenlabs

# Pin version for reproducibility
pip install elevenlabs==1.x.x
echo "elevenlabs==1.x.x" >> requirements.txt
```

```python
# Import changes (if upgrading from very old versions)
# Old:
from elevenlabs import generate, set_api_key
set_api_key("sk_...")
audio = generate(text="Hello", voice="Rachel")

# New:
from elevenlabs.client import ElevenLabsClient
client = ElevenLabsClient(api_key="sk_...")
audio = client.text_to_speech.convert(
    voice_id="21m00Tcm4TlvDq8ikWAM",
    text="Hello",
    model_id="eleven_multilingual_v2",
)
```

### Step 7: Validation After Upgrade

```bash
# Run tests
npm test

# Smoke test TTS
curl -s -o /dev/null -w "%{http_code}" \
  -X POST "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM" \
  -H "xi-api-key: ${ELEVENLABS_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"text":"Upgrade test.","model_id":"eleven_flash_v2_5"}'

# Verify voice list still works
curl -s https://api.elevenlabs.io/v1/voices \
  -H "xi-api-key: ${ELEVENLABS_API_KEY}" | jq '.voices | length'
```

## Rollback Procedure

```bash
# Node.js — pin to previous version
npm install @elevenlabs/elevenlabs-js@previous.version.here --save-exact

# Python
pip install elevenlabs==previous.version.here

# Git rollback
git revert HEAD  # Revert upgrade commit
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `Cannot find module` | Old package name | Update import to `@elevenlabs/elevenlabs-js` |
| `model_not_found` | Deprecated model ID | Map to current model (see table) |
| WebSocket fails after model change | eleven_v3 doesn't support WS | Use `eleven_flash_v2_5` or `eleven_multilingual_v2` |
| Voice settings ignored | Wrong parameter names | Verify `stability`, `similarity_boost`, `style`, `speed` |

## Resources

- [ElevenLabs JS SDK Releases](https://github.com/elevenlabs/elevenlabs-js/releases)
- [ElevenLabs Python SDK Changelog](https://pypi.org/project/elevenlabs/#history)
- [ElevenLabs Models](https://elevenlabs.io/docs/overview/models)
- [ElevenLabs Changelog](https://elevenlabs.io/docs/changelog)

## Next Steps

For CI integration during upgrades, see `elevenlabs-ci-integration`.
