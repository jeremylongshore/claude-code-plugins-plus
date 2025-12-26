---
name: scan-api-security
description: Scan API for security vulnerabilities
shortcut: apis
---
# Scan API Security

Perform comprehensive automated security scanning to identify OWASP API Security Top 10 vulnerabilities, misconfigurations, and potential attack vectors with detailed remediation guidance.

## When to Use This Command

Use `/scan-api-security` when you need to:
- Audit API security before production deployment
- Perform regular security assessments
- Validate security fixes and patches
- Comply with security standards (OWASP, PCI DSS)
- Identify authentication and authorization flaws
- Detect data exposure and injection vulnerabilities

DON'T use this when:
- Scanning third-party APIs without permission (illegal)
- As a replacement for manual security review (use both)
- Performance testing is the primary goal (use load testing instead)

## Design Decisions

This command implements **OWASP ZAP + Custom Scanners** as the primary approach because:
- Industry-standard security testing framework
- Comprehensive vulnerability coverage
- Active and passive scanning modes
- API-specific security checks
- Detailed reporting and remediation guidance
- Integration with CI/CD pipelines

**Alternative considered: Burp Suite**
- More features for manual testing
- Better for complex authentication flows
- Commercial license required
- Recommended for enterprise environments

**Alternative considered: Manual testing only**
- More thorough for business logic flaws
- Time-consuming and expensive
- Inconsistent coverage
- Recommended as complement to automated scanning

## Prerequisites

Before running this command:
1. API documentation (OpenAPI/Swagger preferred)
2. Test environment with realistic data
3. Authentication credentials for all roles
4. Permission to perform security testing
5. Baseline security requirements defined

## Implementation Process

### Step 1: Configure Security Scanner
Set up OWASP ZAP or similar tools with API-specific rules and authentication.

### Step 2: Perform Automated Scanning
Run comprehensive automated scans for known vulnerability patterns.

### Step 3: Execute Manual Verification
Verify critical findings and test business logic vulnerabilities.

### Step 4: Analyze Results
Review findings, eliminate false positives, and prioritize by severity.

### Step 5: Generate Security Report
Create detailed report with findings, evidence, and remediation steps.

## Output Format

The command generates:
- `security-report.html` - Executive summary with charts
- `vulnerabilities.json` - Machine-readable findings
- `evidence/` - Screenshots and request/response logs
- `remediation-guide.md` - Fix recommendations by priority
- `security-tests.py` - Regression tests for found issues
- `compliance-checklist.md` - Standards compliance status

## Code Examples

### Example 1: Comprehensive API Security Scanner

