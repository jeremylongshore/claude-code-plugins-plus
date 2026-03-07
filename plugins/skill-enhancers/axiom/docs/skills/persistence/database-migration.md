# Database Migration

Safe database schema evolution for SQLite/GRDB/SwiftData. Prevents data loss with additive migrations and testing workflows.

**When to use**: Adding/modifying database columns, encountering "FOREIGN KEY constraint failed", "no such column", "cannot add NOT NULL column" errors, creating schema migrations for SQLite/GRDB/SwiftData

## Key Features

- Safe migration patterns (additive, idempotent, transactional)
- Testing checklist (fresh install + migration paths)
- Common errors and fixes
- GRDB and SwiftData examples
- Multi-layered prevention for 100k+ user apps

**Philosophy**: Migrations are immutable after shipping. Make them additive, idempotent, and thoroughly tested to prevent data loss.

**TDD Tested**: Already bulletproof, no changes needed during pressure testing

## Example Prompts

These are real questions developers ask that this skill answers:

- **"I need to add a column to my live app without losing user data."**
  → Covers safe additive patterns including idempotency checks and avoiding data loss

- **"I'm getting 'cannot add NOT NULL column' errors when migrating."**
  → Explains why NOT NULL fails with existing rows and shows the safe pattern (nullable first, backfill later)

- **"I need to change a column from text to integer. Can I just ALTER the type?"**
  → Demonstrates the safe pattern: add new column → migrate data → deprecate old (NEVER delete)

- **"I'm adding a foreign key relationship. How do I add it without breaking existing data?"**
  → Covers safe patterns: add column → populate data → add index (SQLite limitations explained)

- **"Users reported crashes after the last update. I changed a migration in production."**
  → Explains migrations are immutable after shipping and how to create a new migration to fix issues
