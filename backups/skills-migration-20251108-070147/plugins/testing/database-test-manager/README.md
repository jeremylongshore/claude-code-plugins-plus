# Database Test Manager

Database testing utilities with test data setup, transaction rollback, and schema validation.

## Installation

```bash
/plugin install database-test-manager@claude-code-plugins-plus
```

## Usage

```bash
/db-test
# or shortcut
/dbt
```

## Features

- **Test Data Factories**: Generate realistic test data with Faker
- **Transaction Management**: Automatic rollback after tests
- **Schema Validation**: Test migrations and constraints
- **Custom Assertions**: Database-specific test matchers
- **Performance Testing**: Query optimization validation
- **Multi-Database**: PostgreSQL, MySQL, SQLite, MongoDB support

## Example Workflow

```bash
# Generate database testing utilities
/db-test

# Claude creates:
#  Test data factories
#  Transaction wrappers
#  Database assertions
#  Migration tests
#  Cleanup strategies
```

## Supported Technologies

- Prisma
- TypeORM
- Sequelize
- SQLAlchemy
- ActiveRecord

## Files

- `commands/db-test.md` - Database testing command

## License

MIT
