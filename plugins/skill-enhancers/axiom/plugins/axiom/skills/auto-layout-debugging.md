---
name: auto-layout-debugging
description: Use when encountering "Unable to simultaneously satisfy constraints" errors, constraint conflicts, ambiguous layout warnings, or views positioned incorrectly - systematic debugging workflow for Auto Layout issues in iOS
version: 1.0.0
---

# Auto Layout Debugging

## When to Use This Skill

Use when:
- Seeing "Unable to simultaneously satisfy constraints" errors in console
- Views positioned incorrectly or not appearing
- Constraint warnings during app launch or navigation
- Ambiguous layout errors
- Views appearing at unexpected sizes
- Debug View Hierarchy shows misaligned views
- Storyboard/XIB constraints behaving differently at runtime

## Overview

**Core Principle**: Auto Layout constraint errors follow predictable patterns. Systematic debugging with proper tools identifies issues in minutes instead of hours.

**Time Savings**: Typical constraint debugging without this workflow: 30-60 minutes. With systematic approach: 5-10 minutes.

---

## Quick Decision Tree

```
Constraint error in console?
├─ Can't identify which views?
│  └─ Use Symbolic Breakpoint + Memory Address Identification
├─ Constraint conflicts shown?
│  └─ Use Constraint Priority Resolution
├─ Ambiguous layout (multiple solutions)?
│  └─ Use _autolayoutTrace to find missing constraints
└─ Views positioned incorrectly but no errors?
   └─ Use Debug View Hierarchy + Show Constraints
```

---

## Understanding Constraint Error Messages

### Anatomy of Error Message

```
Unable to simultaneously satisfy constraints.
Probably at least one of the constraints in the following list you don't need.

(
    "<NSLayoutConstraint:0x7f8b9c6...  'UIView-Encapsulated-Layout-Width' ... (active)>",
    "<NSLayoutConstraint:0x7f8b9c5...  UILabel:0x7f8b9c4... .width == 300   (active)>",
    "<NSLayoutConstraint:0x7f8b9c3...  UILabel:0x7f8b9c4... .leading == ... + 20   (active)>",
    "<NSLayoutConstraint:0x7f8b9c2...  ... .trailing == UILabel:0x7f8b9c4... .trailing + 20   (active)>"
)

Will attempt to recover by breaking constraint
<NSLayoutConstraint:0x7f8b9c5... UILabel:0x7f8b9c4... .width == 300   (active)>
```

**Key Components**:
1. **Memory addresses** - `0x7f8b9c4...` identifies views and constraints
2. **Visual Format** - Human-readable constraint description
3. **`(active)` status** - Constraint is currently enforced
4. **Recovery action** - Which constraint system will break (usually lowest priority)

### System-Generated Constraints

**UIView-Encapsulated-Layout-Width/Height**:
- Created by UIKit for cells, system views
- Often source of conflicts
- Usually correct; your constraints are the problem

**Autoresizing Mask Constraints**:
- Format: `h=--&` or `v=&--`
- `-` = fixed dimension
- `&` = flexible dimension
- Example: `h=--&` = fixed left margin and width, flexible right margin

---

## Debugging Workflow

### Step 1: Set Up Symbolic Breakpoint (One-Time Setup)

**Purpose**: Break when constraint conflict occurs, before system breaks constraint.

**Setup**:
1. Open Breakpoint Navigator (⌘+7 or ⌘+8)
2. Click `+` → "Symbolic Breakpoint"
3. **Symbol**: `UIViewAlertForUnsatisfiableConstraints`
4. (Optional) Add **Action** → "Sound" → select sound
5. (Optional) Check "Automatically continue after evaluating actions"

**Why this works**: Pauses execution at exact moment of constraint conflict, giving you debugger access to all views and constraints.

---

### Step 2: Identify Views from Memory Addresses

When breakpoint hits, console shows memory addresses like `UILabel:0x7f8b9c4...`

#### Technique 1: Use %rbx Register (When Breakpoint Hits)

```lldb
# Print all involved views and constraints
po $arg1

# Or on older Xcode versions
po $rbx
```

**Output**: NSArray containing all conflicting constraints and affected views.

