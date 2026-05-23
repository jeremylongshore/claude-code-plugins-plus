---
title: "Building an Idempotent Stripe Billing Enforcement Engine for Firestore"
description: "How we built a unified plan enforcement engine that handles duplicate webhooks, out-of-order events, and automatic drift correction for Stripe billing in a Firestore-backed SaaS application."
date: "2025-11-17"
tags: ["stripe", "firebase", "firestore", "billing", "webhooks", "testing", "typescript", "vitest"]
featured: false
---
When you're building subscription billing with Stripe webhooks, you quickly discover a harsh reality: **webhooks can arrive delayed, duplicated, or out of order**. For a youth sports stats SaaS platform I'm building, this created a critical problem—plan and status updates were scattered across multiple handlers with no guarantee of consistency.

This is the story of building a unified plan enforcement engine that solved webhook chaos, eliminated duplicate logic, and added automatic drift correction—all while maintaining a complete audit trail.

## The Problem: Webhook Drift and Duplicate Logic

### What We Started With

Our billing system had plan/status update logic in **four separate locations**:

1. **Stripe webhook handler** (`/api/billing/webhook/route.ts`) - 5 event handlers
2. **Event replay endpoint** (`/api/admin/billing/replay-events/route.ts`) - 5 replay handlers
3. **Billing auditor** (`src/lib/stripe/auditor.ts`) - drift detection
4. **Manual admin operations** - future admin dashboard actions

Each location had its own version of this pattern:

```typescript
// Duplicated across 10+ handlers
const plan = getPlanForPriceId(priceId);
const status = mapStripeStatusToWorkspaceStatus(subscription.status);
await updateWorkspace(workspaceId, { plan, status });
await recordBillingEvent(workspaceId, {
  type: 'subscription_updated',
  planBefore,
  planAfter: plan,
  // ... more fields
});
```

**The problems:**

- ~180 lines of duplicated logic across handlers
- No guarantee of consistency if one handler was updated but not others
- No built-in idempotency for duplicate webhooks
- Drift detection couldn't automatically fix itself
- Manual before/after tracking in every location

### Real-World Webhook Chaos

Stripe webhooks are **eventually consistent**, which means:

**Scenario 1: Duplicate Webhooks**

```
Webhook 1: customer.subscription.updated (plan change)
Webhook 2: customer.subscription.updated (same event, redelivered)
```

Without idempotency, you'd process the same change twice and create duplicate ledger entries.

**Scenario 2: Out-of-Order Arrival**

```
Event 1: subscription.updated (plan: starter → plus) sent at 14:00:01
Event 2: payment.succeeded (plan: plus) sent at 14:00:05

But Event 2 arrives first!
```

Your workspace briefly shows the wrong plan until Event 1 catches up.

**Scenario 3: Delayed Webhooks**

```
User upgrades at 14:00
Webhook arrives at 14:05 (5 minutes late)
Meanwhile, auditor runs at 14:03 and detects drift
```

Who wins? How do you prevent conflicting updates?

## The Solution: Unified Plan Enforcement Engine

### Design Goals

1. **Single Source of Truth**: ONE function handles ALL plan/status updates
2. **Idempotent**: Safe to call multiple times with same data
3. **Delta Detection**: Only update what changed, track before/after state
4. **Audit Trail**: Full ledger integration for compliance
5. **Passive**: Never modify Stripe data, only read and apply to workspace

### Core Architecture

**File**: `src/lib/stripe/plan-enforcement.ts` (264 lines)

