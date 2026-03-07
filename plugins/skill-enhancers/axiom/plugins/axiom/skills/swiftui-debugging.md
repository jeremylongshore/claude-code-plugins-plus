---
name: swiftui-debugging
description: Use when debugging SwiftUI view updates, preview crashes, or layout issues - diagnostic decision trees to identify root causes quickly and avoid misdiagnosis under pressure
version: 1.2.0
last_updated: TDD-tested with production deadline and intermittent bug scenarios, added 3 real-world examples
---

# SwiftUI Debugging

## Overview

SwiftUI debugging falls into three categories, each with a different diagnostic approach:

1. **View Not Updating** – You changed something but the view didn't redraw. Decision tree to identify whether it's struct mutation, lost binding identity, accidental view recreation, or missing observer pattern.
2. **Preview Crashes** – Your preview won't compile or crashes immediately. Decision tree to distinguish between missing dependencies, state initialization failures, and Xcode cache corruption.
3. **Layout Issues** – Views appearing in wrong positions, wrong sizes, overlapping unexpectedly. Quick reference patterns for common scenarios.

**Core principle**: Start with observable symptoms, test systematically, eliminate causes one by one. Don't guess.

**Requires**: Xcode 15+, iOS 14+
**Related skills**: `xcode-debugging` (cache corruption diagnosis), `swift-concurrency` (observer patterns)

## When to Use SwiftUI Debugging

**Use this skill when:**
- ✅ A view isn't updating when you expect it to
- ✅ Preview crashes or won't load
- ✅ Layout looks wrong on specific devices
- ✅ You're tempted to bandaid with @ObservedObject everywhere

**Use `xcode-debugging` instead when:**
- App crashes at runtime (not preview)
- Build fails completely
- You need environment diagnostics

**Use `swift-concurrency` instead when:**
- Questions about async/await or MainActor
- Data race warnings

## View Not Updating – Decision Tree

The most common frustration: you changed @State but the view didn't redraw. The root cause is always one of four things.

### Step 1: Can You Reproduce in a Minimal Preview?

```swift
#Preview {
  YourView()
}
```

**YES** → The problem is in your code. Continue to Step 2.

**NO** → It's likely Xcode state or cache corruption. Skip to Preview Crashes section.

### Step 2: Diagnose the Root Cause

#### Root Cause 1: Struct Mutation

**Symptom**: You modify a @State value directly, but the view doesn't update.

**Why it happens**: SwiftUI doesn't see direct mutations on structs. You need to reassign the entire value.

```swift
// ❌ WRONG: Direct mutation doesn't trigger update
@State var items: [String] = []

func addItem(_ item: String) {
    items.append(item)  // SwiftUI doesn't see this change
}

// ✅ RIGHT: Reassignment triggers update
@State var items: [String] = []

func addItem(_ item: String) {
    var newItems = items
    newItems.append(item)
    self.items = newItems  // Full reassignment
}

// ✅ ALSO RIGHT: Use a binding
@State var items: [String] = []

var itemsBinding: Binding<[String]> {
    Binding(
        get: { items },
        set: { items = $0 }
    )
}
```

**Fix it**: Always reassign the entire struct value, not pieces of it.

---

#### Root Cause 2: Lost Binding Identity

**Symptom**: You pass a binding to a child view, but changes in the child don't update the parent.

**Why it happens**: You're passing `.constant()` or creating a new binding each time, breaking the two-way connection.

```swift
// ❌ WRONG: Constant binding is read-only
@State var isOn = false

ToggleChild(value: .constant(isOn))  // Changes ignored

// ❌ WRONG: New binding created each render
@State var name = ""

TextField("Name", text: Binding(
    get: { name },
    set: { name = $0 }
))  // New binding object each time parent renders

// ✅ RIGHT: Pass the actual binding
@State var isOn = false

ToggleChild(value: $isOn)

// ✅ RIGHT: Create binding once, not in body
@State var name = ""
@State var nameBinding: Binding<String>?

var body: some View {
    if nameBinding == nil {
        nameBinding = Binding(
            get: { name },
            set: { name = $0 }
        )
    }
    return TextField("Name", text: nameBinding!)
}
```

**Fix it**: Pass `$state` directly when possible. If creating custom bindings, create them in `init` or cache them, not in `body`.

---

#### Root Cause 3: Accidental View Recreation

