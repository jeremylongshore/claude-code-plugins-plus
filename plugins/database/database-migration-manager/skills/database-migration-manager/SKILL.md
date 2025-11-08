---
name: managing-database-migrations
description: |
  This skill enables Claude to manage database schema changes through version-controlled migrations. It is activated when the user requests to create, apply, or rollback database migrations. The skill supports generating timestamped migration files with both up and down migrations for PostgreSQL, MySQL, SQLite, and MongoDB. It helps in tracking schema evolution and ensuring safe database modifications. Use this skill when the user mentions "database migration", "schema change", "add column", "rollback migration", or "create migration".
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
version: 1.0.0
---

## Overview

This skill empowers Claude to handle database migrations, including creating new migrations, applying changes, and rolling back previous modifications. It ensures that database schema changes are managed safely and efficiently.

## How It Works

1. **Migration Request**: The user requests a database migration task (e.g., "create a migration").
2. **Migration File Generation**: Claude generates a timestamped migration file, including both "up" (apply changes) and "down" (rollback changes) migrations.
3. **Database Support**: The generated migration file is compatible with PostgreSQL, MySQL, SQLite, or MongoDB.

## When to Use This Skill

This skill activates when you need to:
- Create a new database migration file.
- Add a column to an existing database table.
- Rollback a previous database migration.
- Manage database schema changes.

## Examples

### Example 1: Adding a Column

User request: "Create a migration to add an 'email' column to the 'users' table."

The skill will:
1. Generate a new migration file with timestamped name.
2. Populate the 'up' migration with SQL to add the 'email' column to the 'users' table.
3. Populate the 'down' migration with SQL to remove the 'email' column from the 'users' table.

### Example 2: Rolling Back a Migration

User request: "Rollback the last database migration."

The skill will:
1. Identify the most recently applied migration.
2. Execute the 'down' migration script associated with that migration.
3. Confirm the successful rollback.

## Best Practices

- **Idempotency**: Ensure your migrations are idempotent, meaning they can be applied multiple times without unintended side effects.
- **Transactions**: Wrap migration steps within transactions to ensure atomicity; either all changes succeed, or none do.
- **Naming Conventions**: Use clear and descriptive names for your migration files (e.g., `YYYYMMDDHHMMSS_add_email_to_users`).

## Integration

This skill can be used independently or in conjunction with other plugins for database management, ORM integration, and deployment automation.