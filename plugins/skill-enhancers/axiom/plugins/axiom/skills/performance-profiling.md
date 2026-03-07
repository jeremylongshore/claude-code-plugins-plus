---
name: performance-profiling
description: Use when app feels slow, memory grows over time, battery drains fast, or you want to profile proactively - decision trees to choose the right Instruments tool, deep workflows for Time Profiler/Allocations/Core Data, and pressure scenarios for misinterpreting results
version: 1.2.0
last_updated: TDD-tested with deadline pressure, manager authority pressure, and Self Time vs Total Time misinterpretation scenarios, added 3 real-world examples
---

# Performance Profiling

## Overview

iOS app performance problems fall into distinct categories, each with a specific diagnosis tool. This skill helps you **choose the right tool**, **use it effectively**, and **interpret results correctly** under pressure.

**Core principle**: Measure before optimizing. Guessing about performance wastes more time than profiling.

**Requires**: Xcode 15+, iOS 14+
**Related skills**: `swiftui-performance` (SwiftUI-specific profiling with Instruments 26), `memory-debugging` (memory leak diagnosis)

## When to Use Performance Profiling

**Use this skill when:**
- ✅ App feels slow (UI lags, loads take 5+ seconds)
- ✅ Memory grows over time (Xcode shows increasing memory usage)
- ✅ Battery drains fast (device gets hot, battery depletes in hours)
- ✅ You want to profile proactively (before users complain)
- ✅ You're unsure which Instruments tool to use
- ✅ Profiling results are confusing or contradictory

**Use `memory-debugging` instead when:**
- Investigating specific memory leaks with retain cycles
- Using Instruments Allocations in detail mode

**Use `swiftui-performance` instead when:**
- Analyzing SwiftUI view body updates
- Using SwiftUI Instrument specifically

## Performance Decision Tree

Before opening Instruments, narrow down what you're actually investigating.

### Step 1: What's the Symptom?

```
App performance problem?
├─ App feels slow or lags (UI interactions stall, scrolling stutters)
│  └─ → Use Time Profiler (measure CPU usage)
├─ Memory grows over time (Xcode shows increasing memory)
│  └─ → Use Allocations (measure object creation)
├─ Data loading is slow (parsing, database queries, API calls)
│  └─ → Use Core Data instrument (if using Core Data)
│  └─ → Use Time Profiler (if it's computation)
└─ Battery drains fast (device gets hot, depletes in hours)
   └─ → Use Energy Impact (measure power consumption)
```

### Step 2: Can You Reproduce It?

**YES** – Use Instruments to measure it (profiling is most accurate)

**NO** – Use profiling proactively
- Enable Core Data SQL debugging to catch N+1 queries
- Profile app during normal use (scrolling, loading, navigation)
- Establish baseline metrics before changes

### Step 3: Which Instruments Tool?

**Time Profiler** – Slowness, UI lag, CPU spikes
**Allocations** – Memory growth, memory pressure, object counts
**Core Data** – Query performance, fetch times, fault fires
**Energy Impact** – Battery drain, sustained power draw
**Network Link Conditioner** – Connection-related slowness
**System Trace** – Thread blocking, main thread blocking, scheduling

---

## Time Profiler Deep Dive

Use Time Profiler when your app feels slow or laggy. It measures CPU time spent in each function.

### Workflow: Record and Analyze

**Step 1: Launch Instruments**
```bash
open -a Instruments
```

Select "Time Profiler" template.

**Step 2: Attach to Running App**
1. Start your app in simulator or device
2. In Instruments, select your app from the target dropdown
3. Click Record (red circle)
4. Interact with the slow part (scroll, tap buttons, load data)
5. Stop recording after 10-30 seconds of interaction

**Step 3: Read the Call Stack**

The top panel shows a timeline of CPU usage over time. Look for:
- **Tall spikes** – Brief CPU-intensive operations
- **Sustained high usage** – Continuous expensive work
- **Main thread blocking** – UI thread doing work (causes UI lag)

**Step 4: Drill Down to Hot Spots**

In the call tree, click "Heaviest Stack Trace" to see which functions use the most CPU:

