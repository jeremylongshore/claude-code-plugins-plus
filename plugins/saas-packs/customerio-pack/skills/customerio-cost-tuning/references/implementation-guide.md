# Customer.io Cost Tuning - Implementation Guide

### Step 1: Profile Cleanup
```typescript
// scripts/profile-audit.ts
import { APIClient, RegionUS } from '@customerio/track';

interface ProfileAudit {
  total: number;
  inactive30Days: number;
  inactive90Days: number;
  noEmail: number;
  suppressed: number;
  recommendations: string[];
}

async function auditProfiles(): Promise<ProfileAudit> {
  const audit: ProfileAudit = {
    total: 0,
    inactive30Days: 0,
    inactive90Days: 0,
    noEmail: 0,
    suppressed: 0,
    recommendations: []
  };

  // Query via Customer.io App API or export
  // Analyze profile data

  const now = Math.floor(Date.now() / 1000);
  const thirtyDaysAgo = now - (30 * 24 * 60 * 60);
  const ninetyDaysAgo = now - (90 * 24 * 60 * 60);

  // Example analysis
  if (audit.inactive90Days > audit.total * 0.3) {
    audit.recommendations.push(
      'Consider archiving profiles inactive >90 days to reduce costs'
    );
  }

  if (audit.noEmail > audit.total * 0.1) {
    audit.recommendations.push(
      'Remove profiles without email addresses (cannot receive communications)'
    );
  }

  return audit;
}
```

### Step 2: Suppress Inactive Users
```typescript
// lib/profile-management.ts
import { TrackClient, RegionUS } from '@customerio/track';

const client = new TrackClient(
  process.env.CUSTOMERIO_SITE_ID!,
  process.env.CUSTOMERIO_API_KEY!,
  { region: RegionUS }
);

// Suppress users who haven't engaged
async function suppressInactiveUsers(
  userIds: string[],
  dryRun: boolean = true
): Promise<{ suppressed: string[]; errors: string[] }> {
  const results = { suppressed: [] as string[], errors: [] as string[] };

  for (const userId of userIds) {
    if (dryRun) {
      console.log(`[DRY RUN] Would suppress: ${userId}`);
      results.suppressed.push(userId);
      continue;
    }

    try {
      await client.suppress(userId);
      results.suppressed.push(userId);
    } catch (error: any) {
      results.errors.push(`${userId}: ${error.message}`);
    }
  }

  return results;
}

// Delete users to fully remove from billing
async function deleteUsers(
  userIds: string[],
  dryRun: boolean = true
): Promise<{ deleted: string[]; errors: string[] }> {
  const results = { deleted: [] as string[], errors: [] as string[] };

  for (const userId of userIds) {
    if (dryRun) {
      console.log(`[DRY RUN] Would delete: ${userId}`);
      results.deleted.push(userId);
      continue;
    }

    try {
      await client.destroy(userId);
      results.deleted.push(userId);
    } catch (error: any) {
      results.errors.push(`${userId}: ${error.message}`);
    }
  }

  return results;
}
```

### Step 3: Event Deduplication
```typescript
// lib/smart-tracking.ts
import { LRUCache } from 'lru-cache';
import { TrackClient } from '@customerio/track';

const recentEvents = new LRUCache<string, number>({
  max: 100000,
  ttl: 3600000 // 1 hour
});

interface TrackingConfig {
  dedupWindowMs: number;
  skipEvents: string[];
  sampleRate: Record<string, number>;
}

const config: TrackingConfig = {
  dedupWindowMs: 60000, // 1 minute dedup window
  skipEvents: [
    'page_viewed', // High volume, low value
    'heartbeat'
  ],
  sampleRate: {
    'feature_used': 0.1, // Sample 10% of feature usage
    'search_performed': 0.5 // Sample 50% of searches
  }
};

export function shouldTrackEvent(
  userId: string,
  eventName: string,
  data?: Record<string, any>
): boolean {
  // Skip excluded events
  if (config.skipEvents.includes(eventName)) {
    return false;
  }

  // Apply sampling for high-volume events
  const sampleRate = config.sampleRate[eventName];
  if (sampleRate !== undefined && Math.random() > sampleRate) {
    return false;
  }

  // Deduplicate identical events
  const eventKey = `${userId}:${eventName}:${JSON.stringify(data || {})}`;
  if (recentEvents.has(eventKey)) {
    return false;
  }

  recentEvents.set(eventKey, Date.now());
  return true;
}
```

### Step 4: Email Cost Optimization
```typescript
// lib/email-optimization.ts
interface EmailOptimizationConfig {
  // Skip transactional emails for users who never open
  skipInactiveAfterDays: number;
  // Consolidate multiple notifications
  batchNotifications: boolean;
  batchWindowMinutes: number;
  // Suppress bounced emails
  suppressAfterBounces: number;
}

const emailConfig: EmailOptimizationConfig = {
  skipInactiveAfterDays: 180, // Skip users inactive 6 months
  batchNotifications: true,
  batchWindowMinutes: 30,
  suppressAfterBounces: 3
};

// Check if user should receive emails
async function shouldSendEmail(
  userId: string,
  emailType: 'transactional' | 'marketing'
): Promise<boolean> {
  // Always send critical transactional (password reset, security)
  if (emailType === 'transactional') {
    return true;
  }

  // Check engagement history
  const user = await getUserMetrics(userId);

  // Skip users who haven't opened in 6 months
  const sixMonthsAgo = Date.now() - (180 * 24 * 60 * 60 * 1000);
  if (user.lastEmailOpenedAt < sixMonthsAgo) {
    return false;
  }

  // Skip users with high bounce count
  if (user.bounceCount >= emailConfig.suppressAfterBounces) {
    return false;
  }

  return true;
}
```

### Step 5: Usage Monitoring Dashboard
```typescript
// lib/usage-monitor.ts
interface UsageMetrics {
  period: string;
  profiles: {
    total: number;
    new: number;
    deleted: number;
  };
  events: {
    total: number;
    byType: Record<string, number>;
  };
  emails: {
    sent: number;
    delivered: number;
    opened: number;
    bounced: number;
  };
  estimatedCost: number;
}

async function getUsageMetrics(
  startDate: Date,
  endDate: Date
): Promise<UsageMetrics> {
  // Query Customer.io Reporting API
  // or aggregate from your tracking

  return {
    period: `${startDate.toISOString()} - ${endDate.toISOString()}`,
    profiles: {
      total: 10000,
      new: 500,
      deleted: 100
    },
    events: {
      total: 50000,
      byType: {
        'signed_up': 500,
        'feature_used': 20000,
        'page_viewed': 25000 // Candidate for sampling
      }
    },
    emails: {
      sent: 15000,
      delivered: 14500,
      opened: 4350,
      bounced: 150
    },
    estimatedCost: 299 // Monthly estimate
  };
}

// Alert on unexpected usage spikes
function checkUsageAlerts(metrics: UsageMetrics): string[] {
  const alerts: string[] = [];

  // Profile growth alert
  if (metrics.profiles.new > metrics.profiles.total * 0.1) {
    alerts.push('Unusual profile growth detected');
  }

  // Event volume alert
  if (metrics.events.total > 100000) {
    alerts.push('High event volume - consider sampling');
  }

  // Bounce rate alert
  if (metrics.emails.bounced / metrics.emails.sent > 0.05) {
    alerts.push('High bounce rate - clean email list');
  }

  return alerts;
}
```

### Step 6: Cost Reduction Checklist

```markdown
