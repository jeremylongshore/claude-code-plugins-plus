# OpenEvidence Cost Tuning - Implementation Details

## Usage Tracker
```typescript
export class UsageTracker {
  async trackQuery(userId: string): Promise<void> { /* Redis-based daily/monthly tracking */ }
  async trackDeepConsult(userId: string): Promise<void> { /* Track expensive DeepConsult usage */ }
  async canMakeQuery(): Promise<{ allowed: boolean; reason?: string }> { /* Check daily limits */ }
  async canRunDeepConsult(): Promise<{ allowed: boolean; reason?: string }> { /* Check budget */ }
}
```

## Smart DeepConsult Management
```typescript
// DeepConsult costs 100x+ more than regular queries
export function shouldUseDeepConsult(question: string, context: ClinicalContext, userTier: string): DeepConsultDecision {
  const simplePatterns = [/what is the (dose|dosage)/i, /half-life of/i, /side effects of/i];
  if (simplePatterns.some(p => p.test(question))) {
    return { shouldUseDeepConsult: false, reason: 'Simple question - regular query sufficient' };
  }
  const complexPatterns = [/compare.*treatments?/i, /systematic review/i, /evidence (for|against)/i];
  if (complexPatterns.some(p => p.test(question)) && userTier !== 'free') {
    return { shouldUseDeepConsult: true, reason: 'Complex research question benefits from DeepConsult' };
  }
  return { shouldUseDeepConsult: false, reason: 'Standard clinical query recommended' };
}
```

## User Quotas & Tiering
```typescript
const USER_TIERS = {
  free: { dailyQueries: 10, monthlyQueries: 100, deepConsultsPerMonth: 0 },
  professional: { dailyQueries: 100, monthlyQueries: 2000, deepConsultsPerMonth: 10 },
  enterprise: { dailyQueries: 1000, monthlyQueries: 30000, deepConsultsPerMonth: 100 },
};
```

## Cost Reporting Dashboard
```typescript
export async function generateCostReport(startDate: Date, endDate: Date): Promise<CostReport> {
  const usage = await aggregateUsage(startDate, endDate);
  return {
    period: { start: startDate, end: endDate },
    summary: { totalQueries: usage.queries, totalDeepConsults: usage.deepConsults, estimatedCost: calculateCost(usage) },
    breakdown: { bySpecialty: usage.bySpecialty, byUser: usage.byUser, byDay: usage.byDay },
    recommendations: generateRecommendations(usage),
  };
}
```
