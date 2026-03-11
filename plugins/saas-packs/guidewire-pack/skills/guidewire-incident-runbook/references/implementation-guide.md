# Guidewire Incident Runbook - Implementation Guide

## Incident Severity Levels

| Severity | Definition | Response Time | Examples |
|----------|------------|---------------|----------|
| SEV-1 | Complete outage | 15 minutes | All users cannot access system |
| SEV-2 | Major degradation | 30 minutes | Critical workflow blocked |
| SEV-3 | Partial degradation | 2 hours | Non-critical feature unavailable |
| SEV-4 | Minor issue | 24 hours | Cosmetic or low-impact issue |

## Incident Response Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          Incident Response Workflow                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐              │
│  │  DETECT   │───▶│  TRIAGE   │───▶│  RESPOND  │───▶│  RESOLVE  │              │
│  │           │    │           │    │           │    │           │              │
│  │ • Alert   │    │ • Severity│    │ • Diagnose│    │ • Fix     │              │
│  │ • Monitor │    │ • Impact  │    │ • Mitigate│    │ • Verify  │              │
│  │ • Report  │    │ • Assign  │    │ • Escalate│    │ • Document│              │
│  └───────────┘    └───────────┘    └───────────┘    └───────────┘              │
│        │                │                │                │                     │
│        └────────────────┴────────────────┴────────────────┘                     │
│                                    │                                            │
│                         ┌──────────▼──────────┐                                 │
│                         │    POST-INCIDENT    │                                 │
│                         │                     │                                 │
│                         │ • Review            │                                 │
│                         │ • Root Cause        │                                 │
│                         │ • Action Items      │                                 │
│                         └─────────────────────┘                                 │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Common Incident Scenarios

### Scenario 1: API Unavailability

**Symptoms:**
- HTTP 503 responses
- Connection timeouts
- "Service Unavailable" errors

**Diagnosis Steps:**

```bash
# 1. Check Guidewire Cloud Console health
curl -s https://gcc.guidewire.com/api/v1/status \
  -H "Authorization: Bearer ${TOKEN}" | jq

# 2. Check application health endpoints
curl -s "${POLICYCENTER_URL}/common/v1/system-info" \
  -H "Authorization: Bearer ${TOKEN}"

# 3. Review recent logs
# In Guidewire Cloud Console: Observability > Logs
# Query: level:ERROR AND timestamp:[now-15m TO now]

# 4. Check for recent deployments
# GCC: Deployments > Recent Activity
```

**Resolution Steps:**