```
Time Profiler Results

MyViewController.viewDidLoad() – 500ms (40% of total)
  ├─ DataParser.parse() – 350ms
  │  └─ JSONDecoder.decode() – 320ms
  └─ UITableView.reloadData() – 150ms
```

**Self Time** = Time spent IN that function (not in functions it calls)
**Total Time** = Time spent in that function + everything it calls

### Common Mistakes & Fixes

#### ❌ Mistake 1: Blaming the Wrong Function

```swift
// ❌ WRONG: Profile shows DataParser.parse() is 80% CPU
// Conclusion: "DataParser is slow, let me optimize it"

// ✅ RIGHT: Check what DataParser is calling
// If JSONDecoder.decode() is doing 99% of the work,
// optimize JSON decoding, not DataParser
```

**The issue**: A function with high Total Time might be calling slow code, not doing slow work itself.

**Fix**: Look at Self Time, not Total Time. Drill down to see what each function calls.

#### ❌ Mistake 2: Profiling the Wrong Code Path

```swift
// ❌ WRONG: Profile app in Simulator
// Simulator CPU is different than real device
// Results don't reflect actual device performance

// ✅ RIGHT: Profile on actual device
// Device settings: Developer Mode enabled, Xcode attached
```

**Fix**: Always profile on actual device for accurate CPU measurements.

#### ❌ Mistake 3: Not Isolating the Problem

```swift
// ❌ WRONG: Profile entire app startup
// Sees 2000ms startup time, many functions involved

// ✅ RIGHT: Profile just the slow part
// "App feels slow when scrolling" → profile only scrolling
// Separate concerns: startup slow vs interaction slow
```

**Fix**: Reproduce the specific slow operation, not the entire app.

### Pressure Scenario: "Profile Shows Function X is 80% CPU"

**The temptation**: "I must optimize function X!"