```javascript
// security-scanner.js
const ZAPClient = require('zaproxy');
const axios = require('axios');
const jwt = require('jsonwebtoken');
const { createHash } = require('crypto');

class APISecurityScanner {
  constructor(apiUrl, options = {}) {
    this.apiUrl = apiUrl;
    this.zapOptions = {
      proxy: options.zapProxy || 'http://localhost:8080',
      apiKey: options.zapApiKey || 'your-zap-api-key'
    };
    this.zap = new ZAPClient(this.zapOptions);
    this.findings = [];
    this.credentials = options.credentials || {};
  }

  async runComprehensiveScan() {
    console.log('Starting comprehensive API security scan...');

    try {
      // Phase 1: Authentication Testing
      await this.testAuthentication();

      // Phase 2: Authorization Testing
      await this.testAuthorization();

      // Phase 3: Input Validation
      await this.testInputValidation();

      // Phase 4: Data Exposure
      await this.testDataExposure();

      // Phase 5: Rate Limiting
      await this.testRateLimiting();

      // Phase 6: Security Headers
      await this.testSecurityHeaders();

      // Phase 7: OWASP Top 10 API
      await this.testOWASPTop10();

      // Generate report
      return this.generateReport();
    } catch (error) {
      console.error('Security scan failed:', error);
      throw error;
    }
  }

  async testAuthentication() {
    console.log('Testing authentication mechanisms...');

    const tests = [
      // Test 1: Broken Authentication
      {
        name: 'JWT Algorithm Confusion',
        test: async () => {
          const token = jwt.sign({ user: 'admin' }, 'secret', { algorithm: 'HS256' });
          const modifiedToken = token.replace('HS256', 'none');

          try {
            const response = await axios.get(`${this.apiUrl}/protected`, {
              headers: { Authorization: `Bearer ${modifiedToken}` }
            });

            if (response.status === 200) {
              this.addFinding({
                severity: 'CRITICAL',
                category: 'Authentication',
                title: 'JWT Algorithm Confusion Vulnerability',
                description: 'API accepts JWT tokens with "none" algorithm',
                evidence: { token: modifiedToken, response: response.data },
                remediation: 'Explicitly verify JWT algorithm, reject "none"'
              });
            }
          } catch (error) {
            // Expected behavior - authentication should fail
          }
        }
      },

      // Test 2: Weak Password Policy
      {
        name: 'Weak Password Policy',
        test: async () => {
          const weakPasswords = ['123456', 'password', 'admin'];

          for (const password of weakPasswords) {
            try {
              const response = await axios.post(`${this.apiUrl}/register`, {
                username: 'testuser',
                password: password
              });

              if (response.status === 201) {
                this.addFinding({
                  severity: 'HIGH',
                  category: 'Authentication',
                  title: 'Weak Password Policy',
                  description: `API accepts weak password: "${password}"`,
                  evidence: { password, response: response.status },
                  remediation: 'Implement strong password requirements'
                });
              }
            } catch (error) {
              // Good - weak password rejected
            }
          }
        }
      },

      // Test 3: Session Fixation
      {
        name: 'Session Fixation',
        test: async () => {
          const fixedSession = 'fixed-session-id-12345';

          try {
            // Try to set a fixed session ID
            const response = await axios.post(`${this.apiUrl}/login`,
              { username: 'user', password: 'pass' },
              { headers: { 'Cookie': `sessionId=${fixedSession}` } }
            );

            const setCookie = response.headers['set-cookie'];
            if (setCookie && setCookie.includes(fixedSession)) {
              this.addFinding({
                severity: 'HIGH',
                category: 'Authentication',
                title: 'Session Fixation Vulnerability',
                description: 'API accepts client-provided session IDs',
                evidence: { providedSession: fixedSession, setCookie },
                remediation: 'Always generate new session IDs on login'
              });
            }
          } catch (error) {
            // Expected - login might fail
          }
        }
      }
    ];

    for (const test of tests) {
      try {
        await test.test();
      } catch (error) {
        console.error(`Test "${test.name}" failed:`, error.message);
      }
    }
  }

  async testAuthorization() {
    console.log('Testing authorization controls...');

    // Test IDOR vulnerabilities
    const userTokens = {
      user1: await this.getAuthToken('user1', 'password1'),
      user2: await this.getAuthToken('user2', 'password2')
    };

    // Try to access user2's data with user1's token
    try {
      const response = await axios.get(`${this.apiUrl}/users/user2/profile`, {
        headers: { Authorization: `Bearer ${userTokens.user1}` }
      });

      if (response.status === 200) {
        this.addFinding({
          severity: 'CRITICAL',
          category: 'Authorization',
          title: 'Insecure Direct Object Reference (IDOR)',
          description: 'User can access other users\' private data',
          evidence: {
            authenticatedAs: 'user1',
            accessedData: 'user2/profile',
            response: response.data
          },
          remediation: 'Implement proper authorization checks for all resources'
        });
      }
    } catch (error) {
      // Good - access denied
    }

    // Test privilege escalation
    try {
      const response = await axios.post(`${this.apiUrl}/admin/users`,
        { role: 'admin' },
        { headers: { Authorization: `Bearer ${userTokens.user1}` } }
      );

      if (response.status === 200) {
        this.addFinding({
          severity: 'CRITICAL',
          category: 'Authorization',
          title: 'Privilege Escalation',
          description: 'Regular user can perform admin actions',
          evidence: { endpoint: '/admin/users', response: response.status },
          remediation: 'Implement role-based access control (RBAC)'
        });
      }
    } catch (error) {
      // Expected - should be forbidden
    }
  }

  async testInputValidation() {
    console.log('Testing input validation...');

    const injectionPayloads = {
      sql: ["' OR '1'='1", "admin'--", "1; DROP TABLE users--"],
      nosql: ['{"$gt": ""}', '{"$ne": null}', '{"$regex": ".*"}'],
      command: ['| ls -la', '; cat /etc/passwd', '`whoami`'],
      xxe: ['<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>'],
      xss: ['<script>alert(1)</script>', 'javascript:alert(1)', '<img src=x onerror=alert(1)>']
    };

    for (const [type, payloads] of Object.entries(injectionPayloads)) {
      for (const payload of payloads) {
        try {
          const response = await axios.post(`${this.apiUrl}/search`, {
            query: payload
          });

          // Check if payload appears unescaped in response
          if (response.data && JSON.stringify(response.data).includes(payload)) {
            this.addFinding({
              severity: 'CRITICAL',
              category: 'Injection',
              title: `${type.toUpperCase()} Injection Vulnerability`,
              description: `API vulnerable to ${type} injection`,
              evidence: { payload, response: response.data },
              remediation: `Implement proper input validation and parameterized queries`
            });
          }
        } catch (error) {
          // Error might indicate successful injection prevention
        }
      }
    }
  }

  async testDataExposure() {
    console.log('Testing for excessive data exposure...');

    try {
      const response = await axios.get(`${this.apiUrl}/users`);

      if (response.data && Array.isArray(response.data)) {
        const sensitiveFields = ['password', 'ssn', 'creditCard', 'apiKey', 'secret'];
        const exposedFields = [];

        response.data.forEach(user => {
          sensitiveFields.forEach(field => {
            if (user[field] !== undefined) {
              exposedFields.push(field);
            }
          });
        });

        if (exposedFields.length > 0) {
          this.addFinding({
            severity: 'HIGH',
            category: 'Data Exposure',
            title: 'Sensitive Data Exposure',
            description: 'API returns sensitive fields in responses',
            evidence: { exposedFields: [...new Set(exposedFields)] },
            remediation: 'Filter sensitive fields from API responses'
          });
        }
      }
    } catch (error) {
      console.error('Data exposure test failed:', error.message);
    }
  }

  async testRateLimiting() {
    console.log('Testing rate limiting...');

    const endpoint = `${this.apiUrl}/login`;
    const requests = [];
    const requestCount = 100;

    // Send rapid requests
    for (let i = 0; i < requestCount; i++) {
      requests.push(
        axios.post(endpoint, {
          username: 'test',
          password: `attempt${i}`
        }).catch(err => ({ status: err.response?.status }))
      );
    }

    const responses = await Promise.all(requests);
    const successfulRequests = responses.filter(r => r.status !== 429).length;

    if (successfulRequests === requestCount) {
      this.addFinding({
        severity: 'HIGH',
        category: 'Rate Limiting',
        title: 'Missing Rate Limiting',
        description: 'API endpoints lack rate limiting protection',
        evidence: {
          endpoint,
          requestsSent: requestCount,
          successfulRequests
        },
        remediation: 'Implement rate limiting on all endpoints'
      });
    }
  }

  async testSecurityHeaders() {
    console.log('Testing security headers...');

    try {
      const response = await axios.get(this.apiUrl);
      const headers = response.headers;

      const requiredHeaders = {
        'x-content-type-options': 'nosniff',
        'x-frame-options': 'DENY',
        'x-xss-protection': '1; mode=block',
        'strict-transport-security': 'max-age=31536000',
        'content-security-policy': null // Just check existence
      };

      const missingHeaders = [];

      for (const [header, expectedValue] of Object.entries(requiredHeaders)) {
        if (!headers[header]) {
          missingHeaders.push(header);
        } else if (expectedValue && headers[header] !== expectedValue) {
          missingHeaders.push(`${header} (incorrect value)`);
        }
      }

      if (missingHeaders.length > 0) {
        this.addFinding({
          severity: 'MEDIUM',
          category: 'Security Headers',
          title: 'Missing Security Headers',
          description: 'Important security headers are missing',
          evidence: { missingHeaders },
          remediation: 'Add all recommended security headers'
        });
      }
    } catch (error) {
      console.error('Security headers test failed:', error.message);
    }
  }

  async testOWASPTop10() {
    console.log('Running OWASP API Security Top 10 tests...');

    // Use ZAP for comprehensive scanning
    await this.zap.core.newSession('api-security-scan', true);
    await this.zap.core.setMode('attack');

    // Configure context
    const contextId = await this.zap.context.newContext('API Context');
    await this.zap.context.includeInContext(contextId, `${this.apiUrl}.*`);

    // Run active scan
    const scanId = await this.zap.ascan.scan(this.apiUrl, true, true);

    // Wait for scan completion
    let progress = 0;
    while (progress < 100) {
      progress = await this.zap.ascan.status(scanId);
      await this.delay(5000);
      console.log(`Scan progress: ${progress}%`);
    }

    // Get results
    const alerts = await this.zap.core.alerts(this.apiUrl);

    alerts.forEach(alert => {
      this.addFinding({
        severity: this.mapZAPSeverity(alert.risk),
        category: 'OWASP Scan',
        title: alert.name,
        description: alert.description,
        evidence: {
          url: alert.url,
          param: alert.param,
          attack: alert.attack,
          evidence: alert.evidence
        },
        remediation: alert.solution
      });
    });
  }

  addFinding(finding) {
    this.findings.push({
      ...finding,
      timestamp: new Date().toISOString(),
      id: createHash('md5').update(JSON.stringify(finding)).digest('hex')
    });
  }

  mapZAPSeverity(risk) {
    const mapping = {
      'High': 'CRITICAL',
      'Medium': 'HIGH',
      'Low': 'MEDIUM',
      'Informational': 'LOW'
    };
    return mapping[risk] || 'MEDIUM';
  }

  async getAuthToken(username, password) {
    try {
      const response = await axios.post(`${this.apiUrl}/login`, {
        username,
        password
      });
      return response.data.token;
    } catch (error) {
      console.error(`Failed to authenticate ${username}`);
      return null;
    }
  }

  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  generateReport() {
    const report = {
      scanDate: new Date().toISOString(),
      targetAPI: this.apiUrl,
      summary: {
        total: this.findings.length,
        critical: this.findings.filter(f => f.severity === 'CRITICAL').length,
        high: this.findings.filter(f => f.severity === 'HIGH').length,
        medium: this.findings.filter(f => f.severity === 'MEDIUM').length,
        low: this.findings.filter(f => f.severity === 'LOW').length
      },
      findings: this.findings,
      recommendations: this.generateRecommendations()
    };

    // Save report
    require('fs').writeFileSync(
      'security-report.json',
      JSON.stringify(report, null, 2)
    );

    console.log('\nSecurity Scan Complete!');
    console.log(`Total findings: ${report.summary.total}`);
    console.log(`Critical: ${report.summary.critical}`);
    console.log(`High: ${report.summary.high}`);

    return report;
  }

  generateRecommendations() {
    const recommendations = [];

    if (this.findings.some(f => f.category === 'Authentication')) {
      recommendations.push({
        priority: 1,
        title: 'Strengthen Authentication',
        actions: [
          'Implement MFA for sensitive operations',
          'Use secure session management',
          'Enforce strong password policies'
        ]
      });
    }

    if (this.findings.some(f => f.category === 'Authorization')) {
      recommendations.push({
        priority: 1,
        title: 'Implement Proper Authorization',
        actions: [
          'Use role-based access control (RBAC)',
          'Validate user permissions for each request',
          'Implement resource-level authorization'
        ]
      });
    }

    return recommendations;
  }
}

// Usage
const scanner = new APISecurityScanner('https://api.example.com', {
  credentials: {
    admin: { username: 'admin', password: 'admin123' },
    user: { username: 'user', password: 'user123' }
  },
  zapProxy: 'http://localhost:8080',
  zapApiKey: 'your-zap-api-key'
});

scanner.runComprehensiveScan()
  .then(report => {
    console.log('Security scan completed successfully');
    // Send report via email or integrate with issue tracker
  })
  .catch(error => {
    console.error('Security scan failed:', error);
    process.exit(1);
  });
```

