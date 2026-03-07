# iOS System Integration

Siri, Shortcuts, Handoff, drag and drop, and other system-level integrations.

## Siri Integration

### SiriKit Domains

Your app can integrate with Siri through predefined domains:

| Domain | Example Intents |
|--------|-----------------|
| Messaging | Send message, search messages |
| Lists & Notes | Create note, add to list |
| Payments | Send payment, request payment |
| Workouts | Start workout, end workout |
| Media | Play media, add to library |
| Ride booking | Request ride, get ride status |
| Car commands | Lock car, get car status |
| Visual codes | Look up barcode, QR code |

### Designing for Voice

**Confirmation dialogs:**
```
Siri: "Send $50 to Sarah for dinner?"
User: "Yes" / "Change amount" / "Cancel"
```

**Guidelines:**
- Confirm significant actions
- Allow easy correction
- Provide visual feedback alongside voice
- Handle ambiguity gracefully

### Custom Intents

For actions not in predefined domains:

```swift
// Define in Intents.intentdefinition
Intent: OrderCoffee
Parameters: coffeeType, size, location
```

**Best practices:**
- Use descriptive parameter names
- Provide good examples
- Support synonyms
- Test with various phrasings

### Siri Shortcuts

Allow users to create custom voice triggers:

```swift
// Donate shortcut when user completes action
let activity = NSUserActivity(activityType: "com.app.order-favorite")
activity.title = "Order my usual coffee"
activity.isEligibleForSearch = true
activity.isEligibleForPrediction = true
activity.suggestedInvocationPhrase = "Order my usual"

view.userActivity = activity
```

**Guidelines:**
- Donate shortcuts for repeated actions
- Suggest clear invocation phrases
- Provide relevant parameters
- Test in Shortcuts app

---

## Shortcuts App Integration

### App Shortcuts (iOS 16+)

Pre-built shortcuts that appear automatically:

```swift
struct MyAppShortcuts: AppShortcutsProvider {
    static var appShortcuts: [AppShortcut] {
        AppShortcut(
            intent: OrderCoffeeIntent(),
            phrases: [
                "Order coffee with \(.applicationName)",
                "Get my usual from \(.applicationName)"
            ],
            shortTitle: "Order Coffee",
            systemImageName: "cup.and.saucer.fill"
        )
    }
}
```

### Shortcut Actions

Expose app functionality as Shortcuts actions:

**Good candidates:**
- Actions users repeat frequently
- Actions that can run without UI
- Data that can be passed to other apps
- Automatable workflows

**Design considerations:**
- Clear action names (verb + object)
- Meaningful parameters with defaults
- Useful outputs for chaining
- Error messages that explain what went wrong

---

## Handoff

### Enabling Handoff

Allow users to continue activities across Apple devices:

```swift
let activity = NSUserActivity(activityType: "com.app.viewing-item")
activity.title = "Viewing Product: \(product.name)"
activity.userInfo = ["productID": product.id]
activity.isEligibleForHandoff = true
activity.webpageURL = URL(string: "https://myapp.com/product/\(product.id)")

userActivity = activity
```

### Handoff Guidelines

**Do:**
- Continue at exactly where user left off
- Restore scroll position, form state, etc.
- Support universal links as fallback
- Update activity as context changes

**Don't:**
- Require re-authentication
- Lose user's work
- Show significantly different content

### Web Fallback

If app isn't installed on receiving device:
```swift
activity.webpageURL = URL(string: "https://myapp.com/activity/\(id)")
```

---

## Drag and Drop

### Supporting Drag

```swift
.draggable(item) {
    // Drag preview
    ItemPreview(item: item)
}
```

### Supporting Drop

```swift
.dropDestination(for: ItemType.self) { items, location in
    // Handle dropped items
    return true
}
```

### Drag and Drop Guidelines

**Visual feedback:**
- Show clear drag preview
- Indicate valid drop targets
- Animate transitions smoothly

**Multi-item:**
- Support selecting multiple items
- Stack preview for multiple items
- Handle batch operations

**Cross-app:**
- Export standard data types (images, text, URLs)
- Accept common formats
- Maintain quality during transfer

### Platform Considerations

| Platform | Drag Initiation |
|----------|-----------------|
| iPhone | Long press + drag (within app) |
| iPad | Long press or tap + drag |
| Mac (Catalyst) | Click + drag |

