---
name: ios-hig-design
description: 'Design native iOS interfaces following Apple Human Interface Guidelines. Use when the user mentions "iPhone app", "iPad layout", "SwiftUI", "UIKit", "Dynamic Island", "safe areas", "HIG compliance", "SF Symbols", "haptic feedback", "iOS accessibility", "make my app feel native", or "follow Apple design guidelines". Also trigger when building tab bars, navigation stacks, sheets, or modals for iOS, implementing dark mode, or adapting layouts across screen sizes. Covers navigation patterns, accessibility, SF Symbols, and platform conventions. For general UI polish, see refactoring-ui. For affordance design, see design-everyday-things.'
license: MIT
metadata:
  author: wondelai
  version: "1.4.0"
---

# iOS Human Interface Guidelines Design Skill

Framework for designing native iOS interfaces that feel intuitive, consistent, and aligned with Apple's design philosophy. Based on Apple's Human Interface Guidelines, the definitive resource for apps that integrate seamlessly with iPhone, iPad, and the Apple ecosystem.

## Core Principle

Apple's iOS design philosophy rests on three pillars: **clarity** (every element legible and purposeful), **deference** (the interface never overshadows the content it presents), and **depth** (layering, transitions, and realistic motion convey hierarchy and spatial relationships).

**The foundation:** The best iOS apps internalize this philosophy rather than following HIG rules mechanically. Native components, system conventions, and platform consistency aren't constraints---they're the reason iOS users trust and enjoy apps that feel like they belong.

## Scoring

**Goal: 10/10.** Rate iOS interfaces or SwiftUI/UIKit code 0-10 against the principles below. Always state the current score and the specific improvements needed to reach 10/10.

## iOS Design Framework

### 1. Layout & Safe Areas

**Core concept:** iOS devices have specific screen dimensions, safe area insets, and hardware intrusions (notch, Dynamic Island, home indicator) that every layout must respect.

**Why it works:** When layouts respect safe areas and standard spacing, the app feels native and trustworthy---no content hides behind hardware features, and the visual rhythm matches the platform.

**Key insights:**
- Design for the smallest screen first (375pt width, iPhone SE)
- Safe areas protect content from the notch, Dynamic Island, and home indicator---never place interactive elements under them
- Standard content margins: 16-20pt from screen edges; spacing increments: 8 / 16 / 24pt
- Minimum touch target and list row height: 44pt

**Product applications:**

| Context | Layout Pattern | Example |
|---------|---------------|---------|
| **Status bar** | 59pt height, always respected | Time, signal, battery area |
| **Navigation bar** | 44pt standard row + 58pt large title | Back button, title, actions |
| **Content area** | Flexible, scrollable, respects safe area | Main app content |
| **Tab bar** | 49pt height, translucent with blur | 2-5 primary destinations |
| **Home indicator** | 34pt inset at bottom | System gesture area |

**Copy patterns:**
- Use `VStack { }`, which respects safe areas by default
- Use `.ignoresSafeArea()` only for backgrounds and decoration, never interactive content
- Test on multiple sizes, including iPhone SE and Pro Max

**Ethical boundary:** Never hide critical content or controls behind hardware intrusions---every device deserves equal access to all functionality.

See: [references/navigation.md](references/navigation.md) for detailed navigation bar and tab bar specifications.

### 2. Typography & Dynamic Type

**Core concept:** iOS uses the San Francisco (SF Pro) typeface with semantic text styles that automatically scale for accessibility via Dynamic Type.

**Why it works:** Semantic styles create consistent hierarchy across the platform, and Dynamic Type lets every user---including those with visual impairments---read at their preferred size without breaking layouts.

**Key insights:**
- Large Title: 34pt Bold; Title: 17pt Medium; Body: 17pt Regular; Caption: 12-13pt; secondary text: 15pt at 60% opacity
- Minimum text size 11pt (captions/secondary only); minimum contrast 4.5:1 (WCAG AA)
- Line height at least 1.3x font size; optimal line length 35-50 characters on mobile
- Always left-aligned, non-justified text

