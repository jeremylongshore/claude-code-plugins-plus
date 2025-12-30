---
name: sentry-policy-guardrails
description: |
  Implement governance and policy guardrails for Sentry.
  Use when enforcing organizational standards, compliance rules,
  or standardizing Sentry usage across teams.
  Trigger with phrases like "sentry governance", "sentry standards",
  "sentry policy", "enforce sentry configuration".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Sentry Policy Guardrails

## Overview
Implement organizational policies and guardrails for Sentry usage.

## Configuration Standards

### Shared Configuration Package
```typescript
// packages/sentry-config/index.ts
import * as Sentry from '@sentry/node';

export interface SentryConfigOptions {
  serviceName: string;
  environment: string;
  version?: string;
  additionalTags?: Record<string, string>;
}

// Enforced organization defaults
const ORGANIZATION_DEFAULTS = {
  // Never send PII without explicit opt-in
  sendDefaultPii: false,

  // Standard sample rates
  sampleRate: 1.0,
  tracesSampleRate: 0.1,

  // Standard breadcrumb limit
  maxBreadcrumbs: 50,

  // Standard ignore patterns
  ignoreErrors: [
    'ResizeObserver loop limit exceeded',
    'Non-Error promise rejection',
    /^Network request failed/,
  ],
};

export function initSentryWithPolicy(options: SentryConfigOptions): void {
  const dsn = process.env.SENTRY_DSN;

  if (!dsn && options.environment === 'production') {
    throw new Error('SENTRY_DSN required in production');
  }

  Sentry.init({
    dsn,
    environment: options.environment,
    release: options.version,
    serverName: options.serviceName,

    // Apply organization defaults (cannot be overridden)
    ...ORGANIZATION_DEFAULTS,

    // Required tags
    initialScope: {
      tags: {
        service: options.serviceName,
        team: process.env.TEAM_NAME || 'unknown',
        ...options.additionalTags,
      },
    },

    // Enforced PII scrubbing
    beforeSend: enforcedBeforeSend,
  });
}

function enforcedBeforeSend(
  event: Sentry.Event,
  hint: Sentry.EventHint
): Sentry.Event | null {
  // Always scrub sensitive data
  return scrubSensitiveData(event);
}
```

### Usage in Services
```typescript
// services/user-service/src/index.ts
import { initSentryWithPolicy } from '@mycompany/sentry-config';

// Teams can't bypass organization policies
initSentryWithPolicy({
  serviceName: 'user-service',
  environment: process.env.NODE_ENV || 'development',
  version: process.env.GIT_SHA,
  additionalTags: {
    feature_area: 'authentication',
  },
});
```

## Compliance Enforcement

### Required Data Scrubbing
```typescript
// Enforced by shared config - cannot be disabled
function scrubSensitiveData(event: Sentry.Event): Sentry.Event {
  // Remove sensitive headers
  if (event.request?.headers) {
    const sensitiveHeaders = [
      'authorization',
      'cookie',
      'x-api-key',
      'x-auth-token',
    ];
    for (const header of sensitiveHeaders) {
      delete event.request.headers[header];
    }
  }

  // Scrub credit cards
  event = scrubPattern(event, /\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b/g, '[CARD]');

  // Scrub SSNs
  event = scrubPattern(event, /\b\d{3}-\d{2}-\d{4}\b/g, '[SSN]');

  // Scrub emails in extra/contexts (keep user email if explicitly set)
  event = scrubPattern(event, /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g, '[EMAIL]');

  return event;
}

function scrubPattern(event: Sentry.Event, pattern: RegExp, replacement: string): Sentry.Event {
  const scrub = (obj: any): any => {
    if (typeof obj === 'string') {
      return obj.replace(pattern, replacement);
    }
    if (Array.isArray(obj)) {
      return obj.map(scrub);
    }
    if (obj && typeof obj === 'object') {
      return Object.fromEntries(
        Object.entries(obj).map(([k, v]) => [k, scrub(v)])
      );
    }
    return obj;
  };

  return scrub(event);
}
```

### Environment Enforcement
```typescript
// Prevent test data in production
function validateEnvironment(event: Sentry.Event): Sentry.Event | null {
  const env = process.env.NODE_ENV;

  // Block test data in production
  if (env === 'production') {
    const message = event.message?.toLowerCase() || '';
    const tags = event.tags || {};

    if (
      message.includes('test') ||
      tags.test === 'true' ||
      event.user?.email?.includes('@test.com')
    ) {
      console.warn('Blocked test data from production Sentry');
      return null;
    }
  }

  return event;
}
```

