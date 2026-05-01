# iOS Widgets & App Extensions

Design guidelines for widgets, App Clips, and system extensions.


## Table of Contents
1. [Widget Design](#widget-design)
2. [Widget Configuration](#widget-configuration)
3. [App Clips](#app-clips)
4. [Share Extensions](#share-extensions)
5. [Action Extensions](#action-extensions)
6. [Live Activities](#live-activities)
7. [Widget Development Tips](#widget-development-tips)

---

## Widget Design

### Widget Philosophy

Widgets provide **glanceable information** on the Home Screen, Lock Screen, and StandBy mode. They are not mini-apps—they're windows into your app's most useful content.

**Key principles:**
- Show immediately useful information
- Update content thoughtfully (not constantly)
- Respect the user's Home Screen aesthetic
- Drive users to the app for deeper engagement

### Widget Sizes

**Home Screen widgets:**

| Size | Name | Grid Units | Use Case |
|------|------|------------|----------|
| Small | `systemSmall` | 2×2 | Single piece of information |
| Medium | `systemMedium` | 4×2 | Key content + one interaction |
| Large | `systemLarge` | 4×4 | Rich content, multiple items |
| Extra Large | `systemExtraLarge` | 8×4 | iPad only, dashboard view |

**Lock Screen widgets (iOS 16+):**

| Size | Name | Characteristics |
|------|------|-----------------|
| Circular | `accessoryCircular` | Small icon or gauge |
| Rectangular | `accessoryRectangular` | Text + small visual |
| Inline | `accessoryInline` | Text only, above time |

### Widget Content Guidelines

**Do:**
- Show the most important information
- Update content at meaningful intervals
- Use the app's visual style
- Support multiple sizes (let users choose)
- Provide multiple widget types if you have different use cases

**Don't:**
- Cram too much information
- Show stale data
- Use widgets for advertising
- Require interaction to see content
- Update too frequently (drains battery)

### Small Widget Design

```
┌─────────────────────┐
│                     │
│    [Icon/Image]     │
│                     │
│    Primary Info     │
│    Secondary        │
│                     │
└─────────────────────┘
```

**Guidelines:**
- One tap target (entire widget)
- Essential info only
- Clear visual hierarchy
- No buttons or complex interactions

### Medium Widget Design

```
┌─────────────────────────────────────────┐
│  [Icon]                                 │
│  Title               ┌─────────────┐    │
│  Subtitle            │   Action    │    │
│                      └─────────────┘    │
│  Additional context                     │
└─────────────────────────────────────────┘
```

**Guidelines:**
- Can have multiple tap targets
- Show 2-4 pieces of information
- Actions should be quick (open to specific view)

### Large Widget Design

```
┌─────────────────────────────────────────┐
│  Header                          Edit   │
├─────────────────────────────────────────┤
│  ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │ Item 1  │ │ Item 2  │ │ Item 3  │   │
│  └─────────┘ └─────────┘ └─────────┘   │
│                                         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │ Item 4  │ │ Item 5  │ │ Item 6  │   │
│  └─────────┘ └─────────┘ └─────────┘   │
└─────────────────────────────────────────┘
```

**Guidelines:**
- Multiple tap targets allowed
- Show a collection or dashboard
- Include clear visual grouping
- Optional: Edit configuration

### Lock Screen Widget Design

Lock Screen widgets have limited space and no color.

**Circular:**
```
┌─────┐
│ 73° │  Temperature
│ ☀️  │  Weather icon
└─────┘
```

**Rectangular:**
```
┌─────────────────────┐
│ Next Event          │
│ Team Meeting @ 2pm  │
└─────────────────────┘
```

**Best practices:**
- Design for small size
- Use SF Symbols (render well)
- Test in Light and Dark modes
- Consider StandBy mode (larger display)

---

## Widget Configuration

### User-Configurable Widgets

Allow users to customize what the widget shows:

```swift
struct ConfigurationIntent: WidgetConfigurationIntent {
    static var title: LocalizedStringResource = "Configuration"

    @Parameter(title: "City")
    var city: City?

    @Parameter(title: "Units")
    var units: TemperatureUnit
}
```

**Configuration UI:**
- Keep options simple (few parameters)
- Provide sensible defaults
- Preview changes before confirming

### Widget Families

Support multiple sizes:

```swift
struct MyWidget: Widget {
    var body: some WidgetConfiguration {
        StaticConfiguration(kind: "MyWidget", provider: Provider()) { entry in
            MyWidgetView(entry: entry)
        }
        .supportedFamilies([.systemSmall, .systemMedium, .systemLarge])
    }
}
```

---

## App Clips

### What App Clips Are

App Clips are lightweight versions of your app (<10MB) for quick, focused tasks without full installation.

**Invocation points:**
- NFC tags
- QR codes
- App Clip codes
- Safari Smart App Banner
- Maps
- Messages

### App Clip Design Principles

**1. Focus on one task**
- Rent a bike
- Order food
- Pay for parking

**2. Minimize required information**
- Only ask for what's essential
- Use Sign in with Apple
- Use Apple Pay

**3. Fast experience**
- User expects to finish in under a minute
- No lengthy onboarding
- Minimal UI, maximum function

**4. Encourage full app download**
- Show value of full app
- Make download easy (banner)
- Don't block functionality to force download

### App Clip UI Guidelines

```
┌─────────────────────────────────────────┐
│  [Header: What you can do]              │
├─────────────────────────────────────────┤
│                                         │
│  [Primary action UI]                    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │        [Apple Pay]              │    │
│  └─────────────────────────────────┘    │
│                                         │
├─────────────────────────────────────────┤
│  Get the full app for more features     │
│  ┌─────────────────────────────────┐    │
│  │        Download App             │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

### App Clip Code Design

App Clip Codes are scannable codes that launch App Clips:

```
       ┌─────────────────┐
      ╱                   ╲
     │   [App Clip Code]   │
     │   Circular pattern  │
     │   with NFC chip     │
      ╲                   ╱
       └─────────────────┘
         Scan or tap to
         rent a scooter
```

**Placement guidelines:**
- Clear call to action below code
- Explain what will happen
- Accessible height (3.5-5 feet)
- Well-lit, clean surface

---

## Share Extensions

### Share Extension Design

```
┌─────────────────────────────────────────┐
│  Post to [App Name]                 ✕   │
├─────────────────────────────────────────┤
│  ┌─────────────────────────────────┐    │
│  │ [Preview of content]            │    │
│  └─────────────────────────────────┘    │
│                                         │
│  Add a comment...                       │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │           Share               │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

**Guidelines:**
- Show preview of shared content
- Minimal configuration options
- Quick completion (< 10 seconds ideal)
- Clear success/error feedback

---

## Action Extensions

### Action Extension Design

Action extensions process content in place:

```
┌─────────────────────────────────────────┐
│  Markup                             Done │
├─────────────────────────────────────────┤
│                                         │
│  [Modified content preview]             │
│                                         │
├─────────────────────────────────────────┤
│  [Tools for modification]               │
└─────────────────────────────────────────┘
```

**Guidelines:**
- Focus on specific task
- Return modified content to host app
- Match system UI conventions
- Support undo/cancel

---

## Live Activities

### What Live Activities Are

Real-time updates on Lock Screen and Dynamic Island for ongoing events:
- Sports scores
- Delivery tracking
- Timers
- Ride sharing

### Live Activity Design

**Lock Screen (expanded):**
```
┌─────────────────────────────────────────┐
│  [Leading]     [Center]      [Trailing] │
│  Team A           vs           Team B   │
│    24            Q3             21      │
└─────────────────────────────────────────┘
```

**Dynamic Island (compact):**
```
┌──────────────────────────────────────┐
│  🏀  24 - 21  Q3                     │
└──────────────────────────────────────┘
```

**Dynamic Island (expanded):**
```
┌────────────────────────────────────────┐
│  Lakers          vs          Celtics   │
│    24                          21      │
│  ────────────────────────────────────  │
│       Q3  •  4:32 remaining            │
└────────────────────────────────────────┘
```

### Live Activity Guidelines

**Do:**
- Update only when meaningful changes occur
- Design for all Dynamic Island states
- Provide clear end states
- Respect 8-hour maximum duration

**Don't:**
- Update every second (unless timer)
- Show static content
- Use for notifications
- Require interaction to see status

---

## Widget Development Tips

### Timeline Updates

```swift
func getTimeline(in context: Context, completion: @escaping (Timeline<Entry>) -> ()) {
    let entries = [
        SimpleEntry(date: Date(), data: currentData),
        SimpleEntry(date: Date().addingTimeInterval(60*15), data: futureData)
    ]

    let timeline = Timeline(entries: entries, policy: .atEnd)
    completion(timeline)
}
```

**Update policies:**
- `.atEnd` - Update when all entries displayed
- `.after(date)` - Update at specific time
- `.never` - Only update on user action

### Deep Links

Widgets should link to specific content:

```swift
Link(destination: URL(string: "myapp://item/\(item.id)")!) {
    ItemView(item: item)
}
```

### Placeholder Design

Show meaningful placeholder while loading:

```swift
struct PlaceholderView: View {
    var body: some View {
        VStack {
            RoundedRectangle(cornerRadius: 8)
                .fill(Color.gray.opacity(0.3))
            RoundedRectangle(cornerRadius: 4)
                .fill(Color.gray.opacity(0.2))
        }
    }
}
```
