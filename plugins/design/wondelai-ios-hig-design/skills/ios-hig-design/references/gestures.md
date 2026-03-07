# iOS Gestures & Interactions

## Standard Gestures (Never Override)

| Gesture | Standard Action |
|---------|-----------------|
| Swipe right from left edge | Navigate back |
| Swipe down on modal | Dismiss modal |
| Pull down on list | Refresh content |
| Swipe left on row | Reveal actions (delete, etc.) |
| Pinch | Zoom in/out |
| Long press | Context menu |

## Haptic Feedback

Provide tactile feedback for meaningful interactions:

```swift
// Impact feedback (physical actions)
let impact = UIImpactFeedbackGenerator(style: .medium)
impact.impactOccurred()

// Notification feedback (outcomes)
let notification = UINotificationFeedbackGenerator()
notification.notificationOccurred(.success)  // or .warning, .error

// Selection feedback (UI changes)
let selection = UISelectionFeedbackGenerator()
selection.selectionChanged()
```

## Animation Guidelines

- Use spring animations for natural, bouncy feel
- Respect `reduceMotion` accessibility setting
- Keep animations brief and purposeful

```swift
@Environment(\.accessibilityReduceMotion) var reduceMotion

var animation: Animation {
    reduceMotion ? .none : .spring()
}

withAnimation(animation) {
    // Animate property changes
}
```