**Product applications:**

| Context | Typography Pattern | Example |
|---------|-------------------|---------|
| **Screen titles** | `.largeTitle` or `.title` style | Large title collapses on scroll |
| **Body content** | `.body` style, 17pt | List items, descriptions |
| **Secondary info** | `.subheadline` or `.footnote` | Timestamps, metadata |
| **Tab labels** | 10pt SF text | Tab bar item labels |
| **Buttons** | `.body` weight semibold | Primary action text |

**Copy patterns:**
- Use `.font(.title)`, `.font(.body)`, `.font(.caption)` instead of hardcoded sizes; `@ScaledMetric` for custom spacing that scales
- Prefer weight and color variation over extreme size differences for hierarchy
- Test all layouts at the largest Dynamic Type size

**Ethical boundary:** Never disable Dynamic Type or fix font sizes that block accessibility scaling---every user deserves readable text.

See: [references/typography.md](references/typography.md) for complete text styles, font sizes, and Dark Mode typography rules.

### 3. Color & Dark Mode

**Core concept:** iOS provides semantic system colors that automatically adapt between light and dark appearances while preserving contrast and hierarchy.

**Why it works:** Semantic colors maintain readability across appearances without manual intervention, so Dark Mode users get a first-class experience and the app feels polished and native.

**Key insights:**
- Use `Color(.label)`, `Color(.secondaryLabel)`, `Color(.systemBackground)` instead of hardcoded colors
- `Color(.systemBlue)` is the default tint; `.systemRed` for destructive actions; `.systemGreen` for success
- Dark Mode inverts text colors and shifts backgrounds darker while keeping relative hierarchy; accent colors need lower brightness and higher saturation to pop
- Maintain 4.5:1 contrast in both modes; preview both during development

**Product applications:**

| Context | Color Pattern | Example |
|---------|--------------|---------|
| **Primary text** | `Color(.label)` | Adapts white/black per mode |
| **Secondary text** | `Color(.secondaryLabel)` | 60% opacity in both modes |
| **Backgrounds** | `Color(.systemBackground)` / `.secondarySystemBackground` | Layered depth |
| **Destructive actions** | `Color(.systemRed)` | Delete buttons, warnings |
| **Interactive tint** | App accent color or `.systemBlue` | Links, toggle states |

**Copy patterns:**
- Use `.preferredColorScheme(.light)` and `.dark` in previews to test both modes side by side
- Define custom colors in the Asset Catalog with light/dark variants, not in code
- Never assume a background is white or black; test with Increase Contrast enabled

**Ethical boundary:** Dark Mode is not optional polish---never ship an app that is unreadable or broken in it.

See: [references/colors-depth.md](references/colors-depth.md) for semantic colors, Dark Mode palette, and contrast ratio guidelines.

### 4. Navigation Patterns

**Core concept:** iOS uses a layered navigation model: tab bars for primary destinations, navigation stacks for hierarchical drilling, and modals for focused tasks.

**Why it works:** Consistent navigation means users always know where they are, how they got there, and how to go back; violating these patterns makes the app feel foreign on iOS.

**Key insights:**
- Tab bar: 2-5 primary destinations, always visible, remembers state per tab
- Navigation bar: back button (top-left), title (center or large), actions (top-right); large title collapses on scroll
- Modals for focused tasks; dismiss via swipe-down or explicit close button
- Never use hamburger menus---iOS users expect tab bars
- Search bar can sit below the nav bar, hidden until pulled down

**Product applications:**

| Context | Navigation Pattern | Example |
|---------|-------------------|---------|
| **App structure** | Tab bar with 3-5 tabs | Home, Search, Profile |
| **Content hierarchy** | Push navigation (drill-down) | List > Detail > Edit |
| **Focused tasks** | Modal presentation | Compose, settings, filters |
| **Search** | Pull-down search bar | Spotlight-style search |
| **Split view** | iPad sidebar + detail | Mail, Notes on iPad |

