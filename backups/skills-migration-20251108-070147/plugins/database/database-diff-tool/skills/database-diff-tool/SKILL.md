---
name: comparing-database-schemas
description: |
  This skill leverages the database-diff-tool plugin to compare database schemas, generate migration scripts, and provide rollback procedures. It is triggered when the user requests database schema comparisons, migration script generation, or database synchronization. Use this skill when asked to identify differences between database schemas (PostgreSQL or MySQL), create safe migration scripts with transaction safety, validate changes before deployment, or generate rollback procedures. The skill is activated by requests involving terms like "database diff", "schema comparison", "generate migration script", "database synchronization", or `/db-diff`.
---

## Overview

This skill empowers Claude to perform production-grade database schema comparisons, generate safe migration scripts, and create rollback procedures. It simplifies the process of keeping database schemas synchronized across different environments, ensuring data integrity and minimizing downtime during deployments.

## How It Works

1. **Schema Comparison**: The plugin compares the schemas of two specified databases (PostgreSQL or MySQL), identifying differences in tables, columns, indexes, constraints, and triggers.
2. **Migration Script Generation**: Based on the schema differences, the plugin generates a safe migration script that can be used to update the target database schema. The script includes transaction safety to prevent data corruption.
3. **Rollback Procedure Generation**: The plugin also generates a rollback procedure that can be used to revert the changes made by the migration script in case of errors.

## When to Use This Skill

This skill activates when you need to:
- Compare database schemas between different environments (e.g., development, staging, production).
- Generate migration scripts to update a database schema to the latest version.
- Create rollback procedures to revert database schema changes.
- Synchronize database schemas across multiple environments to ensure consistency.

## Examples

### Example 1: Generating a Migration Script

User request: "Generate a migration script to update the staging database schema to match production."

The skill will:
1. Connect to both the staging and production databases.
2. Compare the schemas of the two databases using the database-diff-tool plugin.
3. Generate a migration script that updates the staging database schema to match the production schema, including transaction safety and rollback procedures.

### Example 2: Comparing Database Schemas

User request: "Compare the database schemas of the development and testing environments."

The skill will:
1. Connect to both the development and testing databases.
2. Compare the schemas of the two databases using the database-diff-tool plugin.
3. Report the differences between the two schemas, including any missing tables, columns, indexes, or constraints.

## Best Practices

- **Database Credentials**: Ensure that Claude has access to the necessary database credentials to connect to the databases being compared.
- **Backup**: Always back up the database before running any migration scripts.
- **Validation**: Validate the generated migration script in a test environment before deploying it to production.

## Integration

This skill can be integrated with other CI/CD tools to automate the database migration process. It can also be used in conjunction with other database management tools to monitor database schema changes and ensure data integrity.