### Example 2: Python Security Testing Framework

```python
# api_security_scanner.py
import requests
import json
import hashlib
import time
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
from enum import Enum
import jwt
import base64
from urllib.parse import urlparse

class Severity(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

@dataclass
class SecurityFinding:
    severity: Severity
    category: str
    title: str
    description: str
    evidence: Dict[str, Any]
    remediation: str
    cwe_id: str = None
    owasp_category: str = None

class APISecurityTester:
    def __init__(self, base_url: str, auth_token: str = None):
        self.base_url = base_url
        self.session = requests.Session()
        if auth_token:
            self.session.headers['Authorization'] = f'Bearer {auth_token}'
        self.findings: List[SecurityFinding] = []

    def run_security_tests(self):
        """Run comprehensive security test suite."""
        print("Starting API Security Testing...")

        test_suites = [
            self.test_broken_authentication,
            self.test_broken_authorization,
            self.test_excessive_data_exposure,
            self.test_lack_of_resources_rate_limiting,
            self.test_security_misconfiguration,
            self.test_injection_vulnerabilities,
            self.test_improper_assets_management,
            self.test_insufficient_logging
        ]

        for test_suite in test_suites:
            try:
                test_suite()
            except Exception as e:
                print(f"Test suite failed: {e}")

        return self.generate_report()

    def test_injection_vulnerabilities(self):
        """Test for various injection vulnerabilities."""
        print("Testing for injection vulnerabilities...")

        # SQL Injection payloads
        sql_payloads = [
            "' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users--",
            "1' AND '1' = '1"
        ]

        # Test each endpoint with injection payloads
        endpoints = ['/search', '/users', '/products']

        for endpoint in endpoints:
            for payload in sql_payloads:
                try:
                    response = self.session.get(
                        f"{self.base_url}{endpoint}",
                        params={'q': payload}
                    )

                    # Check for SQL error messages in response
                    error_indicators = [
                        'SQL syntax',
                        'mysql_fetch',
                        'ORA-01',
                        'PostgreSQL',
                        'SQLite'
                    ]

                    response_text = response.text.lower()
                    for indicator in error_indicators:
                        if indicator.lower() in response_text:
                            self.add_finding(
                                severity=Severity.CRITICAL,
                                category="Injection",
                                title="SQL Injection Vulnerability",
                                description=f"Endpoint {endpoint} vulnerable to SQL injection",
                                evidence={
                                    "endpoint": endpoint,
                                    "payload": payload,
                                    "indicator": indicator
                                },
                                remediation="Use parameterized queries",
                                cwe_id="CWE-89"
                            )
                            break

                except Exception as e:
                    pass

    def test_broken_authentication(self):
        """Test for authentication vulnerabilities."""
        print("Testing authentication mechanisms...")

        # Test JWT vulnerabilities
        test_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

        # Try token with 'none' algorithm
        header = base64.urlsafe_b64encode(
            json.dumps({"alg": "none", "typ": "JWT"}).encode()
        ).decode().rstrip('=')

        payload = test_token.split('.')[1]
        none_token = f"{header}.{payload}."

        response = self.session.get(
            f"{self.base_url}/profile",
            headers={'Authorization': f'Bearer {none_token}'}
        )

        if response.status_code == 200:
            self.add_finding(
                severity=Severity.CRITICAL,
                category="Authentication",
                title="JWT None Algorithm Vulnerability",
                description="API accepts JWT tokens with 'none' algorithm",
                evidence={"token": none_token[:50] + "..."},
                remediation="Explicitly verify JWT algorithm",
                cwe_id="CWE-347"
            )

    def add_finding(self, **kwargs):
        """Add a security finding to the results."""
        finding = SecurityFinding(**kwargs)
        self.findings.append(finding)
        print(f"  Found: {finding.title} ({finding.severity.value})")

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive security report."""
        report = {
            "scan_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "target_api": self.base_url,
            "total_findings": len(self.findings),
            "severity_breakdown": {
                "CRITICAL": len([f for f in self.findings if f.severity == Severity.CRITICAL]),
                "HIGH": len([f for f in self.findings if f.severity == Severity.HIGH]),
                "MEDIUM": len([f for f in self.findings if f.severity == Severity.MEDIUM]),
                "LOW": len([f for f in self.findings if f.severity == Severity.LOW])
            },
            "findings": [asdict(f) for f in self.findings]
        }

        # Save report
        with open("security_report.json", "w") as f:
            json.dump(report, f, indent=2)

        print(f"\nSecurity scan complete. Found {len(self.findings)} issues.")
        return report

# Usage example
if __name__ == "__main__":
    scanner = APISecurityTester("https://api.example.com")
    report = scanner.run_security_tests()
    print(f"Report saved to security_report.json")
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| "Connection refused to ZAP" | ZAP proxy not running | Start ZAP daemon on configured port |
| "Permission denied" | No authorization for security testing | Obtain written permission before scanning |
| "Rate limited during scan" | Too many requests | Reduce scan speed, add delays |
| "False positive findings" | Overly aggressive rules | Manually verify and tune scanner rules |
| "Incomplete scan results" | Scan timeout | Increase timeout, scan in phases |

## Configuration Options

**Scan Modes**
- `passive`: Non-intrusive scanning only
- `active`: Full vulnerability testing
- `targeted`: Focus on specific vulnerabilities
- `compliance`: Check against standards

**Authentication Types**
- `bearer`: JWT/OAuth tokens
- `basic`: Username/password
- `apikey`: API key authentication
- `certificate`: Client certificates

## Best Practices

DO:
- Always get written permission before scanning
- Test in non-production environments first
- Verify findings manually to eliminate false positives
- Document all security tests performed
- Prioritize fixes based on severity and exploitability
- Retest after implementing fixes

DON'T:
- Scan production APIs during peak hours
- Ignore low-severity findings (defense in depth)
- Share vulnerability details publicly
- Rely solely on automated scanning
- Skip retesting after remediation

## Security Standards Compliance

**OWASP API Security Top 10 (2023)**
1. Broken Object Level Authorization
2. Broken Authentication
3. Broken Object Property Level Authorization
4. Unrestricted Resource Consumption
5. Broken Function Level Authorization
6. Unrestricted Access to Sensitive Business Flows
7. Server Side Request Forgery
8. Security Misconfiguration
9. Improper Inventory Management
10. Unsafe Consumption of APIs

## Related Commands

- `/api-authentication-builder` - Implement secure authentication
- `/api-rate-limiter` - Add rate limiting protection
- `/api-monitoring-dashboard` - Monitor security events
- `/api-response-validator` - Validate API responses

## Version History

- v1.0.0 (2024-10): Initial implementation with OWASP API Top 10 coverage
- Planned v1.1.0: Add GraphQL and gRPC security testing