**Symptom**: The view updates, but @State values reset to initial state. You see brief flashes of initial values.

**Why it happens**: The view got a new identity (removed from a conditional, moved in a container, or the container itself was recreated), causing SwiftUI to treat it as a new view.

```swift
// ❌ WRONG: View identity changes when condition flips
@State var count = 0

var body: some View {
    VStack {
        if showCounter {
            Counter()  // Gets new identity each time showCounter changes
        }
        Button("Toggle") {
            showCounter.toggle()
        }
    }
}

// Counter gets recreated, @State count resets to 0

// ✅ RIGHT: Preserve identity with opacity or hidden
@State var count = 0

var body: some View {
    VStack {
        Counter()
            .opacity(showCounter ? 1 : 0)
        Button("Toggle") {
            showCounter.toggle()
        }
    }
}

// ✅ ALSO RIGHT: Use id() if you must conditionally show
@State var count = 0

var body: some View {
    VStack {
        if showCounter {
            Counter()
                .id("counter")  // Stable identity
        }
        Button("Toggle") {
            showCounter.toggle()
        }
    }
}
```

**Fix it**: Preserve view identity by using `.opacity()` instead of conditionals, or apply `.id()` with a stable identifier.

---

#### Root Cause 4: Missing Observer Pattern

**Symptom**: An object changed, but views observing it didn't update.

**Why it happens**: You're not using @StateObject or @ObservedObject, so SwiftUI doesn't know to watch for changes.

```swift
// ❌ WRONG: Property changes don't trigger update
class Model {
    @Published var count = 0
}

struct ContentView: View {
    let model = Model()  // New instance each render

    var body: some View {
        Text("\(model.count)")
        Button("Increment") {
            model.count += 1  // View doesn't update
        }
    }
}

// ✅ RIGHT: Use @StateObject for owned instances
struct ContentView: View {
    @StateObject var model = Model()

    var body: some View {
        Text("\(model.count)")
        Button("Increment") {
            model.count += 1  // View updates
        }
    }
}

// ✅ RIGHT: Use @ObservedObject for injected instances
struct ContentView: View {
    @ObservedObject var model: Model  // Passed in from parent

    var body: some View {
        Text("\(model.count)")
    }
}
```

**Fix it**: Use `@StateObject` if you own the object, `@ObservedObject` if it's injected, or `@EnvironmentObject` if it's shared across the tree.

---

### Decision Tree Summary

```
View not updating?
├─ Can reproduce in preview?
│  ├─ YES: Problem is in code
│  │  ├─ Modified struct directly? → Struct Mutation
│  │  ├─ Passed binding to child? → Lost Binding Identity
│  │  ├─ View inside conditional? → Accidental Recreation
│  │  └─ Object changed but view didn't? → Missing Observer
│  └─ NO: Likely cache/Xcode state → See Preview Crashes
```

## Preview Crashes – Decision Tree

When your preview won't load or crashes immediately, the three root causes are distinct.

### Step 1: What's the Error?

#### Error Type 1: "Cannot find in scope" or "No such module"

**Root cause**: Preview missing a required dependency (@EnvironmentObject, @Environment, imported module).

```swift
// ❌ WRONG: ContentView needs a model, preview doesn't provide it
struct ContentView: View {
    @EnvironmentObject var model: AppModel

    var body: some View {
        Text(model.title)
    }
}

#Preview {
    ContentView()  // Crashes: model not found
}

// ✅ RIGHT: Provide the dependency
#Preview {
    ContentView()
        .environmentObject(AppModel())
}

// ✅ ALSO RIGHT: Check for missing imports
// If using custom types, make sure they're imported in preview file

#Preview {
    MyCustomView()  // Make sure MyCustomView is defined or imported
}
```

**Fix it**: Trace the error, find what's missing, provide it to the preview.

---

#### Error Type 2: Fatal error or Silent crash (no error message)

**Root cause**: State initialization failed at runtime. The view tried to access data that doesn't exist.

