# Database Migration Manager Plugin

Manage database migrations with version control, rollback capabilities, and automated schema evolution tracking.

## Installation

```bash
/plugin install database-migration-manager@claude-code-plugins-plus
```

## Usage

```bash
/migration
```

## Features

- **Multi-Database Support**: PostgreSQL, MySQL, SQLite, MongoDB
- **Version Control**: Timestamped migrations with up/down support
- **Best Practices**: Idempotent operations, transaction support
- **Templates**: Pre-built migration templates for common operations
- **Safety**: Rollback support and validation checks

## Example

```bash
/migration
```

**Prompt:** "Create a migration to add a 'role' column to the users table"

**Result:** Generates a timestamped migration file with both up and down migrations.

## Requirements

- Basic understanding of SQL or your ORM
- Database connection configured in your project
- Migration tool installed (if using ORM)

## Files

- `commands/migration.md` - Migration management command

## License

MIT