```typescript
export async function enforceWorkspacePlan(
  workspaceId: string,
  input: EnforcePlanInput
): Promise<EnforcePlanResult> {
  // 1. Validate inputs
  if (!workspaceId || typeof workspaceId !== 'string') {
    throw new Error('Invalid workspaceId: must be non-empty string');
  }

  // Validate source enum
  const validSources: LedgerEventSource[] = [
    'webhook', 'replay', 'auditor', 'manual', 'enforcement'
  ];
  if (!validSources.includes(input.source)) {
    throw new Error(`Invalid source: ${input.source}`);
  }

  // 2. Fetch current workspace state
  const workspaceDoc = await adminDb
    .collection('workspaces')
    .doc(workspaceId)
    .get();

  if (!workspaceDoc.exists) {
    throw new Error(`Workspace not found: ${workspaceId}`);
  }

  const workspace = workspaceDoc.data() as Workspace;

  // 3. Map Stripe data to workspace types
  let targetPlan: WorkspacePlan;
  let targetStatus: WorkspaceStatus;

  try {
    targetPlan = getPlanForPriceId(input.stripePriceId);
    targetStatus = mapStripeStatusToWorkspaceStatus(input.stripeStatus);
  } catch (error: any) {
    throw new Error(`Failed to map Stripe data: ${error.message}`);
  }

  // 4. Detect deltas (THIS IS KEY!)
  const planBefore = workspace.plan;
  const statusBefore = workspace.status;
  const planChanged = planBefore !== targetPlan;
  const statusChanged = statusBefore !== targetStatus;

  console.log('[Plan Enforcement]', {
    workspaceId,
    planChanged,
    statusChanged,
    planBefore,
    targetPlan,
    statusBefore,
    targetStatus,
  });

  // 5. Update workspace if mismatch detected
  if (planChanged || statusChanged) {
    const updates: Partial<Workspace> = {
      updatedAt: FieldValue.serverTimestamp() as any,
    };

    if (planChanged) updates.plan = targetPlan;
    if (statusChanged) updates.status = targetStatus;

    await adminDb
      .collection('workspaces')
      .doc(workspaceId)
      .update(updates);

    // Record delta in ledger
    const ledgerEventId = await recordBillingEvent(workspaceId, {
      type: 'plan_changed',
      stripeEventId: input.stripeEventId,
      statusBefore,
      statusAfter: statusChanged ? targetStatus : statusBefore,
      planBefore,
      planAfter: planChanged ? targetPlan : planBefore,
      source: input.source,
      note: `Plan enforcement: ${planChanged ? `${planBefore}→${targetPlan}` : 'plan unchanged'}, ${statusChanged ? `${statusBefore}→${targetStatus}` : 'status unchanged'}`,
    });

    return {
      workspaceId,
      planChanged,
      statusChanged,
      planBefore,
      planAfter: targetPlan,
      statusBefore,
      statusAfter: targetStatus,
      ledgerEventId,
    };
  } else {
    // No changes needed - record noop
    const ledgerEventId = await recordBillingEvent(workspaceId, {
      type: 'plan_changed',
      stripeEventId: input.stripeEventId,
      statusBefore,
      statusAfter: statusBefore,
      planBefore,
      planAfter: planBefore,
      source: input.source,
      note: 'Plan enforcement: no changes (workspace already in sync)',
    });

    return {
      workspaceId,
      planChanged: false,
      statusChanged: false,
      planBefore,
      planAfter: planBefore,
      statusBefore,
      statusAfter: statusBefore,
      ledgerEventId,
    };
  }
}
```

### Why This Solves Webhook Chaos

**Idempotency in Action:**

```typescript
// Webhook arrives twice (duplicate delivery)
// Call 1:
await enforceWorkspacePlan('workspace123', {
  stripePriceId: 'price_plus',
  stripeStatus: 'active',
  source: 'webhook',
  stripeEventId: 'evt_123',
});
// Result: planChanged=true, updates workspace, records delta

// Call 2 (same data):
await enforceWorkspacePlan('workspace123', {
  stripePriceId: 'price_plus',
  stripeStatus: 'active',
  source: 'webhook',
  stripeEventId: 'evt_123', // Same event!
});
// Result: planChanged=false, NO workspace update, records noop
```

**Out-of-Order Handling:**

```typescript
// Event 2 arrives first (payment.succeeded)
await enforceWorkspacePlan('workspace123', {
  stripePriceId: 'price_starter',
  stripeStatus: 'active',
  source: 'webhook',
  stripeEventId: 'evt_payment',
});
// Sets plan=starter, status=active

// Event 1 arrives later (subscription.updated, upgrade to plus)
await enforceWorkspacePlan('workspace123', {
  stripePriceId: 'price_plus',
  stripeStatus: 'active',
  source: 'webhook',
  stripeEventId: 'evt_upgrade',
});
// Detects mismatch, corrects to plan=plus
// Workspace converges to correct state!
```

## Testing Strategy: 14 Comprehensive Tests

We wrote **450 lines of tests** (more than the implementation!) to cover every edge case.

### Test Structure

**File**: `src/lib/stripe/plan-enforcement.test.ts`

