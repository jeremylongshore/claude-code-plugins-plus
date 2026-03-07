# Swift Concurrency

Swift 6 strict concurrency patterns – async/await, MainActor, Sendable, actor isolation, and data race prevention.

**When to use**: Debugging Swift 6 concurrency errors (actor isolation, data races, Sendable warnings), implementing @MainActor classes, converting delegate callbacks to async-safe patterns

## Key Features

- Quick decision tree for concurrency errors
- Copy-paste templates for common patterns
  - Delegate capture (weak self)
  - Sendable conformance
  - MainActor isolation
  - Background task patterns
- Anti-patterns to avoid
- Code review checklist

**Philosophy**: Swift 6's strict concurrency catches bugs at compile time instead of runtime crashes.

**TDD Tested**: Critical checklist contradiction found and fixed during pressure testing

## Example Prompts

These are real questions developers ask that this skill answers:

- **"I'm getting 'Main actor-isolated property accessed from nonisolated context' errors everywhere."**
  → Covers Pattern 2 (Value Capture Before Task) that solves most delegate method concurrency errors

- **"My code is throwing 'Type does not conform to Sendable' warnings when I try to pass data between background work and MainActor."**
  → Explains Sendable conformance and shows patterns for enums, structs, and classes crossing actor boundaries

- **"I have a task stored as a property and it's causing memory leaks. How do I write it correctly with weak self?"**
  → Demonstrates Pattern 3 with the difference between stored and short-lived tasks

- **"I'm new to Swift 6 concurrency. What are the critical patterns I need to know?"**
  → Provides 6 copy-paste-ready patterns covering delegates, Sendable, tasks, snapshots, MainActor, and background work

- **"How do I know when to use @MainActor vs nonisolated vs @concurrent?"**
  → Clarifies isolation rules with decision tree for each scenario and real-world examples
