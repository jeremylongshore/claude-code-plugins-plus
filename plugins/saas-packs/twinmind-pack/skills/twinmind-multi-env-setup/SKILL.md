---
name: twinmind-multi-env-setup
description: |
  Configure TwinMind across development, staging, and production environments with separate accounts and API key management.
  Use when implementing multi env setup,
  or managing TwinMind meeting AI operations.
  Trigger with phrases like "twinmind multi env setup", "twinmind multi env setup".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: ['saas', 'twinmind', 'deployment']

---
# TwinMind Multi-Environment Setup

## Overview
Configure TwinMind across development, staging, and production environments with separate accounts and API key management. TwinMind uses the Ear-3 speech model (5.26% WER, 3.8% DER) for transcription, with GPT-4, Claude, and Gemini for AI summarization.

## Prerequisites
- TwinMind account (Free, Pro $10/mo, or Enterprise)
- Chrome extension installed and authenticated
- API access (Pro/Enterprise tier)

## Instructions

### Step 1: Enterprise Configuration

TwinMind Enterprise supports on-premise deployment, custom AI models, and unlimited context tokens.

```javascript
// TwinMind configuration
const config = {
  apiKey: process.env.TWINMIND_API_KEY,
  model: "ear-3", // Transcription model
  aiModels: ["gpt-4", "claude", "gemini"], // Summary models
};
```

### Step 2: Role Configuration

```javascript
// TwinMind Multi-Environment Setup implementation
// Enterprise tier features
const twinmind = {
  ssoProvider: "okta",
  teamSharing: true,
  customModels: ["gpt-4-turbo"],
  onPremise: true,
};

// Configure team access
async function configureTeam() {
  const team = await twinmind.createTeam({ name: "Engineering", members: ["user1", "user2"] });
  console.log("Team configured:", team.id);
}
```

### Step 3: Verification

```bash
# Verify TwinMind enterprise setup
curl -H "Authorization: Bearer $TWINMIND_API_KEY" https://api.twinmind.com/v1/team/members | jq .
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
- TwinMind Multi-Environment Setup configured and verified
- TwinMind integration operational
- Enterprise features enabled

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
See `twinmind-observability` for monitoring setup.

## Examples

**Basic**: Configure multi env setup with default TwinMind settings for standard meeting workflows.

**Enterprise**: Deploy on-premise with custom AI models and SSO for team-wide meeting intelligence.