**Copy patterns:**
- Back button text should be the previous screen's title, not "Back"
- Tab labels are single words ("Home", "Search"); modal titles describe the task ("New Message", "Edit Profile")
- Use `NavigationStack` (not deprecated `NavigationView`) in SwiftUI

**Ethical boundary:** Never trap users in flows without a clear exit---every screen needs an obvious way back or out.

### 5. Controls & Inputs

**Core concept:** iOS provides a rich library of native controls (buttons, lists, toggles, pickers, menus, text fields) that users already understand and expect.

**Why it works:** Native controls ship with built-in accessibility, haptics, and learned interaction patterns; custom controls create friction and miss edge cases Apple already solved.

**Key insights:**
- Page-level actions go in the nav bar (top) or action bar (bottom)
- Primary buttons are filled with the theme color; secondary are outlined or text-only
- Destructive actions use red and require confirmation when irreversible
- Lists (table views) are the fundamental iOS content pattern
- Match keyboard type to input (`.emailAddress`, `.phonePad`, `.URL`); use `.textContentType` for autofill

**Product applications:**

| Context | Control Pattern | Example |
|---------|----------------|---------|
| **Forms** | Native text fields with proper keyboard types | Email field with @ keyboard |
| **Settings** | Grouped list with toggles, disclosure | iOS Settings style |
| **Selection** | Picker, segmented control, or action sheet | Date picker, sort options |
| **Destructive actions** | Red button + confirmation alert | "Delete Account" flow |
| **Context actions** | Long press menu or swipe actions | Edit, share, delete on row |

**Copy patterns:**
- Pair `.keyboardType(.emailAddress)` with `.textContentType(.emailAddress)`
- Prefer system confirmations: `.alert()` or `.confirmationDialog()`; use `.swipeActions` on list rows
- Place primary action buttons at the bottom of the screen within thumb reach

**Ethical boundary:** Never disguise ads as native controls or make destructive actions easy to trigger accidentally.

See: [references/components.md](references/components.md) for buttons, lists, input controls, menus, and confirmation dialogs. See also: [references/keyboard-input.md](references/keyboard-input.md) for keyboard types and input patterns.

### 6. Accessibility

**Core concept:** iOS has world-class accessibility features (VoiceOver, Dynamic Type, Switch Control, Voice Control), and every app must support them as a first-class concern.

**Why it works:** Over 1 billion people live with some form of disability, and accessible apps benefit everyone (larger text in sunlight, VoiceOver while driving). App Store guidelines require it.

**Key insights:**
- Every interactive element needs an `.accessibilityLabel`; use `.accessibilityValue` for state and `.accessibilityHint` for effect
- Group related elements with `.accessibilityElement(children: .combine)`
- Support Dynamic Type at all sizes; test at the largest setting
- Minimum touch target 44 x 44pt; minimum text contrast 4.5:1 (WCAG AA)
- Never convey meaning through color alone

**Product applications:**

| Context | Accessibility Pattern | Example |
|---------|----------------------|---------|
| **Icons** | `.accessibilityLabel("Favorite")` | Heart icon with label |
| **Sliders** | `.accessibilityValue("\(Int(volume * 100))%")` | Volume control |
| **Buttons** | `.accessibilityHint("Shares this item")` | Share button |
| **Groups** | `.accessibilityElement(children: .combine)` | Avatar + name row |
| **Images** | Decorative: `.accessibilityHidden(true)` | Background patterns |

**Copy patterns:**
- Write labels as nouns ("Favorite", "Settings"); write hints as actions ("Shares this item with others")
- Test the complete app flow using only VoiceOver
- Use Xcode's Accessibility Inspector to audit contrast and labels

**Ethical boundary:** Shipping an inaccessible app excludes real people---treat VoiceOver testing as seriously as visual testing.

See: [references/accessibility.md](references/accessibility.md) for VoiceOver implementation, Dynamic Type support, and the accessibility checklist.

### 7. Icons & Images

**Core concept:** iOS uses SF Symbols as the standard icon system and requires app icons in specific sizes with the signature superellipse ("squircle") mask applied automatically.

