# SQLiteData

SQLiteData (Point-Free) patterns, critical gotchas, batch performance, and CloudKit sync.

**When to use**: Working with SQLiteData @Table models, @FetchAll/@FetchOne queries, StructuredQueries post-migration crashes, batch imports, deciding when to drop to GRDB

## Key Features

- @Table model patterns
- Query patterns with @FetchAll/@FetchOne
- StructuredQueries crash prevention
- Batch import performance
- CloudKit sync setup
- When to drop to GRDB for performance

## Example Prompts

These are real questions developers ask that this skill answers:

- **"I'm building a task app with type-safe queries. How do I set up @Table models and filter by priority?"**
  → Shows @Table definitions, @Query with predicates, and type-safe filtering

- **"I need to sync tasks to other devices via CloudKit."**
  → Covers CloudKit integration, record sharing, and sync conflict handling

- **"I'm importing 50,000 notes from an API. How do I batch insert efficiently?"**
  → Shows batch operations, background writes, and progress tracking patterns

- **"After updating the app, queries are crashing with StructuredQueries errors."**
  → Explains StructuredQueries migration issues, safe recovery, and prevention strategies

- **"I have complex queries with joins across 4 tables. Should I use SQLiteData or drop to GRDB?"**
  → Explains when to use SQLiteData vs raw GRDB for performance-critical queries
