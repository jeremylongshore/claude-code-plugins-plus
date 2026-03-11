---
name: implementing-database-audit-logging
description: |
  Process use when you need to track database changes for compliance and security monitoring.
  This skill implements audit logging using triggers, application-level logging, CDC, or native logs.
  Trigger with phrases like "implement database audit logging", "add audit trails",
  "track database changes", or "monitor database activity for compliance".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(psql:*), Bash(mysql:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Database Audit Logger

## Overview

Implement database audit logging to track all data modifications (INSERT, UPDATE, DELETE) with full before/after values, user identity, timestamps, and application context. This skill supports trigger-based auditing for PostgreSQL and MySQL, change data capture (CDC) patterns, and application-level audit logging.

## Prerequisites

- Database credentials with CREATE TABLE, CREATE FUNCTION, and CREATE TRIGGER permissions
- `psql` or `mysql` CLI for executing audit setup DDL
- Understanding of applicable compliance requirements (which tables, which operations, retention period)
- Estimated storage for audit logs: plan for 10-30% of the audited table's data volume per year
- Separate tablespace or storage volume for audit data to prevent audit growth from affecting application performance

## Instructions

1. Identify tables requiring audit logging based on compliance and business needs:
   - Tables containing PII (users, contacts, addresses) -- GDPR/HIPAA requirement
   - Tables containing financial data (transactions, payments, invoices) -- SOX/PCI-DSS requirement
   - Tables containing access control data (roles, permissions, API keys) -- security requirement
   - Determine which operations to audit per table: INSERT, UPDATE, DELETE, or all three

2. Create the audit log table with comprehensive metadata:
   ```sql
   CREATE TABLE audit_log (
     id BIGSERIAL PRIMARY KEY,
     table_name VARCHAR(100) NOT NULL,
     record_id TEXT NOT NULL,
     action VARCHAR(10) NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
     old_values JSONB,
     new_values JSONB,
     changed_columns TEXT[],
     changed_by VARCHAR(100),
     changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
     client_ip INET,
     application_name VARCHAR(100),
     transaction_id BIGINT
   );
   ```

3. Add indexes for common audit queries:
   - `CREATE INDEX idx_audit_table_record ON audit_log (table_name, record_id)`
   - `CREATE INDEX idx_audit_changed_at ON audit_log (changed_at)`
   - `CREATE INDEX idx_audit_changed_by ON audit_log (changed_by)`
   - `CREATE INDEX idx_audit_action ON audit_log (table_name, action)`

4. Create the PostgreSQL audit trigger function:
   ```sql
   CREATE OR REPLACE FUNCTION audit_trigger_func() RETURNS TRIGGER AS $$
   BEGIN
     IF TG_OP = 'INSERT' THEN
       INSERT INTO audit_log (table_name, record_id, action, new_values, changed_by, client_ip, application_name, transaction_id)
       VALUES (TG_TABLE_NAME, NEW.id::text, 'INSERT', to_jsonb(NEW), current_setting('app.user', true), inet_client_addr(), current_setting('application_name'), txid_current());
     ELSIF TG_OP = 'UPDATE' THEN
       INSERT INTO audit_log (table_name, record_id, action, old_values, new_values, changed_by, client_ip, application_name, transaction_id)
       VALUES (TG_TABLE_NAME, NEW.id::text, 'UPDATE', to_jsonb(OLD), to_jsonb(NEW), current_setting('app.user', true), inet_client_addr(), current_setting('application_name'), txid_current());
     ELSIF TG_OP = 'DELETE' THEN
       INSERT INTO audit_log (table_name, record_id, action, old_values, changed_by, client_ip, application_name, transaction_id)
       VALUES (TG_TABLE_NAME, OLD.id::text, 'DELETE', to_jsonb(OLD), current_setting('app.user', true), inet_client_addr(), current_setting('application_name'), txid_current());
     END IF;
     RETURN COALESCE(NEW, OLD);
   END;
   $$ LANGUAGE plpgsql;
   ```

5. Attach triggers to each audited table:
   - `CREATE TRIGGER audit_users AFTER INSERT OR UPDATE OR DELETE ON users FOR EACH ROW EXECUTE FUNCTION audit_trigger_func()`
   - Repeat for each table requiring audit logging

6. Pass application-level user context to the database session so audit logs capture the actual application user (not just the database role):
   - At the start of each request: `SET LOCAL app.user = 'user@example.com'`
   - For connection pools, set in the connection checkout hook
   - This value is captured by `current_setting('app.user', true)` in the trigger

7. Partition the audit_log table by month for efficient querying and archival:
   - `CREATE TABLE audit_log (...) PARTITION BY RANGE (changed_at)`
   - Create monthly partitions: `CREATE TABLE audit_log_2024_01 PARTITION OF audit_log FOR VALUES FROM ('2024-01-01') TO ('2024-02-01')`
   - Automate partition creation for future months

8. Protect audit log integrity:
   - Revoke UPDATE and DELETE permissions on audit_log from all application users
   - Grant only INSERT permission to the trigger execution context
   - Consider using `pg_audit` extension for additional tamper protection
   - Ship audit logs to an external system (SIEM, S3) for independent retention

9. Create compliance report queries:
   - **Change history for a record**: `SELECT * FROM audit_log WHERE table_name = 'users' AND record_id = '12345' ORDER BY changed_at`
   - **All changes by a user**: `SELECT * FROM audit_log WHERE changed_by = 'user@example.com' ORDER BY changed_at DESC`
   - **Bulk operations detection**: `SELECT changed_by, table_name, action, COUNT(*) FROM audit_log WHERE changed_at > NOW() - INTERVAL '1 hour' GROUP BY 1,2,3 HAVING COUNT(*) > 100`
   - **Off-hours activity**: `SELECT * FROM audit_log WHERE EXTRACT(HOUR FROM changed_at) NOT BETWEEN 8 AND 18`

10. Set up audit log archival: move audit records older than the retention period to cold storage (S3, Azure Blob). Maintain the archive manifest for retrieval. Typical retention: 1-3 years in database, 7+ years in cold storage for financial data.

## Output

- **Audit table DDL** with proper columns, indexes, and partitioning
- **Audit trigger function** capturing full before/after values with user context
- **Trigger attachment scripts** for each audited table
- **Compliance report queries** for common audit scenarios
- **Archival configuration** for audit log lifecycle management

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| Audit trigger slows INSERT/UPDATE operations | Trigger overhead on high-write tables | Audit only critical columns instead of full rows; use asynchronous audit with `pg_notify` and a listener process; batch audit writes |
| Audit table consuming excessive disk space | High write volume tables generating millions of audit records | Partition by month; archive old partitions to cold storage; audit only specific columns with `WHEN` clause on trigger |
| `current_setting('app.user')` returns NULL | Application not setting session variable before database operations | Set default in trigger: `COALESCE(current_setting('app.user', true), current_user)`; add connection pool checkout hook |
| Audit log INSERT fails, blocking application operation | Audit table full, permission error, or constraint violation | Use `BEGIN ... EXCEPTION WHEN OTHERS THEN NULL; END` in trigger to prevent audit failures from blocking operations; alert on audit failures |
| Cannot determine which columns changed in UPDATE | Full row stored as JSON, no column-level diff | Add `changed_columns` computation in trigger: compare OLD and NEW field by field; store only changed fields in `new_values` |

## Examples

**HIPAA-compliant audit logging for a healthcare database**: Audit triggers on patient_records, prescriptions, and lab_results tables capture all modifications with practitioner identity. Audit logs are immutable (no UPDATE/DELETE grants), partitioned monthly, and archived to encrypted S3 after 1 year. Quarterly compliance reports show access patterns per practitioner and flag unusual access (patient records accessed without an appointment).

**Detecting unauthorized data modifications**: Audit log query reveals 500 DELETE operations on the billing table by a service account at 3 AM, outside normal business hours. Alert triggers for bulk operations exceeding 100 rows. Investigation traces the operations to a misconfigured cleanup job. Audit log provides the complete list of deleted records for restoration.

**GDPR data access request fulfillment**: When a user requests their data access log under GDPR Article 15, the audit system provides a complete history of who accessed or modified their personal data: `SELECT changed_by, action, changed_at, changed_columns FROM audit_log WHERE table_name = 'users' AND record_id = '12345' ORDER BY changed_at`. The report is generated within the 30-day compliance window.

## Resources

- PostgreSQL triggers: https://www.postgresql.org/docs/current/plpgsql-trigger.html
- pgAudit extension: https://www.pgaudit.org/
- MySQL audit log plugin: https://dev.mysql.com/doc/refman/8.0/en/audit-log.html
- GDPR data processing records: https://gdpr-info.eu/art-30-gdpr/
- SOX compliance for databases: https://www.postgresql.org/docs/current/pgaudit.html