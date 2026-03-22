---
name: abridge-cost-tuning
description: |
  Optimize Abridge clinical AI costs through tier selection, session management,
  and usage monitoring for healthcare organizations.
  Use when analyzing Abridge billing, optimizing encounter volume,
  or right-sizing your Abridge contract for provider count.
  Trigger: "abridge cost", "abridge pricing", "abridge billing",
  "abridge budget", "abridge ROI".
allowed-tools: Read, Write, Edit, Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, healthcare, ai, abridge, cost-optimization]
compatible-with: claude-code
---

# Abridge Cost Tuning

## Overview

Abridge pricing is enterprise, sales-led, and per-provider. Cost optimization focuses on maximizing provider adoption (to justify per-provider cost), reducing wasted sessions, and choosing the right tier for your org size.

## Pricing Model (Enterprise)

| Factor | Impact | Optimization Lever |
|--------|--------|-------------------|
| Provider count | Primary cost driver | Only enroll active providers |
| EHR depth | Integration complexity premium | Start with basic, upgrade incrementally |
| Specialty count | Some specialties cost more | Phase specialty rollout |
| Session volume | Included in per-provider pricing | No per-session cost concern |
| Patient summaries | May be add-on | Enable only for portal-integrated sites |
| Languages | Included (28+ languages) | No incremental cost |

## Instructions

### Step 1: Provider Utilization Tracking

```typescript
// src/cost/provider-utilization.ts
interface ProviderUsage {
  providerId: string;
  enrolledDate: Date;
  sessionsThisMonth: number;
  lastSessionDate: Date | null;
  adoptionStatus: 'active' | 'low_usage' | 'dormant' | 'never_used';
}

function classifyProviderUsage(provider: ProviderUsage): string {
  if (provider.sessionsThisMonth === 0 && !provider.lastSessionDate) return 'never_used';
  if (provider.sessionsThisMonth === 0) return 'dormant';

  const daysSinceEnrolled = (Date.now() - provider.enrolledDate.getTime()) / 86400000;
  const sessionsPerDay = provider.sessionsThisMonth / Math.min(daysSinceEnrolled, 30);

  if (sessionsPerDay < 1) return 'low_usage';
  return 'active';
}

function generateUtilizationReport(providers: ProviderUsage[]): {
  total: number;
  active: number;
  lowUsage: number;
  dormant: number;
  neverUsed: number;
  wastedLicenseCost: string;
} {
  const classified = providers.map(p => ({ ...p, status: classifyProviderUsage(p) }));

  const active = classified.filter(p => p.status === 'active').length;
  const lowUsage = classified.filter(p => p.status === 'low_usage').length;
  const dormant = classified.filter(p => p.status === 'dormant').length;
  const neverUsed = classified.filter(p => p.status === 'never_used').length;
  const wastedPercent = ((dormant + neverUsed) / providers.length * 100).toFixed(1);

  return {
    total: providers.length,
    active,
    lowUsage,
    dormant,
    neverUsed,
    wastedLicenseCost: `${wastedPercent}% of licenses are unused`,
  };
}
```

### Step 2: Session Waste Detection

```typescript
// src/cost/session-waste.ts
interface SessionMetrics {
  sessionId: string;
  durationSeconds: number;
  segmentCount: number;
  noteGenerated: boolean;
  noteAccepted: boolean;
  noteEdited: boolean;
}

function detectSessionWaste(sessions: SessionMetrics[]): {
  totalSessions: number;
  wastedSessions: number;
  wasteReasons: Record<string, number>;
} {
  const wasteReasons: Record<string, number> = {
    abandoned: 0,           // Session started but no note generated
    too_short: 0,           // < 30 seconds of content
    rejected: 0,            // Note generated but clinician rejected it
    duplicate: 0,           // Multiple sessions for same encounter
  };

  for (const session of sessions) {
    if (!session.noteGenerated && session.segmentCount > 0) wasteReasons.abandoned++;
    if (session.durationSeconds < 30) wasteReasons.too_short++;
    if (session.noteGenerated && !session.noteAccepted) wasteReasons.rejected++;
  }

  const wastedSessions = Object.values(wasteReasons).reduce((a, b) => a + b, 0);

  return { totalSessions: sessions.length, wastedSessions, wasteReasons };
}
```

### Step 3: ROI Calculator

```typescript
// src/cost/roi-calculator.ts
interface RoiInputs {
  providerCount: number;
  avgEncountersPerProviderPerDay: number;
  avgMinutesSavedPerEncounter: number;  // Abridge claims 2-3 hours/day savings
  providerHourlyRate: number;           // Loaded cost including benefits
  abridgeAnnualCost: number;            // Total contract value
  workingDaysPerYear: number;
}

function calculateRoi(inputs: RoiInputs): {
  annualTimeSavedHours: number;
  annualLaborSavings: number;
  netSavings: number;
  roiPercent: number;
  paybackMonths: number;
} {
  const dailyMinutesSaved = inputs.avgEncountersPerProviderPerDay * inputs.avgMinutesSavedPerEncounter;
  const annualHoursSaved = (dailyMinutesSaved / 60) * inputs.workingDaysPerYear * inputs.providerCount;
  const annualLaborSavings = annualHoursSaved * inputs.providerHourlyRate;
  const netSavings = annualLaborSavings - inputs.abridgeAnnualCost;
  const roiPercent = (netSavings / inputs.abridgeAnnualCost) * 100;
  const paybackMonths = (inputs.abridgeAnnualCost / annualLaborSavings) * 12;

  return {
    annualTimeSavedHours: Math.round(annualHoursSaved),
    annualLaborSavings: Math.round(annualLaborSavings),
    netSavings: Math.round(netSavings),
    roiPercent: Math.round(roiPercent),
    paybackMonths: Math.round(paybackMonths * 10) / 10,
  };
}

// Example: 50 providers, 15 encounters/day, 5 min saved each, $150/hr loaded
// ROI = significant positive return within first year
```

### Step 4: Cost Optimization Recommendations

```typescript
// src/cost/recommendations.ts
function generateCostRecommendations(
  utilization: ReturnType<typeof generateUtilizationReport>,
  waste: ReturnType<typeof detectSessionWaste>,
): string[] {
  const recs: string[] = [];

  if (utilization.neverUsed > 0) {
    recs.push(`Remove ${utilization.neverUsed} never-used provider licenses`);
  }
  if (utilization.dormant > 0) {
    recs.push(`Re-engage or remove ${utilization.dormant} dormant providers`);
  }
  if (waste.wasteReasons.abandoned > waste.totalSessions * 0.1) {
    recs.push('Investigate high abandoned session rate — may indicate training gap');
  }
  if (waste.wasteReasons.rejected > waste.totalSessions * 0.2) {
    recs.push('High note rejection rate — review note templates with clinical leads');
  }

  return recs;
}
```

## Output

- Provider utilization report with waste identification
- Session waste detection with categorized reasons
- ROI calculator for contract justification
- Actionable cost optimization recommendations

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Usage data unavailable | API doesn't expose metrics | Request usage reports from Abridge CSM |
| ROI negative | Low adoption | Focus on provider training before renewal |
| High waste rate | Poor onboarding | Invest in provider change management |

## Resources

- [Abridge Pricing](https://www.abridge.com/)
- [Abridge ROI Studies](https://www.abridge.com/platform)

## Next Steps

For architecture design, see `abridge-reference-architecture`.
