# GRDB

Raw GRDB for complex queries, ValueObservation, DatabaseMigrator patterns.

**When to use**: Writing raw SQL queries with GRDB, complex joins, ValueObservation for reactive queries, DatabaseMigrator patterns, dropping down from SQLiteData for performance

## Key Features

- Raw SQL query patterns
- ValueObservation for reactive queries
- DatabaseMigrator setup
- Complex joins and aggregations
- Performance optimization
- Direct SQLite access patterns

## Example Prompts

These are real questions developers ask that this skill answers:

- **"I need to query messages with their authors and reaction counts in one query."**
  → Shows complex JOIN queries with multiple tables and aggregations

- **"I want to observe notes with a specific tag and update the UI whenever they change."**
  → Covers ValueObservation patterns for reactive query updates

- **"I'm importing thousands of chat records and need custom migration logic."**
  → Explains migration registration, data transforms, and safe rollback patterns

- **"My query is slow (takes 10+ seconds). How do I profile and optimize it?"**
  → Covers EXPLAIN QUERY PLAN, database.trace for profiling, and index creation

- **"I need to fetch tasks grouped by due date with completion counts."**
  → Demonstrates when GRDB's raw SQL is clearer than type-safe wrappers
