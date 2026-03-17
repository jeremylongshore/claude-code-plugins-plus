# iOS Human Interface Guidelines -- Implementation Guide

## Overview

Apply Apple's iOS HIG principles to design and audit native iOS and web applications for clarity, deference, and depth.

## Three Core iOS Design Values

### 1. Clarity

Text is legible, icons are precise, interactions are intuitive.

```markdown
## Clarity Audit Checklist

Typography:
- [ ] Minimum body text: 17pt (system default)
- [ ] Using Dynamic Type scaling (respects user accessibility settings)
- [ ] SF Pro / SF Compact (or system font) for UI text
- [ ] Sufficient contrast: 4.5:1 minimum (7:1 for AAA)

Icons:
- [ ] Using SF Symbols where possible (automatically scaled)
- [ ] Icons have clear single meaning
- [ ] Touch targets >= 44x44pt

Layout:
- [ ] Safe area insets respected (notch, home indicator)
- [ ] Content not obscured by system UI
```

### 2. Deference

The UI serves the content. Interface is secondary to the experience.

```markdown
## Deference Patterns

Use translucency to maintain context:
- Navigation bars: UIBlurEffect over content
- Tab bars: Frosted glass separates content layers

Avoid:
- Heavy chrome competing with content
- Excessive gradients and shadows
- Animations that distract from the task
```

### 3. Depth

Layers communicate hierarchy and context.

```markdown
## Depth Implementation

System layers (bottom to top):
1. Base layer (primary content)
2. Modals / sheets
3. Popovers
4. Alerts / critical dialogs

SwiftUI sheet presentation:
- .sheet() for non-critical secondary views
- .fullScreenCover() for immersive experiences
- .popover() for iPad contextual options only
```

## Navigation Patterns

```swift
// Tab-based navigation (max 5 tabs)
TabView {
    HomeView()
        .tabItem { Label("Home", systemImage: "house") }
    SearchView()
        .tabItem { Label("Search", systemImage: "magnifyingglass") }
    ProfileView()
        .tabItem { Label("Profile", systemImage: "person") }
}

// Navigation stack (drill-down hierarchy)
NavigationStack {
    List(items) { item in
        NavigationLink(item.title) {
            DetailView(item: item)
        }
    }
    .navigationTitle("My Items")
}
```

## iOS HIG Compliance Checklist

```markdown
Navigation:
- [ ] Back button label is the previous screen title (not "Back")
- [ ] No more than 5 tab bar items
- [ ] Navigation bar title is concise (1-2 words)

Gestures:
- [ ] Swipe back gesture works (not blocked by custom gesture recognizers)
- [ ] Pull-to-refresh available on scrollable lists
- [ ] Long press reveals context menu (not a separate button)

Accessibility:
- [ ] VoiceOver labels set for all custom views
- [ ] Dynamic Type tested at all sizes
- [ ] Haptic feedback used for confirmations
- [ ] Dark Mode supported

Controls:
- [ ] Using system buttons (not custom-styled beyond guidelines)
- [ ] Destructive actions use red tint
- [ ] Primary action is prominently placed (bottom of screen, right side)
```

## References

- [Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/)
- [SF Symbols](https://developer.apple.com/sf-symbols/)
- [SwiftUI Documentation](https://developer.apple.com/xcode/swiftui/)