1. **If Guidewire infrastructure issue:**
   - Check [Guidewire Status Page](https://status.guidewire.com)
   - Open support ticket with Guidewire
   - Notify stakeholders of vendor issue

2. **If integration/configuration issue:**
   ```bash
   # Check integration health
   curl -s "${API_URL}/health" | jq

   # Restart affected services (if self-managed components)
   kubectl rollout restart deployment/integration-service
   ```

3. **If capacity issue:**
   - Scale up instances in GCC
   - Review rate limiting settings
   - Implement request throttling

### Scenario 2: High Error Rate

**Symptoms:**
- Elevated 4xx/5xx responses
- Failed transactions
- User-reported errors

**Diagnosis Steps:**

```typescript
// Error analysis script
async function analyzeErrors(timeRange: string = '1h'): Promise<ErrorAnalysis> {
  const logs = await fetchLogs({
    level: 'ERROR',
    timeRange,
    limit: 1000
  });

  // Group by error type
  const byType = logs.reduce((acc, log) => {
    const key = log.context?.error_type || 'unknown';
    acc[key] = (acc[key] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  // Group by endpoint
  const byEndpoint = logs.reduce((acc, log) => {
    const key = log.context?.endpoint || 'unknown';
    acc[key] = (acc[key] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  // Find most common error
  const topError = Object.entries(byType)
    .sort((a, b) => b[1] - a[1])[0];

  return {
    totalErrors: logs.length,
    errorsByType: byType,
    errorsByEndpoint: byEndpoint,
    topError: topError ? { type: topError[0], count: topError[1] } : null,
    sampleErrors: logs.slice(0, 10)
  };
}
```

**Resolution Steps:**

1. **Authentication errors (401):**
   ```bash
   # Verify OAuth configuration
   curl -s "${GW_HUB_URL}/oauth/token" \
     -d "grant_type=client_credentials&client_id=${CLIENT_ID}&client_secret=${CLIENT_SECRET}" \
     | jq

   # Check if credentials were rotated
   # Verify client ID/secret in secret manager
   ```

2. **Validation errors (422):**
   ```bash
   # Review recent code changes
   git log --oneline --since="2 hours ago"

   # Check if data schema changed
   # Review API response details for specific fields
   ```

3. **Server errors (500):**
   ```bash
   # Check application logs for stack traces
   # Review memory/CPU utilization
   # Check database connection pool
   ```

### Scenario 3: Performance Degradation

**Symptoms:**
- Slow page loads
- High API latency
- Timeout errors

**Diagnosis Steps:**

```gosu
// Performance diagnostic Gosu script
package gw.incident.diagnosis

uses gw.api.database.Query
uses gw.api.util.Logger

class PerformanceDiagnostics {
  private static final var LOG = Logger.forCategory("PerformanceDiagnostics")

  static function runDiagnostics() : DiagnosticReport {
    var report = new DiagnosticReport()

    // Check database connection pool
    report.DatabasePoolStatus = checkDatabasePool()

    // Check slow queries
    report.SlowQueries = findSlowQueries()

    // Check memory usage
    report.MemoryStatus = checkMemory()

    // Check active sessions
    report.ActiveSessions = countActiveSessions()

    return report
  }

  private static function checkDatabasePool() : String {
    var pool = gw.api.database.DatabaseConnectionPool.getInstance()
    var available = pool.AvailableConnections
    var total = pool.TotalConnections
    var waiting = pool.WaitingThreads

    if (waiting > 10) {
      return "CRITICAL: ${waiting} threads waiting for connections"
    } else if (available < total * 0.1) {
      return "WARNING: Only ${available}/${total} connections available"
    }
    return "OK: ${available}/${total} connections available"
  }

  private static function checkMemory() : String {
    var runtime = Runtime.getRuntime()
    var used = (runtime.totalMemory() - runtime.freeMemory()) / 1024 / 1024
    var max = runtime.maxMemory() / 1024 / 1024
    var usedPercent = (used * 100.0 / max) as int

    if (usedPercent > 90) {
      return "CRITICAL: ${usedPercent}% memory used (${used}MB/${max}MB)"
    } else if (usedPercent > 80) {
      return "WARNING: ${usedPercent}% memory used (${used}MB/${max}MB)"
    }
    return "OK: ${usedPercent}% memory used (${used}MB/${max}MB)"
  }
}
```

**Resolution Steps:**

1. **Database bottleneck:**
   ```sql
   -- Find long-running queries
   SELECT pid, now() - query_start AS duration, query
   FROM pg_stat_activity
   WHERE state = 'active'
     AND now() - query_start > interval '30 seconds'
   ORDER BY duration DESC;

   -- Kill long-running query if necessary
   SELECT pg_terminate_backend(pid);
   ```

2. **Memory pressure:**
   ```bash
   # Trigger garbage collection (if necessary)
   # This is typically managed by JVM

   # Consider scaling up instances
   # In GCC: Infrastructure > Scaling > Adjust instance size
   ```

3. **Integration bottleneck:**
   ```bash
   # Check external service health
   for endpoint in $INTEGRATION_ENDPOINTS; do
     curl -s -w "\\n%{time_total}s" "${endpoint}/health"
   done

   # Enable circuit breaker if external service is slow
   ```

### Scenario 4: Data Integrity Issue

**Symptoms:**
- Incorrect calculations
- Missing data
- Data inconsistency between systems

**Diagnosis Steps:**

```gosu
// Data integrity check
package gw.incident.data

uses gw.api.database.Query
uses gw.api.util.Logger

class DataIntegrityChecker {
  private static final var LOG = Logger.forCategory("DataIntegrity")

  static function checkPolicyIntegrity() : List<String> {
    var issues = new ArrayList<String>()

    // Check for policies without accounts
    var orphanPolicies = Query.make(Policy)
      .compare(Policy#Account, Equals, null)
      .select()
      .Count

    if (orphanPolicies > 0) {
      issues.add("Found ${orphanPolicies} policies without accounts")
    }

    // Check for claims without policies
    var orphanClaims = Query.make(Claim)
      .compare(Claim#Policy, Equals, null)
      .select()
      .Count

    if (orphanClaims > 0) {
      issues.add("Found ${orphanClaims} claims without policies")
    }

    // Check for premium calculation mismatches
    var premiumMismatches = Query.make(PolicyPeriod)
      .select()
      .where(\pp -> pp.TotalPremiumRPT != pp.calculatePremium())
      .Count

    if (premiumMismatches > 0) {
      issues.add("Found ${premiumMismatches} premium calculation mismatches")
    }

    return issues
  }
}
```

**Resolution Steps:**

1. **Immediate mitigation:**
   - Disable affected functionality if critical
   - Notify affected users
   - Create support ticket

2. **Data correction:**
   ```gosu
   // Careful: Run in test environment first!
   gw.transaction.Transaction.runWithNewBundle(\bundle -> {
     // Fix specific data issue
     var affectedRecords = Query.make(Entity)
       .compare(Entity#Field, Equals, badValue)
       .select()

     affectedRecords.each(\record -> {
       var r = bundle.add(record)
       r.Field = correctValue
       LOG.info("Corrected record: ${r.PublicID}")
     })
   })
   ```

## Incident Communication Templates

### Initial Notification (SEV-1/SEV-2)

```
INCIDENT: [Brief Description]
SEVERITY: SEV-[1/2]
STATUS: Investigating

IMPACT:
- [Describe user impact]
- [Number of users/systems affected]

CURRENT STATUS:
- Issue detected at [TIME]
- Team is actively investigating
- Next update in 30 minutes

INCIDENT COMMANDER: [Name]
CONTACT: [Slack channel / Bridge call]
```

### Status Update

```
INCIDENT UPDATE: [Brief Description]
STATUS: [Investigating / Mitigating / Resolved]

UPDATES SINCE LAST COMMUNICATION:
- [Update 1]
- [Update 2]

CURRENT ACTIONS:
- [Action being taken]

NEXT STEPS:
- [Planned action]
- Next update: [TIME]
```

### Resolution Notification

```
INCIDENT RESOLVED: [Brief Description]

DURATION: [Start time] - [End time] ([X] hours [Y] minutes)

ROOT CAUSE:
[Brief description of root cause]

RESOLUTION:
[What was done to fix the issue]

IMPACT SUMMARY:
- [Number of affected users/transactions]
- [Business impact if known]

FOLLOW-UP ACTIONS:
- Post-incident review scheduled for [DATE]
- [Any immediate follow-up items]
```

## Post-Incident Review Template

```markdown
# Post-Incident Review: [Incident Title]

## Incident Summary
- **Date:** [Date]
- **Duration:** [Start] - [End]
- **Severity:** SEV-[X]
- **Incident Commander:** [Name]

## Timeline
| Time | Event |
|------|-------|
| HH:MM | [Event description] |
| HH:MM | [Event description] |

## Root Cause
[Detailed description of the root cause]

## Impact
- **Users Affected:** [Number]
- **Transactions Affected:** [Number]
- **Revenue Impact:** [If applicable]

## What Went Well
- [Positive aspect 1]
- [Positive aspect 2]

## What Could Be Improved
- [Improvement area 1]
- [Improvement area 2]

## Action Items
| Action | Owner | Due Date |
|--------|-------|----------|
| [Action description] | [Name] | [Date] |

## Lessons Learned
[Key takeaways for the team]
```

## Emergency Contacts

| Role | Name | Contact |
|------|------|---------|
| Primary On-Call | [Rotation] | PagerDuty |
| Secondary On-Call | [Rotation] | PagerDuty |
| Engineering Manager | [Name] | [Phone] |
| Guidewire Support | - | support.guidewire.com |
| Security Incident | Security Team | security@company.com |
