# Persistence

Comprehensive database patterns for safe schema evolution and choosing the right persistence framework for your needs.

## Skills

- **[Database Migration](/skills/persistence/database-migration)** – Safe schema evolution for SQLite/GRDB/SwiftData, prevents data loss
  - *"I need to add a column to my live app without losing user data. How do I migrate safely?"*
  - *"I'm getting 'cannot add NOT NULL column' errors. What does this mean?"*

- **[SQLiteData](/skills/persistence/sqlitedata)** – Point-Free's SQLiteData patterns, batch performance, and CloudKit sync
  - *"I'm building a task app with type-safe queries. How do I set up @Table models and filter by priority?"*
  - *"I'm importing 50,000 notes from an API. How do I batch insert efficiently without blocking the UI?"*

- **[GRDB](/skills/persistence/grdb)** – Raw SQL queries, ValueObservation, and DatabaseMigrator patterns
  - *"I need to query messages with their authors and reaction counts in one query. How do I write the JOIN?"*
  - *"I want to observe notes with a specific tag and update the UI whenever they change."*

- **[SwiftData](/skills/persistence/swiftdata)** – iOS 26+ features, @Model, @Query patterns, and Swift 6 concurrency
  - *"I have a notes app with folders. How do I filter and sort with @Query?"*
  - *"When a user deletes a task list, all tasks should auto-delete too. How do I set up cascading deletes?"*