**Why it works:** SF Symbols align perfectly with San Francisco text, scale with Dynamic Type, and adapt to weights and sizes; consistent iconography makes the interface feel cohesive and native.

**Key insights:**
- Use SF Symbols (`Image(systemName:)`) for all standard icons---they scale with text
- App icons: export 1024x1024px square; iOS applies the squircle mask (corner radius = side x 0.222 with 61% smoothing)
- iOS 18+ supports light, dark, and tinted icon variants
- Avoid text in app icons; keep designs simple with recognizable silhouettes

**Product applications:**

| Context | Icon Pattern | Example |
|---------|-------------|---------|
| **Tab bar** | SF Symbols, filled variant for selected | `house.fill`, `magnifyingglass` |
| **Navigation bar** | SF Symbols at regular weight | `gear`, `plus`, `ellipsis` |
| **List accessories** | SF Symbols, secondary color | `chevron.right`, `checkmark` |
| **App icon** | 1024px square, simple bold design | Single recognizable glyph |

**Copy patterns:**
- Use `Image(systemName: "heart.fill")`; apply `.symbolRenderingMode(.hierarchical)` for multi-color depth
- Size symbols relative to text with `.imageScale(.large)` or `.font()`
- Browse symbols in the free SF Symbols app from Apple

**Ethical boundary:** Never use icons that suggest functionality that doesn't exist or contradict iOS conventions (trash = delete, not archive).

See: [references/app-icons.md](references/app-icons.md) for icon size tables, shape specifications, and design guidelines.

### 8. Gestures & Haptics

**Core concept:** iOS defines standard gestures (swipe back, pull to refresh, long press for context menu) and haptic feedback patterns that must be respected and never overridden.

**Why it works:** Gestures are muscle memory---overriding swipe-back or repurposing pull-to-refresh disorients users. Haptics provide invisible confirmation that an action registered.

**Key insights:**
- Never override: swipe-right-from-edge (back), swipe-down on modal (dismiss), pull-down on list (refresh)
- Swipe-left on rows reveals actions; long press shows context menus; pinch zooms images and maps
- Three haptic types: impact (physical actions), notification (outcomes), selection (UI changes)
- Haptics should be subtle and meaningful---never constant or annoying

**Product applications:**

| Context | Gesture/Haptic Pattern | Example |
|---------|----------------------|---------|
| **Navigation** | Swipe right from left edge | System back gesture |
| **Modals** | Swipe down to dismiss | Sheet dismissal |
| **Lists** | Pull to refresh, swipe for actions | Refresh content, delete row |
| **Confirmation** | `.success` haptic on completion | Payment confirmed |
| **Selection** | Selection haptic on toggle/pick | Picker wheel scroll |

**Copy patterns:**
- `UIImpactFeedbackGenerator(style: .medium)` for physical interactions; `UISelectionFeedbackGenerator()` for UI state changes
- `UINotificationFeedbackGenerator()` with `.success`, `.warning`, `.error` for outcomes
- Call `.prepare()` before triggering haptics to minimize latency

**Ethical boundary:** Haptic feedback should confirm, never coerce.

See: [references/gestures.md](references/gestures.md) for the standard gesture table, haptic patterns, and animation guidelines.

## Common Mistakes

| Mistake | Why It Fails | Fix |
|---------|-------------|-----|
| **Overriding standard gestures** | Breaks muscle memory for swipe-back, pull-refresh | Use system gestures as intended; custom gestures only for supplementary actions |
| **Touch targets under 44pt** | Mis-taps, frustration, accessibility failures | Make all interactive elements at least 44 x 44pt |
| **Ignoring safe areas** | Content hidden behind notch, Dynamic Island, home indicator | Respect safe area insets; `.ignoresSafeArea()` only for backgrounds |
| **Using Android patterns on iOS** | Hamburger menus, top tabs, FABs feel foreign | Use tab bars, bottom sheets, native iOS components |
| **Skipping Dark Mode** | Broken layouts, unreadable text for Dark Mode users | Use semantic colors; test both appearances |
| **Hardcoding font sizes** | Breaks Dynamic Type, excludes low-vision users | Use semantic text styles (`.title`, `.body`, `.caption`) throughout |
| **Low contrast text** | Fails WCAG AA; unreadable in sunlight | Maintain 4.5:1 minimum; test with Increase Contrast |
| **Not testing on real devices** | Simulator misses performance, haptics, safe area edge cases | Test on physical devices at smallest and largest sizes |