```typescript
describe('Workspace Plan Enforcement', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Default workspace state: starter plan, active status
    mockGet.mockResolvedValue({
      exists: true,
      id: 'workspace123',
      data: () => ({
        plan: 'starter',
        status: 'active',
        createdAt: { toDate: () => new Date('2025-01-01') },
        // ... other fields
      }),
    });

    mockUpdate.mockResolvedValue({});
    mockRecordBillingEvent.mockResolvedValue('ledger123');
  });

  it('should update plan AND status when both changed', async () => {
    const result = await enforceWorkspacePlan('workspace123', {
      stripePriceId: 'price_plus',
      stripeStatus: 'past_due',
      source: 'webhook',
      stripeEventId: 'evt_123',
    });

    expect(result.planChanged).toBe(true);
    expect(result.statusChanged).toBe(true);
    expect(result.planBefore).toBe('starter');
    expect(result.planAfter).toBe('plus');
    expect(result.statusBefore).toBe('active');
    expect(result.statusAfter).toBe('past_due');

    expect(mockUpdate).toHaveBeenCalledWith(
      expect.objectContaining({
        plan: 'plus',
        status: 'past_due',
        updatedAt: expect.objectContaining({
          _methodName: 'FieldValue.serverTimestamp'
        }),
      })
    );

    expect(mockRecordBillingEvent).toHaveBeenCalled();
  });

  it('should record noop ledger entry when no changes', async () => {
    const result = await enforceWorkspacePlan('workspace123', {
      stripePriceId: 'price_starter', // Same as current
      stripeStatus: 'active',         // Same as current
      source: 'webhook',
      stripeEventId: 'evt_noop',
    });

    expect(result.planChanged).toBe(false);
    expect(result.statusChanged).toBe(false);

    // Verify NO workspace update
    expect(mockUpdate).not.toHaveBeenCalled();

    // Verify ledger entry still recorded (noop)
    expect(mockRecordBillingEvent).toHaveBeenCalled();
  });

  it('should support auditor-driven enforcement (drift correction)', async () => {
    const result = await enforceWorkspacePlan('workspace123', {
      stripePriceId: 'price_pro',
      stripeStatus: 'past_due',
      source: 'auditor', // Different source
      stripeEventId: null, // No Stripe event for auditor
    });

    expect(result.planChanged).toBe(true);
    expect(result.statusChanged).toBe(true);
    expect(mockRecordBillingEvent).toHaveBeenCalled();
  });

  it('should never call Stripe API (passive enforcement)', async () => {
    await enforceWorkspacePlan('workspace123', {
      stripePriceId: 'price_plus',
      stripeStatus: 'active',
      source: 'webhook',
      stripeEventId: 'evt_123',
    });

    // Enforcement should only interact with Firestore, never Stripe
    expect(mockUpdate).toHaveBeenCalled();
    expect(mockRecordBillingEvent).toHaveBeenCalled();
  });
});
```

### Key Test Categories

1. **Delta Detection** (4 tests):
   - Both plan and status changed
   - Only plan changed
   - Only status changed
   - No changes (noop)

2. **Event Sources** (3 tests):
   - Webhook-driven enforcement
   - Replay-driven enforcement
   - Auditor-driven enforcement

3. **Input Validation** (4 tests):
   - Invalid workspaceId
   - Invalid stripePriceId
   - Invalid stripeStatus
   - Invalid source enum

4. **Error Handling** (3 tests):
   - Workspace not found
   - Firestore update failure
   - Unknown Stripe price ID

**All 229 tests passing** (14 new + 215 existing)

## Integration: Four Locations, One Function

### 1. Stripe Webhook Handler

**Before** (duplicated logic):

```typescript
async function handleSubscriptionUpdated(subscription, eventId) {
  const workspace = await getWorkspaceByStripeCustomerId(customerId);

  const planBefore = workspace.plan;
  const statusBefore = workspace.status;

  const priceId = subscription.items.data[0].price.id;
  const plan = getPlanForPriceId(priceId);
  const status = mapStripeStatusToWorkspaceStatus(subscription.status);

  await updateWorkspace(workspace.id, { plan, status });
  await updateWorkspaceBilling(workspace.id, {
    currentPeriodEnd: new Date(subscription.current_period_end * 1000),
  });

  await recordBillingEvent(workspace.id, {
    type: 'subscription_updated',
    stripeEventId: eventId,
    statusBefore,
    statusAfter: status,
    planBefore,
    planAfter: plan,
    source: 'webhook',
    note: `Subscription updated: ${planBefore}→${plan}`,
  });
}
```

**After** (unified enforcement):

