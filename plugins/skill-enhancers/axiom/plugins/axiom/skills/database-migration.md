---
name: database-migration
description: Use when adding/modifying database columns, encountering "FOREIGN KEY constraint failed", "no such column", "cannot add NOT NULL column" errors, or creating schema migrations for SQLite/GRDB/SQLiteData - prevents data loss with safe migration patterns and testing workflows for iOS/macOS apps
---

# Database Migration

## Overview

Safe database schema evolution for production apps with user data. **Core principle:** Migrations are immutable after shipping. Make them additive, idempotent, and thoroughly tested.

## Example Prompts

These are real questions developers ask that this skill is designed to answer:

**1. "I need to add a new column to store user preferences, but the app is already live with user data. How do I do this safely?"**
→ The skill covers safe additive patterns for adding columns without losing existing data, including idempotency checks

**2. "I'm getting 'cannot add NOT NULL column' errors when I try to migrate. What does this mean and how do I fix it?"**
→ The skill explains why NOT NULL columns fail with existing rows, and shows the safe pattern (nullable first, backfill later)

**3. "I need to change a column from text to integer. Can I just ALTER the column type?"**
→ The skill demonstrates the safe pattern: add new column → migrate data → deprecate old (NEVER delete)

**4. "I'm adding a foreign key relationship between tables. How do I add the relationship without breaking existing data?"**
→ The skill covers safe foreign key patterns: add column → populate data → add index (SQLite limitations explained)

**5. "Users are reporting crashes after the last update. I changed a migration but the app is already in production. What do I do?"**
→ The skill explains migrations are immutable after shipping; shows how to create a new migration to fix the issue rather than modifying the old one

---

## ⛔ NEVER Do These (Data Loss Risk)

**These actions DESTROY user data in production:**

