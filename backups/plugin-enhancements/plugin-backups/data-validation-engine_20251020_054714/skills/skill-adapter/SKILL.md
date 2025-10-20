---
name: Validating Database Integrity
description: |
  This skill utilizes the data-validation-engine plugin to ensure database integrity. It automatically validates data types, ranges, formats, referential integrity, and business rules. Use this skill when you need to implement data validation, enforce constraints, or improve data quality within a database. It is triggered by requests for "data validation", "database integrity", or "validation rules". The plugin supports multi-database environments and production-ready implementations.
---

## Overview

This skill empowers Claude to implement comprehensive data validation at both the database and application levels, ensuring data integrity and adherence to defined rules. It leverages the data-validation-engine plugin to automate the process of defining and enforcing validation rules.

## How It Works

1. **Rule Definition**: Claude analyzes the request and identifies the specific data validation requirements (e.g., data types, ranges, formats).
2. **Validation Implementation**: Claude uses the data-validation-engine plugin to generate and apply the necessary validation rules to the database schema or application logic.
3. **Verification**: Claude confirms the successful implementation of the validation rules and reports any errors or conflicts.

## When to Use This Skill

This skill activates when you need to:
- Implement data validation for a new database schema.
- Enforce data integrity constraints on existing database tables.
- Validate data input within an application to prevent invalid data from being stored.

## Examples

### Example 1: Implementing Data Type Validation

User request: "Implement data validation to ensure the 'age' column in the 'users' table is an integer."

The skill will:
1. Use the data-validation-engine plugin to add a constraint to the 'users' table, enforcing that the 'age' column must contain integer values.
2. Verify that the constraint is active and prevents non-integer values from being inserted into the 'age' column.

### Example 2: Validating Email Format

User request: "Add data validation to ensure the 'email' column in the 'customers' table contains a valid email address format."

The skill will:
1. Use the data-validation-engine plugin to add a constraint to the 'customers' table, using a regular expression to validate the format of the 'email' column.
2. Test the constraint with valid and invalid email addresses to ensure it functions correctly.

## Best Practices

- **Comprehensive Coverage**: Validate all relevant data points to ensure complete data integrity.
- **Clear Error Messages**: Provide informative error messages to users when validation fails, guiding them to correct the data.
- **Regular Review**: Periodically review and update validation rules to reflect changing business requirements.

## Integration

This skill integrates seamlessly with other database management and application development tools within the Claude Code ecosystem. It can be used in conjunction with schema design tools, data migration utilities, and application frameworks to ensure data integrity throughout the entire development lifecycle.