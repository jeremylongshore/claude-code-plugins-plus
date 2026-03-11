# Evernote Incident Runbook - Implementation Guide

> Full implementation details for the parent SKILL.md.


## Incident Classification

| Severity | Impact | Response Time | Example |
|----------|--------|---------------|---------|
| P1 - Critical | All users affected | 15 min | Complete API outage |
| P2 - High | Major feature broken | 30 min | OAuth failures |
| P3 - Medium | Partial degradation | 2 hours | High error rate |
| P4 - Low | Minor issues | 1 day | Slow response times |


## Incident Response Procedures

### INC-01: Complete API Outage

**Symptoms:**
- All Evernote API calls failing
- 5xx errors from Evernote
- Connection timeouts

**Investigation:**

```bash
curl -I https://www.evernote.com/
curl -I https://sandbox.evernote.com/

```

```javascript
// Step 3: Run diagnostic
async function diagnoseOutage() {
  const results = {
    timestamp: new Date().toISOString(),
    checks: []
  };

  // DNS resolution
  try {
    const dns = require('dns').promises;
    const addresses = await dns.resolve4('www.evernote.com');
    results.checks.push({ name: 'DNS', status: 'ok', addresses });
  } catch (error) {
    results.checks.push({ name: 'DNS', status: 'failed', error: error.message });
  }

  // TCP connectivity
  try {
    const net = require('net');
    await new Promise((resolve, reject) => {
      const socket = net.connect(443, 'www.evernote.com');
      socket.setTimeout(5000);
      socket.on('connect', () => { socket.destroy(); resolve(); });
      socket.on('error', reject);
      socket.on('timeout', () => { socket.destroy(); reject(new Error('Timeout')); });
    });
    results.checks.push({ name: 'TCP', status: 'ok' });
  } catch (error) {
    results.checks.push({ name: 'TCP', status: 'failed', error: error.message });
  }

  // HTTPS request
  try {
    const https = require('https');
    await new Promise((resolve, reject) => {
      const req = https.get('https://www.evernote.com/', { timeout: 10000 }, (res) => {
        results.checks.push({ name: 'HTTPS', status: 'ok', statusCode: res.statusCode });
        resolve();
      });
      req.on('error', reject);
    });
  } catch (error) {
    results.checks.push({ name: 'HTTPS', status: 'failed', error: error.message });
  }

  return results;
}
```

**Mitigation:**

1. Activate circuit breaker to prevent cascading failures
2. Enable graceful degradation (show cached data)
3. Display user-friendly error message
4. Monitor Evernote status page

```javascript
// Activate graceful degradation
const degradationMode = {
  enabled: true,
  reason: 'Evernote service unavailable',
  startTime: Date.now(),

  shouldServeFromCache: true,
  shouldBlockWrites: true,
  userMessage: 'Note syncing is temporarily unavailable. Your changes will sync when service is restored.'
};

// Apply to endpoints
app.use((req, res, next) => {
  if (degradationMode.enabled) {
    res.locals.degradationMode = degradationMode;
  }
  next();
});
```

**Resolution:**
1. Monitor Evernote status for resolution
2. Gradually re-enable API calls
3. Trigger sync for affected users
4. Document incident timeline

---

### INC-02: Rate Limit Crisis

**Symptoms:**
- Frequent RATE_LIMIT_REACHED errors
- rateLimitDuration > 300 seconds
- Multiple users affected

**Investigation:**

```javascript
// Check rate limit metrics
async function analyzeRateLimits() {
  const metrics = await prometheusQuery(`
    sum(increase(evernote_rate_limits_total[1h])) by (api_key)
  `);

  const apiCallRate = await prometheusQuery(`
    sum(rate(evernote_api_calls_total[5m])) by (operation)
  `);

  return {
    rateLimitsLastHour: metrics,
    currentCallRate: apiCallRate,
    suspectedCauses: identifyCauses(apiCallRate)
  };
}

function identifyCauses(callRate) {
  const causes = [];

  // Check for polling abuse
  if (callRate['NoteStore.getSyncState'] > 1) {
    causes.push('Excessive sync state polling');
  }

  // Check for inefficient requests
  if (callRate['NoteStore.getResource'] > 10) {
    causes.push('Individual resource fetching (should batch)');
  }

  return causes;
}
```

**Mitigation:**

```javascript
// Emergency rate limiting
class EmergencyRateLimiter {
  constructor() {
    this.globalPause = false;
    this.pauseUntil = 0;
  }

  async activateEmergencyPause(durationSeconds) {
    this.globalPause = true;
    this.pauseUntil = Date.now() + (durationSeconds * 1000);

    console.warn(`Emergency rate limit pause activated for ${durationSeconds}s`);

    // Notify operations
    await alertOps('Emergency rate limit pause', {
      duration: durationSeconds,
      reason: 'Excessive rate limits detected'
    });

    // Auto-deactivate
    setTimeout(() => {
      this.globalPause = false;
      console.info('Emergency rate limit pause deactivated');
    }, durationSeconds * 1000);
  }

  async checkBeforeRequest() {
    if (this.globalPause) {
      const waitTime = this.pauseUntil - Date.now();
      if (waitTime > 0) {
        throw new Error(`Rate limit emergency: retry in ${Math.ceil(waitTime / 1000)}s`);
      }
    }
  }
}
```