```swift
// ❌ WRONG: Index out of bounds at runtime
struct ListView: View {
    @State var selectedIndex = 10
    let items = ["a", "b", "c"]

    var body: some View {
        Text(items[selectedIndex])  // Crashes: index 10 doesn't exist
    }
}

// ❌ WRONG: Optional forced unwrap fails
struct DetailView: View {
    @State var data: Data?

    var body: some View {
        Text(data!.title)  // Crashes if data is nil
    }
}

// ✅ RIGHT: Safe defaults
struct ListView: View {
    @State var selectedIndex = 0  // Valid index
    let items = ["a", "b", "c"]

    var body: some View {
        if selectedIndex < items.count {
            Text(items[selectedIndex])
        }
    }
}

// ✅ RIGHT: Handle optionals
struct DetailView: View {
    @State var data: Data?

    var body: some View {
        if let data = data {
            Text(data.title)
        } else {
            Text("No data")
        }
    }
}
```

**Fix it**: Review your @State initializers. Check array bounds, optional unwraps, and default values.

---

#### Error Type 3: Works fine locally but preview won't load

**Root cause**: Xcode cache corruption. The preview process has stale information about your code.

**Diagnostic checklist**:
- Preview worked yesterday, code hasn't changed → Likely cache
- Restarting Xcode fixes it temporarily but returns → Definitely cache
- Same code builds in simulator fine but preview fails → Cache
- Multiple unrelated previews fail at once → Cache

**Fix it** (in order):
1. Restart Preview Canvas: `Cmd+Option+P`
2. Restart Xcode completely (File → Close Window, then reopen project)
3. Nuke derived data: `rm -rf ~/Library/Developer/Xcode/DerivedData`
4. Rebuild: `Cmd+B`

If still broken after all four steps: It's not cache, see Error Types 1 or 2.

---

### Decision Tree Summary

```
Preview crashes?
├─ Error message visible?
│  ├─ "Cannot find in scope" → Missing Dependency
│  ├─ "Fatal error" or silent crash → State Init Failure
│  └─ No error → Likely Cache Corruption
└─ Try: Restart Preview → Restart Xcode → Nuke DerivedData
```

## Layout Issues – Quick Reference

Layout problems are usually visually obvious. Match your symptom to the pattern.

### Pattern 1: Views Overlapping in ZStack

**Symptom**: Views stacked on top of each other, some invisible.

**Root cause**: Z-order is wrong or you're not controlling visibility.

```swift
// ❌ WRONG: Can't see the blue view
ZStack {
    Rectangle().fill(.blue)
    Rectangle().fill(.red)
}

// ✅ RIGHT: Use zIndex to control layer order
ZStack {
    Rectangle().fill(.blue).zIndex(0)
    Rectangle().fill(.red).zIndex(1)
}

// ✅ ALSO RIGHT: Hide instead of removing from hierarchy
ZStack {
    Rectangle().fill(.blue)
    Rectangle().fill(.red).opacity(0.5)
}
```

---

### Pattern 2: GeometryReader Sizing Weirdness

**Symptom**: View is tiny or taking up the entire screen unexpectedly.

**Root cause**: GeometryReader sizes itself to available space; parent doesn't constrain it.

```swift
// ❌ WRONG: GeometryReader expands to fill all available space
VStack {
    GeometryReader { geo in
        Text("Size: \(geo.size)")
    }
    Button("Next") { }
}
// Text takes entire remaining space

// ✅ RIGHT: Constrain the geometry reader
VStack {
    GeometryReader { geo in
        Text("Size: \(geo.size)")
    }
    .frame(height: 100)

    Button("Next") { }
}
```

---

### Pattern 3: SafeArea Complications

**Symptom**: Content hidden behind notch, or not using full screen space.

**Root cause**: `.ignoresSafeArea()` applied to wrong view.

```swift
// ❌ WRONG: Only the background ignores safe area
ZStack {
    Color.blue.ignoresSafeArea()
    VStack {
        Text("Still respects safe area")
    }
}

// ✅ RIGHT: Container ignores, children position themselves
ZStack {
    Color.blue
    VStack {
        Text("Can now use full space")
    }
}
.ignoresSafeArea()

// ✅ ALSO RIGHT: Be selective about which edges
ZStack {
    Color.blue
    VStack { ... }
}
.ignoresSafeArea(edges: .horizontal)  // Only horizontal
```

---

### Pattern 4: frame() vs fixedSize() Confusion

**Symptom**: Text truncated, buttons larger than text, sizing behavior unpredictable.

**Root cause**: Mixing `frame()` (constrains) with `fixedSize()` (expands to content).

