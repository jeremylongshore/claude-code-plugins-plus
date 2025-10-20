---
name: Managing Database Testing
description: |
  This skill manages database testing by generating test data, wrapping tests in transactions, and validating database schemas. It is used to create robust and reliable database interactions. Claude uses this skill when the user requests database testing utilities, including test data generation, transaction management, schema validation, or migration testing. Trigger this skill by mentioning "database testing," "test data factories," "transaction rollback," "schema validation," or using the `/db-test` or `/dbt` commands.
---

## Overview

This skill empowers Claude to create and manage comprehensive database testing workflows. It facilitates the generation of realistic test data, ensures transactional integrity with automatic rollbacks, and validates database schema integrity.

## How It Works

1. **Test Data Generation**: Generates realistic test data using factories and fixtures, populating the database with relevant information for testing.
2. **Transaction Wrapping**: Wraps database tests within transactions, ensuring that any changes made during the test are automatically rolled back, maintaining a clean testing environment.
3. **Schema Validation**: Validates the database schema against expected structures and constraints, identifying potential issues with migrations or data integrity.

## When to Use This Skill

This skill activates when you need to:
- Generate test data for database interactions.
- Implement transaction management for database tests.
- Validate database schema and migrations.

## Examples

### Example 1: Generating Test Data

User request: "Generate test data factories for my PostgreSQL database using Faker to populate users and products tables."

The skill will:
1. Create Python code utilizing Faker and a database library (e.g., SQLAlchemy) to generate realistic user and product data.
2. Provide instructions on how to execute the generated code to seed the database.

### Example 2: Implementing Transaction Rollback

User request: "Wrap my database integration tests in transactions with automatic rollback to ensure a clean state after each test."

The skill will:
1. Generate code that utilizes database transaction management features to wrap test functions.
2. Implement automatic rollback mechanisms to revert any changes made during the test execution.

## Best Practices

- **Data Realism**: Utilize Faker or similar libraries to generate realistic test data that accurately reflects production data.
- **Transaction Isolation**: Ensure proper transaction isolation levels to prevent interference between concurrent tests.
- **Schema Validation**: Regularly validate database schema against expected structures to identify migration issues early.

## Integration

This skill seamlessly integrates with other code generation and execution tools within Claude Code. It can be used in conjunction with file management and code editing skills to create, modify, and execute database testing scripts.