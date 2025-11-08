---
name: implementing-database-audit-logging
description: |
  This skill helps implement database audit logging for tracking changes and ensuring compliance. It is triggered when the user requests to "implement database audit logging", "add audit trails", "track database changes", or mentions "audit_log" in relation to a database. The skill provides options for trigger-based auditing, application-level logging, Change Data Capture (CDC), and parsing database logs. It generates a basic audit table schema and guides the user through selecting the appropriate auditing strategy.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
version: 1.0.0
---

## Overview

This skill automates the process of setting up database audit logging. It helps users choose an appropriate auditing strategy and provides a basic audit table schema. It simplifies the implementation of robust audit trails for compliance and debugging purposes.

## How It Works

1. **Identify Request**: Detects user intent to implement database audit logging.
2. **Present Audit Strategies**: Offers a selection of auditing strategies: Trigger-Based, Application-Level, CDC, and Database Logs.
3. **Generate Audit Table Schema**: Provides a basic SQL schema for an audit log table.

## When to Use This Skill

This skill activates when you need to:
- Implement database audit logging for compliance requirements.
- Track changes to specific database tables.
- Debug data inconsistencies by reviewing historical changes.
- Securely monitor database activity.

## Examples

### Example 1: Implementing Audit Logging for a Specific Table

User request: "Implement database audit logging for the users table."

The skill will:
1. Present the available audit logging strategies (Trigger-Based, Application-Level, CDC, Database Logs).
2. Provide the basic audit table schema.
3. Guide the user to choose an appropriate method and tailor the schema to the "users" table.

### Example 2: Adding Audit Trails for Compliance

User request: "Add audit trails to my database to meet compliance regulations."

The skill will:
1. Present the available audit logging strategies.
2. Provide the basic audit table schema.
3. Assist in selecting a strategy that aligns with compliance requirements (e.g., CDC for real-time monitoring).

## Best Practices

- **Strategy Selection**: Choose the audit logging strategy that best suits your application's needs and performance requirements. Trigger-based auditing can impact performance, while CDC might require more complex infrastructure.
- **Data Sensitivity**: Consider the sensitivity of the data being audited and implement appropriate security measures to protect the audit logs.
- **Retention Policy**: Define a clear retention policy for audit logs to manage storage and comply with regulatory requirements.

## Integration

This skill can be used in conjunction with other database management plugins to automate the creation of triggers or configure CDC pipelines. It also integrates with logging and monitoring tools to provide a centralized view of database activity.