```swift
// ❌ WRONG: fixedSize() overrides frame()
Text("Long text here")
    .frame(width: 100)
    .fixedSize()  // Overrides the frame constraint

// ✅ RIGHT: Use frame() to constrain
Text("Long text here")
    .frame(width: 100, alignment: .leading)
    .lineLimit(1)

// ✅ RIGHT: Use fixedSize() only for natural sizing
VStack(spacing: 0) {
    Text("Small")
        .fixedSize()  // Sizes to text
    Text("Large")
        .fixedSize()
}
```

---

### Pattern 5: Modifier Order Matters

**Symptom**: Padding, corners, or shadows appearing in wrong place.

**Root cause**: Applying modifiers in wrong order. SwiftUI applies bottom-to-top.

```swift
// ❌ WRONG: Corners applied after padding
Text("Hello")
    .padding()
    .cornerRadius(8)  // Corners are too large

// ✅ RIGHT: Corners first, then padding
Text("Hello")
    .cornerRadius(8)
    .padding()

// ❌ WRONG: Shadow after frame
Text("Hello")
    .frame(width: 100)
    .shadow(radius: 4)  // Shadow only on frame bounds

// ✅ RIGHT: Shadow includes all content
Text("Hello")
    .shadow(radius: 4)
    .frame(width: 100)
```

## Pressure Scenarios & Real-World Constraints

When you're under deadline pressure, you'll be tempted to shortcuts that hide problems instead of fixing them.

### Scenario 1: "Preview keeps crashing, we ship tomorrow"

**Red flags you might hear:**
- "Just rebuild everything"
- "Delete derived data and don't worry about it"
- "Ship without validating in preview"
- "It works on my machine, good enough"

**The danger**: You skip diagnosis, cache issue recurs after 2 weeks in production, you're debugging while users hit crashes.

**What to do instead** (5-minute protocol, total):
1. Restart Preview Canvas: `Cmd+Option+P` (30 seconds)
2. Restart Xcode (2 minutes)
3. Nuke derived data: `rm -rf ~/Library/Developer/Xcode/DerivedData` (30 seconds)
4. Rebuild: `Cmd+B` (2 minutes)
5. Still broken? Use the dependency or initialization decision trees above

**Time cost**: 5 minutes diagnosis + 2 minutes fix = **7 minutes total**

**Cost of skipping**: 30 min shipping + 24 hours debug cycle = **24+ hours total**

---

### Scenario 2: "View won't update, let me just wrap it in @ObservedObject"

**Red flags you might think:**
- "Adding @ObservedObject everywhere will fix it"
- "Use ObservableObject as a band-aid"
- "Add @Published to random properties"
- "It's probably a binding issue, I'll just create a custom binding"

**The danger**: You're treating symptoms, not diagnosing. Same view won't update in other contexts. You've just hidden the bug.

**What to do instead** (2-minute diagnosis):
1. Can you reproduce in a minimal preview? If NO → cache corruption (see Scenario 1)
2. If YES: Test each root cause in order:
   - Does the view have @State that you're modifying directly? → Struct Mutation
   - Did the view move into a conditional recently? → View Recreation
   - Are you passing bindings to children that have changed? → Lost Binding Identity
   - Only if none of above: Missing Observer
3. Fix the actual root cause, not with @ObservedObject band-aid

**Decision principle**: If you can't name the specific root cause, you haven't diagnosed yet. Don't code until you can answer "the problem is struct mutation because...".

---

### Scenario 2b: "Intermittent updates - it works sometimes, not always"

**Red flags you might think:**
- "It must be a threading issue, let me add @MainActor everywhere"
- "Let me try @ObservedObject, @State, and custom Binding until something works"
- "Delete DerivedData and hope cache corruption fixes it"
- "This is unfixable, let me ship without this feature"

**The danger**: You're exhausted after 2 hours of guessing. You're 17 hours from App Store submission. You're panicking. Every minute feels urgent, so you stop diagnosing and start flailing.

Intermittent bugs are the MOST important to diagnose correctly. One wrong guess now creates a new bug. You ship with a broken view AND a new bug. App Store rejects you. You miss launch.

**What to do instead** (60-minute systematic diagnosis):

**Step 1: Reproduce in preview** (15 min)
- Create minimal preview of just the broken view
- Tap/interact 20 times
- Does it fail intermittently, consistently, or never?
  - **Fails in preview**: Real bug in your code, use decision tree above
  - **Works in preview but fails in app**: Cache or environment issue, use Preview Crashes decision tree
  - **Can't reproduce at all**: Intermittent race condition, investigate further

**Step 2: Isolate the variable** (15 min)
- If it's intermittent in preview: Likely view recreation
  - Did the view recently move into a conditional? Remove it and test
  - Did you add `if` logic that might recreate the parent? Remove it and test
- If it works in preview but fails in app: Likely environment/cache issue
  - Try on different device/simulator
  - Try after clearing DerivedData

**Step 3: Apply the specific fix** (30 min)
- Once you've identified view recreation: Use `.opacity()` instead of conditionals
- Once you've identified struct mutation: Use full reassignment
- Once you've verified it's cache: Nuke DerivedData properly

**Step 4: Verify 100% reliability** (until submission)
- Run the same interaction 30+ times
- Test on multiple devices/simulators
- Get QA to verify
- Only ship when it's 100% reproducible (not the bug, the FIX)

**Time cost**: 60 minutes diagnosis + 30 minutes fix + confidence = **submit at 9am**

**Cost of guessing**: 2 hours already + 3 more hours guessing + new bug introduced + crash reports post-launch + emergency patch + reputation damage = **miss launch + post-launch chaos**

**The decision principle**: Intermittent bugs require SYSTEMATIC diagnosis. The slower you go in diagnosis, the faster you get to the fix. Guessing is the fastest way to disaster.

**Professional script for co-leads who suggest guessing:**

> "I appreciate the suggestion. Adding @ObservedObject everywhere is treating the symptom, not the root cause. The skill says intermittent bugs create NEW bugs when we guess. I need 60 minutes for systematic diagnosis. If I can't find the root cause by then, we'll disable the feature and ship a clean v1.1. The math shows we have time—I can complete diagnosis, fix, AND verification before the deadline."

---

### Scenario 3: "Layout looks wrong on iPad, we're out of time"

**Red flags you might think:**
- "Add some padding and magic numbers"
- "It's probably a safe area thing, let me just ignore it"
- "Let's lock this to iPhone only"
- "GeometryReader will solve this"

**The danger**: Magic numbers break on other sizes. SafeArea ignoring is often wrong. Locking to iPhone means you ship a broken iPad experience.

**What to do instead** (3-minute diagnosis):
1. Run in simulator or device
2. Use Debug View Hierarchy: Debug menu → View Hierarchy (takes 30 seconds to load)
3. Check: Is the problem SafeArea, ZStack ordering, or GeometryReader sizing?
4. Use the correct pattern from the Quick Reference above

**Time cost**: 3 minutes diagnosis + 5 minutes fix = **8 minutes total**

**Cost of magic numbers**: Ship wrong, report 2 weeks later, debug 4 hours, patch in update = **2+ weeks delay**

---

## Quick Reference

### Common View Update Fixes

```swift
// Fix 1: Reassign the full struct
@State var items: [String] = []
var newItems = items
newItems.append("new")
self.items = newItems

// Fix 2: Pass binding correctly
@State var value = ""
ChildView(text: $value)  // Pass binding, not value

// Fix 3: Preserve view identity
View().opacity(isVisible ? 1 : 0)  // Not: if isVisible { View() }

// Fix 4: Observe the object
@StateObject var model = MyModel()
@ObservedObject var model: MyModel
```

### Common Preview Fixes

```swift
// Fix 1: Provide dependencies
#Preview {
    ContentView()
        .environmentObject(AppModel())
}

// Fix 2: Safe defaults
@State var index = 0  // Not 10, if array has 3 items

// Fix 3: Nuke cache
// Terminal: rm -rf ~/Library/Developer/Xcode/DerivedData
```

### Common Layout Fixes

```swift
// Fix 1: Z-order
Rectangle().zIndex(1)

// Fix 2: Constrain GeometryReader
GeometryReader { geo in ... }.frame(height: 100)

// Fix 3: SafeArea
ZStack { ... }.ignoresSafeArea()

// Fix 4: Modifier order
Text().cornerRadius(8).padding()  // Corners first
```

## Real-World Examples

### Example 1: List Item Doesn't Update When Tapped

**Scenario**: You have a list of tasks. When you tap a task to mark it complete, the checkmark should appear, but it doesn't.

**Code**:
```swift
struct TaskListView: View {
    @State var tasks: [Task] = [...]

    var body: some View {
        List {
            ForEach(tasks, id: \.id) { task in
                HStack {
                    Image(systemName: task.isComplete ? "checkmark.circle.fill" : "circle")
                    Text(task.title)
                    Spacer()
                    Button("Done") {
                        // ❌ WRONG: Direct mutation
                        task.isComplete.toggle()
                    }
                }
            }
        }
    }
}
```