#### Technique 2: Set View Background Color

```lldb
# Set background color on suspected view
expr ((UIView *)0x7f8b9c4...).backgroundColor = [UIColor redColor]

# Continue execution to see which view turned red
```

**Result**: Visually identifies which view corresponds to memory address.

#### Technique 3: Print View Hierarchy

**Objective-C projects**:
```lldb
po [[UIWindow keyWindow] _autolayoutTrace]
```

**Swift projects**:
```lldb
expr -l objc++ -O -- [[UIWindow keyWindow] _autolayoutTrace]
```

**Output**: Entire view hierarchy with `*` marking ambiguous layouts.

**Example**:
```
*<UIView:0x7f8b9c4...>
|   <UILabel:0x7f8b9c3...>
```

The `*` indicates this UIView has ambiguous constraints.

#### Technique 4: Print Constraints for Specific View

```lldb
# Horizontal constraints (axis: 0)
po [0x7f8b9c4... constraintsAffectingLayoutForAxis:0]

# Vertical constraints (axis: 1)
po [0x7f8b9c4... constraintsAffectingLayoutForAxis:1]
```

**Output**: All constraints affecting that view's layout.

---

### Step 3: Use Debug View Hierarchy

**When to use**: Views positioned incorrectly, constraints not visible in code.

**Workflow**:
1. **Trigger the issue** - Navigate to screen with constraint problems
2. **Pause execution** - Click "Debug View Hierarchy" button in debug bar (or Debug → View Debugging → Capture View Hierarchy)
3. **Inspect 3D view** - Rotate view hierarchy to see layering
4. **Enable "Show Constraints"** - Shows all constraints as lines
5. **Select view** - Right panel shows all constraints affecting selected view

**Key Features**:
- **Show Clipped Content** - Reveals views positioned off-screen
- **Show Constraints** - Visualizes constraint relationships
- **Filter Bar** - Search for specific views by class or memory address

**Finding Issues**:
- Purple constraints = satisfied
- Orange/red constraints = conflicts
- Select constraint → see both views it connects

---

### Step 4: Name Your Constraints (Prevention)

**Why**: Makes error messages readable instead of cryptic memory addresses.

#### In Interface Builder (Storyboards/XIBs)

1. Select constraint in Document Outline
2. Open Attributes Inspector
3. Set **Identifier** field (e.g., "ProfileImageWidthConstraint")

**Before**:
```
<NSLayoutConstraint:0x7f8b9c5... UILabel:0x7f8b9c4... .width == 300   (active)>
```

**After**:
```
<NSLayoutConstraint:0x7f8b9c5... 'ProfileImageWidthConstraint' UILabel:0x7f8b9c4... .width == 300   (active)>
```

#### Programmatically

```swift
let widthConstraint = imageView.widthAnchor.constraint(equalToConstant: 100)
widthConstraint.identifier = "ProfileImageWidthConstraint"
widthConstraint.isActive = true
```

**Impact**: Instantly know which constraint is breaking without hunting through code.

---

### Step 5: Name Your Views (Prevention)

**Why**: Error messages show view class AND your custom label.

#### In Interface Builder

1. Select view in Document Outline
2. Open Identity Inspector
3. Set **Label** field (e.g., "Profile Image View")

**Before**:
```
<UIImageView:0x7f8b9c4... (active)>
```

**After**:
```
<UIImageView:0x7f8b9c4... 'Profile Image View' (active)>
```

#### Programmatically

```swift
imageView.accessibilityIdentifier = "ProfileImageView"
```

**Note**: Xcode automatically uses textual components (UILabel text, UIButton titles) as identifiers when available.

---

## Common Constraint Conflict Patterns

### Pattern 1: Conflicting Fixed Widths

**Symptom**:
```
Container width: 375
Child width: 300
Child leading: 20
Child trailing: 20
// 20 + 300 + 20 = 340 ≠ 375
```

**❌ WRONG**:
```swift
// Conflicting constraints
imageView.widthAnchor.constraint(equalToConstant: 300).isActive = true
imageView.leadingAnchor.constraint(equalTo: view.leadingAnchor, constant: 20).isActive = true
imageView.trailingAnchor.constraint(equalTo: view.trailingAnchor, constant: -20).isActive = true
// Over-constrained: width + leading + trailing = 3 horizontal constraints (only need 2)
```

