---
name: scanning-database-security
description: |
  Process use when you need to work with security and compliance.
  This skill provides security scanning and vulnerability detection with comprehensive guidance and automation.
  Trigger with phrases like "scan for vulnerabilities", "implement security controls",
  or "audit security".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(psql:*), Bash(mysql:*), Bash(mongosh:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Database Security Scanner

## Overview

Audit database security configurations, user privileges, network exposure, and data protection controls for PostgreSQL, MySQL, and MongoDB. This skill scans for common vulnerabilities including excessive privileges, missing encryption, default passwords, exposed network ports, unpatched versions, and SQL injection vectors in application code. Findings are prioritized by severity with specific remediation steps.

## Prerequisites

- Database admin credentials for querying system catalogs and security settings
- `psql`, `mysql`, or `mongosh` CLI tools installed
- Access to database configuration files (`postgresql.conf`, `pg_hba.conf`, `my.cnf`, `mongod.conf`)
- Application source code access for SQL injection scanning (using Grep/Glob tools)
- Knowledge of applicable compliance frameworks (SOC 2, HIPAA, PCI-DSS, GDPR)

## Instructions

1. Check authentication configuration by reviewing `pg_hba.conf` (PostgreSQL) or `mysql.user` table. Flag any entries using `trust` authentication, allowing connections without passwords. Verify `password_encryption = scram-sha-256` (not `md5`) in PostgreSQL.

2. Audit user privileges by querying role memberships and grants:
   - PostgreSQL: `SELECT r.rolname, r.rolsuper, r.rolinherit, r.rolcreaterole, r.rolcreatedb FROM pg_roles r WHERE r.rolcanlogin = true`
   - MySQL: `SELECT user, host, Super_priv, Grant_priv, File_priv FROM mysql.user`
   - Flag users with superuser/SUPER privilege, excessive grants, or `GRANT OPTION`

3. Scan for default or weak credentials. Check for accounts with no password: PostgreSQL `SELECT rolname FROM pg_roles WHERE rolpassword IS NULL AND rolcanlogin = true`. Check for well-known default accounts (postgres with default password, root without password, admin/admin).

4. Verify network security:
   - Check `listen_addresses` in postgresql.conf (should not be `*` in production without firewall)
   - Verify SSL/TLS is enforced: `SHOW ssl` should return `on`; `pg_hba.conf` should use `hostssl` instead of `host`
   - Confirm database port is not exposed to the public internet

5. Check encryption at rest:
   - Verify tablespace encryption or volume-level encryption is enabled
   - Scan for sensitive data stored in plaintext: `SELECT column_name, data_type FROM information_schema.columns WHERE column_name ILIKE '%password%' OR column_name ILIKE '%ssn%' OR column_name ILIKE '%credit_card%'`
   - Flag columns storing PII without encryption or hashing

6. Scan application source code for SQL injection vulnerabilities using Grep:
   - Search for string concatenation in SQL queries: patterns like `"SELECT * FROM " + variable` or `f"SELECT * FROM {table}"`
   - Search for missing parameterized queries: raw SQL construction without bind parameters
   - Flag ORM `raw()` or `execute()` calls with string interpolation

7. Review database object permissions:
   - Check for PUBLIC grants on sensitive tables: `SELECT grantee, table_name, privilege_type FROM information_schema.table_privileges WHERE grantee = 'PUBLIC'`
   - Verify functions are created with `SECURITY DEFINER` only when necessary
   - Check for world-readable backup files on the filesystem

8. Audit logging configuration:
   - Verify `log_connections = on`, `log_disconnections = on` in PostgreSQL
   - Check `log_statement = 'ddl'` or `'all'` for sensitive databases
   - Confirm audit logs are shipped to a tamper-proof location

9. Check for known CVEs by comparing the database version against the latest security advisories. Flag databases running versions with known critical vulnerabilities.

10. Generate a security findings report with severity levels (Critical, High, Medium, Low), affected components, evidence (query output showing the vulnerability), and specific remediation commands.

## Output

- **Security findings report** with severity-ranked vulnerabilities and evidence
- **Remediation scripts** (SQL) for revoking excessive privileges, fixing authentication, enabling SSL
- **Hardened configuration templates** for postgresql.conf, pg_hba.conf, or my.cnf
- **SQL injection findings** listing vulnerable code locations with fix suggestions
- **Compliance checklist** mapping findings to SOC 2, HIPAA, or PCI-DSS controls

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| Permission denied querying pg_roles or mysql.user | Scanner account lacks privilege to read user metadata | Grant `pg_read_all_settings` and `pg_read_all_stats` roles; or run scan with superuser credentials in a controlled session |
| Cannot access postgresql.conf from SQL | File-system access restricted; `pg_file_settings` view not available | Use `SHOW ALL` to check runtime settings; request file access from ops team; use `pg_settings` catalog view |
| SSL certificate errors during scan | Self-signed certificates or expired certificates on database | Note as a finding; generate new certificates with `openssl`; configure `ssl_cert_file` and `ssl_key_file` |
| Source code scan produces false positives | Dynamic SQL construction that uses proper parameterization | Review flagged locations manually; whitelist confirmed-safe patterns; focus on string concatenation with user input |
| Database version check shows EOL version | Database version no longer receiving security patches | Prioritize as critical finding; plan upgrade path; apply last available patches as interim measure |

## Examples

**PostgreSQL security audit revealing over-privileged roles**: Scan discovers 5 application users with `SUPERUSER` privilege, `pg_hba.conf` using `trust` for local connections, and SSL disabled. Remediation: revoke SUPERUSER, create application-specific roles with minimum privileges, switch to `scram-sha-256` authentication, and enable SSL with Let's Encrypt certificates.

**SQL injection scan of a Node.js application**: Grep finds 12 instances of `db.query("SELECT * FROM users WHERE id = " + req.params.id)` across 4 files. Remediation: replace with parameterized queries `db.query("SELECT * FROM users WHERE id = $1", [req.params.id])`. Each finding includes file path, line number, and corrected code.

**PCI-DSS compliance check for payment database**: Scan verifies: credit card numbers stored as hashed values (pass), audit logging enabled for cardholder data tables (pass), database admin accounts shared among team members (fail - individual accounts required), backups unencrypted on S3 (fail - enable SSE-S3). Produces compliance gap report with remediation timeline.

## Resources

- CIS PostgreSQL Benchmark: https://www.cisecurity.org/benchmark/postgresql
- CIS MySQL Benchmark: https://www.cisecurity.org/benchmark/oracle_mysql
- PostgreSQL security documentation: https://www.postgresql.org/docs/current/auth-pg-hba-conf.html
- OWASP SQL Injection Prevention: https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html
- Database security checklist: https://www.postgresql.org/docs/current/auth-methods.html
