---
name: grdb
description: Use when writing raw SQL queries with GRDB, complex joins, ValueObservation for reactive queries, DatabaseMigrator patterns, query profiling under performance pressure, or dropping down from SQLiteData for performance - direct SQLite access for iOS/macOS
version: 1.1.0
last_updated: TDD-tested with complex query performance scenarios
---

# GRDB

## Overview

Direct SQLite access using [GRDB.swift](https://github.com/groue/GRDB.swift) - a toolkit for SQLite databases with type-safe queries, migrations, and reactive observation.

**Core principle:** Type-safe Swift wrapper around raw SQL with full SQLite power when you need it.

**Requires:** iOS 13+, Swift 5.7+
**License:** MIT (free and open source)

## When to Use GRDB

**Use raw GRDB when you need:**
- ✅ Complex SQL joins across multiple tables
- ✅ Custom aggregation queries (GROUP BY, HAVING)
- ✅ Reactive queries with ValueObservation
- ✅ Full control over SQL for performance
- ✅ Advanced migration logic

**Use SQLiteData instead when:**
- Type-safe `@Table` models are sufficient
- CloudKit sync needed
- Prefer declarative queries over SQL

**Use SwiftData when:**
- Simple CRUD with native Apple integration
- Don't need raw SQL control

**For migrations:** See the `database-migration` skill for safe schema evolution patterns.

## Example Prompts

These are real questions developers ask that this skill is designed to answer:

**1. "I need to query messages with their authors and count of reactions in one query. How do I write the JOIN?"**
→ The skill shows complex JOIN queries with multiple tables and aggregations

**2. "I want to observe a filtered list and update the UI whenever notes with a specific tag change."**
→ The skill covers ValueObservation patterns for reactive query updates

**3. "I'm importing thousands of chat records and need custom migration logic. How do I use DatabaseMigrator?"**
→ The skill explains migration registration, data transforms, and safe rollback patterns

**4. "My query is slow (takes 10+ seconds). How do I profile and optimize it?"**
→ The skill covers EXPLAIN QUERY PLAN, database.trace for profiling, and index creation

**5. "I need to fetch tasks grouped by due date with completion counts, ordered by priority. Raw SQL seems easier than type-safe queries."**
→ The skill demonstrates when GRDB's raw SQL is clearer than type-safe wrappers

---

## Database Setup

### DatabaseQueue (Single Connection)

```swift
import GRDB

// File-based database
let dbPath = NSSearchPathForDirectoriesInDomains(.documentDirectory, .userDomainMask, true)[0]
let dbQueue = try DatabaseQueue(path: "\(dbPath)/db.sqlite")

// In-memory database (tests)
let dbQueue = try DatabaseQueue()
```

### DatabasePool (Connection Pool)

```swift
// For apps with heavy concurrent access
let dbPool = try DatabasePool(path: dbPath)
```

**Use Queue for:** Most apps (simpler, sufficient)
**Use Pool for:** Heavy concurrent writes from multiple threads

## Record Types

### Using Codable

```swift
struct Track: Codable {
    var id: String
    var title: String
    var artist: String
    var duration: TimeInterval
}

// Fetch
let tracks = try dbQueue.read { db in
    try Track.fetchAll(db, sql: "SELECT * FROM tracks")
}

// Insert
try dbQueue.write { db in
    try track.insert(db)  // Codable conformance provides insert
}
```

### FetchableRecord (Read-Only)

```swift
struct TrackInfo: FetchableRecord {
    var title: String
    var artist: String
    var albumTitle: String

    init(row: Row) {
        title = row["title"]
        artist = row["artist"]
        albumTitle = row["album_title"]
    }
}

let results = try dbQueue.read { db in
    try TrackInfo.fetchAll(db, sql: """
        SELECT tracks.title, tracks.artist, albums.title as album_title
        FROM tracks
        JOIN albums ON tracks.albumId = albums.id
        """)
}
```

### PersistableRecord (Write)

```swift
struct Track: Codable, PersistableRecord {
    var id: String
    var title: String

    // Customize table name
    static let databaseTableName = "tracks"
}

try dbQueue.write { db in
    var track = Track(id: "1", title: "Song")
    try track.insert(db)

    track.title = "Updated"
    try track.update(db)

    try track.delete(db)
}
```

## Raw SQL Queries

### Reading Data

```swift
// Fetch all rows
let rows = try dbQueue.read { db in
    try Row.fetchAll(db, sql: "SELECT * FROM tracks WHERE genre = ?", arguments: ["Rock"])
}

// Fetch single value
let count = try dbQueue.read { db in
    try Int.fetchOne(db, sql: "SELECT COUNT(*) FROM tracks")
}

// Fetch into Codable
let tracks = try dbQueue.read { db in
    try Track.fetchAll(db, sql: "SELECT * FROM tracks ORDER BY title")
}
```

### Writing Data

```swift
try dbQueue.write { db in
    try db.execute(sql: """
        INSERT INTO tracks (id, title, artist, duration)
        VALUES (?, ?, ?, ?)
        """, arguments: ["1", "Song", "Artist", 240])
}
```

### Transactions

```swift
try dbQueue.write { db in
    // Automatic transaction - all or nothing
    for track in tracks {
        try track.insert(db)
    }
    // Commits automatically on success, rolls back on error
}
```

## Type-Safe Query Interface

### Filtering

```swift
let request = Track
    .filter(Column("genre") == "Rock")
    .filter(Column("duration") > 180)

let tracks = try dbQueue.read { db in
    try request.fetchAll(db)
}
```

### Sorting

```swift
let request = Track
    .order(Column("title").asc)
    .limit(10)
```

### Joins

```swift
struct TrackWithAlbum: FetchableRecord {
    var trackTitle: String
    var albumTitle: String
}

let request = Track
    .joining(required: Track.belongsTo(Album.self))
    .select(Column("title").forKey("trackTitle"), Column("album_title").forKey("albumTitle"))

let results = try dbQueue.read { db in
    try TrackWithAlbum.fetchAll(db, request)
}
```

## Complex Joins

```swift
let sql = """
    SELECT
        tracks.title as track_title,
        albums.title as album_title,
        artists.name as artist_name,
        COUNT(plays.id) as play_count
    FROM tracks
    JOIN albums ON tracks.albumId = albums.id
    JOIN artists ON albums.artistId = artists.id
    LEFT JOIN plays ON plays.trackId = tracks.id
    WHERE artists.genre = ?
    GROUP BY tracks.id
    HAVING play_count > 10
    ORDER BY play_count DESC
    LIMIT 50
    """

struct TrackStats: FetchableRecord {
    var trackTitle: String
    var albumTitle: String
    var artistName: String
    var playCount: Int

    init(row: Row) {
        trackTitle = row["track_title"]
        albumTitle = row["album_title"]
        artistName = row["artist_name"]
        playCount = row["play_count"]
    }
}

let stats = try dbQueue.read { db in
    try TrackStats.fetchAll(db, sql: sql, arguments: ["Rock"])
}
```

## ValueObservation (Reactive Queries)

### Basic Observation

```swift
import GRDB
import Combine

let observation = ValueObservation.tracking { db in
    try Track.fetchAll(db)
}

// Start observing with Combine
let cancellable = observation.publisher(in: dbQueue)
    .sink(
        receiveCompletion: { _ in },
        receiveValue: { tracks in
            print("Tracks updated: \(tracks.count)")
        }
    )
```

### SwiftUI Integration

```swift
import GRDB
import GRDBQuery  // https://github.com/groue/GRDBQuery

@Query(Tracks())
var tracks: [Track]

struct Tracks: Queryable {
    static var defaultValue: [Track] { [] }

    func publisher(in dbQueue: DatabaseQueue) -> AnyPublisher<[Track], Error> {
        ValueObservation
            .tracking { db in try Track.fetchAll(db) }
            .publisher(in: dbQueue)
            .eraseToAnyPublisher()
    }
}
```

**See:** [GRDBQuery documentation](https://github.com/groue/GRDBQuery) for SwiftUI reactive bindings.

### Filtered Observation

```swift
func observeGenre(_ genre: String) -> ValueObservation<[Track]> {
    ValueObservation.tracking { db in
        try Track
            .filter(Column("genre") == genre)
            .fetchAll(db)
    }
}

let cancellable = observeGenre("Rock")
    .publisher(in: dbQueue)
    .sink { tracks in
        print("Rock tracks: \(tracks.count)")
    }
```

## Migrations

### DatabaseMigrator

```swift
var migrator = DatabaseMigrator()

// Migration 1: Create tables
migrator.registerMigration("v1") { db in
    try db.create(table: "tracks") { t in
        t.column("id", .text).primaryKey()
        t.column("title", .text).notNull()
        t.column("artist", .text).notNull()
        t.column("duration", .real).notNull()
    }
}

// Migration 2: Add column
migrator.registerMigration("v2_add_genre") { db in
    try db.alter(table: "tracks") { t in
        t.add(column: "genre", .text)
    }
}

// Migration 3: Add index
migrator.registerMigration("v3_add_indexes") { db in
    try db.create(index: "idx_genre", on: "tracks", columns: ["genre"])
}

// Run migrations
try migrator.migrate(dbQueue)
```

**For migration safety patterns:** See the `database-migration` skill.

### Migration with Data Transform

```swift
migrator.registerMigration("v4_normalize_artists") { db in
    // 1. Create new table
    try db.create(table: "artists") { t in
        t.column("id", .text).primaryKey()
        t.column("name", .text).notNull()
    }

    // 2. Extract unique artists
    try db.execute(sql: """
        INSERT INTO artists (id, name)
        SELECT DISTINCT
            lower(replace(artist, ' ', '_')) as id,
            artist as name
        FROM tracks
        """)

    // 3. Add foreign key to tracks
    try db.alter(table: "tracks") { t in
        t.add(column: "artistId", .text)
            .references("artists", onDelete: .cascade)
    }

    // 4. Populate foreign keys
    try db.execute(sql: """
        UPDATE tracks
        SET artistId = (
            SELECT id FROM artists
            WHERE artists.name = tracks.artist
        )
        """)
}
```

## Performance Patterns

### Batch Writes

```swift
try dbQueue.write { db in
    for batch in tracks.chunked(into: 500) {
        for track in batch {
            try track.insert(db)
        }
    }
}
```

### Prepared Statements

```swift
try dbQueue.write { db in
    let statement = try db.makeStatement(sql: """
        INSERT INTO tracks (id, title, artist, duration)
        VALUES (?, ?, ?, ?)
        """)

    for track in tracks {
        try statement.execute(arguments: [track.id, track.title, track.artist, track.duration])
    }
}
```

### Indexes

```swift
try db.create(index: "idx_tracks_artist", on: "tracks", columns: ["artist"])
try db.create(index: "idx_tracks_genre_duration", on: "tracks", columns: ["genre", "duration"])

// Unique index
try db.create(index: "idx_tracks_unique_title", on: "tracks", columns: ["title"], unique: true)
```

### Query Planning

```swift
// Analyze query performance
let explanation = try dbQueue.read { db in
    try String.fetchOne(db, sql: "EXPLAIN QUERY PLAN SELECT * FROM tracks WHERE artist = ?", arguments: ["Artist"])
}
print(explanation)
```

## Dropping Down from SQLiteData

When using SQLiteData but need GRDB for specific operations:

```swift
import SQLiteData
import GRDB

@Dependency(\.database) var database  // SQLiteData Database

// Access underlying GRDB DatabaseQueue
try await database.database.write { db in
    // Full GRDB power here
    try db.execute(sql: "CREATE INDEX idx_genre ON tracks(genre)")
}
```

**Common scenarios:**
- Complex JOIN queries
- Custom migrations
- Bulk SQL operations
- ValueObservation setup

## Quick Reference

### Common Operations

```swift
// Read single value
let count = try db.fetchOne(Int.self, sql: "SELECT COUNT(*) FROM tracks")

// Read all rows
let rows = try Row.fetchAll(db, sql: "SELECT * FROM tracks WHERE genre = ?", arguments: ["Rock"])

// Write
try db.execute(sql: "INSERT INTO tracks VALUES (?, ?, ?)", arguments: [id, title, artist])

// Transaction
try dbQueue.write { db in
    // All or nothing
}

// Observe changes
ValueObservation.tracking { db in
    try Track.fetchAll(db)
}.publisher(in: dbQueue)
```

## External Resources

**GRDB:**
- [GitHub](https://github.com/groue/GRDB.swift)
- [Documentation](https://swiftpackageindex.com/groue/GRDB.swift/documentation/grdb)
- [SQL

ite Documentation](https://www.sqlite.org/docs.html)

**SwiftUI Integration:**
- [GRDBQuery](https://github.com/groue/GRDBQuery) - SwiftUI reactive bindings

**Related Axiom Skills:**
- `database-migration` - Safe schema evolution
- `sqlitedata` - Type-safe @Table models with CloudKit
- `swiftdata` - Apple's native persistence

## Production Performance: Query Optimization Under Pressure

### Red Flags - When GRDB Queries Slow Down

If you see ANY of these symptoms:
- ❌ Complex JOIN query takes 10+ seconds
- ❌ ValueObservation runs on every single change (battery drain)
- ❌ Can't explain why migration ran twice on old version

**DO NOT:**
1. Blindly add indexes (don't know which columns help)
2. Move logic to Swift (premature escape from database)
3. Over-engineer migrations (distrust the system)

**DO:**
1. Profile with `database.trace`
2. Use `EXPLAIN QUERY PLAN` to understand execution
3. Trust GRDB's migration versioning system

### Profiling Complex Queries

**When query is slow (10+ seconds):**

```swift
var database = try DatabaseQueue(path: dbPath)

// Enable tracing to see SQL execution
database.trace { print($0) }

// Run the slow query
try database.read { db in
    let results = try Track.fetchAll(db)  // Watch output for execution time
}

// Use EXPLAIN QUERY PLAN to understand execution:
try database.read { db in
    let plan = try String(fetching: db, sql: "EXPLAIN QUERY PLAN SELECT ...")
    print(plan)
    // Look for SCAN (slow, full table) vs SEARCH (fast, indexed)
}
```

**Add indexes strategically:**

```swift
// Add index on frequently queried column
try database.write { db in
    try db.execute(sql: "CREATE INDEX idx_plays_track_id ON plays(track_id)")
}
```

**Time cost:**
- Profile: 10 min (enable trace, run query, read output)
- Understand: 5 min (interpret EXPLAIN QUERY PLAN)
- Fix: 5 min (add index)
- **Total: 20 minutes** (vs 30+ min blindly trying solutions)

### ValueObservation Performance

**When using reactive queries, know the costs:**

```swift
// Re-evaluates query on ANY write to database
ValueObservation.tracking { db in
    try Track.fetchAll(db)
}.start(in: database, onError: { }, onChange: { tracks in
    // Called for every change - CPU spike!
})
```

**Optimization patterns:**

```swift
// Coalesce rapid updates (recommended)
ValueObservation.tracking { db in
    try Track.fetchAll(db)
}.removeDuplicates()  // Skip duplicate results
 .debounce(for: 0.5, scheduler: DispatchQueue.main)  // Batch updates
 .start(in: database, ...)
```

**Decision framework:**
- Small datasets (<1000 records): Use plain `.tracking`
- Medium datasets (1-10k records): Add `.removeDuplicates()` + `.debounce()`
- Large datasets (10k+ records): Use explicit table dependencies or predicates

### Migration Versioning Guarantees

**Trust GRDB's DatabaseMigrator - it prevents re-running migrations:**

```swift
var migrator = DatabaseMigrator()

migrator.registerMigration("v1_initial") { db in
    try db.execute(sql: "CREATE TABLE tracks (...)")
}

migrator.registerMigration("v2_add_plays") { db in
    try db.execute(sql: "CREATE TABLE plays (...)")
}

// GRDB guarantees:
// - Each migration runs exactly ONCE
// - In order (v1, then v2)
// - Safe to call migrate() multiple times
try migrator.migrate(dbQueue)
```

**You don't need defensive SQL (IF NOT EXISTS):**
- GRDB tracks which migrations have run
- Running `migrate()` twice only executes new ones
- Over-engineering adds complexity without benefit

**Trust it.**

---

## Common Mistakes

### ❌ Not using transactions for batch writes
```swift
for track in 50000Tracks {
    try dbQueue.write { db in try track.insert(db) }  // 50k transactions!
}
```
**Fix:** Single transaction with batches

### ❌ Synchronous database access on main thread
```swift
let tracks = try dbQueue.read { db in try Track.fetchAll(db) }  // Blocks UI
```
**Fix:** Use async/await or dispatch to background queue

### ❌ Forgetting to add indexes
```swift
// Slow query without index
try Track.filter(Column("genre") == "Rock").fetchAll(db)
```
**Fix:** Create indexes on frequently queried columns

### ❌ N+1 queries
```swift
for track in tracks {
    let album = try Album.fetchOne(db, key: track.albumId)  // N queries!
}
```
**Fix:** Use JOIN or batch fetch

---

## Version History

- **1.1.0**: Added "Production Performance: Query Optimization Under Pressure" section from TDD testing of complex query performance scenarios. Includes profiling guidance (database.trace + EXPLAIN QUERY PLAN), ValueObservation optimization patterns with size-based decisions, migration versioning guarantees eliminating defensive SQL, and red flags for when to profile vs refactor. Prevents blind index creation and over-engineered migrations under performance pressure
- **1.0.0**: Initial skill covering raw SQL queries, joins, ValueObservation, migrations, and GRDB-specific patterns

---

**Created:** 2025-11-28
**Targets:** iOS 13+, Swift 5.7+
**Framework:** GRDB.swift 6.0+