**The reality**: Function X might be:
- **Calling expensive code** (optimize the called function, not X)
- **Running on main thread** (move to background, it's already optimized)
- **Necessary work that looks slow** (baseline is acceptable, user won't notice)

**What to do instead**:

1. **Check Self Time, not Total Time**
   - Self Time 80%? Function is actually doing expensive work
   - Self Time 5%, Total Time 80%? Function is calling slow code

2. **Drill down one level**
   - What is this function calling?
   - Is the slow code in a library you control?

3. **Check the timeline**
   - Is this 80% sustained (steady slow) or spikes (occasional stalls)?
   - Sustained = optimization needed
   - Spikes = caching might help

4. **Ask: Will users notice?**
   - 500ms background work = user won't notice
   - 500ms on main thread = UI stall, user sees it
   - 50ms on main thread per frame = smooth UI (60fps)

**Time cost**: 5 min (read results) + 2 min (drill down) = **7 minutes to understand**

**Cost of guessing**: 2 hours optimizing wrong function + 1 hour realizing it didn't help + back to square one = **3+ hours wasted**

---

## Allocations Deep Dive

Use Allocations when memory grows over time or you suspect memory pressure issues.

### Workflow: Record and Analyze

**Step 1: Launch Instruments**
```bash
open -a Instruments
```

Select "Allocations" template.

**Step 2: Attach and Record**
1. Start your app
2. In Instruments, select your app
3. Click Record
4. Perform actions that use memory (load data, display images, navigate)
5. Stop recording after memory stabilizes or peaks

**Step 3: Find Memory Growth**

Look at the main chart:
- **Blue line** = Total allocations
- **Sharp climb** = Memory being allocated
- **Flat line** = Memory stable (good)
- **No decline after stopping actions** = Possible leak (or caching)

**Step 4: Identify Persistent Objects**

Under "Statistics":
- Sort by "Persistent" (objects still alive)
- Look for surprisingly large object counts:
  ```
  UIImage: 500 instances (300MB) – Should be <50 for normal app
  NSString: 50000 instances – Should be <1000
  CustomDataModel: 10000 instances – Should be <100
  ```

### Common Mistakes & Fixes

#### ❌ Mistake 1: Confusing "Memory Grew" with "Memory Leak"

```swift
// ❌ WRONG: Memory went from 100MB to 500MB
// Conclusion: "There's a leak, memory keeps growing!"

// ✅ RIGHT: Check what caused the growth
// Loaded 1000 images (normal)
// Cached API responses (normal)
// User has 5000 contacts (normal)
// Memory is being used correctly
```

**The issue**: Growing memory ≠ leak. Apps legitimately use more memory when loading data.

**Fix**: Check Allocations for object counts. If images/data count matches what you loaded, it's normal. If object count keeps growing without actions, that's a leak.

#### ❌ Mistake 2: Not Accounting for Caching

```swift
// ❌ WRONG: Allocations shows 1000 UIImages in memory
// Conclusion: "Memory leak, too many images!"

// ✅ RIGHT: Check if this is intentional caching
// ImageCache holds up to 1000 images by design
// When memory pressure happens, cache is cleared
// Normal behavior
```

**Fix**: Distinguish between intended caching and actual leaks. Leaks don't release under memory pressure.

#### ❌ Mistake 3: Profiling Too Short

```swift
// ❌ WRONG: Record for 5 seconds, see 200MB
// Conclusion: "App uses 200MB, optimize memory"

// ✅ RIGHT: Record for 2-3 minutes, see full lifecycle
// Load data: 200MB
// Navigate away: 180MB (20MB still cached)
// Navigate back: 190MB (cache reused)
// Real baseline: ~190MB at steady state
```

**Fix**: Profile long enough to see memory stabilize. Short recordings capture transient spikes.

### Pressure Scenario: "Memory is 500MB, That's a Leak!"

**The temptation**: "Delete caching, reduce object creation, optimize data structures"

**The reality**: Is 500MB actually large?
- iPhone 14 Pro has 6GB RAM
- Instagram uses 400-600MB on load
- Photos app uses 500MB+ when browsing large library
- 500MB might be completely normal

**What to do instead**:

1. **Establish baseline on real device**
   ```bash
   # On device, open Memory view in Xcode
   Xcode → Debug → Memory Debugger → Check "Real Memory" at app launch
   ```

2. **Check object counts, not total memory**
   - Allocations → Statistics → "Persistent"
   - Are images, views, or data objects 10x expected count?
   - If yes, investigate that object type
   - If no, memory is probably fine

3. **Test under memory pressure**
   - Xcode → Debug → Simulate Memory Warning
   - Does memory drop by 50%+? It's caching (normal)
   - Does memory stay high? Investigate persistent objects

4. **Profile real user journey**
   - Load data (like user does)
   - Navigate around (like user does)
   - Return to app (from background)
   - Check memory at each step

**Time cost**: 5 min (launch Allocations) + 3 min (record app usage) + 2 min (analyze) = **10 minutes**

**Cost of guessing**: Delete caching to "reduce memory" → app reloads data every screen → slower app → users complain → revert changes = **2+ hours wasted**

---

## Core Data Deep Dive

Use Core Data instrument when your app uses Core Data and data loading is slow.

### Workflow: Enable SQL Debugging and Profile

**Step 1: Enable Core Data SQL Logging**

Add to your launch arguments in Xcode:

```
Edit Scheme → Run → Arguments Passed On Launch
Add: -com.apple.CoreData.SQLDebug 1
```

Now SQLite queries print to console:

```
CoreData: sql: SELECT ... FROM tracks WHERE artist = ? (time: 0.015s)
CoreData: sql: SELECT ... FROM albums WHERE id = ? (time: 0.002s)
```

**Step 2: Identify N+1 Query Problem**

Watch the console during a typical user action (load list, scroll, filter):

```
❌ BAD: Loading 100 tracks, then querying album for each
SELECT * FROM tracks (time: 0.050s) → 100 tracks
SELECT * FROM albums WHERE id = 1 (time: 0.005s)
SELECT * FROM albums WHERE id = 2 (time: 0.005s)
SELECT * FROM albums WHERE id = 3 (time: 0.005s)
... 97 more queries
Total: 0.050s + (100 × 0.005s) = 0.550s

✅ GOOD: Fetch tracks WITH album relationship (eager loading)
SELECT tracks.*, albums.* FROM tracks
LEFT JOIN albums ON tracks.albumId = albums.id
(time: 0.050s)
Total: 0.050s
```

**Step 3: Profile with Core Data Instrument**

```bash
open -a Instruments
```

Select "Core Data" template.

Record while performing slow action:

```
Core Data Results

Fetch Requests: 102
Average Fetch Time: 12ms
Slow Fetch: "SELECT * FROM tracks" (180ms)

Fault Fires: 5000
  → Object accessed, requires fetch from database
  → Should use prefetching
```

### Common Mistakes & Fixes

#### ❌ Mistake 1: Not Using Relationships Correctly

```swift
// ❌ WRONG: Fetch tracks, then access album for each
let tracks = try context.fetch(Track.fetchRequest())
for track in tracks {
    print(track.album.title)  // Fires individual query for each
}
// Total: 1 + N queries

// ✅ RIGHT: Fetch with relationship prefetching
let request = Track.fetchRequest()
request.returnsObjectsAsFaults = false
request.relationshipKeyPathsForPrefetching = ["album"]
let tracks = try context.fetch(request)
for track in tracks {
    print(track.album.title)  // Already loaded
}
// Total: 1 query
```

**Fix**: Use `relationshipKeyPathsForPrefetching` to load related objects upfront.

#### ❌ Mistake 2: Not Using Batching

```swift
// ❌ WRONG: Fetch 50,000 records all at once
let request = Track.fetchRequest()
let allTracks = try context.fetch(request)  // Huge memory spike

// ✅ RIGHT: Batch fetch in chunks
let request = Track.fetchRequest()
request.fetchBatchSize = 500  // Fetch 500 at a time
let allTracks = try context.fetch(request)  // Memory efficient
```

**Fix**: Use `fetchBatchSize` for large datasets.

#### ❌ Mistake 3: Not Using Faulting to Reduce Memory

```swift
// ❌ WRONG: Keep all objects in memory
let request = Track.fetchRequest()
request.returnsObjectsAsFaults = false  // Keep all in memory
let allTracks = try context.fetch(request)  // 50,000 objects
// Memory spike if you don't use all of them

// ✅ RIGHT: Use faults (lazy loading)
let request = Track.fetchRequest()
// request.returnsObjectsAsFaults = true (default)
let allTracks = try context.fetch(request)  // Just references
// Only load objects you actually access
```

**Fix**: Leave `returnsObjectsAsFaults` as default (true) unless you need all objects upfront.

### Pressure Scenario: "Core Data Queries Are Slow, Redesign Schema!"

**The temptation**: "The schema is wrong, I need to restructure everything"

**The reality**: 99% of "slow Core Data" is due to:
- ❌ Missing indexes
- ❌ N+1 query problem
- ❌ Fetching too much data at once
- ❌ Not using batch size or prefetching

Redesigning the schema is the LAST thing to try.

**What to do instead**:

1. **Enable SQL debugging** (2 min)
   - Add `-com.apple.CoreData.SQLDebug 1` launch argument
   - Watch what queries execute

2. **Look for N+1 pattern** (3 min)
   - Fetching 100 objects, then individual queries for related data?
   - Add relationship prefetching

3. **Add indexes if needed** (5 min)
   - `@NSManaged var artist: String` with frequent filtering?
   - Add `@Index` in schema

4. **Test improvement** (2 min)
   - Re-run the same action
   - Compare query count and total time
   - If 10x faster, you're done
   - If still slow, go to step 5

5. **Only THEN consider schema changes** (30+ min)
   - But you probably won't get here

**Time cost**: 12 minutes to diagnose + fix = **12 minutes**

**Cost of schema redesign**: 8 hours design + 4 hours migration + 2 hours testing + 1 hour rollback = **15 hours total**

---

## Quick Reference: Other Tools

### Energy Impact (Battery Drain)

**When to use**: App drains battery fast, device gets hot

**Workflow**:
1. Launch Instruments → Energy Impact template
2. Run app normally for 5+ minutes
3. Look for red/orange sustained usage (bad)
4. Drill down to see which subsystems drain battery

**Key metrics**:
- **Sustained Power** – Ongoing energy use (should be minimal)
- **Peaks** – Brief high usage (acceptable)
- **CPU** – Process CPU time
- **GPU** – Graphics rendering
- **Network** – Cellular/WiFi radio
- **Location** – GPS usage

**Common issues**:
- Continuous location updates with 1m accuracy (should be 100m)
- Running timers that wake the device repeatedly
- Excessive network calls (batch requests instead)
- Animating views while not visible

### Network Link Conditioner (Connection Simulation)

**When to use**: App seems slow on 4G, want to test without traveling

**Setup**:
1. Download Additional Tools for Xcode
2. Install Network Link Conditioner
3. Open System Preferences → Network Link Conditioner
4. Choose profile (3G, LTE, WiFi Slow, etc.)
5. Enable and activate profile
6. Run app to test

**Key profiles**:
- **3G** – 1.6Mbps down, 768Kbps up, 150ms latency
- **LTE** – 10Mbps down, 5Mbps up, 20ms latency
- **WiFi Slow** – 10Mbps, 100ms latency
- **Custom** – Set your own parameters

**Note**: Also covered in ui-testing for network-dependent test scenarios.

### System Trace (Thread Blocking, Scheduling)

**When to use**: UI freezes or is janky, but Time Profiler shows low CPU

**Common cause**: Main thread blocked by background task waiting on lock

**Workflow**:
1. Launch Instruments → System Trace template
2. Record while reproducing issue
3. Look for main thread gaps (blocked, not running)
4. Drill down to see what's blocking it

**Key metrics**:
- **Main thread gaps** – Empty spaces = main thread idle/blocked
- **Core scheduling** – Which threads run when
- **Lock contention** – Threads waiting for locks

---

## Pressure Scenarios

### Scenario 1: "Profiling Shows Different Results Each Run"

**The problem**: You run Time Profiler 3 times, get 200ms, 150ms, 280ms. Which is correct?

**Red flags you might think**:
- "Results are unreliable, profiling isn't accurate"
- "Let me just average them"
- "This is too variable, I can't optimize"

**The reality**: Variance is NORMAL. Different runs hit different:
- Cache states (cold cache = slower)
- System load (other apps running)
- CPU frequency (boost/throttle)

**What to do instead**:

1. **Warm up the cache** (first run always slower)
   - Perform the action once (cold cache)
   - Perform again (warm cache) – use this measurement

2. **Control system load**
   - Close other apps
   - Don't touch device during profiling
   - Profile on device (not simulator)

3. **Look for the pattern**
   - Multiple runs: 150ms, 160ms, 155ms (consistent = good)
   - Multiple runs: 150ms, 280ms, 240ms (inconsistent = investigate)
   - Inconsistency = intermittent problem, find it

4. **Trust the slowest run** (worst case scenario)
   - If range is 150-280ms, assume 280ms is real
   - Optimize for worst case

**Time cost**: 10 min (run profiler 3x) + 2 min (interpret) = **12 minutes**

**Cost of ignoring variance**: Miss intermittent performance issue → users see occasional freezes → bad reviews

---

### Scenario 2: "Time Profiler and Allocations Show Different Problems"

**The problem**: Time Profiler shows JSON parsing is slow. Allocations show memory use is normal. Which to fix?

**The answer**: Both are real, prioritize differently.

```
Time Profiler: JSONDecoder.decode() = 500ms
Allocations: Memory = 250MB (normal for app size)

Result: App is slow AND memory is fine
Action: Optimize JSON decoding (not memory)
```

**Common conflicts**:

| Time Profiler | Allocations | Action |
|---|---|---|
| High CPU | Normal memory | Optimize computation (reduce CPU) |
| Low CPU | Memory growing | Find leak or reduce object creation |
| Both high | Both high | Profile which is user-visible first |

**What to do**:

1. **Prioritize by user impact**
   - Slowness (UI lag) = fix first
   - Memory (background issue) = fix second

2. **Check if they're related**
   - Does JSON parsing leak memory? (No → separate issues)
   - Does memory growth slow CPU? (Maybe → fix memory first)

3. **Fix in order of impact**
   - Slow JSON parsing: Affects every data load
   - Normal memory: No user impact
   - → Fix JSON parsing

**Time cost**: 5 min (analyze both results) = **5 minutes**

**Cost of fixing wrong problem**: Spend 4 hours optimizing memory that's fine → no improvement to user experience

---

### Scenario 3: "Profiling Under Deadline Pressure"

**The situation**: Manager says "We ship in 2 hours. Is performance acceptable?"

**Red flags you might think**:
- "Profiling takes too long, let me just ask users"
- "I don't have time to profile properly, ship as-is"
- "One quick run will tell me if it's fine"

**The reality**: Profiling takes 15-20 minutes total. That's 1% of your remaining time.

**What to do instead**:

1. **Profile the critical path** (3 min)
   - What users do most (load list, scroll, search)
   - Not the entire app, just the slow part

2. **Record one proper run** (5 min)
   - Cold cache first time
   - Warm cache second time
   - Use warm cache results

3. **Interpret quickly** (5 min)
   - Time Profiler: Any >100ms on main thread? (If no, fine)
   - Allocations: Any memory growing? (If no, fine)

4. **Ship with confidence** (2 min)
   - If results are acceptable, ship
   - If not, you have 90 minutes to fix or delay

**Time cost**: 15 min profiling + 5 min analysis = **20 minutes**

**Cost of not profiling**: Ship with unknown performance → Users hit slowness → Bad reviews → Emergency hotfix 2 weeks later

**Math**: 20 minutes of profiling now << 2+ weeks of post-launch support

---

## Quick Reference

### Common Operations

```swift
// Time Profiler: Launch Instruments
open -a Instruments

// Core Data: Enable SQL logging
// Edit Scheme → Run → Arguments Passed On Launch
-com.apple.CoreData.SQLDebug 1

// Allocations: Check persistent objects
Instruments → Allocations → Statistics → sort "Persistent"

// Memory warning: Simulate pressure
Xcode → Debug → Simulate Memory Warning

// Energy Impact: Profile battery drain
Instruments → Energy Impact template

// Network Link Conditioner: Simulate 3G
System Preferences → Network Link Conditioner → 3G profile
```

### Decision Tree Summary

```
Performance problem?
├─ App feels slow/laggy?
│  └─ → Time Profiler (measure CPU)
├─ Memory grows over time?
│  └─ → Allocations (find object growth)
├─ Data loading is slow?
│  └─ → Core Data instrument (if using Core Data)
│  └─ → Time Profiler (if computation slow)
└─ Battery drains fast?
   └─ → Energy Impact (measure power)
```

---

## Real-World Examples

### Example 1: Identifying N+1 Query Problem in Core Data

**Scenario**: Your app loads a list of albums with artist names. It's slow (5+ seconds for 100 albums). You suspect Core Data.

**Setup**: Enable SQL logging first
```bash
# Edit Scheme → Run → Arguments Passed On Launch
-com.apple.CoreData.SQLDebug 1
```

**What you see in console**:
```
CoreData: sql: SELECT ... FROM albums WHERE ... (time: 0.050s)
CoreData: sql: SELECT ... FROM artists WHERE id = 1 (time: 0.003s)
CoreData: sql: SELECT ... FROM artists WHERE id = 2 (time: 0.003s)
... 98 more individual queries
Total: 0.050s + (100 × 0.003s) = 0.350s
```

**Diagnosis using the skill**:
- Fetching 100 albums, then individual query for each album's artist = **N+1 query problem** (Core Data Deep Dive, lines 302-325)

**Fix**:
```swift
// ❌ WRONG: Each album access triggers separate artist query
let request = Album.fetchRequest()
let albums = try context.fetch(request)
for album in albums {
    print(album.artist.name)  // Extra query for each
}

// ✅ RIGHT: Prefetch the relationship
let request = Album.fetchRequest()
request.returnsObjectsAsFaults = false
request.relationshipKeyPathsForPrefetching = ["artist"]
let albums = try context.fetch(request)
for album in albums {
    print(album.artist.name)  // Already loaded
}
```

**Result**: 0.350s → 0.050s (7x faster)

---

### Example 2: Finding Where UI Lag Really Comes From

**Scenario**: Your app UI stalls for 1-2 seconds when loading a view. Your co-lead says "Add background threading everywhere." You want to measure first.

**Workflow using the skill** (Time Profiler Deep Dive, lines 82-118):

1. **Open Instruments**:
```bash
open -a Instruments
# Select "Time Profiler"
```

2. **Record the stall**:
```
App launches
Time Profiler records
View loads
Stall happens (observe the spike in Time Profiler)
Stop recording
```

3. **Examine results**:
```
Call Stack shows:

viewDidLoad() – 1500ms
  ├─ loadJSON() – 1200ms (Self Time: 50ms)
  │   └─ loadImages() – 1150ms (Self Time: 1150ms) ← HERE'S THE CULPRIT
  ├─ parseData() – 200ms
  └─ layoutUI() – 100ms
```

4. **Apply the skill** (lines 173-175):
```
loadJSON() has Self Time: 50ms, Total Time: 1200ms
→ loadJSON() isn't slow, something it CALLS is slow
→ loadImages() has Self Time: 1150ms
→ loadImages() is the actual bottleneck
```

5. **Fix the right thing**:
```swift
// ❌ WRONG: Thread everything
DispatchQueue.global().async { loadJSON() }

// ✅ RIGHT: Thread only the slow part
func loadJSON() {
    let data = parseJSON()  // 50ms, fine on main

    // Move ONLY the slow part to background
    DispatchQueue.global().async {
        let images = loadImages()  // 1150ms, now background
        DispatchQueue.main.async {
            updateUI(with: images)
        }
    }
}
```

**Result**: 1500ms → 350ms (4x faster, main thread unblocked)

**Why this matters**: You fixed the ACTUAL bottleneck (1150ms), not guessing blindly about threading.

---

### Example 3: Memory Growing vs Memory Leak

**Scenario**: Allocations shows memory growing from 150MB to 600MB over 30 minutes of app use. Your manager says "Memory leak!" You need to know if it's real.

**Workflow using the skill** (Allocations Deep Dive, lines 199-277):

1. **Launch Allocations in Instruments**

2. **Record normal app usage for 3 minutes**:
```
User loads data → memory grows to 400MB
User navigates around → memory stays at 400MB
User goes to Settings → memory at 400MB
User comes back → memory at 400MB
```

3. **Check Allocations Statistics**:
```
Persistent Objects:
- UIImage: 1200 instances (300MB) ← Large count
- NSString: 5000 instances (4MB)
- CustomDataModel: 800 instances (15MB)
```

4. **Ask the skill questions** (lines 220-240):
- Are 1200 images legitimately loaded? (User loaded photo library with 1000 photos) → YES
- Does memory drop if you trigger memory warning? (Simulate with Xcode) → YES, drops to 180MB
- Is this caching working as designed? → YES

**Diagnosis**: NOT a leak. This is **normal caching** (lines 235-248)
```
Memory growing = apps using data users asked for
Memory dropping under pressure = cache working correctly
Memory staying high indefinitely = possible leak
```

5. **Conclusion**:
```swift
// ✅ This is working correctly
let imageCache = NSCache<NSString, UIImage>()
// Holds up to 1200 images by design
// Clears when system memory pressure happens
// No leak
```

**Result**: No action needed. The "leak" is actually the cache doing its job.

---

## External Resources

**Apple Documentation:**
- [Instruments User Guide](https://help.apple.com/instruments/)
- [Core Data Performance Tuning](https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/CoreDataPerformance/)
- [Energy Impact Instrument](https://developer.apple.com/library/archive/technotes/tn2224/)

**Related Axiom Skills:**
- `memory-debugging` – Deep memory leak diagnosis
- `swiftui-performance` – SwiftUI view profiling with Instruments 26
- `swift-concurrency` – MainActor and thread safety patterns

---

## Version History

- **1.0.0**: Initial skill covering performance decision tree, Time Profiler workflow (CPU, hot spots, call stacks), Allocations workflow (memory growth, object counts, leak diagnosis), Core Data instrument (N+1 queries, prefetching, batch size), quick reference for Energy Impact/Network/System Trace, and pressure scenarios (misinterpreting results, conflicting tool signals, deadline profiling, variance in results)
- **1.1.0**: Added manager authority pressure resistance, Self Time vs Total Time clarity under App Store deadline pressure, professional scripts for pushing back on premature optimization suggestions, verified bulletproof under 4-hour App Store launch deadline with confusing profiling results
- **1.2.0**: Added 3 real-world examples (N+1 query diagnosis with SQL logging, Time Profiler workflow for UI lag, Allocations memory vs leak diagnosis) demonstrating Core Data optimization, measuring before threading, and distinguishing caching from leaks with complete workflows

---

**Created:** 2025-11-30
**Targets:** iOS 14+, Swift 5.5+
**Framework:** Instruments, Core Data
