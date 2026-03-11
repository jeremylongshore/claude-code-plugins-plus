---
name: posthog-reference-architecture
description: |
  Implement PostHog reference architecture with best-practice project layout.
  Use when designing new PostHog integrations, reviewing project structure,
  or establishing architecture standards for PostHog applications.
  Trigger with phrases like "posthog architecture", "posthog best practices",
  "posthog project structure", "how to organize posthog", "posthog layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# PostHog Reference Architecture

## Overview
Production architecture for product analytics with PostHog. Covers event tracking design, feature flag management, experimentation framework, and integration patterns for web and backend applications.

## Prerequisites
- PostHog project (Cloud or self-hosted)
- `posthog-js` and `posthog-node` SDKs
- Understanding of event-driven analytics
- Feature flag strategy planned

## Architecture Diagram

```
set -euo pipefail
┌──────────────────────────────────────────────────────┐
│              Client Applications                      │
│  Web (posthog-js) │ Mobile (posthog-react-native)    │
└──────────┬────────────────────────────┬──────────────┘
           │                            │
           ▼                            ▼
┌──────────────────────────────────────────────────────┐
│              PostHog Platform                         │
│  ┌───────────┐  ┌───────────┐  ┌─────────────────┐   │
│  │ Events    │  │ Feature   │  │ Experiments     │   │
│  │ & Props   │  │ Flags     │  │ (A/B tests)     │   │
│  └─────┬─────┘  └─────┬─────┘  └───────┬─────────┘   │
│        │              │                 │             │
│  ┌─────┴──────────────┴─────────────────┴───────┐     │
│  │         Analytics Engine                      │     │
│  │  Trends │ Funnels │ Retention │ Paths │ SQL  │     │
│  └──────────────────────────────────────────────┘     │
├──────────────────────────────────────────────────────┤
│  Backend (posthog-node)                               │
│  Server Events │ Flag Evaluation │ Group Analytics   │
└──────────────────────────────────────────────────────┘
```

## Instructions

### Step 1: Event Taxonomy Design
```typescript
// events.ts - Define your event taxonomy
export const EVENTS = {
  // User lifecycle
  USER_SIGNED_UP: 'user_signed_up',
  USER_LOGGED_IN: 'user_logged_in',
  USER_ONBOARDING_COMPLETED: 'user_onboarding_completed',

  // Core product actions
  FEATURE_USED: 'feature_used',
  ITEM_CREATED: 'item_created',
  ITEM_SHARED: 'item_shared',
  EXPORT_COMPLETED: 'export_completed',

  // Revenue
  SUBSCRIPTION_STARTED: 'subscription_started',
  SUBSCRIPTION_UPGRADED: 'subscription_upgraded',
  SUBSCRIPTION_CANCELED: 'subscription_canceled',
} as const;

// Standard properties for consistency
interface EventProperties {
  feature_name?: string;
  source?: 'web' | 'mobile' | 'api';
  plan_tier?: 'free' | 'pro' | 'enterprise';
  duration_ms?: number;
}
```

### Step 2: Client-Side Integration
```typescript
import posthog from 'posthog-js';

posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
  api_host: 'https://us.i.posthog.com',
  capture_pageview: true,
  capture_pageleave: true,
  autocapture: true,
  persistence: 'localStorage+cookie',
  loaded: (ph) => {
    if (process.env.NODE_ENV === 'development') {
      ph.opt_out_capturing(); // Disable in dev
    }
  },
});

// Identify users
function identifyUser(userId: string, traits: Record<string, any>) {
  posthog.identify(userId, {
    email: traits.email,
    plan: traits.plan,
    company: traits.company,
  });

  // Set group for company-level analytics
  if (traits.companyId) {
    posthog.group('company', traits.companyId, {
      name: traits.company,
      plan: traits.plan,
    });
  }
}
```

### Step 3: Feature Flag Architecture
```typescript
// flags.ts - Feature flag definitions
export const FLAGS = {
  NEW_DASHBOARD: 'new-dashboard-v2',
  AI_FEATURES: 'ai-features-beta',
  PRICING_EXPERIMENT: 'pricing-page-experiment',
} as const;

// React hook for feature flags
function useFeatureFlag(flagKey: string) {
  const [enabled, setEnabled] = useState(false);

  useEffect(() => {
    posthog.onFeatureFlags(() => {
      setEnabled(posthog.isFeatureEnabled(flagKey) ?? false);
    });
  }, [flagKey]);

  return enabled;
}

// Server-side flag evaluation
import { PostHog } from 'posthog-node';
const serverPosthog = new PostHog(process.env.POSTHOG_API_KEY!);

async function getServerFlags(userId: string) {
  return serverPosthog.getAllFlags(userId);
}
```

### Step 4: Experiment Tracking
```typescript
function trackExperiment(experimentKey: string, userId: string) {
  const variant = posthog.getFeatureFlag(experimentKey);

  posthog.capture('$experiment_started', {
    $experiment_name: experimentKey,
    $experiment_variant: variant,
  });

  return variant;
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Events not appearing | SDK not initialized | Check init call and API key |
| Flag always false | Not loaded yet | Use `onFeatureFlags` callback |
| Missing user properties | Not identified | Call `identify` before capture |
| High event volume | Autocapture too broad | Configure autocapture selectively |

## Examples

### Funnel Tracking Setup
```typescript
// Track a conversion funnel
posthog.capture(EVENTS.ITEM_CREATED, { source: 'web' });
posthog.capture(EVENTS.ITEM_SHARED, { share_method: 'link' });
posthog.capture(EVENTS.EXPORT_COMPLETED, { format: 'pdf' });
```

## Resources
- [PostHog Documentation](https://posthog.com/docs)
- [PostHog Feature Flags](https://posthog.com/docs/feature-flags)
- [PostHog Experiments](https://posthog.com/docs/experiments)

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale