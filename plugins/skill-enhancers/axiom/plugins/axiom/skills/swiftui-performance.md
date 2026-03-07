---
name: swiftui-performance
description: Use when analyzing SwiftUI performance issues, identifying long view body updates, reducing unnecessary view updates, or optimizing SwiftUI rendering - covers the new SwiftUI Instrument in Instruments 26, performance patterns from WWDC 2025, and production crisis decision-making under deadline pressure
version: 1.1.0
last_updated: TDD-tested with production performance crisis scenarios
apple_platforms: iOS 26+, iPadOS 26+, macOS Tahoe+, visionOS 3+
xcode_version: Xcode 26+
---

# SwiftUI Performance Optimization

## When to Use This Skill

Use when:
- App feels less responsive (hitches, hangs, delayed scrolling)
- Animations pause or jump during execution
- Scrolling performance is poor
- Profiling reveals SwiftUI is the bottleneck
- View bodies are taking too long to run
- Views are updating more frequently than necessary
- Need to understand cause-and-effect of SwiftUI updates

## Example Prompts

These are real questions developers ask that this skill is designed to answer:

**1. "My app has janky scrolling and animations are stuttering. How do I figure out if SwiftUI is the cause?"**
→ The skill shows how to use the new SwiftUI Instrument in Instruments 26 to identify if SwiftUI is the bottleneck vs other layers

**2. "I'm using the new SwiftUI Instrument and I see orange/red bars showing long updates. How do I know what's causing them?"**
→ The skill covers the Cause & Effect Graph patterns that show data flow through your app and which state changes trigger expensive updates

**3. "Some views are updating way too often even though their data hasn't changed. How do I find which views are the problem?"**
→ The skill demonstrates unnecessary update detection and Identity troubleshooting with the visual timeline

**4. "I have large data structures and complex view hierarchies. How do I optimize them for SwiftUI performance?"**
→ The skill covers performance patterns: breaking down view hierarchies, minimizing body complexity, and using the @Sendable optimization checklist

**5. "We have a performance deadline and I need to understand what's slow in SwiftUI. What are the critical metrics?"**
→ The skill provides the decision tree for prioritizing optimizations and understands pressure scenarios with professional guidance for trade-offs

---

## Overview

**Core Principle**: Ensure your view bodies update quickly and only when needed to achieve great SwiftUI performance.

**NEW in WWDC 2025**: Next-generation SwiftUI instrument in Instruments 26 provides comprehensive performance analysis with:
- Visual timeline of long updates (color-coded orange/red by severity)
- Cause & Effect Graph showing data flow through your app
- Integration with Time Profiler for CPU analysis
- Hangs and Hitches tracking

**Key Performance Problems**:
1. **Long View Body Updates** - View bodies taking too long to run
2. **Unnecessary View Updates** - Views updating when data hasn't actually changed

---

## The SwiftUI Instrument (Instruments 26)

### Getting Started

**Requirements**:
- Install Xcode 26
- Update devices to latest OS releases (support for recording SwiftUI traces)
- Build app in Release mode for accurate profiling

**Launch**:
1. Open project in Xcode
2. Press **Command-I** to profile
3. Choose **SwiftUI template** from template chooser
4. Click Record button

### Template Contents

The SwiftUI template includes three instruments:

1. **SwiftUI Instrument** (NEW) - Identifies performance issues in SwiftUI code
2. **Time Profiler** - Shows CPU work samples over time
3. **Hangs and Hitches** - Tracks app responsiveness

### SwiftUI Instrument Track Lanes

#### Lane 1: Update Groups
- Shows when SwiftUI is actively doing work
- **Empty during CPU spikes?** → Problem likely outside SwiftUI

#### Lane 2: Long View Body Updates
- Highlights when `body` property takes too long
- **Most common performance issue** - start here

#### Lane 3: Long Representable Updates
- Identifies slow UIViewRepresentable/NSViewRepresentable updates
- UIKit/AppKit integration performance

#### Lane 4: Other Long Updates
- All other types of long SwiftUI work

### Color-Coding System

Updates shown in **orange** and **red** based on likelihood to cause hitches:

- **Red** - Very likely to contribute to hitch/hang (investigate first)
- **Orange** - Moderately likely to cause issues
- **Gray** - Normal updates, not concerning

**Note**: Whether updates actually result in hitches depends on device conditions, but red updates are the highest priority.

---

## Understanding the Render Loop

### Normal Frame Rendering

```
Frame 1:
├─ Handle events (touches, key presses)
├─ Update UI (run view bodies)
│  └─ Complete before frame deadline ✅
├─ Hand off to system
└─ System renders → Visible on screen

Frame 2:
├─ Handle events
├─ Update UI
│  └─ Complete before frame deadline ✅
├─ Hand off to system
└─ System renders → Visible on screen
```

**Result**: Smooth, fluid animations

### Frame with Hitch (Long View Body)

```
Frame 1:
├─ Handle events
├─ Update UI
│  └─ ONE VIEW BODY TOO SLOW
│  └─ Runs past frame deadline ❌
├─ Miss deadline
└─ Previous frame stays visible (HITCH)

Frame 2: (Delayed)
├─ Handle events (delayed by 1 frame)
├─ Update UI
├─ Hand off to system
└─ System renders → Finally visible

Result: Previous frame visible for 2+ frames = animation stutter
```

### Frame with Hitch (Too Many Updates)

```
Frame 1:
├─ Handle events
├─ Update UI
│  ├─ Update 1 (fast)
│  ├─ Update 2 (fast)
│  ├─ Update 3 (fast)
│  ├─ ... (100 more fast updates)
│  └─ Total time exceeds deadline ❌
├─ Miss deadline
└─ Previous frame stays visible (HITCH)
```

**Result**: Many small updates add up to miss deadline

**Key Insight**: View body runtime matters because missing frame deadlines causes hitches, making animations less fluid.