---

## Universal Links

### Setting Up

1. Configure `apple-app-site-association` on your server:
```json
{
  "applinks": {
    "apps": [],
    "details": [{
      "appID": "TEAMID.com.example.app",
      "paths": ["/product/*", "/user/*"]
    }]
  }
}
```

2. Add Associated Domains capability:
```
applinks:example.com
```

### Handling Links

```swift
func application(_ application: UIApplication,
                 continue userActivity: NSUserActivity,
                 restorationHandler: @escaping ([UIUserActivityRestoring]?) -> Void) -> Bool {
    guard userActivity.activityType == NSUserActivityTypeBrowsingWeb,
          let url = userActivity.webpageURL else {
        return false
    }
    return handleUniversalLink(url)
}
```

### Best Practices

- Parse URLs robustly (handle malformed links)
- Navigate to appropriate screen
- Show content immediately (don't require login first)
- Fall back gracefully if content unavailable

---

## Spotlight Search

### Indexing Content

```swift
let attributeSet = CSSearchableItemAttributeSet(contentType: .text)
attributeSet.title = item.title
attributeSet.contentDescription = item.description
attributeSet.thumbnailData = item.thumbnailData

let searchableItem = CSSearchableItem(
    uniqueIdentifier: item.id,
    domainIdentifier: "com.app.items",
    attributeSet: attributeSet
)

CSSearchableIndex.default().indexSearchableItems([searchableItem])
```

### What to Index

**Good candidates:**
- User content (notes, documents)
- Saved items (favorites, history)
- Frequently accessed items

**Avoid:**
- Sensitive data
- Transient content
- Every possible item (be selective)

### Search Result Design

Results appear in Spotlight:
```
┌─────────────────────────────────────────┐
│ 🔲 My Note Title                        │
│    Preview of note content...           │
│    MyApp                                │
└─────────────────────────────────────────┘
```

**Include:**
- Clear title
- Helpful description
- Thumbnail if visual
- Accurate metadata

---

## Focus & Notifications

### Focus Awareness

Respect user's Focus mode:

```swift
UNUserNotificationCenter.current().getNotificationSettings { settings in
    if settings.notificationCenterSetting == .disabled {
        // User has notifications silenced
    }
}
```

### Time Sensitive Notifications

For truly urgent notifications:

```swift
let content = UNMutableNotificationContent()
content.title = "Your ride is here"
content.interruptionLevel = .timeSensitive
```

**Use only when:**
- Immediate action required
- User explicitly opted in
- Content is genuinely time-sensitive

---

## Quick Note Integration

### Adding Quick Note Capability

Allow highlighting content for Quick Note:

```swift
Text(content)
    .contextMenu {
        Button("Add to Quick Note") {
            // System handles this
        }
    }
```

---

## SharePlay

### When to Use SharePlay

- Watching content together
- Collaborative activities
- Shared experiences

### SharePlay Guidelines

**Sync state:**
- Keep all participants in sync
- Handle network latency gracefully
- Provide individual controls where appropriate

**Visual design:**
- Show who's in the session
- Indicate when others interact
- Provide easy leave option

---

## System Appearance

### Supporting Dark Mode

```swift
// Adaptive colors
Color.primary      // Auto light/dark
Color.secondary    // Auto light/dark

// Custom adaptive colors
extension Color {
    static let background = Color("Background") // From asset catalog
}
```

### Supporting Dynamic Type

```swift
Text("Title")
    .font(.title)      // Scales with Dynamic Type

// Custom scalable fonts
.font(.custom("MyFont", size: 17, relativeTo: .body))
```

### Supporting Accessibility

```swift
Text("Content")
    .accessibilityLabel("Detailed description")
    .accessibilityHint("Tap to view details")
```

---

## Best Practices Summary

| Integration | Key Consideration |
|-------------|-------------------|
| Siri | Clear confirmation, handle ambiguity |
| Shortcuts | Expose repeatable, automatable actions |
| Handoff | Preserve exact state across devices |
| Drag & Drop | Clear previews, multi-item support |
| Universal Links | Deep link to specific content |
| Spotlight | Index valuable, non-sensitive content |
| Focus | Respect user's notification preferences |

**Universal principle:** System integrations should feel seamless—users shouldn't think about which device or app they're using.
