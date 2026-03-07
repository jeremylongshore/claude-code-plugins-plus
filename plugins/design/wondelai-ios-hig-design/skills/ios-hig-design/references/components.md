# iOS UI Components

## Buttons

**Page-level actions**: Appear in nav bar (top) or action bar (bottom)

```
┌─────────────────────────────────┐
│ Cancel              Save  Edit  │  ← Nav bar actions
├─────────────────────────────────┤
│                                 │
│         Page Content            │
│                                 │
├─────────────────────────────────┤
│   Share    Copy    Delete       │  ← Action bar
└─────────────────────────────────┘
```

**On-page buttons**: Often appear on cards or sections

- Primary buttons: Filled with theme color
- Secondary buttons: Outlined or text-only
- Destructive actions: Red text/color

## Lists (Table Views)

Lists are fundamental to iOS design. Configure each row with:

**Left side** (optional):
- Icon or image

**Center**:
- Primary text (17pt regular)
- Secondary text (15pt or 12pt, lighter color)
- Tertiary text (if needed)

**Right side** (choose one):
- Chevron (→) — navigates to detail screen
- Text + Chevron — shows current value, tappable to change
- Checkmark (✓) — single selection from list
- Switch — toggle on/off
- Text button — action link

## Input Controls

Most inputs are styled as list items:

**Text Input**:
```
┌─────────────────────────────────┐
│ Email                           │  ← Hint text disappears on typing
└─────────────────────────────────┘
```

**Switch**:
```
┌─────────────────────────────────┐
│ Notifications          [====○] │
└─────────────────────────────────┘
```

**Date/Time Picker**:
```
┌─────────────────────────────────┐
│ Date          [ Jan 15, 2025 ] │  ← Light gray button, expands inline
└─────────────────────────────────┘
```

**Picker Screen Pattern**:
- List item shows current value + chevron
- Tapping navigates to selection screen
- Selected option marked with checkmark

## Pull-Down Menus

For short option lists without navigation:

```swift
Menu("Options") {
    Button("Edit", action: edit)
    Button("Share", action: share)
    Divider()
    Button("Delete", role: .destructive, action: delete)
}
```

## Touch Targets & Spacing

### Minimum Touch Target

**44 × 44 points** — This is non-negotiable for all interactive elements.

```swift
Button("Tap") {
    // Action
}
.frame(minWidth: 44, minHeight: 44)
```

### Standard Spacing Values

| Spacing | Usage |
|---------|-------|
| 8pt | Tight spacing (related elements) |
| 16pt | Standard spacing (sections) |
| 20pt | Screen edge margins |
| 24pt | Loose spacing (major sections) |

```swift
VStack(spacing: 16) {
    // Standard component spacing
}
```

---

## Menu Patterns

### Context Menus

Long-press to reveal contextual actions:

```swift
Text("Item")
    .contextMenu {
        Button("Edit", action: edit)
        Button("Share", action: share)
        Divider()
        Button("Delete", role: .destructive, action: delete)
    }
```

**Guidelines:**
- Group related actions
- Use dividers between groups
- Destructive actions at bottom, marked red
- Include icons where helpful

### Pull-Down Menus

Tap to reveal options without navigation:

```swift
Menu("Options") {
    Button("Sort by Name", action: sortByName)
    Button("Sort by Date", action: sortByDate)
    Divider()
    Menu("Filter") {
        Button("Active", action: filterActive)
        Button("Completed", action: filterCompleted)
    }
}
```

**When to use:**
- 3-6 options that don't need full screen
- Actions that don't require additional input
- Sorting, filtering, view options

### Action Sheets

For important decisions requiring attention:

```swift
.confirmationDialog("Choose Action", isPresented: $showingSheet) {
    Button("Camera") { }
    Button("Photo Library") { }
    Button("Cancel", role: .cancel) { }
}
```

**Guidelines:**
- Title is optional (use for clarity)
- Limit to 5-6 actions
- Cancel is always last
- Destructive actions in red

---

## Confirmation Dialogs

### When to Confirm

| Action | Needs Confirmation? |
|--------|---------------------|
| Delete single item | Sometimes (if permanent) |
| Delete multiple items | Yes |
| Discard unsaved changes | Yes |
| Log out | Usually not |
| Send message | No |
| Purchase | Yes (final step) |

### Alert Structure

```swift
.alert("Delete Item?", isPresented: $showingAlert) {
    Button("Delete", role: .destructive, action: deleteItem)
    Button("Cancel", role: .cancel) { }
} message: {
    Text("This action cannot be undone.")
}
```

**Guidelines:**
- Title: Clear action question
- Message: Explain consequences (brief)
- Buttons: Specific verbs, not just "OK"
- Destructive button on left (less expected position)
- Cancel on right (easy to tap)

### Undo vs. Confirm

**Prefer undo when:**
- Action is recoverable
- Speed matters
- Confirmations would be annoying

**Require confirmation when:**
- Action is irreversible
- Data/money loss possible
- Action affects others

```swift
// Undo pattern
.toolbar {
    Button("Undo") { undoManager.undo() }
}

// Swipe to delete with undo toast
.swipeActions(edge: .trailing) {
    Button("Delete", role: .destructive) {
        withAnimation {
            deleteWithUndo(item)
        }
    }
}
```
