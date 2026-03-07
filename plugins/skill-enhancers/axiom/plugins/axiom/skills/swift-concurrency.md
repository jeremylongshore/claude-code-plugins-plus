---
name: swift-concurrency
description: Swift 6 strict concurrency patterns, fixes, and best practices - Quick reference for actor isolation, Sendable, async/await, and data race prevention
---

# Swift 6 Concurrency Guide

**Purpose**: Quick reference for Swift 6 concurrency patterns
**Swift Version**: Swift 6.0+ with strict concurrency
**iOS Version**: iOS 17+ recommended
**Context**: Helps navigate actor isolation, Sendable, and data race prevention

## When to Use This Skill

✅ **Use this skill when**:
- Debugging Swift 6 concurrency errors (actor isolation, data races, Sendable warnings)
- Implementing `@MainActor` classes or async functions
- Converting delegate callbacks to async-safe patterns
- Deciding between `@MainActor`, `nonisolated`, or actor isolation
- Resolving "Sending 'self' risks causing data races" errors
- Making types conform to `Sendable`
- Offloading CPU-intensive work to background threads

❌ **Do NOT use this skill for**:
- General Swift syntax (use Swift documentation)
- SwiftUI-specific patterns (different context)
- API-specific patterns (use API documentation)

## Example Prompts

These are real questions developers ask that this skill is designed to answer:

**1. "I'm getting 'Main actor-isolated property accessed from nonisolated context' errors in my delegate methods. How do I fix this?"**
→ The skill covers the critical Pattern 2 (Value Capture Before Task) that shows when to capture delegate parameters before the Task context hop

**2. "My code is throwing 'Type does not conform to Sendable' warnings when I try to pass data between background work and MainActor. What does this mean?"**
→ The skill explains Sendable conformance requirements and shows patterns for enums, structs, and classes that cross actor boundaries

**3. "I have a task that's stored as a property and it's causing memory leaks. How do I write it correctly with weak self?"**
→ The skill demonstrates Pattern 3 (Weak Self in Tasks) showing the difference between stored and short-lived tasks

**4. "I'm new to Swift 6 concurrency. What are the critical patterns I need to know to write safe concurrent code?"**
→ The skill provides 6 copy-paste-ready patterns covering delegates, Sendable types, tasks, snapshots, MainActor, and background work

**5. "How do I know when to use @MainActor vs nonisolated vs @concurrent? The rules aren't clear."**
→ The skill clarifies actor isolation rules and provides a decision tree for each scenario with real-world examples

---

## Quick Decision Tree

```
Error: "Main actor-isolated property accessed from nonisolated context"
├─ In delegate method?
│  └─ Use Pattern 2: Value Capture Before Task
├─ In async function?
│  └─ Add @MainActor or call from Task { @MainActor in }
└─ In property getter?
   └─ Use Pattern 4: Atomic Snapshots

Error: "Type does not conform to Sendable"
├─ Is it an enum with no associated values?
│  └─ Use Pattern 1: Add `: Sendable`
├─ Is it a struct with all Sendable properties?
│  └─ Implicit Sendable (do nothing) or explicit `: Sendable`
└─ Is it a class?
   └─ Make @MainActor or add manual Sendable conformance

Error: "Static var requires concurrency annotation"
└─ Use `nonisolated static let` (if immutable)

Warning: Task may cause memory leak
└─ Use Pattern 3: `Task { [weak self] in }`
```

## Common Patterns (Copy-Paste Templates)

### Pattern 1: Sendable Enum/Struct

**When**: Type crosses actor boundaries (passed between @MainActor and background)

```swift
// ✅ Enum (no associated values)
private enum PlaybackState: Sendable {
    case stopped
    case playing
    case paused
}

// ✅ Struct (all properties Sendable)
struct Track: Sendable {
    let id: String
    let title: String
    let artist: String?
}

// ✅ Enum with Sendable associated values
enum Result: Sendable {
    case success(data: Data)
    case failure(error: Error)  // Error is Sendable
}
```

**Why**: Swift 6 requires types crossing actor boundaries to be `Sendable` to prevent data races.

---

### Pattern 2: Delegate Value Capture (CRITICAL)

**When**: `nonisolated` delegate method needs to update @MainActor state

**Why `@MainActor` on delegate doesn't work**: Delegate protocols define methods as nonisolated by the framework. You can't change their isolation.

**❌ WRONG (Accessing delegate parameters directly)**:
```swift
nonisolated func delegate(_ param: SomeType) {
    Task { @MainActor in
        // ❌ Accessing param.value crosses actor boundary unsafely
        self.property = param.value
        print("Status: \(param.status)")
    }
}
```