**✅ CORRECT Option 1** (Remove fixed width):
```swift
// Let width be calculated from leading + trailing
imageView.leadingAnchor.constraint(equalTo: view.leadingAnchor, constant: 20).isActive = true
imageView.trailingAnchor.constraint(equalTo: view.trailingAnchor, constant: -20).isActive = true
// Width will be container width - 40
```

**✅ CORRECT Option 2** (Use priorities):
```swift
let widthConstraint = imageView.widthAnchor.constraint(equalToConstant: 300)
widthConstraint.priority = .defaultHigh // 750 (can be broken if needed)
widthConstraint.isActive = true

imageView.leadingAnchor.constraint(equalTo: view.leadingAnchor, constant: 20).isActive = true
imageView.trailingAnchor.constraint(equalTo: view.trailingAnchor, constant: -20).isActive = true
// Required constraints (1000) will break lower-priority width constraint if needed
```

---

### Pattern 2: UIView-Encapsulated-Layout Conflicts

**Symptom**: Table cells or collection view cells conflicting with `UIView-Encapsulated-Layout-Width`.

**Why it happens**: System sets cell width based on table/collection view. Your constraints fight it.

**❌ WRONG**:
```swift
// In UITableViewCell
contentLabel.widthAnchor.constraint(equalToConstant: 320).isActive = true
// Conflicts with system-determined cell width
```

**✅ CORRECT**:
```swift
// Use relative constraints, not fixed widths
contentLabel.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16).isActive = true
contentLabel.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16).isActive = true
// Width adapts to cell width automatically
```

---

### Pattern 3: Autoresizing Mask Conflicts

**Symptom**: Mixing Auto Layout with `autoresizingMask` or not setting `translatesAutoresizingMaskIntoConstraints = false`.

**❌ WRONG**:
```swift
let imageView = UIImageView()
view.addSubview(imageView)

// Forgot to disable autoresizing mask
imageView.widthAnchor.constraint(equalToConstant: 100).isActive = true
// Conflicts with autoresizing mask constraints
```

**✅ CORRECT**:
```swift
let imageView = UIImageView()
imageView.translatesAutoresizingMaskIntoConstraints = false // ← CRITICAL
view.addSubview(imageView)

imageView.widthAnchor.constraint(equalToConstant: 100).isActive = true
```

**Why**: `translatesAutoresizingMaskIntoConstraints = true` creates automatic constraints that conflict with your explicit constraints.

---

### Pattern 4: Ambiguous Layout (Missing Constraints)

**Symptom**: View appears, but position shifts unexpectedly or `_autolayoutTrace` shows `*` (ambiguous).

**Problem**: Not enough constraints to determine unique position/size.

**❌ WRONG** (Ambiguous X position):
```swift
imageView.topAnchor.constraint(equalTo: view.topAnchor, constant: 20).isActive = true
imageView.widthAnchor.constraint(equalToConstant: 100).isActive = true
imageView.heightAnchor.constraint(equalToConstant: 100).isActive = true
// Missing: horizontal position (leading/trailing/centerX)
```

**✅ CORRECT**:
```swift
imageView.topAnchor.constraint(equalTo: view.topAnchor, constant: 20).isActive = true
imageView.centerXAnchor.constraint(equalTo: view.centerXAnchor).isActive = true // ← Added
imageView.widthAnchor.constraint(equalToConstant: 100).isActive = true
imageView.heightAnchor.constraint(equalToConstant: 100).isActive = true
```

**Rule**: Every view needs:
- **Horizontal**: 2 constraints (e.g., leading + width, OR leading + trailing, OR centerX + width)
- **Vertical**: 2 constraints (e.g., top + height, OR top + bottom, OR centerY + height)

---

### Pattern 5: Priority Conflicts

**Symptom**: Unexpected constraint breaks, but all constraints seem correct.

**Problem**: Multiple constraints at same priority competing.

