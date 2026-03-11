# Evernote Production Checklist - Implementation Guide

> Full implementation details for the parent SKILL.md.


## Pre-Production Checklist

### 1. API Key Configuration

```markdown


## API Key Requirements

- [ ] Production API key requested and approved
- [ ] Consumer key and secret stored in secret manager
- [ ] Sandbox mode disabled for production
- [ ] API key permissions match application needs
- [ ] Rate limit boost requested (if needed for initial sync)


## Key Management

- [ ] Different keys for dev/staging/production
- [ ] Key rotation procedure documented
- [ ] Emergency key revocation process defined
```

### 2. Environment Configuration

```javascript
// config/production.js
module.exports = {
  evernote: {
    // NEVER use sandbox in production
    sandbox: false,

    // Production endpoints
    serviceHost: 'www.evernote.com',

    // Timeouts
    requestTimeout: 30000, // 30 seconds
    connectionTimeout: 10000, // 10 seconds

    // Rate limiting
    maxRequestsPerMinute: 50,
    retryAttempts: 3,
    retryDelay: 1000
  },

  session: {
    secure: true,
    httpOnly: true,
    sameSite: 'strict',
    maxAge: 24 * 60 * 60 * 1000 // 24 hours
  },

  logging: {
    level: 'info',
    redactTokens: true
  }
};
```

### 3. Security Checklist

```markdown


## Authentication & Authorization

- [ ] OAuth 1.0a implemented correctly
- [ ] CSRF protection on OAuth flow
- [ ] OAuth state validation
- [ ] Token expiration handling
- [ ] Token refresh workflow (re-auth before expiry)


## Data Protection

- [ ] Tokens encrypted at rest
- [ ] HTTPS enforced (no HTTP fallback)
- [ ] TLS 1.2+ required
- [ ] Sensitive data redacted from logs
- [ ] PII handling compliant with privacy policy


## Input Validation

- [ ] All user inputs validated
- [ ] ENML content sanitized
- [ ] File upload restrictions enforced
- [ ] SQL injection prevention (if using database)
- [ ] XSS prevention in rendered content
```

### 4. Error Handling

```javascript
// middleware/error-handler.js
const logger = require('../utils/secure-logger');

function productionErrorHandler(err, req, res, next) {
  // Log full error internally
  logger.error('Unhandled error', {
    error: err.message,
    stack: err.stack,
    path: req.path,
    method: req.method,
    userId: req.session?.userId
  });

  // Generic response to user
  const statusCode = err.statusCode || 500;

  // Never expose internal details
  res.status(statusCode).json({
    error: statusCode === 500 ?
      'An unexpected error occurred' :
      err.userMessage || 'Request failed',
    requestId: req.id // For support reference
  });
}

module.exports = productionErrorHandler;
```

### 5. Rate Limit Handling

```javascript
// Production rate limit configuration
const rateLimitConfig = {
  // Conservative defaults
  maxRetries: 3,
  baseDelay: 1000,
  maxDelay: 60000,

  // Batch processing limits
  batchSize: 10,
  batchDelay: 500,

  // Circuit breaker
  failureThreshold: 5,
  recoveryTime: 60000
};

// Circuit breaker implementation
class CircuitBreaker {
  constructor(options) {
    this.failureCount = 0;
    this.failureThreshold = options.failureThreshold || 5;
    this.recoveryTime = options.recoveryTime || 60000;
    this.state = 'CLOSED';
    this.lastFailure = null;
  }

  async execute(operation) {
    if (this.state === 'OPEN') {
      if (Date.now() - this.lastFailure > this.recoveryTime) {
        this.state = 'HALF_OPEN';
      } else {
        throw new Error('Circuit breaker is OPEN');
      }
    }

    try {
      const result = await operation();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  onSuccess() {
    this.failureCount = 0;
    this.state = 'CLOSED';
  }

  onFailure() {
    this.failureCount++;
    this.lastFailure = Date.now();

    if (this.failureCount >= this.failureThreshold) {
      this.state = 'OPEN';
    }
  }
}
```

### 6. Monitoring & Alerting

```javascript
// monitoring/metrics.js
const prometheus = require('prom-client');

// API call metrics
const apiCalls = new prometheus.Counter({
  name: 'evernote_api_calls_total',
  help: 'Total Evernote API calls',
  labelNames: ['operation', 'status']
});

const apiLatency = new prometheus.Histogram({
  name: 'evernote_api_latency_seconds',
  help: 'Evernote API call latency',
  labelNames: ['operation'],
  buckets: [0.1, 0.5, 1, 2, 5, 10]
});

const rateLimits = new prometheus.Counter({
  name: 'evernote_rate_limits_total',
  help: 'Total rate limit hits'
});

const authErrors = new prometheus.Counter({
  name: 'evernote_auth_errors_total',
  help: 'Total authentication errors',
  labelNames: ['type']
});

// Alert thresholds (configure in alerting system)
const alertRules = `
groups:
- name: evernote
  rules:
  - alert: HighRateLimitRate
    expr: rate(evernote_rate_limits_total[5m]) > 0.1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: High Evernote rate limit rate

  - alert: HighAuthErrorRate
    expr: rate(evernote_auth_errors_total[5m]) > 0.05
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: High Evernote authentication error rate

  - alert: HighAPILatency
    expr: histogram_quantile(0.95, evernote_api_latency_seconds) > 5
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: High Evernote API latency
`;
```