**Resolution:**
1. Identify and fix inefficient API usage
2. Increase cache TTLs
3. Implement request coalescing
4. Request rate limit boost from Evernote

---

### INC-03: Authentication Failures

**Symptoms:**
- Users receiving auth errors
- OAuth flow failing
- Token rejections

**Investigation:**

```javascript
// Auth diagnostic
async function diagnoseAuthIssue(userId) {
  const user = await db.users.findById(userId);
  const token = await db.tokens.findByUserId(userId);

  const diagnosis = {
    userId,
    hasToken: !!token,
    tokenExpired: token ? (Date.now() > token.expiresAt) : null,
    tokenExpiresIn: token ? Math.floor((token.expiresAt - Date.now()) / 1000 / 60 / 60) + ' hours' : null
  };

  // Test token validity
  if (token && !diagnosis.tokenExpired) {
    try {
      const client = new Evernote.Client({ token: token.accessToken, sandbox: false });
      const userStore = client.getUserStore();
      await userStore.getUser();
      diagnosis.tokenValid = true;
    } catch (error) {
      diagnosis.tokenValid = false;
      diagnosis.tokenError = {
        code: error.errorCode,
        parameter: error.parameter
      };
    }
  }

  return diagnosis;
}
```

**Common Causes & Fixes:**

| Error Code | Cause | Fix |
|------------|-------|-----|
| 4 (INVALID_AUTH) | Token revoked | Re-authenticate user |
| 5 (AUTH_EXPIRED) | Token expired | Re-authenticate user |
| 3 (PERMISSION_DENIED) | Insufficient permissions | Check API key permissions |

**Resolution:**
```javascript
// Batch re-auth notification
async function notifyUsersToReauth(userIds) {
  for (const userId of userIds) {
    await sendNotification(userId, {
      type: 'REAUTH_REQUIRED',
      message: 'Please reconnect your Evernote account to continue syncing.',
      action: { type: 'REDIRECT', url: '/auth/evernote' }
    });

    await db.tokens.markInvalid(userId);
  }
}
```

---

### INC-04: Data Sync Issues

**Symptoms:**
- Notes not appearing
- Sync state stuck
- Missing changes

**Investigation:**

```javascript
// Sync state diagnostic
async function diagnoseSyncIssue(userId) {
  const syncState = await db.syncState.findByUserId(userId);
  const client = await getClientForUser(userId);

  const remoteSyncState = await client.noteStore.getSyncState();

  return {
    localUSN: syncState.lastUpdateCount,
    remoteUSN: remoteSyncState.updateCount,
    behind: remoteSyncState.updateCount - syncState.lastUpdateCount,
    lastSyncAt: syncState.lastSyncAt,
    needsSync: remoteSyncState.updateCount > syncState.lastUpdateCount,
    fullSyncRequired: syncState.fullSyncRequired
  };
}

// Force resync
async function forceResync(userId) {
  await db.syncState.update(userId, {
    lastUpdateCount: 0,
    fullSyncRequired: true,
    lastSyncAt: null
  });

  // Queue sync job
  await syncQueue.add('full-sync', { userId, priority: 'high' });

  return { status: 'queued', message: 'Full resync initiated' };
}
```

---


## Incident Communication Templates

### Status Page Update

```markdown


## [Investigating] Evernote Integration Issue

**Time:** [TIMESTAMP]
**Status:** Investigating

We are currently investigating issues with Evernote note synchronization.
Some users may experience delays in note updates.

We will provide updates as we learn more.
```

### User Notification

```markdown


## Temporary Sync Delay

Hi [USER],

We're experiencing a temporary delay in syncing notes with Evernote.
Your local changes are saved and will sync automatically when the
issue is resolved.

No action is needed on your part.

Expected resolution: Within 2 hours

Thank you for your patience.
```

### Resolution Update

```markdown


## [Resolved] Evernote Integration Issue

**Time:** [TIMESTAMP]
**Status:** Resolved

The Evernote synchronization issue has been resolved.
All notes should now be syncing normally.

**Root Cause:** [BRIEF DESCRIPTION]
**Duration:** [X hours Y minutes]
**Impact:** [NUMBER] users affected

We apologize for any inconvenience.
```


## Post-Incident Checklist

```markdown


## Post-Incident Review

### Timeline
- [ ] Document incident timeline
- [ ] Record all actions taken
- [ ] Note what worked/didn't work

### Root Cause
- [ ] Identify root cause
- [ ] Determine contributing factors
- [ ] Assess detection time

### Prevention
- [ ] Define preventive measures
- [ ] Update monitoring/alerts
- [ ] Improve runbooks

### Follow-up
- [ ] Schedule post-mortem meeting
- [ ] Assign action items
- [ ] Update documentation
```