## Quick Diagnostic

Audit any iOS interface design:

| Question | If No | Action |
|----------|-------|--------|
| Does the layout respect safe areas on all device sizes? | Content hidden behind hardware | Audit on iPhone SE and Pro Max; fix insets |
| Are all touch targets at least 44 x 44pt? | Mis-taps and accessibility failures | Increase tap areas; `.frame(minWidth: 44, minHeight: 44)` |
| Does the app work fully in Dark Mode? | Broken/unreadable UI for Dark Mode users | Replace hardcoded colors with semantic system colors |
| Does text scale properly with Dynamic Type? | Excludes low-vision users | Use semantic text styles; test at largest setting |
| Can a VoiceOver user complete every task? | App inaccessible to blind users | Add labels, values, hints to all interactive elements |
| Are navigation patterns native iOS? | App feels foreign | Replace hamburger menus with tab bars; standard push/modal navigation |

## Reference Files

- [typography.md](references/typography.md): Text styles, font sizes, Dynamic Type, Dark Mode typography
- [navigation.md](references/navigation.md): Tab bar, navigation bar, modals, search patterns, split views
- [components.md](references/components.md): Buttons, lists, input controls, menus, confirmation dialogs
- [colors-depth.md](references/colors-depth.md): Semantic colors, Dark Mode, contrast ratios
- [gestures.md](references/gestures.md): Standard gestures, haptics, animations
- [accessibility.md](references/accessibility.md): VoiceOver, Dynamic Type, accessibility checklist
- [app-icons.md](references/app-icons.md): Icon sizes, shape, SF Symbols guidelines
- [keyboard-input.md](references/keyboard-input.md): Keyboard types, input accessory views, hardware keyboard support
- [privacy-permissions.md](references/privacy-permissions.md): Permission request timing, pre-permission screens, handling denial
- [widgets-extensions.md](references/widgets-extensions.md): Widget sizes, App Clips design, Live Activities
- [system-integration.md](references/system-integration.md): Siri, Shortcuts, Handoff, drag-drop, universal links

## Further Reading

For the complete guidelines, platform-specific guidance, and latest updates:

- [Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/) --- the definitive reference for all Apple platforms
- [SF Symbols](https://developer.apple.com/sf-symbols/) --- Apple's icon system, 5,000+ configurable symbols
- [Apple Design Resources](https://developer.apple.com/design/resources/) --- official Figma/Sketch templates and UI kits
- [WWDC Design Sessions](https://developer.apple.com/videos/design/) --- videos on design principles and new features
- [*"Designed by Apple in California"*](https://www.amazon.com/Designed-Apple-California/dp/1942303118?tag=wondelai00-20) --- photo book of Apple's design process
- [*"The Design of Everyday Things"*](https://www.amazon.com/Design-Everyday-Things-Revised-Expanded/dp/0465050654?tag=wondelai00-20) by Don Norman --- the human-centered design text that influenced Apple
- [*"Universal Principles of Design"*](https://www.amazon.com/Universal-Principles-Design-Revised-Updated/dp/1592535879?tag=wondelai00-20) by William Lidwell, Kritina Holden, and Jill Butler --- 125 principles applicable to iOS

## About the Author

The **Apple Human Interface Guidelines** are written and maintained by Apple's Human Interface Design team, one of the most influential design organizations in technology. First published in 1984 alongside the original Macintosh, the HIG established principles---direct manipulation, consistency, user control---that defined graphical interface design and have evolved through iPhone, iPad, Apple Watch, and Vision Pro. It remains freely available at developer.apple.com as the essential reference for Apple platforms.