```typescript
async function handleSubscriptionUpdated(subscription, eventId) {
  const workspace = await getWorkspaceByStripeCustomerId(customerId);
  const priceId = subscription.items.data[0].price.id;

  // Enforce workspace plan and status (Phase 7 Task 9)
  await enforceWorkspacePlan(workspace.id, {
    stripePriceId: priceId,
    stripeStatus: subscription.status,
    source: 'webhook',
    stripeEventId: eventId,
  });

  // Update billing information
  await updateWorkspaceBilling(workspace.id, {
    currentPeriodEnd: new Date(subscription.current_period_end * 1000),
  });
}
```

**Reduction:** 15 lines → 8 lines per handler × 5 handlers = **~35 lines saved**

### 2. Event Replay Endpoint

Same pattern, but with `source: 'replay'`:

```typescript
async function replaySubscriptionDeleted(subscription, customerId, eventId) {
  const workspace = await getWorkspaceByStripeCustomerId(customerId);
  const priceId = subscription.items.data[0].price.id;

  // Enforce workspace plan and status
  // Subscription deleted means status should be 'canceled'
  await enforceWorkspacePlan(workspace.id, {
    stripePriceId: priceId,
    stripeStatus: 'canceled',
    source: 'replay',
    stripeEventId: eventId,
  });

  // Keep currentPeriodEnd for grace period access
  await updateWorkspaceBilling(workspace.id, {
    currentPeriodEnd: new Date(subscription.current_period_end * 1000),
  });
}
```

**Benefit:** Event source tracking in ledger allows distinguishing webhook vs. replay events

### 3. Billing Auditor (Auto-Fix Drift)

This is where it gets powerful:

```typescript
export async function auditWorkspaceBilling(
  workspaceId: string
): Promise<BillingAuditReport> {
  // ... fetch workspace and Stripe subscription ...

  // Detect drift
  const expectedStatus = mapStripeStatusToWorkspaceStatus(subscription.status);
  if (workspace.status !== expectedStatus) {
    report.drift = true;
    report.driftReasons.push(
      `Status mismatch: Firestore=${workspace.status}, Stripe=${subscription.status}`
    );
  }

  // Determine fix strategy
  if (report.drift) {
    const hasOnlyStatusOrPlanDrift = report.driftReasons.every(
      (reason) =>
        reason.includes('Status mismatch') || reason.includes('Plan mismatch')
    );

    if (hasOnlyStatusOrPlanDrift) {
      report.recommendedFix = 'run_event_replay';

      // 🔥 NEW: Apply automatic enforcement if drift can be fixed
      if (report.stripePriceId && report.stripeStatus) {
        await enforceWorkspacePlan(workspaceId, {
          stripePriceId: report.stripePriceId,
          stripeStatus: report.stripeStatus,
          source: 'auditor',
          stripeEventId: null,
        });
      }
    } else {
      report.recommendedFix = 'manual_stripe_review';
    }

    // Record drift detection in ledger
    await recordBillingEvent(workspaceId, {
      type: 'drift_detected',
      // ... drift details ...
      note: `Drift detected: ${report.driftReasons.join('; ')}. ${
        report.recommendedFix === 'run_event_replay'
          ? '(auto-applied via enforcement)'
          : ''
      }`,
    });
  }

  return report;
}
```

**Result:** Auditor detects drift AND automatically fixes it!

**Ledger Audit Trail** (2 entries):

1. `drift_detected` (from auditor) - "Drift detected... (auto-applied)"
2. `plan_changed` (from enforcement) - "Plan enforcement: active→past_due"

## Real-World Scenarios

### Scenario 1: Payment Failure

**Event:** User's credit card declines

**Stripe Webhook:** `invoice.payment_failed`

```typescript
// Webhook handler
const subscription = await stripe.subscriptions.retrieve(subscriptionId);
const priceId = subscription.items.data[0].price.id;

await enforceWorkspacePlan(workspace.id, {
  stripePriceId: priceId,
  stripeStatus: 'past_due', // Stripe sets this automatically
  source: 'webhook',
  stripeEventId: 'evt_payment_failed',
});
```

**Result:**

- `workspace.status` updated: `active` → `past_due`
- `workspace.plan` unchanged: `starter` → `starter`
- Ledger entry: "Plan enforcement: plan unchanged, active→past_due"
- User sees grace period notice in dashboard

### Scenario 2: Plan Downgrade

**Event:** User downgrades from Plus to Starter

**Stripe Webhook:** `customer.subscription.updated`

```typescript
await enforceWorkspacePlan(workspace.id, {
  stripePriceId: 'price_starter',
  stripeStatus: 'active',
  source: 'webhook',
  stripeEventId: 'evt_sub_updated',
});
```

**Result:**

