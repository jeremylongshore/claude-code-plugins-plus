---
name: detecting-sql-injection-vulnerabilities
description: |
  Detect and analyze SQL injection vulnerabilities in application code and database queries.
  Use when you need to scan code for SQL injection risks, review query construction, validate input sanitization, or implement secure query patterns.
  Trigger with phrases like "detect SQL injection", "scan for SQLi vulnerabilities", "review database queries", or "check SQL security".
allowed-tools:
- Read
- Write
- Edit
- Grep
- Glob
- Bash(code-scan:*, security-test:*)
version: 1.0.0
license: MIT
---
## Prerequisites

Before using this skill, ensure:
- Application source code accessible in {baseDir}/
- Database query files and ORM configurations available
- Framework information (Django, Rails, Express, Spring, etc.)
- Write permissions for security reports in {baseDir}/security-reports/

## Instructions

### 1. Code Discovery Phase

Locate database interaction code:
- SQL query construction
- ORM usage (ActiveRecord, Hibernate, SQLAlchemy, etc.)
- Stored procedure calls
- Dynamic query builders
- User input handling for database operations

**Common patterns to search**:
- Direct SQL: `SELECT`, `INSERT`, `UPDATE`, `DELETE` statements
- String concatenation with user input
- ORM raw query methods
- Template-based query construction

### 2. Vulnerability Pattern Detection

**Critical SQL Injection Patterns**:

**String Concatenation (Highly Vulnerable)**:
```python
# INSECURE: Direct concatenation
query = "SELECT * FROM users WHERE username = '" + user_input + "'"
cursor.execute(query)

# Attacker input: ' OR '1'='1' --
# Results in: SELECT * FROM users WHERE username = '' OR '1'='1' --'
```

**Formatted Strings (Vulnerable)**:
```javascript
// INSECURE: Template literals
const query = `SELECT * FROM products WHERE id = ${productId}`;
db.query(query);
```

**Dynamic WHERE Clauses (Vulnerable)**:
```php
// INSECURE: Building conditions dynamically
$sql = "SELECT * FROM orders WHERE status = " . $_GET['status'];
mysqli_query($conn, $sql);
```

### 3. Secure Pattern Validation

**Parameterized Queries (Secure)**:
```python
# SECURE: Parameterized query
query = "SELECT * FROM users WHERE username = %s"
cursor.execute(query, (user_input,))
```

**Prepared Statements (Secure)**:
```java
// SECURE: Prepared statement
String query = "SELECT * FROM products WHERE category = ?";
PreparedStatement stmt = conn.prepareStatement(query);
stmt.setString(1, userCategory);
```

**ORM Query Builders (Secure when used properly)**:
```javascript
// SECURE: ORM with parameter binding
const user = await User.findOne({
  where: { username: userInput }
});
```

### 4. Severity Classification

Rate SQL injection risks:
- **Critical**: Direct user input in SQL without sanitization (authentication bypass, data exfiltration)
- **High**: Partially sanitized input or weak escaping (potential bypass)
- **Medium**: ORM misuse or raw queries with limited exposure
- **Low**: SQL in administrative interfaces with access control

### 5. Context Analysis

For each potential vulnerability:
- Input source (GET/POST parameters, cookies, headers)
- Query purpose (SELECT, INSERT, UPDATE, DELETE)
- Data sensitivity (user data, financial records, PII)
- Authentication requirements
- Exploitability assessment

### 6. Generate Security Report

Document findings with:
- Vulnerability location (file, line number)
- Vulnerable code snippet
- Attack vector examples
- Impact assessment
- Secure code replacement
- Framework-specific remediation

## Output

The skill produces:

**Primary Output**: SQL injection vulnerability report saved to {baseDir}/security-reports/sqli-scan-YYYYMMDD.md

