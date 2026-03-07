# Getting Started

Welcome to Axiom, battle-tested Claude Code skills for modern xOS (iOS, iPadOS, watchOS, tvOS) development.

## What is Axiom?

Axiom provides 11 production-ready skills covering:

### 🎨 UI & Design Skills
- **Liquid Glass** – Apple's new material design system (iOS 26+) with expert review checklist
- **SwiftUI Performance** – New SwiftUI Instrument in Instruments 26, Cause & Effect Graph
- **UI Testing** – Recording UI Automation (Xcode 26) with video replay and review

### 🐛 Debugging & Performance
- **Xcode Debugging** – Environment-first diagnostics for BUILD FAILED, simulator hangs, zombie processes
- **Memory Debugging** – Systematic leak diagnosis with 5 patterns covering 90% of real-world issues
- **Build Troubleshooting** – Dependency conflicts, CocoaPods/SPM resolution failures

### ⚡ Concurrency & Async
- **Swift Concurrency** – Swift 6 strict concurrency patterns, async/await, MainActor, Sendable

### 💾 Data & Persistence
- **Database Migration** – Safe schema evolution for SQLite/GRDB/SwiftData
- **SQLiteData** – Point-Free's SQLiteData patterns, batch imports, CloudKit sync
- **GRDB** – Raw SQL queries, ValueObservation, DatabaseMigrator
- **SwiftData** – iOS 26+ features, @Model, @Query, Swift 6 concurrency

## Prerequisites

- macOS (Darwin 25.2.0 or later recommended)
- [Claude Code](https://claude.ai/download) installed
- Xcode 26+ (for latest features)
- iOS 26+ SDK (for latest platform features)

## Quick Start

### 1. Add the Marketplace

In Claude Code, run:

```
/plugin marketplace add https://charleswiltgen.github.io/Axiom/
```

### 2. Install the Plugin

From the marketplace, search for "axiom" and install it, or use:

```bash
claude plugin install axiom@axiom-marketplace
```

### 3. Verify Installation

```bash
claude plugin list
# You should see: axiom@0.1.3
```

### 4. Use Skills

Skills are automatically suggested by Claude Code based on context, or invoke them directly:

```bash
# UI & Design
/skill axiom:liquid-glass
/skill axiom:swiftui-performance
/skill axiom:ui-testing

# Debugging & Performance
/skill axiom:xcode-debugging
/skill axiom:memory-debugging
/skill axiom:build-troubleshooting

# Concurrency & Async
/skill axiom:swift-concurrency

# Data & Persistence
/skill axiom:database-migration
/skill axiom:sqlitedata
/skill axiom:grdb
/skill axiom:swiftdata
```

## Common Workflows

### Implementing Liquid Glass

When adding Liquid Glass to your app:

1. Use `axiom:liquid-glass` skill
2. Review Regular vs Clear variant decision criteria
3. Apply `.glassEffect()` to navigation layer elements
4. Run the Expert Review Checklist (7 sections) to validate implementation
5. Test across light/dark modes and accessibility settings

### Optimizing SwiftUI Performance

When app feels sluggish or animations stutter:

1. Use `axiom:swiftui-performance` skill
2. Profile with Instruments 26 using SwiftUI template
3. Check Long View Body Updates lane for expensive operations
4. Use Cause & Effect Graph to identify unnecessary updates
5. Apply formatter caching or granular dependencies patterns

### Recording UI Tests

When writing UI tests for new features:

1. Use `axiom:ui-testing` skill
2. Record interactions with Recording UI Automation (Xcode 26)
3. Replay across devices, languages, and configurations
4. Review video recordings to debug failures
5. Apply condition-based waiting for reliable tests

### Debugging Xcode Build Failures

When you encounter BUILD FAILED or mysterious Xcode issues:

1. Use `axiom:xcode-debugging` skill
2. Run mandatory environment checks (Derived Data, processes, simulators)
3. Follow the decision tree for your specific error
4. Apply quick fixes before debugging code

### Fixing Swift Concurrency Errors

When you see actor isolation or Sendable errors:

1. Use `axiom:swift-concurrency` skill
2. Match your error to the decision tree
3. Copy the relevant pattern template (delegate capture, weak self, etc.)
4. Run the code review checklist

### Creating Safe Database Migrations

When adding database columns or changing schema:

1. Use `axiom:database-migration` skill
2. Follow safe patterns (additive, idempotent, transactional)
3. Write tests for both fresh install and migration paths
4. Test manually on device before shipping

## What's Next?

- [View all skills →](/skills/)
- [Contributing guide →](https://github.com/CharlesWiltgen/Axiom/blob/main/CONTRIBUTING.md)
