# SwiftUI Debugging

Diagnostic decision trees for SwiftUI view updates, preview crashes, and layout issues with 3 real-world examples.

**When to use**: View doesn't update, preview crashes, layout looks wrong, intermittent rendering issues

## Key Features

- **View Not Updating Decision Tree** – 4-step diagnostic to identify struct mutation, binding identity loss, accidental view recreation, or missing observer pattern
- **Preview Crashes Decision Tree** – 3-branch diagnostic for missing dependencies, state initialization failures, or Xcode cache corruption
- **Layout Issues Quick Reference** – ZStack ordering, GeometryReader sizing, SafeArea, frame/fixedSize, modifier order
- **Real-World Examples** (3 complete workflows):
  - List item doesn't update when tapped (struct mutation diagnosis)
  - Preview crashes with "No Such Module" (missing dependency diagnosis)
  - TextField value changes don't appear (binding identity diagnosis)
- **Pressure Scenarios** – Intermittent bugs under App Store Review deadline, co-lead authority pressure, professional push-back scripts

**Requirements**: Xcode 15+, iOS 14+

## Example Prompts

These are real questions developers ask that this skill answers:

- **"List item doesn't update even though the data changed."**
  → Demonstrates struct mutation diagnosis with SwiftUI update cycle

- **"Preview keeps crashing with mysterious dependency errors."**
  → Covers preview crash decision tree: missing dependencies, state init failures, cache corruption

- **"TextField value changes don't appear on screen."**
  → Shows binding identity diagnosis and when to use @State vs @Binding correctly

- **"Layout looks wrong. Elements are in the wrong positions."**
  → Covers ZStack ordering, GeometryReader sizing, SafeArea, and modifier order issues

- **"I'm getting intermittent rendering glitches under deadline pressure."**
  → Provides systematic troubleshooting under App Store Review stress with professional push-back scripts

## Root Causes

### Struct Mutation
You're modifying a @State value directly instead of reassigning it. SwiftUI can't see the change.

```swift
// ❌ WRONG
@State var items: [String] = []
items.append("new")  // Direct mutation—SwiftUI doesn't see it

// ✅ RIGHT
@State var items: [String] = []
items.append("new")
self.items = items  // Reassignment triggers update
```

### Lost Binding Identity
You're passing `.constant()` or creating a new binding each render, breaking the two-way connection.

```swift
// ❌ WRONG
TextField("Search", text: .constant(searchText))

// ✅ RIGHT
TextField("Search", text: $searchText)
```

### Accidental View Recreation
The view moved into a conditional or changed identity, losing its @State and resetting to defaults.

```swift
// ❌ WRONG
if showCounter {
    Counter()  // New identity each time condition changes
}

// ✅ RIGHT
Counter().opacity(showCounter ? 1 : 0)  // Preserve identity
```

### Missing Observer
You're not using @StateObject or @ObservedObject, so SwiftUI doesn't watch for changes.

```swift
// ❌ WRONG
let model = MyModel()

// ✅ RIGHT
@StateObject var model = MyModel()
```

## Preview Crashes

### Missing Dependencies
```swift
// ❌ WRONG
#Preview {
    TaskDetailView(task: Task(...))
}

// ✅ RIGHT
#Preview {
    let config = ModelConfiguration(isStoredInMemoryOnly: true)
    let container = try! ModelContainer(for: Task.self, configurations: config)
    return TaskDetailView(task: Task(title: "Sample"))
        .modelContainer(container)
}
```

### State Initialization Failure
Check array bounds, optional unwraps, and default values.

### Cache Corruption
If preview worked yesterday and code hasn't changed:
1. Restart Preview Canvas: `Cmd+Option+P`
2. Restart Xcode
3. Nuke derived data: `rm -rf ~/Library/Developer/Xcode/DerivedData`

## Related Skills

- **xcode-debugging** – For Xcode cache corruption and build issues
- **swift-concurrency** – For @MainActor and async/await patterns
- **swiftui-performance** – For performance optimization with SwiftUI Instrument

## Quick Start

1. Can you reproduce in a minimal preview? YES → code issue; NO → cache/environment
2. Which root cause applies? Struct mutation → Lost binding → View recreation → Missing observer
3. Apply the specific fix for that cause
4. Verify in preview before shipping

**Key principle**: Start with observable symptoms, test systematically, eliminate causes one by one. Don't guess.

---

**Learn more**: See the full skill at `/skills/ui-design/swiftui-debugging` in Claude Code