❌ **NEVER use DROP TABLE** with user data
❌ **NEVER modify shipped migrations** (create new one instead)
❌ **NEVER recreate tables** to change schema (loses data)
❌ **NEVER add NOT NULL column** without DEFAULT value
❌ **NEVER delete columns** (SQLite doesn't support DROP COLUMN safely)

**If you're tempted to do any of these, STOP and use the safe patterns below.**

## Mandatory Rules

**ALWAYS follow these:**

1. **Additive only:** Add new columns/tables, never delete
2. **Idempotent:** Check existence before creating (safe to run twice)
3. **Transactional:** Wrap entire migration in single transaction
4. **Test both paths:** Fresh install AND migration from previous version
5. **Nullable first:** Add columns as NULL, backfill later if needed
6. **Immutable:** Once shipped to users, migrations cannot be changed

## Safe Patterns

### Adding Column (Most Common)

```swift
// ✅ Safe pattern
func migration00X_AddNewColumn() throws {
    try database.write { db in
        // 1. Check if column exists (idempotency)
        let hasColumn = try db.columns(in: "tableName")
            .contains { $0.name == "newColumn" }

        if !hasColumn {
            // 2. Add as nullable (works with existing rows)
            try db.execute(sql: """
                ALTER TABLE tableName
                ADD COLUMN newColumn TEXT
            """)
        }
    }
}
```

**Why this works:**
- Nullable columns don't require DEFAULT
- Existing rows get NULL automatically
- No data transformation needed
- Safe for users upgrading from old versions

### Adding Column with Default Value

```swift
// ✅ Safe pattern with default
func migration00X_AddColumnWithDefault() throws {
    try database.write { db in
        let hasColumn = try db.columns(in: "tracks")
            .contains { $0.name == "playCount" }

        if !hasColumn {
            try db.execute(sql: """
                ALTER TABLE tracks
                ADD COLUMN playCount INTEGER DEFAULT 0
            """)
        }
    }
}
```

### Changing Column Type (Advanced)

**Pattern**: Add new column → migrate data → deprecate old (NEVER delete)

```swift
// ✅ Safe pattern for type change
func migration00X_ChangeColumnType() throws {
    try database.write { db in
        // Step 1: Add new column with new type
        try db.execute(sql: """
            ALTER TABLE users
            ADD COLUMN age_new INTEGER
        """)

        // Step 2: Migrate existing data
        try db.execute(sql: """
            UPDATE users
            SET age_new = CAST(age_old AS INTEGER)
            WHERE age_old IS NOT NULL
        """)

        // Step 3: Application code uses age_new going forward
        // (Never delete age_old column - just stop using it)
    }
}
```

### Adding Foreign Key Constraint

```swift
// ✅ Safe pattern for foreign keys
func migration00X_AddForeignKey() throws {
    try database.write { db in
        // Step 1: Add new column (nullable initially)
        try db.execute(sql: """
            ALTER TABLE tracks
            ADD COLUMN album_id TEXT
        """)

        // Step 2: Populate the data
        try db.execute(sql: """
            UPDATE tracks
            SET album_id = (
                SELECT id FROM albums
                WHERE albums.title = tracks.album_name
            )
        """)

        // Step 3: Add index (helps query performance)
        try db.execute(sql: """
            CREATE INDEX IF NOT EXISTS idx_tracks_album_id
            ON tracks(album_id)
        """)

        // Note: SQLite doesn't allow adding FK constraints to existing tables
        // The foreign key relationship is enforced at the application level
    }
}
```

### Complex Schema Refactoring

**Pattern**: Break into multiple migrations

```swift
// Migration 1: Add new structure
func migration010_AddNewTable() throws {
    try database.write { db in
        try db.execute(sql: """
            CREATE TABLE IF NOT EXISTS new_structure (
                id TEXT PRIMARY KEY,
                data TEXT
            )
        """)
    }
}

// Migration 2: Copy data
func migration011_MigrateData() throws {
    try database.write { db in
        try db.execute(sql: """
            INSERT INTO new_structure (id, data)
            SELECT id, data FROM old_structure
        """)
    }
}

// Migration 3: Add indexes
func migration012_AddIndexes() throws {
    try database.write { db in
        try db.execute(sql: """
            CREATE INDEX IF NOT EXISTS idx_new_structure_data
            ON new_structure(data)
        """)
    }
}

// Old structure stays around (deprecated in code)
```

## Testing Checklist

**BEFORE deploying any migration:**

```swift
// Test 1: Migration path (CRITICAL - tests data preservation)
@Test func migrationFromV1ToV2Succeeds() async throws {
    let db = try Database(inMemory: true)

    // Simulate v1 schema
    try db.write { db in
        try db.execute(sql: "CREATE TABLE tableName (id TEXT PRIMARY KEY)")
        try db.execute(sql: "INSERT INTO tableName (id) VALUES ('test1')")
    }

    // Run v2 migration
    try db.runMigrations()

    // Verify data survived + new column exists
    try db.read { db in
        let count = try Int.fetchOne(db, sql: "SELECT COUNT(*) FROM tableName")
        #expect(count == 1)  // Data preserved

        let columns = try db.columns(in: "tableName").map { $0.name }
        #expect(columns.contains("newColumn"))  // New column exists
    }
}
```

**Test 2:** Fresh install (run all migrations, verify final schema)
```swift
@Test func freshInstallCreatesCorrectSchema() async throws {
    let db = try Database(inMemory: true)

    // Run all migrations
    try db.runMigrations()

    // Verify final schema
    try db.read { db in
        let tables = try db.tables()
        #expect(tables.contains("tableName"))

        let columns = try db.columns(in: "tableName").map { $0.name }
        #expect(columns.contains("id"))
        #expect(columns.contains("newColumn"))
    }
}
```

**Test 3:** Idempotency (run migrations twice, should not throw)
```swift
@Test func migrationsAreIdempotent() async throws {
    let db = try Database(inMemory: true)

    // Run migrations twice
    try db.runMigrations()
    try db.runMigrations()  // Should not throw

    // Verify still correct
    try db.read { db in
        let count = try Int.fetchOne(db, sql: "SELECT COUNT(*) FROM tableName")
        #expect(count == 0)  // No duplicate data
    }
}
```

**Manual testing (before TestFlight):**
1. Install v(n-1) build on device → add real user data
2. Install v(n) build (with new migration)
3. Verify: App launches, data visible, no crashes

## Decision Tree

```
What are you trying to do?
├─ Add new column?
│  └─ ALTER TABLE ADD COLUMN (nullable) → Done
├─ Add column with default?
│  └─ ALTER TABLE ADD COLUMN ... DEFAULT value → Done
├─ Change column type?
│  └─ Add new column → Migrate data → Deprecate old → Done
├─ Delete column?
│  └─ Mark as deprecated in code → Never delete from schema → Done
├─ Rename column?
│  └─ Add new column → Migrate data → Deprecate old → Done
├─ Add foreign key?
│  └─ Add column → Populate data → Add index → Done
└─ Complex refactor?
   └─ Break into multiple migrations → Test each step → Done
```

## Common Errors

| Error | Fix |
|-------|-----|
| `FOREIGN KEY constraint failed` | Check parent row exists, or disable FK temporarily |
| `no such column: columnName` | Add migration to create column |
| `cannot add NOT NULL column` | Use nullable column first, backfill in separate migration |
| `table tableName already exists` | Add `IF NOT EXISTS` clause |
| `duplicate column name` | Check if column exists before adding (idempotency) |

## Common Mistakes

❌ **Adding NOT NULL without DEFAULT**
```swift
// ❌ Fails on existing data
ALTER TABLE albums ADD COLUMN rating INTEGER NOT NULL
```

✅ **Correct: Add as nullable first**
```swift
ALTER TABLE albums ADD COLUMN rating INTEGER  // NULL allowed
// Backfill in separate migration if needed
UPDATE albums SET rating = 0 WHERE rating IS NULL
```

❌ **Forgetting to check for existence** - Always add `IF NOT EXISTS` or manual check

❌ **Modifying shipped migrations** - Create new migration instead

❌ **Not testing migration path** - Always test upgrade from previous version

## GRDB-Specific Patterns

### DatabaseMigrator Setup

```swift
var migrator = DatabaseMigrator()

// Migration 1
migrator.registerMigration("v1") { db in
    try db.execute(sql: """
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL
        )
    """)
}

// Migration 2
migrator.registerMigration("v2") { db in
    let hasColumn = try db.columns(in: "users")
        .contains { $0.name == "email" }

    if !hasColumn {
        try db.execute(sql: """
            ALTER TABLE users
            ADD COLUMN email TEXT
        """)
    }
}

// Apply migrations
try migrator.migrate(dbQueue)
```

### Checking Migration Status

```swift
// Check which migrations have been applied
let appliedMigrations = try dbQueue.read { db in
    try migrator.appliedMigrations(db)
}
print("Applied migrations: \(appliedMigrations)")

// Check if migrations are needed
let hasBeenMigrated = try dbQueue.read { db in
    try migrator.hasBeenMigrated(db)
}
```

## SwiftData Migrations

For SwiftData (iOS 17+), use `VersionedSchema` and `SchemaMigrationPlan`:

```swift
// Define schema versions
enum MyAppSchemaV1: VersionedSchema {
    static var versionIdentifier = Schema.Version(1, 0, 0)
    static var models: [any PersistentModel.Type] {
        [Track.self, Album.self]
    }
}

enum MyAppSchemaV2: VersionedSchema {
    static var versionIdentifier = Schema.Version(2, 0, 0)
    static var models: [any PersistentModel.Type] {
        [Track.self, Album.self, Playlist.self]  // Added Playlist
    }
}

// Define migration plan
enum MyAppMigrationPlan: SchemaMigrationPlan {
    static var schemas: [any VersionedSchema.Type] {
        [MyAppSchemaV1.self, MyAppSchemaV2.self]
    }

    static var stages: [MigrationStage] {
        [migrateV1toV2]
    }

    static let migrateV1toV2 = MigrationStage.custom(
        fromVersion: MyAppSchemaV1.self,
        toVersion: MyAppSchemaV2.self,
        willMigrate: nil,
        didMigrate: { context in
            // Custom migration logic here
        }
    )
}
```

## Real-World Impact

**Before:** Developer adds NOT NULL column → migration fails for 50% of users → emergency rollback → data inconsistency

**After:** Developer adds nullable column → tests both paths → smooth deployment → backfills data in v2

**Key insight:** Migrations can't be rolled back in production. Get them right the first time through thorough testing.

---

**Last Updated**: 2025-11-28
**Frameworks**: SQLite, GRDB, SwiftData
**Status**: Production-ready patterns for safe schema evolution
