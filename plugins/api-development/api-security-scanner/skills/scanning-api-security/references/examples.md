# API Security Scanner Examples

## Endpoint Auth Matrix Scan

```javascript
// security/auth-matrix.js
const { execSync } = require('child_process');

function scanAuthMatrix(routeFiles) {
  const endpoints = [];
  for (const file of routeFiles) {
    const content = fs.readFileSync(file, 'utf8');
    const routes = content.match(/app\.(get|post|put|patch|delete)\('"['"]/gi) || [];

    for (const route of routes) {
      const [, method, path] = route.match(/app\.(\w+)\('"/);
      const hasAuth = content.includes('authenticateToken') || content.includes('requireAuth');
      const hasRateLimit = content.includes('rateLimiter') || content.includes('rateLimit');

      endpoints.push({ method: method.toUpperCase(), path, hasAuth, hasRateLimit, file });
    }
  }

  const unprotected = endpoints.filter(e =>
    ['POST', 'PUT', 'PATCH', 'DELETE'].includes(e.method) && !e.hasAuth
  );

  return { endpoints, unprotected, total: endpoints.length };
}

// Output:
// | Method | Path            | Auth | Rate Limit | Status  |
// |--------|-----------------|------|------------|---------|
// | POST   | /users          | yes  | yes        | PASS    |
// | DELETE | /users/:id      | yes  | no         | WARNING |
// | POST   | /webhooks/test  | no   | no         | FAIL    |
```

## BOLA Detection (Broken Object Level Authorization)

```javascript
// security/bola-check.js
function checkBOLA(routeHandlers) {
  const findings = [];

  for (const handler of routeHandlers) {
    const code = fs.readFileSync(handler.file, 'utf8');
    const hasParamId = handler.path.includes(':id') || handler.path.includes(':userId');

    if (hasParamId) {
      const hasOwnershipCheck =
        code.includes('req.user.id') && (code.includes('=== ') || code.includes('where'));
      const usesDirectFindById =
        code.includes('findById(req.params') || code.includes('findByPk(req.params');

      if (usesDirectFindById && !hasOwnershipCheck) {
        findings.push({
          severity: 'HIGH',
          type: 'BOLA',
          path: handler.path,
          file: handler.file,
          detail: 'Resource accessed by ID without ownership verification',
        });
      }
    }
  }
  return findings;
}
```

## Mass Assignment Detection

```javascript
function checkMassAssignment(files) {
  const findings = [];
  const dangerousPatterns = [
    /\.create\(req\.body\)/g,
    /\.update\(req\.body\)/g,
    /Object\.assign\(\w+,\s*req\.body\)/g,
    /\{\.\.\.req\.body\}/g,
  ];

  for (const file of files) {
    const content = fs.readFileSync(file, 'utf8');
    for (const pattern of dangerousPatterns) {
      const matches = content.matchAll(pattern);
      for (const match of matches) {
        findings.push({
          severity: 'HIGH',
          type: 'MASS_ASSIGNMENT',
          file,
          line: content.substring(0, match.index).split('\n').length,
          detail: `Direct body passthrough: ${match[0]}`,
          fix: 'Use explicit field allowlist: { name: req.body.name, email: req.body.email }',
        });
      }
    }
  }
  return findings;
}
```

## SQL Injection Pattern Detection

```javascript
function checkInjection(files) {
  const findings = [];
  const patterns = [
    { regex: /`SELECT.*\$\{req\./g, type: 'SQL_INJECTION', severity: 'CRITICAL' },
    { regex: /query\(`.*\+.*req\./g, type: 'SQL_INJECTION', severity: 'CRITICAL' },
    { regex: /\$where.*req\./g, type: 'NOSQL_INJECTION', severity: 'CRITICAL' },
    { regex: /exec\(.*req\./g, type: 'COMMAND_INJECTION', severity: 'CRITICAL' },
    { regex: /eval\(.*req\./g, type: 'CODE_INJECTION', severity: 'CRITICAL' },
  ];

  for (const file of files) {
    const content = fs.readFileSync(file, 'utf8');
    for (const { regex, type, severity } of patterns) {
      const matches = content.matchAll(regex);
      for (const match of matches) {
        findings.push({ severity, type, file,
          line: content.substring(0, match.index).split('\n').length,
          detail: `Potential ${type}: ${match[0].substring(0, 60)}...`,
        });
      }
    }
  }
  return findings;
}
```

## Security Headers Check

```javascript
function checkSecurityHeaders(baseUrl) {
  const required = {
    'strict-transport-security': /max-age=\d+/,
    'x-content-type-options': /nosniff/,
    'x-frame-options': /DENY|SAMEORIGIN/,
  };

  const findings = [];
  const resp = await fetch(baseUrl);

  for (const [header, pattern] of Object.entries(required)) {
    const value = resp.headers.get(header);
    if (!value) {
      findings.push({ severity: 'MEDIUM', type: 'MISSING_HEADER', header });
    } else if (!pattern.test(value)) {
      findings.push({ severity: 'LOW', type: 'WEAK_HEADER', header, value });
    }
  }

  const cors = resp.headers.get('access-control-allow-origin');
  if (cors === '*') {
    findings.push({ severity: 'HIGH', type: 'CORS_WILDCARD',
      detail: 'CORS allows all origins on authenticated endpoint' });
  }
  return findings;
}
```

## OWASP Top 10 Compliance Report

```markdown
# API Security Scan Report

| OWASP Category | Status | Findings |
|---------------|--------|----------|
| API1 - Broken Object Level Auth | WARN | 2 endpoints lack ownership checks |
| API2 - Broken Authentication | PASS | All auth flows verified |
| API3 - Excessive Data Exposure | FAIL | 3 endpoints return full DB records |
| API4 - Lack of Resources/Rate Limiting | WARN | /webhooks missing rate limit |
| API5 - Broken Function Level Auth | PASS | Admin endpoints protected |
| API6 - Mass Assignment | FAIL | 2 handlers use req.body directly |
| API7 - Security Misconfiguration | PASS | Headers correctly configured |
| API8 - Injection | PASS | All queries parameterized |
| API9 - Improper Assets Management | PASS | No undocumented endpoints |
| API10 - Insufficient Logging | WARN | Audit logging missing on 1 endpoint |

Critical: 0 | High: 5 | Medium: 3 | Low: 1
```

## CI Security Gate

```yaml
# .github/workflows/security.yml
- name: Run API security scan
  run: node scripts/security-scan.js --output reports/security.json
- name: Check for blockers
  run: |
    CRITICAL=$(jq '[.findings[] | select(.severity=="CRITICAL")] | length' reports/security.json)
    HIGH=$(jq '[.findings[] | select(.severity=="HIGH")] | length' reports/security.json)
    if [ "$CRITICAL" -gt 0 ] || [ "$HIGH" -gt 0 ]; then
      echo "Security scan found $CRITICAL critical and $HIGH high findings"
      exit 1
    fi
```

## Dependency Vulnerability Scan

```bash
# Node.js
npm audit --json | jq '.vulnerabilities | to_entries[] | select(.value.severity == "critical" or .value.severity == "high")'

# Python
pip-audit --format json --output audit.json

# Go
govulncheck ./...
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
