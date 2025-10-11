---
description: Scan database for security vulnerabilities
---

# Database Security Scanner

Identify security vulnerabilities in database configuration.

## Security Checks

1. **Weak Passwords**: Default or empty passwords
2. **Excessive Permissions**: Over-privileged users
3. **Unencrypted Connections**: No SSL/TLS
4. **SQL Injection Vectors**: Vulnerable queries
5. **Exposed Ports**: Publicly accessible databases
6. **Missing Auditing**: No logging enabled

## Security Best Practices

```sql
-- Enforce SSL
ALTER SYSTEM SET ssl = on;

-- Require strong passwords
CREATE ROLE app_user WITH LOGIN PASSWORD 'complex_password123!';

-- Principle of least privilege
GRANT SELECT, INSERT, UPDATE ON users TO app_user;
REVOKE ALL ON pg_catalog FROM public;
```

## When Invoked

Perform security audit of database configuration.