**Diagnosis using the skill**:
1. Can you reproduce in preview? YES
2. Are you modifying the struct directly? YES → **Struct Mutation** (Root Cause 1)

**Fix**:
```swift
Button("Done") {
    // ✅ RIGHT: Full reassignment
    if let index = tasks.firstIndex(where: { $0.id == task.id }) {
        tasks[index].isComplete.toggle()
    }
}
```

**Why this works**: SwiftUI detects the array reassignment, triggering a redraw. The task in the List updates.

---

### Example 2: Preview Crashes with "No Such Module"

**Scenario**: You created a custom data model. It works fine in the app, but the preview crashes with "Cannot find 'CustomModel' in scope".

**Code**:
```swift
import SwiftUI

// ❌ WRONG: Preview missing the dependency
#Preview {
    TaskDetailView(task: Task(...))
}

struct TaskDetailView: View {
    @Environment(\.modelContext) var modelContext
    let task: Task  // Custom model

    var body: some View {
        Text(task.title)
    }
}
```

**Diagnosis using the skill**:
1. What's the error? "Cannot find in scope" → **Missing Dependency** (Error Type 1)
2. What does TaskDetailView need? The Task model and modelContext

**Fix**:
```swift
#Preview {
    let config = ModelConfiguration(isStoredInMemoryOnly: true)
    let container = try! ModelContainer(for: Task.self, configurations: config)

    return TaskDetailView(task: Task(title: "Sample"))
        .modelContainer(container)
}
```

**Why this works**: Providing the environment object and model container satisfies the view's dependencies. Preview loads successfully.

---

### Example 3: Text Field Value Changes Don't Appear

**Scenario**: You have a search field. You type characters, but the text doesn't appear in the UI. However, the search results DO update.

**Code**:
```swift
struct SearchView: View {
    @State var searchText = ""

    var body: some View {
        VStack {
            // ❌ WRONG: Passing constant binding
            TextField("Search", text: .constant(searchText))

            Text("Results for: \(searchText)")  // This updates
            List {
                ForEach(results(for: searchText), id: \.self) { result in
                    Text(result)
                }
            }
        }
    }

    func results(for text: String) -> [String] {
        // Returns filtered results
    }
}
```

**Diagnosis using the skill**:
1. Can you reproduce in preview? YES
2. Are you passing a binding to a child view? YES (TextField)
3. Is it a constant binding? YES → **Lost Binding Identity** (Root Cause 2)

**Fix**:
```swift
// ✅ RIGHT: Pass the actual binding
TextField("Search", text: $searchText)
```

**Why this works**: `$searchText` passes a two-way binding. TextField writes changes back to @State, triggering a redraw. Text field now shows typed characters.

---

## External Resources

**Apple Documentation:**
- [SwiftUI View Fundamentals](https://developer.apple.com/documentation/swiftui)
- [State and Data Flow](https://developer.apple.com/documentation/swiftui/state-and-data-flow)
- [Xcode Previews](https://developer.apple.com/documentation/xcode/previews)

**Related Axiom Skills:**
- `xcode-debugging` – For Xcode cache corruption, build issues
- `swift-concurrency` – For @MainActor and async/await patterns

## Version History

- **1.0.0**: Initial skill covering view update diagnostics (struct mutation, binding identity, view recreation, missing observer), preview crash decision trees (missing dependencies, state init, cache corruption), layout quick reference (ZStack, GeometryReader, SafeArea, frame/fixedSize, modifier order), and pressure scenarios for common shortcuts
- **1.1.0**: Added Scenario 2b (intermittent updates - 60-minute systematic diagnosis protocol with 4-step framework), extended pressure scenario for App Store Review deadline, added professional push-back script for co-leads suggesting shortcuts, verified under maximum pressure (App Store submission deadlines, cannot reproduce consistently, authority pressure from co-leads)
- **1.2.0**: Added 3 real-world examples (List item doesn't update when tapped, Preview crashes with missing dependencies, TextField value changes don't appear) demonstrating struct mutation, missing dependencies, and binding identity issues with complete diagnosis workflows

---

**Created:** 2025-11-30
**Targets:** iOS 14+, Swift 5.5+
**Framework:** SwiftUI