### 7. Health Checks

```javascript
// routes/health.js
const express = require('express');
const router = express.Router();

router.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

router.get('/health/detailed', async (req, res) => {
  const checks = {
    timestamp: new Date().toISOString(),
    status: 'ok',
    checks: {}
  };

  // Database check
  try {
    await db.query('SELECT 1');
    checks.checks.database = { status: 'ok' };
  } catch (error) {
    checks.checks.database = { status: 'error', message: 'Connection failed' };
    checks.status = 'degraded';
  }

  // Redis check
  try {
    await redis.ping();
    checks.checks.redis = { status: 'ok' };
  } catch (error) {
    checks.checks.redis = { status: 'error', message: 'Connection failed' };
    checks.status = 'degraded';
  }

  // Evernote API check (use sparingly)
  checks.checks.evernote = {
    status: 'ok',
    note: 'Not actively checked to preserve rate limits'
  };

  const statusCode = checks.status === 'ok' ? 200 : 503;
  res.status(statusCode).json(checks);
});

module.exports = router;
```

### 8. Logging Configuration

```javascript
// logging/production.js
const winston = require('winston');

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: {
    service: 'evernote-integration',
    environment: process.env.NODE_ENV
  },
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({
      filename: 'logs/error.log',
      level: 'error',
      maxsize: 10485760, // 10MB
      maxFiles: 5
    }),
    new winston.transports.File({
      filename: 'logs/combined.log',
      maxsize: 10485760,
      maxFiles: 5
    })
  ]
});

// Never log tokens
logger.add(winston.format((info) => {
  if (info.token) info.token = '[REDACTED]';
  if (info.accessToken) info.accessToken = '[REDACTED]';
  return info;
})());

module.exports = logger;
```

### 9. Deployment Verification

```javascript
// scripts/verify-deployment.js

async function verifyDeployment() {
  console.log('=== Deployment Verification ===\n');

  const checks = [];

  // 1. Environment check
  checks.push({
    name: 'Environment variables',
    pass: !!(process.env.EVERNOTE_CONSUMER_KEY &&
             process.env.EVERNOTE_CONSUMER_SECRET),
    critical: true
  });

  // 2. Sandbox mode disabled
  checks.push({
    name: 'Sandbox mode disabled',
    pass: process.env.EVERNOTE_SANDBOX !== 'true',
    critical: true
  });

  // 3. HTTPS enabled
  checks.push({
    name: 'HTTPS configured',
    pass: process.env.APP_URL?.startsWith('https://'),
    critical: true
  });

  // 4. Session secret set
  checks.push({
    name: 'Session secret configured',
    pass: !!process.env.SESSION_SECRET &&
          process.env.SESSION_SECRET.length >= 32,
    critical: true
  });

  // 5. Logging configured
  checks.push({
    name: 'Logging configured',
    pass: process.env.LOG_LEVEL !== 'debug',
    critical: false
  });

  // Report
  let allPassed = true;
  for (const check of checks) {
    const status = check.pass ? 'PASS' : 'FAIL';
    const critical = check.critical ? '(CRITICAL)' : '';
    console.log(`[${status}] ${check.name} ${critical}`);

    if (!check.pass && check.critical) {
      allPassed = false;
    }
  }

  console.log('\n' + (allPassed ?
    'Deployment verification PASSED' :
    'Deployment verification FAILED - fix critical issues'));

  process.exit(allPassed ? 0 : 1);
}

verifyDeployment();
```


## Production Readiness Checklist

```markdown


## Final Checklist Before Go-Live

### API & Authentication
- [ ] Production API key configured
- [ ] Sandbox mode disabled
- [ ] OAuth flow tested end-to-end
- [ ] Token storage encrypted
- [ ] Token expiration handling tested

### Security
- [ ] HTTPS enforced
- [ ] CSRF protection verified
- [ ] Input validation implemented
- [ ] Error messages don't leak sensitive data
- [ ] Security headers configured (HSTS, CSP, etc.)

### Performance
- [ ] Rate limit handling implemented
- [ ] Circuit breaker configured
- [ ] Timeouts set appropriately
- [ ] Connection pooling enabled
- [ ] Caching strategy implemented

### Monitoring
- [ ] Health check endpoints working
- [ ] Metrics collection configured
- [ ] Alerting rules set up
- [ ] Log aggregation configured
- [ ] Error tracking enabled (Sentry, etc.)

### Operations
- [ ] Runbook documented
- [ ] Rollback procedure tested
- [ ] Backup strategy defined
- [ ] On-call rotation established
- [ ] Incident response plan documented

### Compliance
- [ ] Privacy policy updated
- [ ] Terms of service updated
- [ ] Data retention policy defined
- [ ] GDPR compliance verified (if applicable)
- [ ] User consent mechanisms in place
```