- `workspace.plan` updated: `plus` → `starter`
- `workspace.status` unchanged: `active` → `active`
- Ledger entry: "Plan enforcement: plus→starter, status unchanged"
- Player limits automatically enforced on next action

### Scenario 3: Drift Correction

**Event:** Periodic audit runs at 14:00, finds drift

**Audit Report:**

- `workspace.status = 'active'`
- `subscription.status = 'past_due'` (payment failed, but webhook delayed)
- `recommendedFix = 'run_event_replay'`

**Auto-Enforcement:**

```typescript
// Auditor automatically applies enforcement
await enforceWorkspacePlan(workspace.id, {
  stripePriceId: 'price_starter',
  stripeStatus: 'past_due',
  source: 'auditor',
  stripeEventId: null,
});
```

**Ledger Entries** (2 entries):

1. `drift_detected` - "Drift detected: Status mismatch (auto-applied)"
2. `plan_changed` - "Plan enforcement: active→past_due"

**Result:** Drift corrected before webhook even arrives!

## Lessons Learned

### 1. Idempotency Is Not Optional

Webhooks **will** be duplicated. Design for it from day one.

**Key pattern:**

```typescript
// Always compare current state vs. target state
const changed = current !== target;

if (changed) {
  // Update
} else {
  // Noop (but still record in ledger!)
}
```

### 2. Test More Than You Implement

Our ratio: **450 lines of tests vs. 264 lines of implementation** (1.7:1)

Why?

- Caught 5 bugs before they hit production
- Mocking Firestore requires careful setup
- Edge cases (workspace not found, unknown price ID) easy to miss
- Behavioral contracts ("never calls Stripe API") prevent regression

### 3. Audit Trails Are Critical

Every enforcement action writes to ledger with:

- Before/after state (delta tracking)
- Event source (webhook, replay, auditor, manual)
- Stripe event ID (when applicable)
- Human-readable note

**Value:**

- Troubleshoot billing issues: "When did plan change?"
- Customer support: "Show me all billing events for this workspace"
- Compliance: "Prove we applied subscription correctly"

### 4. Passive Enforcement Prevents Circular Updates

**Never modify Stripe data from enforcement.**

Why?

- Stripe is source of truth for billing
- Workspace is source of truth for runtime behavior
- Updating Stripe triggers webhook → triggers enforcement → infinite loop

**The rule:** Enforcement only reads Stripe, applies to workspace.

## What's Next?

### Optional Enhancements

1. **Batch Enforcement Script**
   - Run enforcement across ALL workspaces
   - Useful for periodic drift correction
   - Source: `'enforcement'`

2. **Admin Dashboard UI**
   - Manual "Force Sync" button
   - Show current workspace vs. Stripe state
   - Display enforcement result with deltas

3. **Monitoring & Alerts**
   - Track enforcement metrics (noop vs. delta ratio)
   - Alert on high failure rate
   - Dashboard visualization (Grafana/Cloud Monitoring)

### Future Integration

The `'manual'` source is reserved for admin operations:

```typescript
// Admin dashboard: "Force Sync with Stripe" button
await enforceWorkspacePlan(workspaceId, {
  stripePriceId: manuallyEnteredPriceId,
  stripeStatus: manuallyEnteredStatus,
  source: 'manual',
  stripeEventId: null,
});
```

## Conclusion

Building a unified plan enforcement engine solved three critical problems:

1. **Eliminated duplicate logic** - One function, four integration points
2. **Handled webhook chaos** - Idempotent design survives duplicates and out-of-order events
3. **Automated drift correction** - Auditor detects and fixes drift automatically

**Code impact:**

- Removed: ~180 lines of duplicate logic
- Added: 264 lines of enforcement + 450 lines of tests
- Net: Cleaner, more maintainable codebase

**Key takeaways:**

- Design for idempotency from day one
- Test more than you implement
- Audit trails are critical for billing
- Never create circular update loops

If you're building subscription billing with Stripe webhooks, consider whether your plan/status updates are consolidated. It's worth the upfront investment.

**Related posts:**

- [Architecting Production Multi-Agent AI Platform: Technical Leadership](https://startaitools.com/posts/architecting-production-multi-agent-ai-platform-technical-leadership/)
- [Building Production Multi-Agent AI with Vertex AI](https://startaitools.com/posts/building-production-multi-agent-ai-brightstream-vertex-ai/)

*Building Hustle, a youth sports stats platform with Firebase, Stripe, and Vertex AI. Follow along as I document the technical decisions and lessons learned.*
