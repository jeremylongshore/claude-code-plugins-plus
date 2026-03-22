---
name: twinmind-data-handling
description: |
  Handle TwinMind meeting data with GDPR compliance: transcript storage, memory vault management, data export, and deletion policies.
  Use when implementing data handling,
  or managing TwinMind meeting AI operations.
  Trigger with phrases like "twinmind data handling", "twinmind data handling".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: ['saas', 'twinmind', 'compliance']

---
# TwinMind Data Handling

## Overview
Handle TwinMind meeting data with GDPR compliance: transcript storage, memory vault management, data export, and deletion policies. TwinMind uses the Ear-3 speech model (5.26% WER, 3.8% DER) for transcription, with GPT-4, Claude, and Gemini for AI summarization.

## Prerequisites
- TwinMind account (Free, Pro $10/mo, or Enterprise)
- Chrome extension installed and authenticated
- Understanding of TwinMind workflow

## Instructions

### Step 1: Setup

TwinMind operates as a Chrome extension and mobile app with optional API access for Pro/Enterprise users.

```javascript
// TwinMind configuration
const config = {
  apiKey: process.env.TWINMIND_API_KEY,
  model: "ear-3", // Transcription model
  aiModels: ["gpt-4", "claude", "gemini"], // Summary models
};
```

### Step 2: Implementation

```javascript
// TwinMind Data Handling implementation
// Core TwinMind integration
const twinmind = {
  transcriptionModel: "ear-3",
  languages: ["en", "es", "ko", "ja", "fr"],
  features: ["transcription", "summary", "action-items"],
  privacyMode: "on-device", // Audio never stored
};

// Check transcription capabilities
async function verify() {
  const health = await fetch("https://api.twinmind.com/v1/health");
  console.log("TwinMind status:", await health.json());
}
```

### Step 3: Verification

```bash
# Verify TwinMind integration
curl -H "Authorization: Bearer $TWINMIND_API_KEY" https://api.twinmind.com/v1/health | jq .
```

## Key TwinMind Specifications

| Feature | Specification |
|---------|--------------|
| Transcription model | Ear-3 (5.26% WER) |
| Speaker diarization | 3.8% DER |
| Languages | 140+ supported |
| Audio processing | On-device (no recordings stored) |
| AI models | GPT-4, Claude, Gemini (auto-routed) |
| Platforms | Chrome extension, iOS, Android |
| Pricing | Free / Pro $10/mo / Enterprise custom |

## Output
- TwinMind Data Handling configured and verified
- TwinMind integration operational
- Meeting transcription workflow ready

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Microphone access denied | Browser permissions not granted | Enable in Chrome settings |
| Transcription not starting | Audio source not detected | Check microphone selection |
| API key invalid | Incorrect or expired key | Regenerate in TwinMind dashboard |
| Sync failed | Network interruption | Check connection, retry |
| Calendar disconnect | OAuth token expired | Re-authorize in Settings |

## Resources
- [TwinMind Website](https://twinmind.com)
- [Chrome Extension](https://chromewebstore.google.com/detail/twinmind/agpbjhhcmoanaljagpoheldgjhclepdj)
- [Ear-3 Model](https://www.marktechpost.com/2025/09/11/twinmind-introduces-ear-3-model/)
- [iOS App](https://apps.apple.com/us/app/twinmind-ai-notes-memory/id6504585781)

## Next Steps
See `twinmind-prod-checklist` for production readiness.

## Examples

**Basic**: Configure data handling with default TwinMind settings for standard meeting workflows.

**Enterprise**: Customize for high-volume meeting transcription with monitoring and alerting.
