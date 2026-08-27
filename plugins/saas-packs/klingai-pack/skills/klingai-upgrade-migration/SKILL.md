---
name: klingai-upgrade-migration
description: 'Migrate between Kling AI model versions safely. Use when upgrading from
  v1.x to v2.x or

  adopting new features. Trigger with phrases like ''klingai upgrade'', ''kling ai
  migrate'',

  ''klingai version update'', ''upgrade kling model''.

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.18.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- kling-ai
- migration
- upgrade
compatibility: Designed for Claude Code
---
# Kling AI Upgrade & Migration

## Overview

Guide for migrating between Kling AI model versions. Covers breaking changes, parameter differences, feature availability, and parallel testing strategies.

## Version History

| Version | Release | Key Changes |
|---------|---------|-------------|
| v1.0 | 2024-06 | Initial T2V + I2V |
| v1.5 | 2024-09 | 1080p, motion brush, I2V-only model |
| v1.6 | 2024-11 | Lip sync, camera paths, effects API |
| v2.0 | 2025-03 | Quality leap, `kling-v2-master` |
| v2.1 | 2025-06 | Optimized I2V, `kling-v2-1-master` for T2V |
| v2.5 Turbo | 2025-09 | 40% faster, best speed/quality ratio |
| v2.6 | 2025-12 | Native audio, 30-48 FPS, highest quality |

## Migration: v1.x to v2.x

```python
# v1.x request
body = {
    "model_name": "kling-v1-6",
    "prompt": "A sunset over mountains",
    "duration": "5",
    "mode": "standard",
}

# v2.x -- only model_name changes
body["model_name"] = "kling-v2-master"
```

**Breaking changes:**

- `kling-v2-1` is I2V-only (no text-to-video support)
- Camera control intensities produce different results at same values
- Generation times differ (v2.x generally slower, higher quality)

## Migration: v2.x to v2.6 with Audio

```python
body["model_name"] = "kling-v2-6"
body["motion_has_audio"] = True  # NEW: synchronized audio

# Cost impact: audio multiplies credits 5x
# 5s standard: 10 -> 50 credits
```

## Feature Availability Matrix

| Feature | v1.0 | v1.5 | v1.6 | v2.0 | v2.1 | v2.5T | v2.6 |
|---------|------|------|------|------|------|-------|------|
| Text-to-video | Y | Y | Y | Y | I2V only | Y | Y |
| Image-to-video | Y | Y | Y | Y | Y | Y | Y |
| Camera control | - | - | Y | Y | Y | Y | Y |
| Motion brush | - | Y | Y | Y | Y | Y | Y |
| Lip sync | - | - | Y | Y | Y | Y | Y |
| Effects | - | - | Y | Y | Y | Y | Y |
| Native audio | - | - | - | - | - | - | Y |
| 1080p | - | Y | Y | Y | Y | Y | Y |

## Parallel A/B Comparison

```python
def compare_models(prompt, models):
    """Generate same prompt across models for comparison."""
    results = {}
    for model in models:
        r = requests.post(f"{BASE}/videos/text2video", headers=get_headers(), json={
            "model_name": model, "prompt": prompt, "duration": "5", "mode": "standard",
        }).json()
        results[model] = {"task_id": r["data"]["task_id"], "start": time.time()}

    # Poll all
    while any("url" not in r for r in results.values()):
        for model, info in results.items():
            if "url" in info or "error" in info:
                continue
            r = requests.get(
                f"{BASE}/videos/text2video/{info['task_id']}", headers=get_headers()
            ).json()
            if r["data"]["task_status"] == "succeed":
                info["url"] = r["data"]["task_result"]["videos"][0]["url"]
                info["time"] = round(time.time() - info["start"])
            elif r["data"]["task_status"] == "failed":
                info["error"] = r["data"].get("task_status_msg")
        time.sleep(10)

    for model, info in results.items():
        print(f"{model}: {info.get('url', info.get('error'))} ({info.get('time', '?')}s)")
    return results
```

## Rollback Strategy

```python
# Feature flag for instant rollback
KLING_MODEL = os.environ.get("KLING_MODEL_VERSION", "kling-v2-master")
body["model_name"] = KLING_MODEL

# To rollback: export KLING_MODEL_VERSION=kling-v1-6
```

## Prerequisites

- A pinned source and target model, a migration owner, an approved credit budget, and a tested feature-flag rollback to the last known-good version.
- Use synthetic prompts and rights-cleared test media only. Confirm that reference images, likenesses, audio, and other inputs have the required consent and do not violate provider content policy.
- Have a sandbox project, draft/watermarked canary destination, acceptance thresholds for quality/latency/cost, and a removal plan for failed outputs before touching production traffic.

## Instructions

1. Snapshot the current request schema, model flag, output retention, and aggregate baseline. Check the provider's current model documentation rather than assuming the version table is current.
2. Run the same synthetic fixture against source and target in sandbox. Compare capability support, policy outcomes, quality, latency, and credit usage without publishing either result.
3. Obtain owner approval for the target, budget delta, and acceptance thresholds. Release behind `KLING_MODEL_VERSION` to one draft/watermarked canary, then expand in measured stages only if every threshold remains green.
4. Keep the source version available until the migration window closes. Revoke temporary test credentials, delete rejected or superseded media, and retain only redacted comparison and approval receipts.

## Output

Produce a migration receipt with source/target model IDs, schema or feature changes, synthetic fixture ID, canary scope, aggregate pass/fail metrics, credit and latency deltas, policy/rights review, owner approval, rollout state, retention deadline, and rollback reference. Do not include prompts, media, likenesses, audio, signed URLs, identities, or secrets.

## Error Handling

- If a model is unavailable or a capability is unsupported, stop the rollout and select an explicitly approved fallback; do not silently substitute a model.
- If quality, latency, cost, policy, or rights thresholds regress, set the feature flag to the last known-good version, cancel queued target jobs where supported, and remove target canary outputs.
- Treat authentication, schema, and policy failures as non-retryable until reviewed. Reconcile in-flight tasks before retrying transient transport errors, and document any partial migration in the receipt.

## Examples

Compare `kling-v1-6` and `kling-v2-master` using `fixture=synthetic-city-01`, `environment=sandbox`, `canary=watermarked`, `max_credit_delta=20%`, and `publish=false`. Record `rights=pass`, `policy=pass`, and owner approval before changing `KLING_MODEL_VERSION`; on any failed threshold, restore `kling-v1-6` and delete the comparison outputs.

## Resources

- [Model Documentation](https://app.klingai.com/global/dev/document-api/apiReference/model/skillsMap)
- [Developer Portal](https://app.klingai.com/global/dev)