## Alert Policies

### Standard Alert Template
```yaml
# Organization-wide alert standards
alert_policies:
  critical:
    name: "Critical Error Rate"
    conditions:
      - event_frequency > 100 per hour
    actions:
      - pagerduty: critical-oncall
      - slack: "#incidents"
    required: true  # Teams cannot disable

  high_error_rate:
    name: "High Error Rate"
    conditions:
      - error_rate > 5%
    actions:
      - slack: team-channel  # Team configures channel
    required: true

  new_issue:
    name: "New Issue Notification"
    conditions:
      - is:unresolved is:new
    actions:
      - slack: team-channel
    required: false  # Optional
```

### Alert Configuration Validation
```typescript
// Validate team alert configurations
interface AlertConfig {
  name: string;
  conditions: string[];
  actions: string[];
}

function validateAlertConfig(config: AlertConfig): string[] {
  const errors: string[] = [];

  // Required alerts must exist
  const requiredAlerts = ['Critical Error Rate', 'High Error Rate'];
  for (const required of requiredAlerts) {
    if (config.name === required && config.actions.length === 0) {
      errors.push(`Required alert "${required}" must have actions configured`);
    }
  }

  // PagerDuty required for critical
  if (config.name.includes('Critical') && !config.actions.some(a => a.includes('pagerduty'))) {
    errors.push('Critical alerts must include PagerDuty action');
  }

  return errors;
}
```

## Project Naming Standards

### Enforced Naming Convention
```typescript
// Project naming: {team}-{service}-{environment}
// Examples: payments-api-production, auth-worker-staging

function validateProjectName(name: string): boolean {
  const pattern = /^[a-z]+-[a-z]+-(?:production|staging|development)$/;
  return pattern.test(name);
}

// API to create project with validation
async function createProject(
  teamSlug: string,
  serviceName: string,
  environment: string
): Promise<void> {
  const projectName = `${teamSlug}-${serviceName}-${environment}`;

  if (!validateProjectName(projectName)) {
    throw new Error(
      `Invalid project name: ${projectName}. ` +
      'Must follow pattern: {team}-{service}-{environment}'
    );
  }

  // Create via Sentry API
  await fetch(`https://sentry.io/api/0/teams/${ORG}/${teamSlug}/projects/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${SENTRY_TOKEN}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ name: projectName }),
  });
}
```

## Audit and Compliance

### Configuration Audit Script
```typescript
// audit-sentry-config.ts
async function auditSentryConfiguration(): Promise<AuditReport> {
  const report: AuditReport = {
    timestamp: new Date(),
    findings: [],
  };

  // Check all projects
  const projects = await getProjects();

  for (const project of projects) {
    // Check naming convention
    if (!validateProjectName(project.name)) {
      report.findings.push({
        severity: 'warning',
        project: project.name,
        issue: 'Project name does not follow naming convention',
      });
    }

    // Check required alerts
    const alerts = await getProjectAlerts(project.id);
    const hasCriticalAlert = alerts.some(a => a.name === 'Critical Error Rate');
    if (!hasCriticalAlert) {
      report.findings.push({
        severity: 'error',
        project: project.name,
        issue: 'Missing required Critical Error Rate alert',
      });
    }

    // Check team assignment
    if (project.teams.length === 0) {
      report.findings.push({
        severity: 'error',
        project: project.name,
        issue: 'Project not assigned to any team',
      });
    }
  }

  return report;
}
```

### Compliance Dashboard
```typescript
// Generate compliance metrics
async function getComplianceMetrics(): Promise<ComplianceMetrics> {
  const projects = await getProjects();
  const total = projects.length;

  return {
    total_projects: total,
    naming_compliant: projects.filter(p => validateProjectName(p.name)).length,
    alerts_configured: projects.filter(p => p.hasRequiredAlerts).length,
    teams_assigned: projects.filter(p => p.teams.length > 0).length,
    compliance_score: calculateComplianceScore(projects),
  };
}
```

## Resources
- [Sentry Organization Settings](https://docs.sentry.io/product/accounts/getting-started/)
- [Sentry API](https://docs.sentry.io/api/)