**❌ WRONG**:
```swift
// Both required (priority 1000)
imageView.widthAnchor.constraint(equalToConstant: 100).isActive = true
imageView.widthAnchor.constraint(greaterThanOrEqualToConstant: 150).isActive = true
// Impossible: width can't be 100 AND >= 150
```

**✅ CORRECT**:
```swift
let preferredWidth = imageView.widthAnchor.constraint(equalToConstant: 100)
preferredWidth.priority = .defaultHigh // 750
preferredWidth.isActive = true

let minWidth = imageView.widthAnchor.constraint(greaterThanOrEqualToConstant: 150)
minWidth.priority = .required // 1000
minWidth.isActive = true

// Result: width will be 150 (required constraint wins)
```

**Priority levels** (higher = stronger):
- `.required` (1000) - Must be satisfied
- `.defaultHigh` (750) - Strong preference
- `.defaultLow` (250) - Weak preference
- Custom: any value 1-999

---

## Debugging Checklist

### Before Debugging
- [ ] Read full error message in console (don't ignore it)
- [ ] Note which constraints are listed as conflicting
- [ ] Check if error is consistent or intermittent

### During Debugging
- [ ] Set symbolic breakpoint at UIViewAlertForUnsatisfiableConstraints
- [ ] Identify views using memory addresses (background color technique)
- [ ] Use Debug View Hierarchy to visualize constraints
- [ ] Check _autolayoutTrace for ambiguous layouts
- [ ] Verify translatesAutoresizingMaskIntoConstraints = false for programmatic views

### After Fixing
- [ ] Test on multiple device sizes (iPhone SE, iPhone Pro Max)
- [ ] Test orientation changes (portrait/landscape)
- [ ] Test with Dynamic Type sizes
- [ ] Verify no console warnings during transitions
- [ ] Add constraint identifiers for future debugging

---

## Advanced Techniques

### Constraint Priority Strategy

**Use case**: View that should be certain size, but can shrink if needed.

```swift
// Preferred size: 200x200
let widthConstraint = imageView.widthAnchor.constraint(equalToConstant: 200)
widthConstraint.priority = .defaultHigh // 750
widthConstraint.isActive = true

let heightConstraint = imageView.heightAnchor.constraint(equalToConstant: 200)
heightConstraint.priority = .defaultHigh // 750
heightConstraint.isActive = true

// But never smaller than 100x100
imageView.widthAnchor.constraint(greaterThanOrEqualToConstant: 100).isActive = true
imageView.heightAnchor.constraint(greaterThanOrEqualToConstant: 100).isActive = true

// And never larger than container
imageView.widthAnchor.constraint(lessThanOrEqualTo: containerView.widthAnchor).isActive = true
imageView.heightAnchor.constraint(lessThanOrEqualTo: containerView.heightAnchor).isActive = true
```

**Result**: Image is 200x200 when space available, shrinks to fit container (min 100x100).

---

### Content Hugging and Compression Resistance

**Content Hugging** (resist expanding):
```swift
// Label should not stretch beyond its text width
label.setContentHuggingPriority(.defaultHigh, for: .horizontal)
```

**Compression Resistance** (resist shrinking):
```swift
// Label should not truncate if possible
label.setContentCompressionResistancePriority(.required, for: .horizontal)
```

**Common pattern**:
```swift
// In horizontal stack: priorityLabel (hugs) + spacer + valueLabel (hugs)
priorityLabel.setContentHuggingPriority(.defaultHigh, for: .horizontal)
valueLabel.setContentHuggingPriority(.defaultHigh, for: .horizontal)

// Spacer fills remaining space (low hugging priority)
spacerView.setContentHuggingPriority(.defaultLow, for: .horizontal)
```

---

### Debugging Transformed Views

**Problem**: View transformations (rotate, scale) don't affect Auto Layout.

**Gotcha**:
```swift
imageView.transform = CGAffineTransform(rotationAngle: .pi / 4) // 45° rotation
// Auto Layout still uses original (un-rotated) frame for calculations
```

**Solution**: Auto Layout works correctly, but visual debugging can be confusing. Use original frame for constraint debugging.

---

## Troubleshooting

### Issue: Breakpoint Never Hits

**Check**:
1. Symbolic breakpoint symbol is exactly `UIViewAlertForUnsatisfiableConstraints`
2. Breakpoint is enabled (checkmark visible)
3. Constraint conflict actually exists (check console for error message)

---

### Issue: Can't Identify View from Memory Address

**Solution 1**: Use background color technique
```lldb
expr ((UIView *)0x7f8b9c4...).backgroundColor = [UIColor redColor]
continue
```

**Solution 2**: Print recursive description
```lldb
po [0x7f8b9c4... recursiveDescription]
```

**Solution 3**: Check view's class
```lldb
po [0x7f8b9c4... class]
```

---

### Issue: Debug View Hierarchy Shows No Constraints

**Check**:
1. Click "Show Constraints" button in debug bar (looks like constraint icon)
2. Select specific view to see its constraints in right panel
3. Constraints may be satisfied (purple) vs conflicting (orange/red)

---

### Issue: Constraints Change at Runtime

**Check**:
1. UIKit system constraints (UIView-Encapsulated-Layout) added for cells/system views
2. Dynamic Type changes (font size changes = size invalidation)
3. Orientation changes triggering new constraints
4. View controller lifecycle (viewDidLoad vs viewWillLayoutSubviews)

---

## Common Mistakes

### ❌ Ignoring Console Warnings

**Wrong**: Seeing constraint warning, continuing anyway.

**Correct**: Fix every constraint warning immediately. They compound and cause unpredictable layout later.

---

### ❌ Not Setting Identifiers

**Wrong**: Debugging constraints by memory address.

**Correct**: Always set constraint identifiers. 30 seconds now saves 30 minutes later.

---

### ❌ Over-Constraining

**Wrong**: Setting leading + trailing + width.

**Correct**: Use 2 of 3 (leading + trailing, OR leading + width, OR trailing + width).

---

### ❌ Mixing Auto Layout and Frames

**Wrong**:
```swift
imageView.frame = CGRect(x: 50, y: 50, width: 100, height: 100) // Manual frame
imageView.widthAnchor.constraint(equalToConstant: 100).isActive = true // Auto Layout
```

**Correct**: Choose one approach. If using Auto Layout, set `translatesAutoresizingMaskIntoConstraints = false` and let constraints determine position/size.

---

## Real-World Impact

**Before** (no systematic approach):
- 30-60 minutes per constraint conflict
- Trial-and-error constraint changes
- Frustration from cryptic error messages
- Breaking working constraints to fix new ones

**After** (systematic debugging):
- 5-10 minutes per constraint conflict
- Targeted fixes with Debug View Hierarchy
- Named constraints = instant identification
- Symbolic breakpoint catches issues immediately

---

## Related Skills

- For Xcode environment issues: See `xcode-debugging` skill
- For SwiftUI layout issues: See `swiftui-performance` skill
- For testing UI: See `ui-testing` skill

---

## References

- [Apple Auto Layout Guide - Debugging](https://developer.apple.com/library/archive/documentation/UserExperience/Conceptual/AutolayoutPG/DebuggingTricksandTips.html)
- [Stack Overflow - UIViewAlertForUnsatisfiableConstraints](https://stackoverflow.com/questions/26389273/how-to-trap-on-uiviewalertforunsatisfiableconstraints)
- [Auto Layout Debugging in Swift](https://medium.com/ios-os-x-development/auto-layout-debugging-in-swift-93bcd21a4abf)

---

## Key Takeaways

1. **Name everything** - Constraints and views with identifiers save hours of debugging
2. **Use symbolic breakpoint** - Catch constraint conflicts at source, not after recovery
3. **Debug View Hierarchy** - Visualize constraints instead of guessing
4. **Memory address → View** - Background color technique instantly identifies mystery views
5. **Two constraints per axis** - Avoid over-constraining (leading + trailing + width = conflict)
6. **Priorities matter** - Use .required (1000) for must-haves, .defaultHigh (750) for preferences
7. **Systematic wins** - Following workflow saves 30-50 minutes per conflict

---

**Last Updated**: 2024
**Minimum Requirements**: Xcode 12+, iOS 11+ (symbolic breakpoints work on all versions)