**✅ CORRECT (Capture Before Task)**:
```swift
nonisolated func delegate(_ param: SomeType) {
    // ✅ Step 1: Capture delegate parameter values BEFORE Task
    let value = param.value
    let status = param.status

    // ✅ Step 2: Task hop to MainActor
    Task { @MainActor in
        // ✅ Step 3: Now safe to access self (we're on MainActor)
        // ✅ Use captured values from delegate parameters
        self.property = value
        print("Status: \(status)")
    }
}
```

**Why**: Delegate methods are `nonisolated` (called from library's threads). Delegate parameters must be captured BEFORE the Task creates MainActor context. Once inside `Task { @MainActor in }`, accessing `self` is safe because you're on MainActor.

**Rule**: Capture all delegate parameter values before Task. Accessing `self` inside the Task is safe and expected.

**Real-world example** (chat message delegate):
```swift
// Delegate method called from network layer's thread
nonisolated func didReceiveMessage(_ message: Message, fromUser user: User) {
    // ✅ Capture delegate parameters
    let messageText = message.content
    let senderName = user.displayName

    Task { @MainActor in
        // ✅ Safe: accessing self properties (we're on MainActor now)
        self.messages.append(message)
        self.unreadCount += 1

        // ✅ Use captured delegate parameters
        self.showNotification(text: messageText, from: senderName)
    }
}
```

**Key distinction**:
- Delegate parameters (`message`, `user`) → Must capture before Task
- Self properties (`self.messages`) → Safe to access inside `Task { @MainActor in }`

---

### Pattern 3: Weak Self in Tasks

**When**: Task is stored as a property OR runs for a long time

**❌ WRONG (Memory Leak)**:
```swift
class MusicPlayer {
    private var progressTask: Task<Void, Never>?

    func startMonitoring() {
        progressTask = Task {  // ❌ Strong capture of self
            while !Task.isCancelled {
                await self.updateProgress()
            }
        }
    }
}
// MusicPlayer → progressTask → closure → self (CYCLE)
```

**✅ CORRECT (No Leak)**:
```swift
class MusicPlayer {
    private var progressTask: Task<Void, Never>?

    func startMonitoring() {
        progressTask = Task { [weak self] in  // ✅ Weak capture
            guard let self = self else { return }

            while !Task.isCancelled {
                await self.updateProgress()
            }
        }
    }

    deinit {
        progressTask?.cancel()  // Clean up
    }
}
```

**Why**: Task strongly captures `self`, creating retain cycle if stored as property. Use `[weak self]` to break cycle.

**Note**: Short-lived Tasks (not stored) can use strong captures:
```swift
// ✅ OK: Task executes immediately and completes
func quickUpdate() {
    Task {  // Strong capture OK (not stored)
        await self.refresh()
    }
}
```

---

### Pattern 4: Atomic Snapshots

**When**: Reading multiple properties from an object that could change mid-access

**❌ WRONG (Torn Reads)**:
```swift
var currentTime: TimeInterval {
    get async {
        // ❌ If state changes between reads, torn read!
        return player?.currentTime ?? 0
    }
}
```

**✅ CORRECT (Atomic Snapshot)**:
```swift
var currentTime: TimeInterval {
    get async {
        // ✅ Cache reference first for atomic snapshot
        guard let player = player else { return 0 }
        return player.currentTime
    }
}
```

**Why**: If state changes between reads, you could read inconsistent data. Caching ensures all properties come from the same instance.

---

### Pattern 5: MainActor for UI Code

**When**: Code touches UI (views, view controllers, observable objects)

```swift
// ✅ View models should be @MainActor
@MainActor
class PlayerViewModel: ObservableObject {
    @Published var currentTrack: Track?
    @Published var isPlaying: Bool = false

    func play(_ track: Track) async {
        // Already on MainActor, can update @Published properties
        self.currentTrack = track
        self.isPlaying = true
    }
}

// ✅ SwiftUI views are implicitly @MainActor
struct PlayerView: View {
    @StateObject var viewModel = PlayerViewModel()

    var body: some View {
        // UI code automatically on MainActor
    }
}
```

---

### Pattern 6: Background Work with @concurrent (Swift 6.2+)

**When**: CPU-intensive operations that should always run on background thread

```swift
// ✅ Force background execution
@concurrent
func extractMetadata(from url: URL) async -> Metadata {
    // Always runs on background thread pool
    // Good for: file I/O, image processing, parsing
    let data = try? Data(contentsOf: url)
    return parseMetadata(data)
}

// Usage (automatically offloads to background)
let metadata = await extractMetadata(from: fileURL)
```

**Note**: `@concurrent` requires Swift 6.2 (Xcode 16.2+, iOS 18.2+)

---

## Anti-Patterns (DO NOT DO THIS)

### Anti-Pattern 1: Accessing Self Before Task Hop
```swift
// ❌ NEVER DO THIS
nonisolated func delegate(_ param: Type) {
    Task { @MainActor in
        self.property = param.value  // ❌ WRONG: accessing self before hop
    }
}
```

### Anti-Pattern 2: Strong Self in Stored Tasks
```swift
// ❌ NEVER DO THIS
progressTask = Task {  // ❌ Memory leak!
    while true {
        await self.update()
    }
}
```

### Anti-Pattern 3: Using nonisolated(unsafe) Without Justification
```swift
// ❌ DON'T DO THIS
nonisolated(unsafe) var currentTrack: Track?  // ❌ Mutable! Data race possible!

// ✅ DO THIS
@MainActor var currentTrack: Track?  // ✅ Actor-isolated, safe
```

**Rule**: Only use `nonisolated(unsafe)` for:
- Static immutable values you're certain are thread-safe
- Legacy global state that can't be refactored (document why)

---

## Common Swift 6 Errors & Fixes

### Error: "Main actor-isolated property ... accessed from nonisolated context"

**Fix**: Use Pattern 2 (Value Capture Before Task)

---

### Error: "Type ... does not conform to the Sendable protocol"

**Fix**: Add `Sendable` conformance to the type:
```swift
enum State: Sendable {  // ✅ Add Sendable
    case idle
    case active
}
```

---

### Error: "Static property ... must be Sendable"

**Fix**: Use `nonisolated static let` (for immutable data):
```swift
nonisolated static let defaultValue = "Hello"
```

---

### Warning: "Capture of 'self' with non-Sendable type in a @Sendable closure"

**Fix**: Use `[weak self]` in Task:
```swift
Task { [weak self] in  // ✅ Weak capture
    guard let self = self else { return }
    // ...
}
```

---

## Build Settings for Swift 6

**Enable strict concurrency checking:**

```
Build Settings → Swift Compiler - Concurrency
→ "Strict Concurrency Checking" = Complete
```

**What it does**:
- Compile-time data race prevention
- Enforces actor isolation
- Requires explicit Sendable conformance

---

## Code Review Checklist

Use this when reviewing new code or fixing concurrency warnings:

### 1. Delegate Methods
- [ ] All delegate methods marked `nonisolated`
- [ ] Delegate parameter values captured **before** Task creation
- [ ] Accessing `self` inside `Task { @MainActor in }` is safe and expected
- [ ] Captured values used for delegate parameters only

### 2. Types Crossing Actors
- [ ] Enums have `: Sendable` if crossing actors
- [ ] Structs have all Sendable properties
- [ ] No classes crossing actors (use @MainActor or actors)

### 3. Tasks
- [ ] Stored Tasks use `[weak self]`
- [ ] Short-lived Tasks can use strong self
- [ ] Task inherits actor context from creation point

### 4. Property Access
- [ ] Multi-property access uses cached reference
- [ ] No torn reads from changing state
- [ ] Optional unwrapping with `?? fallback`

### 5. Actor Isolation
- [ ] UI-touching code is @MainActor
- [ ] Background work is nonisolated or uses @concurrent
- [ ] No blocking operations on MainActor

---

## Real-World Impact

**Before:** Random crashes, data races, "works on my machine" bugs
**After:** Compile-time guarantees, no data races, predictable behavior

**Key insight:** Swift 6's strict concurrency catches bugs at compile time instead of runtime crashes.

---

## Reference Documentation

**Apple Resources**:
- [Swift Concurrency Documentation](https://docs.swift.org/swift-book/LanguageGuide/Concurrency.html)
- [Adopting strict concurrency in Swift 6](https://developer.apple.com/documentation/swift/adoptingswift6)
- [Sendable Protocol](https://developer.apple.com/documentation/swift/sendable)
- [WWDC 2022: Eliminate data races using Swift Concurrency](https://developer.apple.com/videos/play/wwdc2022/110351/)
- [WWDC 2021: Protect mutable state with Swift actors](https://developer.apple.com/videos/play/wwdc2021/10133/)

---

**Last Updated**: 2025-11-28
**Status**: Production-ready patterns for Swift 6 strict concurrency