**Report Structure**:
```
# SQL Injection Vulnerability Report
Scan Date: 2024-01-15
Application: E-commerce Platform
Framework: Django 4.2

## Executive Summary
- Total Vulnerabilities: 12
- Critical: 3
- High: 5
- Medium: 3
- Low: 1

## Critical Findings

### 1. Authentication Bypass via SQL Injection
**File**: {baseDir}/src/auth/login.py
**Line**: 45
**Severity**: CRITICAL (CVSS 9.8)

**Vulnerable Code**:
```python
def authenticate_user(username, password):
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    user = db.execute(query).fetchone()
    return user is not None
```

**Attack Vector**:
```
Username: admin' --
Password: anything

Resulting Query: SELECT * FROM users WHERE username='admin' --' AND password='anything'
Effect: Password check bypassed, authentication as admin succeeds
```

**Impact**:
- Complete authentication bypass
- Unauthorized access to any account
- Administrative privilege escalation
- No audit trail of compromise

**Remediation**:
```python
def authenticate_user(username, password):
    query = "SELECT * FROM users WHERE username=%s AND password=%s"
    user = db.execute(query, (username, password)).fetchone()
    return user is not None
```

**Additional Recommendations**:
- Use password hashing (bcrypt, Argon2)
- Implement account lockout after failed attempts
- Add MFA for admin accounts

### 2. Data Exfiltration via UNION-based SQLi
**File**: {baseDir}/src/api/products.py
**Line**: 78
**Severity**: CRITICAL (CVSS 8.6)

[Similar detailed structure...]

## Summary by File
- {baseDir}/src/auth/: 4 vulnerabilities (2 critical)
- {baseDir}/src/api/: 6 vulnerabilities (1 critical, 5 high)
- {baseDir}/src/reports/: 2 vulnerabilities (2 medium)

## Remediation Checklist
- [ ] Replace all string concatenation with parameterized queries
- [ ] Audit ORM raw query usage
- [ ] Implement input validation layer
- [ ] Enable SQL query logging for monitoring
- [ ] Deploy WAF rules for SQLi detection
- [ ] Conduct penetration testing after fixes
```

**Secondary Outputs**:
- SARIF format for GitHub Security scanning
- JSON for vulnerability management systems
- CWE mapping (CWE-89: SQL Injection)

## Error Handling

**Common Issues and Resolutions**:

1. **Framework Not Recognized**
   - Error: "Unknown ORM or database framework"
   - Resolution: Apply generic SQL injection pattern detection
   - Note: Framework-specific recommendations unavailable

2. **Obfuscated or Minified Code**
   - Error: "Cannot analyze compiled/minified code"
   - Resolution: Request source code or unminified version
   - Limitation: Reduced detection accuracy

3. **False Positives on Sanitized Input**
   - Error: "Flagged code that uses proper sanitization"
   - Resolution: Manual review required, check sanitization implementation
   - Enhancement: Whitelist known-safe patterns

4. **Dynamic Query Construction**
   - Error: "Complex query building logic difficult to analyze"
   - Resolution: Trace data flow manually, flag for manual review
   - Recommendation: Refactor to simpler, auditable patterns

5. **Stored Procedures**
   - Error: "Cannot analyze stored procedure definitions"
   - Resolution: Request SQL files or database exports
   - Alternative: Focus on application-level code

## Resources

**OWASP Resources**:
- SQL Injection Prevention Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html
- OWASP Top 10 - Injection: https://owasp.org/www-project-top-ten/

**Vulnerability Databases**:
- CWE-89: SQL Injection: https://cwe.mitre.org/data/definitions/89.html
- CAPEC-66: SQL Injection: https://capec.mitre.org/data/definitions/66.html

**Framework-Specific Guides**:
- Django Security: https://docs.djangoproject.com/en/stable/topics/security/
- Rails Security: https://guides.rubyonrails.org/security.html
- Node.js Best Practices: https://nodejs.org/en/docs/guides/security/

**Testing Tools**:
- SQLMap: Automated SQL injection testing
- Burp Suite: Manual testing and exploitation
- OWASP ZAP: Automated scanning

**Secure Coding Examples**:
- Parameterized queries by language/framework
- Input validation patterns
- Escaping techniques (when parameterization impossible)
- Least privilege database user configuration