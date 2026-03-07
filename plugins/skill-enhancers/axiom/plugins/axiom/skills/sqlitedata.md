---
name: sqlitedata
description: Use when working with SQLiteData (Point-Free) - @Table models, queries with @FetchAll/@FetchOne, CloudKit sync setup, StructuredQueries post-migration crashes, batch imports, production crisis decision-making under App Store deployment pressure, and when to drop to GRDB - type-safe SQLite persistence patterns for iOS
version: 1.1.0
last_updated: TDD-tested with App Store migration crisis scenarios
---

# SQLiteData

## Overview

Type-safe SQLite persistence using [SQLiteData](https://pointfreeco.github.io/sqlite-data/) ([GitHub](https://github.com/pointfreeco/sqlite-data)) by Point-Free. Built on [GRDB](https://github.com/groue/GRDB.swift), providing SwiftData-like ergonomics with CloudKit sync support.

**Core principle:** Value types (`struct`) + `@Table` macros + static methods for type-safe database operations.

**Requires:** iOS 17+, Swift 6 concurrency
**License:** MIT (free and open source)

## When to Use SQLiteData

**Choose SQLiteData when you need:**
- ✅ Type-safe SQLite with compiler-checked queries
- ✅ CloudKit sync with record sharing
- ✅ Large datasets (50k+ records) with fast performance
- ✅ Value types (structs) instead of classes
- ✅ Swift 6 strict concurrency support

**Use SwiftData instead when:**
- Simple CRUD with native Apple integration
- Prefer `@Model` classes over structs
- Don't need CloudKit record sharing

**Use raw GRDB when:**
- Complex SQL joins across multiple tables
- Custom migration logic
- Performance-critical batch operations

**For migrations:** See the `database-migration` skill for safe schema evolution patterns.

## Example Prompts

These are real questions developers ask that this skill is designed to answer:

**1. "I'm building a task app with type-safe queries. How do I set up @Table models and filter tasks by priority?"**
→ The skill shows `@Table` definitions, `@Query` with predicates, and type-safe filtering

**2. "I need to sync tasks to other devices via CloudKit. How do I set up sync with record sharing?"**
→ The skill covers CloudKit integration, record sharing, and sync conflict handling

**3. "I'm importing 50,000 notes from an API. How do I batch insert efficiently without blocking the UI?"**
→ The skill shows batch operations, background writes, and progress tracking patterns

**4. "After updating the app, some queries are crashing with StructuredQueries errors. How do I fix it?"**
→ The skill explains StructuredQueries migration issues, safe recovery, and prevention strategies

**5. "I have complex queries with joins across 4 tables. Should I use SQLiteData or drop to GRDB?"**
→ The skill explains when to use SQLiteData vs raw GRDB for performance-critical queries

---

## @Table Model Definitions

### Basic Table

```swift
import SQLiteData

@Table
struct Track: Identifiable, Sendable {
    @Attribute(.primaryKey)
    var id: String

    var title: String
    var artist: String
    var duration: TimeInterval
    var genre: String?  // Optional columns are nullable
}
```

**Key patterns:**
- Use `struct`, not `class` (value types)
- Conform to `Sendable` for Swift 6 concurrency
- Use `@Attribute(.primaryKey)` for primary key
- Optional properties (`String?`) map to nullable SQL columns

### Foreign Keys

```swift
@Table
struct Track: Identifiable, Sendable {
    @Attribute(.primaryKey)
    var id: String

    var title: String
    var albumId: String  // Foreign key (explicit, not @Relationship)
}

@Table
struct Album: Identifiable, Sendable {
    @Attribute(.primaryKey)
    var id: String

    var title: String
    var artist: String
}
```

**Important:** SQLiteData uses explicit foreign key columns, not `@Relationship` macros like SwiftData.

## Database Setup

```swift
import SQLiteData
import Dependencies

// 1. Create database dependency
extension DependencyValues {
    var musicDatabase: Database {
        get { self[DatabaseKey.self] }
        set { self[DatabaseKey.self] = newValue }
    }
}

private struct DatabaseKey: DependencyKey {
    static let liveValue: Database = {
        let path = NSSearchPathForDirectoriesInDomains(.documentDirectory, .userDomainMask, true)[0]
        let dbPath = "\(path)/music.db"
        return try! DatabaseQueue(path: dbPath)
    }()
}

// 2. Use in your code
struct MusicRepository {
    @Dependency(\.musicDatabase) var database

    func fetchTracks() async throws -> [Track] {
        try await Track.fetchAll(database)
    }
}
```

**Pattern:** SQLiteData works well with [swift-dependencies](https://github.com/pointfreeco/swift-dependencies) for dependency injection.

## Query Patterns

### Fetch All

```swift
// Fetch all tracks
let tracks = try await Track.fetchAll(database)

// With @FetchAll property wrapper (SwiftUI)
@FetchAll<Track>
var tracks: [Track]
```

### Fetch One

```swift
// Fetch by primary key
let track = try await Track.fetchOne(database, key: "track123")

// With @FetchOne property wrapper
@FetchOne<Track>
var track: Track?
```

### Filtering

```swift
// Type-safe where clause
let rockTracks = try await Track
    .where { $0.genre == "Rock" }
    .fetchAll(database)

// Multiple conditions
let results = try await Track
    .where { $0.genre == "Rock" && $0.duration > 180 }
    .fetchAll(database)
```

### Sorting

```swift
let sorted = try await Track
    .order { $0.title.ascending }
    .fetchAll(database)
```

## Insert/Update/Delete

### Insert

```swift
let track = Track(
    id: "track1",
    title: "Song Name",
    artist: "Artist",
    duration: 240,
    genre: "Rock"
)

// ✅ CORRECT: Static method pattern
try await Track.insert { track }.execute(database)

// ❌ WRONG: GRDB Active Record pattern (doesn't work with @Table)
try track.insert(database)  // Won't compile
```

**Critical:** SQLiteData uses **static methods**, not instance methods. This is different from GRDB's Active Record pattern.

### Update

```swift
try await Track
    .update { $0.genre = "Pop" }
    .where { $0.id == "track1" }
    .execute(database)
```

### Delete

```swift
try await Track
    .delete()
    .where { $0.id == "track1" }
    .execute(database)
```

## Batch Operations

### Batch Insert (Fast)

For large datasets (50k+ records):

```swift
func importTracks(_ tracks: [Track]) async throws {
    let batchSize = 500  // Optimal for GRDB

    for i in stride(from: 0, to: tracks.count, by: batchSize) {
        let batchEnd = min(i + batchSize, tracks.count)
        let batch = Array(tracks[i..<batchEnd])

        // Single transaction per batch
        try await database.write { db in
            for track in batch {
                try Track.insert { track }.execute(db)
            }
        }

        print("Imported \(batchEnd)/\(tracks.count)")
    }
}
```

**Performance:**
- 50,000 records in ~30-45 seconds
- Batching reduces 50k transactions to 100 transactions (500 records each)
- Each `database.write { }` block is ONE transaction

### Why Batching Matters

| Pattern | Transactions | Time for 50k records |
|---------|--------------|---------------------|
| One-by-one | 50,000 | ~4 hours |
| Batched (500 each) | 100 | ~45 seconds |
| Single transaction | 1 | ~20 seconds (risky) |

**Recommendation:** Use batch size 500 for resilience. Single transaction is faster but rolls back entirely on any failure.

## ⚠️ Critical Gotchas

### 1. StructuredQueries Post-Migration Crash

**Problem:** Using `.where{}` queries immediately after running a migration causes SEGFAULT.

```swift
// ❌ THIS WILL CRASH
func testMigration() async throws {
    // Run migration that adds column
    try await migrator.migrate(database)

    // CRASH: StructuredQueries keypath cache is stale
    let tracks = try await Track
        .where { $0.genre == "Rock" }  // SEGFAULT here
        .fetchAll(database)
}
```

**Error:**
```
Exception Type:    EXC_BAD_ACCESS (SIGSEGV)
Exception Codes:   KERN_INVALID_ADDRESS at 0xfffffffffffffff8
Triggered by:      GRDB.DatabaseQueue
```

**Root Cause:** Migration updates GRDB schema, but StructuredQueries keypath cache remains stale. Next `.where{}` query uses old memory offsets → SEGFAULT.

**Solution:** Close and reopen database after migrations:

```swift
// ✅ CORRECT
func testMigration() async throws {
    try await migrator.migrate(database)

    // Close and reopen to refresh schema cache
    try database.close()
    database = try DatabaseQueue(path: dbPath)

    // Now queries work
    let tracks = try await Track
        .where { $0.genre == "Rock" }
        .fetchAll(database)
}
```

**Alternative:** Use raw GRDB filter (bypasses StructuredQueries):

```swift
import GRDB

// Works immediately after migration (no cache)
let tracks = try Track.filter(Column("genre") == "Rock").fetchAll(db)
```

### 2. Static .where{} in Tests Crash

**Problem:** Using `static let` for `.where{}` queries in tests causes crashes.

```swift
// ❌ THIS CRASHES IN TESTS
extension Track {
    static let rockTracks = Track.where { $0.genre == "Rock" }
}

func testRockTracks() async throws {
    let tracks = try await Track.rockTracks.fetchAll(database)  // CRASH
}
```

**Error:**
```
Exception Type:    EXC_BAD_ACCESS (SIGSEGV)
Address:           0xfffffffffffffff8 (-8)
Location:          static Table.where(_:) + 200 (Where.swift:51)
```

**Root Cause:** Schema loads before database exists in test setup → keypath cache has invalid offsets.

**Solution:** Use computed properties or functions:

```swift
// ✅ CORRECT: Computed property
extension Track {
    static var rockTracks: some Query<Track> {
        Track.where { $0.genre == "Rock" }
    }
}

// ✅ CORRECT: Function
extension Track {
    static func genre(_ name: String) -> some Query<Track> {
        Track.where { $0.genre == name }
    }
}
```

### 3. Wrong Insert Pattern

**Problem:** Using GRDB's Active Record pattern with `@Table` structs.

```swift
let track = Track(...)

// ❌ WRONG: Active Record (instance method)
try track.insert(database)  // Won't compile

// ✅ CORRECT: SQLiteData static method
try Track.insert { track }.execute(database)
```

**Why:** `@Table` macro generates static methods, not instance methods. This is intentional to work with value types (structs).

## CloudKit Sync

### Basic Setup

```swift
import SQLiteData
import CloudKit

// 1. Configure database with CloudKit
let container = CKContainer.default()
let database = try DatabaseQueue(
    path: dbPath,
    cloudKit: .init(
        container: container,
        recordZone: CKRecordZone(zoneName: "MusicLibrary")
    )
)

// 2. Mark tables for sync
@Table(.cloudKit)  // Sync this table
struct Track: Identifiable, Sendable {
    @Attribute(.primaryKey)
    var id: String
    var title: String
}

// 3. Start sync engine
try await database.startCloudKitSync()
```

### Conflict Resolution

```swift
database.cloudKitConflictResolver = { serverRecord, clientRecord in
    // Last-write-wins strategy
    return serverRecord.modificationDate > clientRecord.modificationDate
        ? .useServer
        : .useClient
}
```

**For detailed CloudKit sync patterns:** See [SQLiteData CloudKit docs](https://pointfreeco.github.io/sqlite-data/documentation/sqlitedata/cloudkit)

## When to Drop to GRDB

Use raw GRDB for:

### Complex Joins

```swift
import GRDB

let sql = """
    SELECT tracks.*, albums.title as album_title
    FROM tracks
    JOIN albums ON tracks.albumId = albums.id
    WHERE albums.artist = ?
    """

let results = try database.read { db in
    try Row.fetchAll(db, sql: sql, arguments: ["Artist Name"])
}
```

### Custom Migrations

```swift
import GRDB

var migrator = DatabaseMigrator()

migrator.registerMigration("v1_complex_migration") { db in
    // Full GRDB power for complex schema changes
    try db.execute(sql: "...")
}
```

### ValueObservation (Reactive Queries)

```swift
import GRDB

let observation = ValueObservation.tracking { db in
    try Track.fetchAll(db)
}

let cancellable = observation.start(in: database) { tracks in
    print("Tracks updated: \(tracks.count)")
}
```

**For GRDB patterns:** See the `grdb` skill for raw SQL and advanced database operations.

## Performance Tips

### Use Indexes

```swift
migrator.registerMigration("v2_add_indexes") { db in
    try db.create(index: "idx_tracks_genre", on: "Track", columns: ["genre"])
    try db.create(index: "idx_tracks_artist", on: "Track", columns: ["artist"])
}
```

### Batch Writes

Always batch large operations (use 500 records per transaction as baseline).

### Avoid N+1 Queries

```swift
// ❌ BAD: N+1 queries
for track in tracks {
    let album = try await Album.fetchOne(database, key: track.albumId)
}

// ✅ GOOD: Single query with join or batch fetch
let albumIds = tracks.map(\.albumId)
let albums = try await Album
    .where { albumIds.contains($0.id) }
    .fetchAll(database)
```

## Comparison: SQLiteData vs SwiftData

| Feature | SQLiteData | SwiftData |
|---------|-----------|-----------|
| **Type** | Value types (struct) | Reference types (class) |
| **Macro** | `@Table` | `@Model` |
| **Primary Key** | `@Attribute(.primaryKey)` | `@Attribute(.unique)` |
| **Queries** | `@FetchAll` / `@FetchOne` | `@Query` |
| **Injection** | `@Dependency(\.database)` | `@Environment(\.modelContext)` |
| **CloudKit** | Full sync + sharing | Sync only (no sharing) |
| **Performance** | Excellent (raw SQL) | Good (Core Data) |
| **Learning Curve** | Moderate | Easy |

## Quick Reference

### Common Operations

```swift
// Fetch all
let all = try await Track.fetchAll(database)

// Fetch one by key
let one = try await Track.fetchOne(database, key: "id")

// Filter
let filtered = try await Track.where { $0.genre == "Rock" }.fetchAll(database)

// Insert
try await Track.insert { track }.execute(database)

// Update
try await Track.update { $0.genre = "Pop" }.where { $0.id == "id" }.execute(database)

// Delete
try await Track.delete().where { $0.id == "id" }.execute(database)

// Count
let count = try await Track.fetchCount(database)
```

## External Resources

**SQLiteData:**
- [Documentation](https://pointfreeco.github.io/sqlite-data/)
- [GitHub](https://github.com/pointfreeco/sqlite-data)
- [Point-Free Episodes](https://www.pointfree.co) (video tutorials, subscription)

**Dependencies:**
- [swift-dependencies](https://github.com/pointfreeco/swift-dependencies) - Dependency injection (pairs well with SQLiteData)
- [GRDB](https://github.com/groue/GRDB.swift) - Underlying database engine

**Related Axiom Skills:**
- `database-migration` - Safe schema evolution patterns
- `grdb` - Raw SQL and advanced GRDB features
- `swiftdata` - Apple's native persistence framework

## Production Crisis: When Migrations Cause App Store Crashes

### The StructuredQueries Migration Crash

**Scenario**: Users updating to iOS 26 build crash on launch. Error: `EXC_BAD_ACCESS KERN_INVALID_ADDRESS at 0xfffffffffffffff8`

**Under pressure:**
- Temptation: Delete old schema and recreate (fast, destructive)
- Better: Search this skill for "StructuredQueries" and follow safe path

**The problem** (lines 250-274):
```
Migration → GRDB schema updated
→ SQLiteData StructuredQueries cache becomes stale
→ Next .where{} query uses old memory offsets
→ CRASH (SEGFAULT)
```

**The fix** (lines 276-291):
```swift
// Close and reopen to refresh cache
try await migrator.migrate(database)
try database.close()
database = try DatabaseQueue(path: dbPath)

// Now .where{} queries work
let tracks = try await Track.where { $0.genre == "Rock" }.fetchAll(database)
```

**Time cost:**
- Understanding problem: 5 min (search skill for "StructuredQueries")
- Implementing fix: 30 min
- Testing: 15 min
- **Total: 50 minutes**, zero data loss

**Alternative if close/reopen doesn't work** (lines 294-300):
```swift
// Bypass StructuredQueries, use raw GRDB
let tracks = try Track.filter(Column("genre") == "Rock").fetchAll(db)
```

### Decision Framework Under Pressure

When migration causes crashes:

**DO NOT:**
- ❌ Delete schema and recreate (data loss)
- ❌ Ship guess-fixes without testing (worsens crash)
- ❌ Ignore this skill section (solution is here)

**DO:**
- ✅ Search this skill for error keyword (e.g., "KERN_INVALID_ADDRESS", "StructuredQueries")
- ✅ Implement documented fix (close/reopen or raw GRDB)
- ✅ Test in simulator before App Store submission

**Time budget:**
- Search + understand: 5-10 min
- Implement: 30 min
- Test: 15 min
- **Total: 50 min** (most App Store update windows allow 3-4 hours)

### If You Must Ship Emergency Mitigation

**Temporary fix while proper solution is tested:**
```swift
// Disable StructuredQueries globally during migration
database.disableStructuredQueries = true
try await migrator.migrate(database)
database.disableStructuredQueries = false
```

**This buys time:**
- Unblocks app update (users can install)
- Preserves user data (no deletion)
- Proper fix queued for next release

### Honest Pressure Points (When Panic Tempts Nuclear Option)

**If you're tempted to delete schema under pressure:**
1. **Stop.** Search this skill for the error keyword first
2. **Document.** The fact that you found this section proves safe path exists
3. **Ship safe mitigation.** 50 minutes for proper fix < 24 hours to recover from data loss

**Why nuclear option backfires:**
- Users lose all local data (playlists, favorites)
- App reviews tank (4.5 stars → 2 stars typical)
- Support tickets explode
- Recovery takes weeks of backfills and apologies

**Why proper fix wins:**
- Users keep all data
- Trust preserved
- Clean recovery
- Skill exists because others solved this already

---

## Common Mistakes

### ❌ Using instance methods
```swift
try track.insert(database)  // Won't compile
```
**Fix:** Use static methods: `try Track.insert { track }.execute(database)`

### ❌ Querying immediately after migration
```swift
try migrator.migrate(database)
let tracks = try Track.where { ... }.fetchAll(database)  // CRASH
```
**Fix:** Close/reopen database or use raw GRDB filter

### ❌ Static queries in tests
```swift
static let rockTracks = Track.where { $0.genre == "Rock" }  // CRASH
```
**Fix:** Use computed properties or functions

### ❌ Single-record inserts for large datasets
```swift
for track in 50000Tracks {
    try Track.insert { track }.execute(database)  // 4 hours!
}
```
**Fix:** Batch in groups of 500 per transaction

---

## Version History

- **1.1.0**: Added "Production Crisis: When Migrations Cause App Store Crashes" section from TDD testing of iOS 26 StructuredQueries migration failure scenario. Includes decision framework preventing destructive schema recreation, time-cost analysis (50 min safe fix vs 24hr+ data loss recovery), emergency mitigation patterns, and honest pressure points analysis. Ensures developers search for documented solutions before choosing data-loss options
- **1.0.0**: Initial skill covering @Table models, batch operations, CloudKit sync, critical StructuredQueries gotcha, and GRDB fallback patterns

---

**Created:** 2025-11-28
**Targets:** iOS 17+, Swift 6
**Framework:** SQLiteData 1.0+ (Point-Free)
