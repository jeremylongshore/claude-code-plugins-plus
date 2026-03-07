# Performance Profiling

Instruments decision trees and profiling workflows for CPU, memory, and battery optimization with 3 real-world examples.

**When to use**: App feels slow, memory grows over time, battery drains fast, want to profile proactively

## Key Features

- **Performance Decision Tree** – Choose the right tool (Time Profiler, Allocations, Core Data, Energy Impact)
- **Time Profiler Deep Dive** – CPU analysis, hot spots, Self Time vs Total Time distinction, 4x improvement example
- **Allocations Deep Dive** – Memory growth diagnosis, object counts, leak vs caching, distinguishing real issues
- **Core Data Deep Dive** – N+1 query detection with SQL logging, prefetching, batch optimization, 7x improvement example
- **Real-World Examples** (3 complete workflows):
  - Identifying N+1 query problem in Core Data (SQL logging, diagnosis, prefetching fix)
  - Finding where UI lag really comes from (Time Profiler workflow, Self Time vs Total Time)
  - Memory growing vs memory leak (Allocations workflow, distinguishing caching from leaks)
- **Pressure Scenarios** – App Store deadline pressure, manager authority pressure, misinterpretation prevention

**Requirements**: Xcode 15+, iOS 14+

## Example Prompts

These are real questions developers ask that this skill answers:

- **"Scrolling is slow and I need to know if it's Core Data or SwiftUI."**
  → Shows how to use Time Profiler and Core Data instruments to pinpoint the bottleneck

- **"My app feels slow but I don't know what to optimize first."**
  → Provides decision tree for choosing the right profiling tool and interpreting results

- **"I profiled with Time Profiler but Self Time and Total Time are confusing."**
  → Explains the distinction and shows how to identify real hot spots vs call stacks

- **"I have a deadline and my app feels slow. What should I optimize?"**
  → Provides systematic profiling under pressure with professional guidance for trade-offs

- **"Memory keeps growing. Is it a leak or normal? How do I tell?"**
  → Covers Allocations instrument decision tree to distinguish caching from actual leaks

## Decision Tree

```
App performance problem?
├─ App feels slow/lags?          → Time Profiler (measure CPU)
├─ Memory grows over time?        → Allocations (find object growth)
├─ Data loading is slow?          → Core Data instrument (if using Core Data)
│                                 → Time Profiler (if computation slow)
└─ Battery drains fast?           → Energy Impact (measure power)
```

## Core Profiling Tools

### Time Profiler
Measures CPU time spent in each function. Identifies hot spots and main thread blocking.

**When to use**: App stalls, UI lag, CPU usage high

**Key metrics**:
- **Self Time** = Time spent IN that function
- **Total Time** = Time in that function + everything it calls
- If Self Time is low but Total Time is high → something it calls is slow

### Allocations
Measures memory growth and object creation. Identifies memory leaks vs normal caching.

**When to use**: Memory grows, want to check for leaks, memory pressure issues

**Key metrics**:
- Growing count + growing memory = possible leak
- Memory drops under pressure = normal caching
- Memory stays high indefinitely = leak

### Core Data Instrument
Analyzes SQLite queries and Core Data performance.

**When to use**: Using Core Data, data loading is slow, queries look expensive

**Setup**:
```bash
# Edit Scheme → Run → Arguments Passed On Launch
-com.apple.CoreData.SQLDebug 1
```

**Common issue**: N+1 queries (fetching parent, then individual query per child)

```swift
// ❌ WRONG: Individual query for each relationship
for item in items {
    print(item.relationship.title)  // Extra query each time
}

// ✅ RIGHT: Prefetch the relationship
let request = Item.fetchRequest()
request.relationshipKeyPathsForPrefetching = ["relationship"]
let items = try context.fetch(request)
for item in items {
    print(item.relationship.title)  // Already loaded
}
```

### Energy Impact
Measures power consumption by CPU, GPU, network, location, and other subsystems.

**When to use**: Battery drains fast, device gets hot

## Core Principle

**Measure before optimizing.** Guessing about performance wastes more time than profiling.

The cost of misdiagnosis:
- Blindly threading code: 2+ hours guessing wrong functions
- Wrong optimization: 4+ hours fixing something that wasn't the bottleneck
- Systematic diagnosis: 15-20 minutes to find the real issue

## Real-World Workflow

1. **Identify the symptom** (slow, memory, battery)
2. **Choose the right tool** from decision tree
3. **Record a profile** (cold run first, then warm)
4. **Analyze results** (read call stacks, check metrics)
5. **Identify root cause** (which function/query/object is actually the problem)
6. **Fix the right thing** (not a guess, but evidence-based)
7. **Verify improvement** (re-profile to confirm the fix worked)

## Related Skills

- **swiftui-performance** – SwiftUI Instrument for view profiling
- **memory-debugging** – Deep memory leak diagnosis with Instruments
- **xcode-debugging** – Xcode environment issues

## Quick Start

1. What's the symptom? (slow/memory/battery)
2. Which tool? (Time Profiler/Allocations/Core Data/Energy Impact)
3. Record a profile while reproducing the issue
4. Analyze the call stack or statistics
5. Identify the root cause
6. Fix based on evidence, not guesses

**Key principle**: Self Time vs Total Time distinction prevents optimization rabbit holes.

---

**Learn more**: See the full skill at `/skills/debugging/performance-profiling` in Claude Code
