# iOS Navigation Patterns

## Tab Bar (Primary Navigation)

The tab bar provides access to main app destinations.

- **Position**: Bottom of screen, always visible (except modals/keyboards)
- **Items**: 2-5 tabs maximum
- **Overflow**: Use "More" tab if >5 destinations needed
- **Selected state**: Fill color indicates active tab
- **Labels**: 10-11pt SF text
- **Background**: Slightly translucent with background blur ("frosted glass")

**Behavior**:
- Each tab remembers its navigation state
- Tapping active tab returns to root screen of that tab
- Tab bar hidden during modals and keyboard display

## Navigation Bar (Contextual Navigation)

- **Back button**: Top-left, allows return to previous screen
- **Actions**: Top-right, context-specific actions
- **Title**: Center (scrolled state) or left-aligned large title (unscrolled)

**Scroll Behavior**:
- Large title collapses to compact centered title on scroll
- Search bar can move or hide on scroll
- Smooth animated transitions between states

## Navigating Back

| Method | Context |
|--------|---------|
| "Back" button (top-left) | Standard navigation |
| Swipe right from left edge | Standard navigation |
| "Cancel" / "Done" button | Modal views |
| Swipe down on content | Modals, fullscreen media |

## Modal Sheets

Use modals for focused tasks that shouldn't interrupt context completely.

- Slides up from bottom
- Previous screen visible (recessed) in background
- Dismiss via: close button, swipe down, or completing task

---

## Search UI Patterns

### Search Bar Placement

| Context | Placement |
|---------|-----------|
| Primary search (core feature) | Navigation bar, persistent |
| Secondary search | Below nav, hidden on scroll |
| List filtering | Above list, inline |

### Search Behavior

**States:**
1. **Inactive:** Placeholder text, magnifying glass icon
2. **Active/Focused:** Keyboard appears, cancel button shows
3. **Typing:** Results update (instant or debounced)
4. **Results:** Displayed in list below

**SwiftUI implementation:**
```swift
.searchable(
    text: $searchText,
    placement: .navigationBarDrawer(displayMode: .always),
    prompt: "Search items"
)
```

### Search Suggestions

- Recent searches
- Trending/popular searches
- Autocomplete suggestions
- Scoped suggestions (filter by category)

```swift
.searchable(text: $searchText) {
    ForEach(suggestions) { suggestion in
        Text(suggestion.name)
            .searchCompletion(suggestion.name)
    }
}
```

---

## Split View Navigation (iPad)

### Two-Column Layout

```
┌──────────────────┬────────────────────────────────┐
│                  │                                │
│  Primary List    │     Detail View                │
│  (Sidebar)       │                                │
│                  │                                │
│  Item 1          │     Selected item details      │
│  Item 2 ←        │                                │
│  Item 3          │                                │
│                  │                                │
└──────────────────┴────────────────────────────────┘
```

**Behavior:**
- Primary column: 320pt default width
- Detail column: Fills remaining space
- Collapse to single column on compact width

### Three-Column Layout

```
┌────────────┬────────────┬──────────────────────────┐
│  Sidebar   │ Content    │    Detail                │
│            │            │                          │
│  Section 1 │  Item A    │    Item details here     │
│  Section 2 │  Item B ←  │                          │
│  Section 3 │  Item C    │                          │
└────────────┴────────────┴──────────────────────────┘
```

**SwiftUI:**
```swift
NavigationSplitView {
    Sidebar()
} content: {
    ContentList()
} detail: {
    DetailView()
}
```

### Responsive Behavior

| Width | Behavior |
|-------|----------|
| Compact (iPhone) | Stack navigation |
| Regular (iPad portrait) | Two-column or overlay |
| Regular (iPad landscape) | Three-column available |

**Best practices:**
- Show placeholder in detail when nothing selected
- Remember selection across rotation
- Support column resizing (where appropriate)
