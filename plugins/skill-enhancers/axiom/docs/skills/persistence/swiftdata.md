# SwiftData

SwiftData with iOS 26+ features, @Model definitions, @Query patterns, Swift 6 concurrency with @MainActor.

**When to use**: Working with SwiftData @Model definitions, @Query in SwiftUI, @Relationship macros, ModelContext patterns, CloudKit integration, iOS 26+ features, Swift 6 concurrency

## Key Features

- @Model definitions
- @Query patterns in SwiftUI
- @Relationship macros
- ModelContext patterns
- CloudKit integration
- iOS 26+ features
- Swift 6 concurrency with @MainActor

## Example Prompts

These are real questions developers ask that this skill answers:

- **"I have a notes app with folders. How do I filter notes by folder and sort by last modified?"**
  → Shows how to use @Query with predicates, sorting, and automatic view updates

- **"When a user deletes a task list, all tasks should auto-delete too."**
  → Explains @Relationship with deleteRule: .cascade and inverse relationships

- **"My chat app syncs to other devices via CloudKit. Sometimes messages conflict."**
  → Covers CloudKit integration, conflict resolution strategies, and sync patterns

- **"I have relationships between User → Messages → Attachments. How do I prevent orphaned data?"**
  → Shows cascading deletes, inverse relationships, and safe deletion patterns

- **"I need to query 50,000 messages but only display 20 at a time."**
  → Covers performance patterns, batch fetching, and limiting queries efficiently