**Reference**:
- [Understanding hitches in your app](https://developer.apple.com/documentation/xcode/understanding-hitches-in-your-app)
- Tech Talk on render loop and fixing hitches

---

## Problem 1: Long View Body Updates

### Identifying Long Updates

1. **Record trace** in Instruments with SwiftUI template
2. **Look at Long View Body Updates lane** - any orange/red bars?
3. **Expand SwiftUI track** to see subtracks
4. **Select View Body Updates subtrack**
5. **Filter to long updates**:
   - Detail pane → Dropdown → Choose "Long View Body Updates summary"

### Analyzing with Time Profiler

**Workflow**:
1. Find long update in Long View Body Updates summary
2. Hover over view name → Click arrow → "Show Updates"
3. Right-click on long update → "Set Inspection Range and Zoom"
4. **Switch to Time Profiler instrument track**

**What you see**:
- Call stacks for samples recorded during view body execution
- Time spent in each frame (leftmost column)
- Your view body nested in deep SwiftUI call stack

**Finding the bottleneck**:
1. Option-click to expand main thread call stack
2. Command-F to search for your view name (e.g., "LandmarkListItemView")
3. Identify expensive operations in time column

### Common Expensive Operations

#### Formatter Creation (Very Expensive)

**❌ WRONG - Creating formatters in view body**:
```swift
struct LandmarkListItemView: View {
    let landmark: Landmark
    @State private var userLocation: CLLocation

    var distance: String {
        // ❌ Creating formatters every time body runs
        let numberFormatter = NumberFormatter()
        numberFormatter.maximumFractionDigits = 1

        let measurementFormatter = MeasurementFormatter()
        measurementFormatter.numberFormatter = numberFormatter

        let meters = userLocation.distance(from: landmark.location)
        let measurement = Measurement(value: meters, unit: UnitLength.meters)
        return measurementFormatter.string(from: measurement)
    }

    var body: some View {
        HStack {
            Text(landmark.name)
            Text(distance) // Calls expensive distance property
        }
    }
}
```

**Why it's slow**:
- Formatters are expensive to create (milliseconds each)
- Created every time view body runs
- Runs on main thread → app waits before continuing UI updates
- Multiple views → time adds up quickly

**✅ CORRECT - Cache formatters centrally**:
```swift
@Observable
class LocationFinder {
    private let formatter: MeasurementFormatter
    private let landmarks: [Landmark]
    private var distanceCache: [Landmark.ID: String] = [:]

    init(landmarks: [Landmark]) {
        self.landmarks = landmarks

        // Create formatters ONCE during initialization
        let numberFormatter = NumberFormatter()
        numberFormatter.maximumFractionDigits = 1

        self.formatter = MeasurementFormatter()
        self.formatter.numberFormatter = numberFormatter

        updateDistances()
    }

    func didUpdateLocations(_ locations: [CLLocation]) {
        guard let location = locations.last else { return }
        updateDistances(from: location)
    }

    private func updateDistances(from location: CLLocation? = nil) {
        guard let location else { return }

        for landmark in landmarks {
            let meters = location.distance(from: landmark.location)
            let measurement = Measurement(value: meters, unit: UnitLength.meters)
            distanceCache[landmark.id] = formatter.string(from: measurement)
        }
    }

    func distanceString(for landmarkID: Landmark.ID) -> String {
        distanceCache[landmarkID] ?? "Unknown"
    }
}

struct LandmarkListItemView: View {
    let landmark: Landmark
    @Environment(LocationFinder.self) private var locationFinder

    var body: some View {
        HStack {
            Text(landmark.name)
            Text(locationFinder.distanceString(for: landmark.id)) // ✅ Fast lookup
        }
    }
}
```

**Benefits**:
- Formatters created once, reused for all landmarks
- Strings pre-calculated when location changes
- View body just reads cached value (instant)
- Long view body updates eliminated

#### Other Expensive Operations

**Complex Calculations**:
```swift
// ❌ Don't calculate in view body
var body: some View {
    let result = expensiveAlgorithm(data) // Complex math, sorting, etc.
    Text("\(result)")
}

// ✅ Calculate in model, cache result
@Observable
class ViewModel {
    private(set) var result: Int = 0

    func updateData(_ data: [Int]) {
        result = expensiveAlgorithm(data) // Calculate once
    }
}
```

**Network/File I/O**:
```swift
// ❌ NEVER do I/O in view body
var body: some View {
    let data = try? Data(contentsOf: fileURL) // ❌ Synchronous I/O
    // ...
}

// ✅ Load asynchronously, store in state
@State private var data: Data?

var body: some View {
    // Just read state
}
.task {
    data = try? await loadData() // Async loading
}
```

**Image Processing**:
```swift
// ❌ Don't process images in view body
var body: some View {
    let thumbnail = image.resized(to: CGSize(width: 100, height: 100))
    Image(uiImage: thumbnail)
}

// ✅ Process images in background, cache
.task {
    await processThumbnails()
}
```

### Verifying the Fix

After implementing fix:

1. Record new trace in Instruments
2. Check Long View Body Updates summary
3. **Verify your view is gone from the list** (or significantly reduced)

**Note**: Updates at app launch may still be long (building initial view hierarchy) - this is normal and won't cause hitches during scrolling.

---

## Problem 2: Unnecessary View Updates

### Why Unnecessary Updates Matter

Even if individual updates are fast, **too many updates add up**:

```
100 fast updates × 2ms each = 200ms total
→ Misses 16.67ms frame deadline
→ Hitch
```

### Identifying Unnecessary Updates

**Scenario**: Tapping a favorite button on one item updates ALL items in a list.

**Expected**: Only the tapped item updates.
**Actual**: All visible items update.

**How to find**:
1. Record trace with user interaction in mind
2. Highlight relevant portion of timeline
3. Expand hierarchy in detail pane
4. **Count updates** - more than expected?

### Understanding SwiftUI's Data Model

SwiftUI uses **AttributeGraph** to define dependencies and avoid re-running views unnecessarily.

#### Attributes & Dependencies

```swift
struct OnOffView: View {
    @State private var isOn: Bool = false

    var body: some View {
        Text(isOn ? "On" : "Off")
    }
}
```

**What SwiftUI creates**:
1. **View attribute** - Stores view struct (recreated frequently)
2. **State storage** - Keeps `isOn` value (persists entire view lifetime)
3. **Signal attribute** - Tracks when state changes
4. **View body attribute** - Depends on state signal
5. **Text attributes** - Depend on view body

**When state changes**:
1. Create transaction (scheduled change for next frame)
2. Mark signal attribute as outdated
3. Walk dependency chain, marking dependent attributes as outdated (just set flag - fast)
4. Before rendering, update all outdated attributes
5. View body runs again, producing new Text struct
6. Continue updates until all needed attributes updated
7. Render frame

### The Cause & Effect Graph

**Purpose**: Visualize **what marked your view body as outdated**.

**Example graph**:
```
[Gesture] → [State Change] → [View Body Update]
               ↓
         [Other View Bodies]
```

**Node types**:
- **Blue nodes** - Your code or actions (gestures, state changes, view bodies)
- **System nodes** - SwiftUI/system work
- **Arrows labeled "update"** - Caused update
- **Arrows labeled "creation"** - Caused view to appear

**Selecting nodes**:
- Click **State change node** → See backtrace of where value was updated
- Click **View body node** → See which views updated and why

**Accessing graph**:
1. Detail pane → Expand hierarchy to find view
2. Hover over view name → Click arrow
3. Choose **"Show Cause & Effect Graph"**

### Example: Favorites List Problem

**Problem**:
```swift
@Observable
class ModelData {
    var favoritesCollection: Collection // Contains array of favorites

    func isFavorite(_ landmark: Landmark) -> Bool {
        favoritesCollection.landmarks.contains(landmark) // ❌ Depends on whole array
    }
}

struct LandmarkListItemView: View {
    let landmark: Landmark
    @Environment(ModelData.self) private var modelData

    var body: some View {
        HStack {
            Text(landmark.name)
            Button {
                modelData.toggleFavorite(landmark) // Modifies array
            } label: {
                Image(systemName: modelData.isFavorite(landmark) ? "heart.fill" : "heart")
            }
        }
    }
}
```

**What happens**:
1. Each view calls `isFavorite()`, accessing `favoritesCollection.landmarks` array
2. `@Observable` creates dependency: **Each view depends on entire array**
3. Tapping button calls `toggleFavorite()`, modifying array
4. **All views** marked as outdated (array changed)
5. **All view bodies run** (even though only one changed)

**Cause & Effect Graph shows**:
```
[Gesture] → [favoritesCollection.landmarks array change] → [All LandmarkListItemViews update]
```

**✅ Solution - Granular Dependencies**:
```swift
@Observable
class LandmarkViewModel {
    var isFavorite: Bool = false

    func toggleFavorite() {
        isFavorite.toggle()
    }
}

@Observable
class ModelData {
    private(set) var viewModels: [Landmark.ID: LandmarkViewModel] = [:]

    init(landmarks: [Landmark]) {
        for landmark in landmarks {
            viewModels[landmark.id] = LandmarkViewModel()
        }
    }

    func viewModel(for landmarkID: Landmark.ID) -> LandmarkViewModel? {
        viewModels[landmarkID]
    }
}

struct LandmarkListItemView: View {
    let landmark: Landmark
    @Environment(ModelData.self) private var modelData

    var body: some View {
        if let viewModel = modelData.viewModel(for: landmark.id) {
            HStack {
                Text(landmark.name)
                Button {
                    viewModel.toggleFavorite() // ✅ Only modifies this view model
                } label: {
                    Image(systemName: viewModel.isFavorite ? "heart.fill" : "heart")
                }
            }
        }
    }
}
```

**Result**:
- Each view depends **only on its own view model**
- Tapping button updates **only that view model**
- **Only one view body runs**

**Cause & Effect Graph shows**:
```
[Gesture] → [Single LandmarkViewModel change] → [Single LandmarkListItemView update]
```

---

## Environment Updates

### How Environment Works

```swift
struct EnvironmentValues {
    // Dictionary-like value type
    var colorScheme: ColorScheme
    var locale: Locale
    // ... many more values
}
```

**Each view has dependency on entire EnvironmentValues struct** via `@Environment` property wrapper.

### What Happens on Environment Change

1. **Any environment value changes** (e.g., dark mode enabled)
2. **All views with `@Environment` dependency notified**
3. **Each view checks** if the specific value it reads changed
4. **If value changed** → View body runs
5. **If value didn't change** → SwiftUI skips running view body (already up-to-date)

**Cost**: Even when body doesn't run, there's still cost of checking for updates.

### Environment Update Nodes in Graph

Two types:

1. **External Environment** - App-level changes from outside SwiftUI (color scheme, accessibility settings)
2. **EnvironmentWriter** - Changes inside SwiftUI via `.environment()` modifier

**Example**:
```
View1 reads colorScheme:
[External Environment] → [View1 body runs] ✅

View2 reads locale (doesn't read colorScheme):
[External Environment] → [View2 body check] (body doesn't run - dimmed icon)
```

**Same update shows as multiple nodes**: Hover/click any node for same update → all highlight together.

### Environment Performance Warning

⚠️ **AVOID storing frequently-changing values in environment**:

```swift
// ❌ DON'T DO THIS
struct ContentView: View {
    @State private var scrollOffset: CGFloat = 0

    var body: some View {
        ScrollView {
            // Content
        }
        .environment(\.scrollOffset, scrollOffset) // ❌ Updates on every scroll frame
        .onPreferenceChange(ScrollOffsetKey.self) { offset in
            scrollOffset = offset
        }
    }
}
```

**Why it's bad**:
- Environment change triggers checks in **all child views**
- Scrolling = 60+ updates/second
- Massive performance hit

**✅ Better approach**:
```swift
// Pass via parameter or @Observable model
struct ContentView: View {
    @State private var scrollViewModel = ScrollViewModel()

    var body: some View {
        ScrollView {
            ChildView(scrollViewModel: scrollViewModel) // Direct parameter
        }
    }
}
```

**Environment is great for**:
- Color scheme
- Locale
- Accessibility settings
- Other relatively stable values

---

## Performance Optimization Checklist

### Before Profiling
- [ ] Build in Release mode (Debug mode has overhead)
- [ ] Test on real devices (Simulator performance ≠ real device)
- [ ] Update device to latest OS (SwiftUI trace support)
- [ ] Identify specific slow interactions to profile

### During Profiling
- [ ] Use SwiftUI template in Instruments 26
- [ ] Focus on Long View Body Updates lane first
- [ ] Check Update Groups lane (empty = problem outside SwiftUI)
- [ ] Record realistic user workflows (not artificial scenarios)
- [ ] Keep profiling sessions short (easier to analyze)

### Analyzing Long View Body Updates
- [ ] Filter detail pane to "Long View Body Updates"
- [ ] Start with red updates, then orange
- [ ] Use Time Profiler to find expensive operations
- [ ] Look for formatter creation, calculations, I/O
- [ ] Check if work can be moved to model layer

### Analyzing Unnecessary Updates
- [ ] Count view body updates - more than expected?
- [ ] Use Cause & Effect Graph to trace data flow
- [ ] Check for whole array/collection dependencies
- [ ] Verify each view depends only on relevant data
- [ ] Avoid frequently-changing environment values

### After Optimization
- [ ] Record new trace to verify improvements
- [ ] Compare before/after Long View Body Updates counts
- [ ] Test on slowest supported device
- [ ] Monitor in real-world usage
- [ ] Profile regularly during development

---

## Production Pressure: When Performance Issues Hit Live

### The Problem

When performance issues appear in production, you face competing pressures:
- **Engineering manager**: "Fix it ASAP"
- **VP of Product**: "Users have been complaining for hours"
- **Deployment window**: 6 hours before next App Store review window
- **Temptation**: Quick fix (add `.compositingGroup()`, disable animation, simplify view)

**The issue**: Quick fixes based on guesses fail 80% of the time and waste your deployment window.

### Red Flags - Resist These Pressure Tactics

If you hear ANY of these under deadline pressure, **STOP and use SwiftUI Instrument**:

- ❌ **"Just add .compositingGroup()"** – Without profiling, you don't know if this helps
- ❌ **"We can roll back if it doesn't work"** – App Store review takes 24 hours; rollback isn't fast
- ❌ **"Other apps use this pattern"** – Doesn't mean it solves YOUR specific problem
- ❌ **"Users will accept degradation for now"** – Once shipped, you're committed for 24 hours
- ❌ **"We don't have time to profile"** – You have less time if you guess wrong

### One SwiftUI Instrument Recording (30-Minute Protocol)

Under production pressure, one good diagnostic recording beats random fixes:

**Time Budget**:
- Build in Release mode: 5 min
- Launch and interact to trigger sluggishness: 3 min
- Record SwiftUI Instrument trace: 5 min
- Review Long View Body Updates lane: 5 min
- Check Cause & Effect Graph: 5 min
- Identify specific expensive view: 2 min

**Total**: 25 minutes to know EXACTLY what's slow

**Then**:
- Apply targeted fix (15-30 min)
- Test in Instruments again (5 min)
- Ship with confidence

**Total time**: 1 hour 15 minutes for diagnosis + fix, leaving 4+ hours for edge case testing.

### Comparing Time Costs

**Option A: Guess and Pray**
- Time to implement: 30 min
- Time to deploy: 20 min
- Time to learn it failed: 24 hours (next App Store review)
- Total delay: 24 hours minimum
- User suffering: Continues through deployment window

**Option B: One SwiftUI Instrument Recording**
- Time to diagnose: 25 min
- Time to apply targeted fix: 20 min
- Time to verify: 5 min
- Time to deploy: 20 min
- Total time: 1.5 hours
- User suffering: Stopped after 2 hours instead of 26+ hours

**Time cost of being wrong**:
- A: 24-hour delay + reputational damage + users suffering
- B: 1.5 hours + you know the actual problem + confidence in the fix

### Real-World Example: Tab Transition Sluggishness

**Pressure scenario**:
- iOS 26 build shipped
- Users report "sluggish tab transitions"
- VP asking for updates every hour
- 6 hours until deployment window closes

**Bad approach** (Option A):
```
Junior suggests: "Add .compositingGroup() to TabView"
You: "Sure, let's try it"
Result: Ships without profiling
Outcome: Doesn't fix issue (compositing wasn't the problem)
Next: 24 hours until next deploy window
VP update: "Users still complaining"
```

**Good approach** (Option B):
```
"Running one SwiftUI Instrument recording of tab transition"
[25 minutes later]
"SwiftUI Instrument shows Long View Body Updates in ProductGridView during transition.
Cause & Effect Graph shows ProductList rebuilding entire grid unnecessarily.
Applying view identity fix (`.id()`) to prevent unnecessary updates"
[30 minutes to implement and test]
"Deployed at 1.5 hours. Verified with Instruments. Tab transitions now smooth."
```

### When to Accept the Pressure (And Still be Right)

Sometimes managers are right to push for speed. Accept the pressure IF:

- [ ] You've run ONE SwiftUI Instrument recording (25 minutes)
- [ ] You know what specific view/operation is expensive
- [ ] You have a targeted fix, not a guess
- [ ] You've verified the fix in Instruments before shipping
- [ ] You're shipping WITH profiling data, not hoping it works

**Document your decision**:
```
Slack to VP + team:

"Completed diagnostic: ProductGridView rebuilding unnecessarily during
tab transitions (confirmed in SwiftUI Instrument, Long View Body Updates).
Applied view identity fix. Verified in Instruments - transitions now 16.67ms.
Deploying now."
```

This shows:
- You diagnosed (not guessed)
- You solved the right problem
- You verified the fix
- You're shipping with confidence

### If You Still Get It Wrong After Profiling

**Honest admission**:
```
"SwiftUI Instrument showed ProductGridView was the bottleneck.
Applied view identity fix, but performance didn't improve as expected.
Root cause is deeper than expected. Requiring architectural change.
Shipping animation disable (.animation(nil) on TabView) as mitigation.
Proper fix queued for next release cycle."
```

This is different from guessing:
- You have **evidence** of the root cause
- You **understand** why the quick fix didn't work
- You're **buying time** with a known mitigation
- You're **committed** to proper fix next cycle

### Decision Framework Under Pressure

**Before shipping ANY fix:**

| Question | Answer Yes? | Action |
|----------|-------------|--------|
| Have you run SwiftUI Instrument? | No | STOP - 25 min diagnostic |
| Do you know which view is expensive? | No | STOP - review Cause & Effect Graph |
| Can you explain in one sentence why the fix helps? | No | STOP - you're guessing |
| Have you verified the fix in Instruments? | No | STOP - test before shipping |
| Did you consider simpler explanations? | No | STOP - check documentation first |

**Answer YES to all five** → Ship with confidence

---

## Common Patterns & Solutions

### Pattern 1: List Item Dependencies

**Problem**: Updating one item updates entire list

**Solution**: Per-item view models with granular dependencies

```swift
// ❌ Shared dependency
@Observable
class ListViewModel {
    var items: [Item] // All views depend on whole array
}

// ✅ Granular dependencies
@Observable
class ListViewModel {
    private(set) var itemViewModels: [Item.ID: ItemViewModel]
}

@Observable
class ItemViewModel {
    var item: Item // Each view depends only on its item
}
```

### Pattern 2: Computed Properties in View Bodies

**Problem**: Expensive computation runs every render

**Solution**: Move to model, cache result

```swift
// ❌ Compute in view
struct MyView: View {
    let data: [Int]

    var body: some View {
        Text("\(data.sorted().last ?? 0)") // Sorts every render
    }
}

// ✅ Compute in model
@Observable
class ViewModel {
    var data: [Int] {
        didSet {
            maxValue = data.max() ?? 0 // Compute once when data changes
        }
    }
    private(set) var maxValue: Int = 0
}

struct MyView: View {
    @Environment(ViewModel.self) private var viewModel

    var body: some View {
        Text("\(viewModel.maxValue)") // Just read cached value
    }
}
```

### Pattern 3: Formatter Reuse

**Problem**: Creating formatters repeatedly

**Solution**: Create once, reuse

```swift
// ❌ Create every time
var body: some View {
    let formatter = DateFormatter()
    formatter.dateStyle = .short
    Text(formatter.string(from: date))
}

// ✅ Reuse formatter
class Formatters {
    static let shortDate: DateFormatter = {
        let f = DateFormatter()
        f.dateStyle = .short
        return f
    }()
}

var body: some View {
    Text(Formatters.shortDate.string(from: date))
}
```

### Pattern 4: Environment for Stable Values Only

**Problem**: Rapidly-changing environment values

**Solution**: Use direct parameters or models

```swift
// ❌ Frequently changing in environment
.environment(\.scrollPosition, scrollPosition) // 60+ updates/second

// ✅ Direct parameter or model
ChildView(scrollPosition: scrollPosition)
```

---

## iOS 26 Performance Improvements

**Automatic improvements** when building with Xcode 26 (no code changes needed):

### Lists
- Update up to **16× faster**
- Large lists on macOS load **6× faster**

### SwiftUI Instrument
- Next-generation performance analysis
- Captures detailed cause-and-effect information
- Makes it easier than ever to understand when and why views update

---

## Debugging Performance Issues

### Step-by-Step Process

1. **Reproduce issue** - Identify specific slow interaction
2. **Profile with Instruments** - SwiftUI template
3. **Check Update Groups lane** - SwiftUI doing work when slow?
4. **Identify problem type**:
   - Long View Body Updates? → Section on Long Updates
   - Too many updates? → Section on Unnecessary Updates
5. **Use Time Profiler** for long updates (find expensive operation)
6. **Use Cause & Effect Graph** for unnecessary updates (find dependency issue)
7. **Implement fix**
8. **Verify with new trace**

### When SwiftUI Isn't the Problem

**Update Groups lane empty during performance issue?**

Problem likely elsewhere:
- Network requests
- Background processing
- Image loading
- Database queries
- Third-party frameworks

**Next steps**:
- [Analyze hangs with Instruments](https://developer.apple.com/documentation/xcode/analyzing-hangs-in-your-app)
- [Optimize CPU performance with Instruments](https://developer.apple.com/documentation/xcode/optimizing-your-app-s-performance)

---

## Real-World Impact

**Example: Landmarks App (from WWDC 2025)**

**Before optimization**:
- Every favorite button tap updated ALL visible landmark views
- Each view recreated formatters for distance calculation
- Scrolling felt janky

**After optimization**:
- Only tapped view updates (granular view models)
- Formatters created once, strings cached
- Smooth 60fps scrolling

**Improvements**:
- 100+ unnecessary view updates → 1 update per action
- Milliseconds saved per view × dozens of views = significant improvement
- Eliminated long view body updates entirely

---

## Reference

**WWDC 2025 Sessions**:
- [Optimize SwiftUI performance with Instruments - WWDC25 Session 306](https://developer.apple.com/videos/play/wwdc2025/306/)
  - New SwiftUI instrument, long view bodies, unnecessary updates, Cause & Effect Graph

**Related Documentation**:
- [Understanding hitches in your app](https://developer.apple.com/documentation/xcode/understanding-hitches-in-your-app)
- [Analyzing hangs with Instruments](https://developer.apple.com/documentation/xcode/analyzing-hangs-in-your-app)
- [Optimizing CPU performance with Instruments](https://developer.apple.com/documentation/xcode/optimizing-your-app-s-performance)

**Other Skills**:
- For memory issues: See `memory-debugging` skill
- For Xcode environment issues: See `xcode-debugging` skill

---

## Key Takeaways

1. **Fast view bodies** - Keep them quick so SwiftUI has time to get UI on screen without delay
2. **Update only when needed** - Design data flow to update views only when necessary
3. **Careful with environment** - Don't store frequently-changing values
4. **Profile early and often** - Use Instruments during development, not just when problems arise
5. **Greatest takeaway**: **Ensure your view bodies update quickly and only when needed to achieve great SwiftUI performance**

---

## Version History

- **1.1.0**: Added "Production Pressure: When Performance Issues Hit Live" section from TDD testing of production crisis scenarios. Includes 30-minute diagnostic protocol with explicit time-cost analysis, red flags for dangerous pressure tactics, real-world tab transition sluggishness example, and 5-question decision framework before shipping. Prevents guessing under deployment deadline pressure and ensures diagnosis-driven fixes
- **1.0.0 (WWDC 2025)**: Initial skill based on new SwiftUI Instrument in Instruments 26, covering long view body updates, unnecessary updates, Cause & Effect Graph, and performance optimization patterns from WWDC 2025 Session 306

---

**Last Updated**: WWDC 2025
**Minimum Requirements**: Xcode 26, iOS 26+/iPadOS 26+/macOS Tahoe+/visionOS 3+
