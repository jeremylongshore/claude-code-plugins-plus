# Critical Findings

## Critical Findings

### 1. Authentication Bypass via SQL Injection
**File**: ${CLAUDE_SKILL_DIR}/src/auth/login.py
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
**File**: ${CLAUDE_SKILL_DIR}/src/api/products.py
**Line**: 78
**Severity**: CRITICAL (CVSS 8.6)

[Similar detailed structure...]