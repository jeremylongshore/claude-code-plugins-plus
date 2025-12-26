---
name: implementing-database-audit-logging
description: |
  Use when you need to track database changes for compliance and security monitoring.
  This skill implements audit logging using triggers, application-level logging, CDC, or native logs.
  Trigger with phrases like "implement database audit logging", "add audit trails",
  "track database changes", or "monitor database activity for compliance".
  
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(psql:*), mysql:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---
## Prerequisites

Before using this skill, ensure:
- Database credentials with CREATE TABLE and CREATE TRIGGER permissions
- Understanding of compliance requirements (GDPR, HIPAA, SOX, PCI-DSS)
- Sufficient storage for audit logs (estimate 10-30% of data size)
- Decision on audit log retention period
- Access to database documentation for table schemas
- Monitoring tools configured for audit log analysis

## Instructions

### Step 1: Define Audit Requirements
1. Identify tables requiring audit logging based on compliance needs
2. Determine events to audit (INSERT, UPDATE, DELETE, SELECT for sensitive data)
3. Define which columns contain sensitive data requiring audit
4. Document retention requirements for audit logs
5. Identify users/roles whose actions need auditing

### Step 2: Choose Audit Strategy
1. **Trigger-Based Auditing**: Best for comprehensive row-level tracking
   - Pros: Automatic, no application changes, captures all changes
   - Cons: Performance overhead, complex trigger maintenance
2. **Application-Level Auditing**: Best for selective auditing
   - Pros: Flexible, lower database overhead, easier debugging
   - Cons: Requires application changes, can miss direct database changes
3. **Change Data Capture (CDC)**: Best for real-time streaming
   - Pros: Minimal performance impact, real-time analysis, external processing
   - Cons: Complex setup, requires CDC infrastructure
4. **Native Database Logs**: Best for general monitoring
   - Pros: No setup, captures everything, built-in
   - Cons: High volume, limited retention, difficult to query

### Step 3: Design Audit Table Schema
1. Create audit log table with these core columns:
   - audit_id (primary key), table_name, action (INSERT/UPDATE/DELETE)
   - record_id (reference to audited record), old_values (JSON), new_values (JSON)
   - changed_by (user), changed_at (timestamp), client_ip, application_context
2. Add indexes on table_name, changed_at, changed_by for query performance
3. Partition audit table by date for efficient archival
4. Configure tablespace for audit logs separate from primary data

### Step 4: Implement Audit Mechanism
1. For trigger-based: Create AFTER INSERT/UPDATE/DELETE triggers on each table
2. Capture old and new row values as JSON in trigger body
3. Record user context (CURRENT_USER, application user, IP address)
4. Handle trigger failures gracefully (log but don't block operations)
5. Test triggers with sample data modifications

### Step 5: Configure Audit Log Management
1. Set up automated archival of old audit logs to cold storage
2. Implement audit log analysis queries for common compliance reports
3. Create alerts for suspicious activities (bulk deletes, off-hours changes)
4. Document audit log query procedures for compliance auditors
5. Schedule periodic audit log reviews with security team

### Step 6: Validate Audit Implementation
1. Perform test operations on audited tables
2. Verify audit log entries are created with complete data
3. Test audit log queries for performance
4. Confirm audit logs cannot be modified by regular users
5. Document audit implementation for compliance documentation

## Output

This skill produces:

**Audit Table Schema**: SQL DDL for audit log table with proper indexes and partitioning

**Audit Triggers**: Database triggers for automatic audit log population on data changes

**Audit Log Queries**: Pre-built SQL queries for compliance reports and change tracking

**Implementation Documentation**: Configuration details, trigger logic, and maintenance procedures

**Compliance Report Templates**: SQL queries for GDPR access logs, SOX change reports, etc.

## Error Handling

**Trigger Performance Issues**:
- Audit only critical tables, not all tables
- Use asynchronous audit logging with queue systems
- Batch audit log inserts instead of individual inserts
- Monitor trigger execution time and optimize trigger logic

**Audit Table Growth**:
- Implement automated archival of audit logs older than retention period
- Partition audit table by month or quarter
- Compress old audit log partitions
- Move historical audit logs to cheaper storage tiers

**Missing Audit Context**:
- Set application context in database session before operations
- Use database session variables to pass user identity
- Implement connection pooling with session initialization
- Log application user separately from database user

**Permission Issues**:
- Ensure audit log table is writable by trigger execution context
- Grant INSERT on audit table to all database users
- Protect audit table from modifications (no UPDATE/DELETE grants)
- Use separate schema for audit tables with restricted access

## Resources

**Audit Table Templates**:
- PostgreSQL audit trigger: `{baseDir}/templates/postgresql-audit-trigger.sql`
- MySQL audit trigger: `{baseDir}/templates/mysql-audit-trigger.sql`
- Audit table schema: `{baseDir}/templates/audit-table-schema.sql`

**Compliance Report Queries**: `{baseDir}/queries/compliance-reports/`
- GDPR data access report
- SOX change audit report
- User activity summary
- Suspicious activity detection

**Audit Strategy Guide**: `{baseDir}/docs/audit-strategy-selection.md`
**Performance Tuning**: `{baseDir}/docs/audit-performance-optimization.md`
**Archival Procedures**: `{baseDir}/scripts/audit-archival.sh`

## Overview

This skill provides automated assistance for the described functionality.

## Examples

Example usage patterns will be demonstrated in context.