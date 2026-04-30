---
name: ios-hig-design
description: |
  Build native iOS interfaces following Apple Human Interface Guidelines. Use when the user mentions "iPhone app", "iPad layout", "SwiftUI", "UIKit", "Dynamic Island", "safe areas", or "HIG compliance". Covers navigation patterns, accessibility, SF Symbols, and platform conventions. For general UI polish, see refactoring-ui. For affordance design, see design-everyday-things. Trigger with 'ios', 'hig', 'design'.
allowed-tools: Read, Glob, Grep
license: MIT
author: Wondelai <hello@wondelai.com>
version: 1.0.1
compatible-with: claude-code, codex, openclaw
tags: [design, compliance, ios-hig]
---
# iOS Human Interface Guidelines Design Skill

Framework for designing native iOS app interfaces that feel intuitive, consistent, and aligned with Apple's design philosophy. Based on Apple's Human Interface Guidelines, the definitive resource for building apps that integrate seamlessly with iPhone, iPad, and the broader Apple ecosystem.

## Core Principle

Apple's iOS design philosophy rests on three foundational pillars: clarity, deference, and depth. Every element must be legible and purposeful (clarity). The interface should never overshadow the content it presents (deference). And layering, transitions, and realistic motion must provide hierarchy and spatial relationships (depth).

**The foundation:** The best iOS apps don't just follow HIG rules mechanically---they internalize the philosophy that the interface exists to serve the user's content and tasks. Native components, system conventions, and platform consistency aren't constraints---they're the reason iOS users trust and enjoy apps that feel like they belong.

## Scoring

**Goal: 10/10.** When reviewing or creating iOS interfaces or SwiftUI/UIKit code, rate them 0-10 based on adherence to the principles below. A 10/10 means full alignment with all guidelines; lower scores indicate gaps to address. Always provide the current score and specific improvements needed to reach 10/10.

## iOS Design Framework

### 1. Layout & Safe Areas

**Core concept:** iOS devices have specific screen dimensions, safe area insets, and hardware intrusions (notch, Dynamic Island, home indicator) that must be respected in every layout.

**Why it works:** When layouts respect safe areas and standard spacing, the app feels native and trustworthy. Users never have content hidden behind hardware features or system UI, and the visual rhythm matches the rest of the platform.

**Key insights:**
- Design for the smallest screen first (375pt width for iPhone SE)
- Safe areas protect content from hardware features---never place interactive elements under the notch, Dynamic Island, or home indicator
- Standard content margins are 16-20pt from screen edges
- Minimum touch target size is 44 x 44pt
- List row minimum height is 44pt
- Standard spacing increments: 8 / 16 / 24pt

**Product applications:**

| Context | Layout Pattern | Example |
|---------|---------------|---------|
| **Status bar** | 59pt height, always respected | Time, signal, battery area |
| **Navigation bar** | 44pt standard row + 58pt large title | Back button, title, actions |
| **Content area** | Flexible, scrollable, respects safe area | Main app content |
| **Tab bar** | 49pt height, translucent with blur | 2-5 primary destinations |
| **Home indicator** | 34pt inset at bottom | System gesture area |

**Copy patterns:**
- Use `VStack { }` which respects safe areas by default
- Use `.ignoresSafeArea()` only for backgrounds and decorative elements, never for interactive content
- Always test on multiple device sizes including iPhone SE and Pro Max

**Ethical boundary:** Never hide critical content or controls behind hardware intrusions. Users with any device should have equal access to all functionality.

See: [references/navigation.md](references/navigation.md) for detailed navigation bar and tab bar specifications.

### 2. Typography & Dynamic Type

**Core concept:** iOS uses the San Francisco (SF Pro) typeface with a semantic text style system that automatically scales for accessibility via Dynamic Type.

**Why it works:** Semantic text styles create consistent visual hierarchy across the platform. Dynamic Type ensures every user---including those with visual impairments---can read content at their preferred size without breaking layouts.

**Key insights:**
- Large Title: 34pt Bold; Title: 17pt Medium; Body: 17pt Regular
- Secondary text: 15pt Regular at 60% opacity; Caption: 12-13pt
- Minimum text size is 11pt (captions/secondary info only)
- Line height minimum 1.3x font size for body text
- Optimal line length: 35-50 characters per line on mobile
- Always use left-aligned, non-justified text
- Minimum contrast ratio: 4.5:1 (WCAG AA)

**Product applications:**

| Context | Typography Pattern | Example |
|---------|-------------------|---------|
| **Screen titles** | `.largeTitle` or `.title` style | Large title collapses on scroll |
| **Body content** | `.body` style, 17pt | List items, descriptions |
| **Secondary info** | `.subheadline` or `.footnote` | Timestamps, metadata |
| **Tab labels** | 10pt SF text | Tab bar item labels |
| **Buttons** | `.body` weight semibold | Primary action text |

**Copy patterns:**
- Use `.font(.title)`, `.font(.body)`, `.font(.caption)` instead of hardcoded sizes
- Prefer weight and color variation over extreme size differences for hierarchy
- Test all layouts at the largest Dynamic Type size to ensure nothing breaks
- Use `@ScaledMetric` for custom spacing that scales with Dynamic Type

**Ethical boundary:** Never disable Dynamic Type or set fixed font sizes that prevent accessibility scaling. Every user deserves readable text.

See: [references/typography.md](references/typography.md) for complete text styles, font sizes, and Dark Mode typography rules.

### 3. Color & Dark Mode

**Core concept:** iOS provides semantic system colors that automatically adapt between light and dark appearances, ensuring proper contrast and visual hierarchy in both modes.

**Why it works:** Semantic colors maintain readability and hierarchy across appearances without manual intervention. Users who prefer Dark Mode get a first-class experience, and apps that support both modes feel polished and native.

**Key insights:**
- Use `Color(.label)`, `Color(.secondaryLabel)`, `Color(.systemBackground)` instead of hardcoded colors
- `Color(.systemBlue)` is the default tint/accent; `.systemRed` for destructive actions; `.systemGreen` for success
- Dark Mode inverts text colors (dark to light) and shifts backgrounds darker while maintaining relative hierarchy
- Accent colors in Dark Mode need lower brightness and higher saturation to pop
- Always preview both modes during development
- Maintain 4.5:1 contrast ratio in both light and dark

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
- Define custom colors in Asset Catalog with light/dark variants, not in code
- Never assume a background is white or black---always use semantic colors
- Test with Increase Contrast accessibility setting enabled

**Ethical boundary:** Dark Mode is not optional polish---it is expected by users. Never ship an app that is unreadable or broken in Dark Mode.

See: [references/colors-depth.md](references/colors-depth.md) for semantic colors, Dark Mode palette, and contrast ratio guidelines.

### 4. Navigation Patterns

**Core concept:** iOS uses a layered navigation model with tab bars for primary destinations, navigation stacks for hierarchical drilling, and modals for focused tasks.

**Why it works:** Consistent navigation patterns mean users always know where they are, how they got there, and how to go back. Violating these patterns creates confusion and makes the app feel foreign on iOS.

**Key insights:**
- Tab bar: 2-5 primary destinations, always visible, remembers state per tab
- Navigation bar: back button (top-left), title (center or large), actions (top-right)
- Large title collapses to compact title on scroll with smooth animation
- Modals for focused tasks; dismiss via swipe-down or explicit close button
- Never use hamburger menus---iOS users expect tab bars
- Search bar can appear below nav bar, hidden until pulled down

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
- Tab labels should be single words: "Home", "Search", "Profile"
- Modal titles should describe the task: "New Message", "Edit Profile"
- Use `NavigationStack` (not deprecated `NavigationView`) in SwiftUI

**Ethical boundary:** Never trap users in flows without a clear exit. Every screen must have an obvious way to go back or dismiss.

See: [references/navigation.md](references/navigation.md) for tab bar, navigation bar, modals, search patterns, and split views.

### 5. Controls & Inputs

**Core concept:** iOS provides a rich library of native controls (buttons, lists, toggles, pickers, menus, text fields) that users already understand and expect.

**Why it works:** Native controls come with built-in accessibility, haptic feedback, and interaction patterns that users have already learned. Custom controls create friction and often miss edge cases that Apple has already solved.

**Key insights:**
- Page-level actions go in the nav bar (top) or action bar (bottom)
- Primary buttons are filled with the theme color; secondary are outlined or text-only
- Destructive actions use red and require confirmation for irreversible operations
- Lists (table views) are the fundamental iOS content pattern
- Match keyboard type to expected input (`.emailAddress`, `.phonePad`, `.URL`)
- Use `.textContentType` for autofill support (email, password, address)

**Product applications:**

| Context | Control Pattern | Example |
|---------|----------------|---------|
| **Forms** | Native text fields with proper keyboard types | Email field with @ keyboard |
| **Settings** | Grouped list with toggles, disclosure | iOS Settings style |
| **Selection** | Picker, segmented control, or action sheet | Date picker, sort options |
| **Destructive actions** | Red button + confirmation alert | "Delete Account" flow |
| **Context actions** | Long press menu or swipe actions | Edit, share, delete on row |

**Copy patterns:**
- Use `.keyboardType(.emailAddress)` and `.textContentType(.emailAddress)` together
- Prefer system alerts for confirmations: `.alert()` or `.confirmationDialog()`
- Use `.swipeActions` on list rows for common actions
- Place primary action buttons at the bottom of the screen within thumb reach

**Ethical boundary:** Never disguise ads as native controls or make destructive actions too easy to trigger accidentally. Confirmation dialogs exist for a reason.

See: [references/components.md](references/components.md) for buttons, lists, input controls, menus, and confirmation dialogs. See also: [references/keyboard-input.md](references/keyboard-input.md) for keyboard types and input patterns.

### 6. Accessibility

**Core concept:** iOS has world-class accessibility features (VoiceOver, Dynamic Type, Switch Control, Voice Control) and every app must support them as a first-class concern, not an afterthought.

**Why it works:** Accessibility is not optional---it is required by app store guidelines and by ethical design practice. Over 1 billion people worldwide live with some form of disability. Accessible apps also benefit all users (larger text in sunlight, VoiceOver while driving).

**Key insights:**
- Every interactive element needs an `.accessibilityLabel` describing what it is
- Use `.accessibilityValue` for current state and `.accessibilityHint` for what it does
- Group related elements with `.accessibilityElement(children: .combine)`
- Support Dynamic Type at all sizes---test at the largest setting
- Minimum touch target: 44 x 44pt
- Minimum contrast ratio: 4.5:1 for text (WCAG AA)
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
- Write accessibility labels as nouns: "Favorite", "Settings", "Close"
- Write hints as actions: "Shares this item with others", "Opens settings"
- Test the complete app flow using only VoiceOver
- Use Accessibility Inspector in Xcode to audit contrast and labels

**Ethical boundary:** Accessibility is not a nice-to-have. Shipping an inaccessible app excludes real people. Treat VoiceOver testing as seriously as visual testing.

See: [references/accessibility.md](references/accessibility.md) for VoiceOver implementation, Dynamic Type support, and accessibility checklist.

### 7. Icons & Images

**Core concept:** iOS uses SF Symbols as the standard icon system and requires app icons in specific sizes with the signature superellipse ("squircle") mask applied automatically.

**Why it works:** SF Symbols are designed to align perfectly with San Francisco text, scale with Dynamic Type, and adapt to different weights and sizes. Consistent iconography makes the interface feel cohesive and native.

**Key insights:**
- Use SF Symbols (`Image(systemName:)`) for all standard icons---they scale with text
- App icons: export as 1024x1024px square; iOS applies the squircle mask automatically
- Icon corner radius formula: side length x 0.222 with 61% corner smoothing
- iOS 18+ supports light, dark, and tinted icon variants
- Avoid text in app icons---it does not scale well
- Keep icon designs simple with recognizable silhouettes

**Product applications:**

| Context | Icon Pattern | Example |
|---------|-------------|---------|
| **Tab bar** | SF Symbols, filled variant for selected | `house.fill`, `magnifyingglass` |
| **Navigation bar** | SF Symbols at regular weight | `gear`, `plus`, `ellipsis` |
| **List accessories** | SF Symbols, secondary color | `chevron.right`, `checkmark` |
| **App icon** | 1024px square, simple bold design | Single recognizable glyph |
| **Widgets** | SF Symbols matching widget style | Consistent with app branding |

**Copy patterns:**
- Use `Image(systemName: "heart.fill")` for SF Symbols
- Apply `.symbolRenderingMode(.hierarchical)` for multi-color depth
- Use `.imageScale(.large)` or `.font()` to size symbols relative to text
- Browse available symbols in the SF Symbols app (free from Apple)

**Ethical boundary:** Never use misleading icons that suggest functionality that does not exist. Icon meaning should match the iOS convention (e.g., trash = delete, not archive).

See: [references/app-icons.md](references/app-icons.md) for icon size tables, shape specifications, and design guidelines.

### 8. Gestures & Haptics

**Core concept:** iOS defines standard gestures (swipe back, pull to refresh, long press for context menu) and haptic feedback patterns that must be respected and never overridden.

**Why it works:** Gestures are muscle memory. When an app overrides the swipe-back gesture or repurposes pull-to-refresh, users feel disoriented and frustrated. Haptics provide invisible confirmation that an action registered, reducing uncertainty.

**Key insights:**
- Never override: swipe-right-from-edge (back), swipe-down on modal (dismiss), pull-down on list (refresh)
- Swipe-left on rows reveals actions (delete, archive, etc.)
- Long press shows context menus
- Pinch to zoom is expected on images and maps
- Use three haptic types: impact (physical actions), notification (outcomes), selection (UI changes)
- Haptics should be subtle and meaningful---never constant or annoying

**Product applications:**

| Context | Gesture/Haptic Pattern | Example |
|---------|----------------------|---------|
| **Navigation** | Swipe right from left edge | System back gesture |
| **Modals** | Swipe down to dismiss | Sheet dismissal |
| **Lists** | Pull to refresh, swipe for actions | Refresh content, delete row |
| **Media** | Pinch to zoom, double-tap | Photo viewer |
| **Confirmation** | `.success` haptic on completion | Payment confirmed |
| **Selection** | Selection haptic on toggle/pick | Picker wheel scroll |

**Copy patterns:**
- Use `UIImpactFeedbackGenerator(style: .medium)` for physical interactions
- Use `UINotificationFeedbackGenerator()` with `.success`, `.warning`, `.error` for outcomes
- Use `UISelectionFeedbackGenerator()` for UI state changes
- Call `.prepare()` before triggering haptics to minimize latency

**Ethical boundary:** Never use aggressive haptics to pressure users into actions. Haptic feedback should confirm, not coerce.

See: [references/gestures.md](references/gestures.md) for standard gesture table, haptic feedback patterns, and animation guidelines.

## Common Mistakes

| Mistake | Why It Fails | Fix |
|---------|-------------|-----|
| **Overriding standard gestures** | Users expect swipe-back, pull-refresh globally; overriding breaks muscle memory | Use system gestures for their intended purposes; add custom gestures only for supplementary actions |
| **Touch targets under 44pt** | Small targets cause mis-taps and frustrate users, especially with accessibility needs | Ensure all interactive elements are at least 44 x 44pt |
| **Ignoring safe areas** | Content hidden behind notch, Dynamic Island, or home indicator | Always respect safe area insets; use `.ignoresSafeArea()` only for backgrounds |
| **Using Android patterns on iOS** | Hamburger menus, top tab bars, material-style FABs feel foreign | Use tab bars for primary navigation, bottom sheets, native iOS components |
| **Skipping Dark Mode** | Users who prefer Dark Mode see broken layouts, unreadable text | Use semantic colors; test both appearances; define light/dark color pairs |
| **Hardcoding font sizes** | Breaks Dynamic Type, excludes users who need larger text | Use semantic text styles (`.title`, `.body`, `.caption`) throughout |
| **Low contrast text** | Fails WCAG AA, unreadable in sunlight or for low-vision users | Maintain 4.5:1 minimum contrast ratio; test with Increase Contrast setting |
| **Not testing on real devices** | Simulator misses performance, haptics, safe area edge cases | Test on physical devices, especially the smallest and largest screen sizes |

## Quick Diagnostic

Audit any iOS interface design:

| Question | If No | Action |
|----------|-------|--------|
| Does the layout respect safe areas on all device sizes? | Content may be hidden behind hardware features | Audit all screens on iPhone SE and Pro Max; fix safe area insets |
| Are all touch targets at least 44 x 44pt? | Users will mis-tap, especially with accessibility needs | Increase tap areas; use `.frame(minWidth: 44, minHeight: 44)` |
| Does the app work fully in Dark Mode? | Dark Mode users see broken/unreadable UI | Replace hardcoded colors with semantic system colors |
| Does text scale properly with Dynamic Type? | Accessibility violation; excludes low-vision users | Replace fixed font sizes with semantic text styles; test at largest setting |
| Can a VoiceOver user complete every task? | App is inaccessible to blind and low-vision users | Add accessibility labels, values, hints to all interactive elements |
| Are navigation patterns native iOS? | App feels foreign; users struggle to navigate | Replace hamburger menus with tab bars; use standard push/modal navigation |

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

This skill is based on Apple's Human Interface Guidelines, the official design documentation for all Apple platforms. For the complete guidelines, platform-specific guidance, and latest updates:

- [Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/) --- The definitive reference for iOS, iPadOS, macOS, watchOS, and visionOS design
- [SF Symbols](https://developer.apple.com/sf-symbols/) --- Apple's icon system with 5,000+ configurable symbols
- [Apple Design Resources (Figma/Sketch)](https://developer.apple.com/design/resources/) --- Official design templates and UI kits
- [WWDC Design Sessions](https://developer.apple.com/videos/design/) --- Video sessions covering design principles and new features
- [*"Designed by Apple in California"*](https://www.amazon.com/Designed-Apple-California/dp/1942303118?tag=wondelai00-20) --- Photo book documenting Apple's design process and philosophy
- [*"The Design of Everyday Things"*](https://www.amazon.com/Design-Everyday-Things-Revised-Expanded/dp/0465050654?tag=wondelai00-20) by Don Norman --- The foundational text on human-centered design that influenced Apple's approach
- [*"Universal Principles of Design"*](https://www.amazon.com/Universal-Principles-Design-Revised-Updated/dp/1592535879?tag=wondelai00-20) by William Lidwell, Kritina Holden, and Jill Butler --- 125 design principles applicable to iOS interface design

## About the Author

The **Apple Human Interface Guidelines** are authored and maintained by Apple's Human Interface Design team, one of the most influential design organizations in technology. The HIG traces its origins to 1984, when Apple published the original *Macintosh Human Interface Guidelines* alongside the launch of the first Macintosh computer. That document established principles---direct manipulation, see-and-point, consistency, WYSIWYG, user control---that defined graphical user interface design for decades. Under the leadership of designers including Jef Raskin, Bruce Tognazzini, and later Jony Ive and Alan Dye, Apple's design philosophy evolved through Mac OS, iPhone (2007), iPad (2010), Apple Watch (2015), and Apple Vision Pro (2024). The HIG has been continuously updated to reflect new interaction paradigms---from mouse to multi-touch to spatial computing---while maintaining the core belief that technology should be intuitive, accessible, and delightful. Today the HIG is freely available at developer.apple.com and remains the essential reference for anyone building apps on Apple platforms.

## Overview

Design native iOS interfaces following Apple Human Interface Guidelines.

## Prerequisites

- Access to the ORM environment or API
- Required CLI tools installed and authenticated
- Familiarity with ORM concepts and terminology

## Instructions

1. Assess the current state of the ORM configuration
2. Identify the specific requirements and constraints
3. Apply the recommended patterns from this skill
4. Validate the changes against expected behavior
5. Document the configuration for team reference

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

See [ORM implementation details](${CLAUDE_SKILL_DIR}/references/implementation.md) for output format specifications.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with ORM |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply ios hig design to a standard project setup with default configuration options.

**Advanced scenario**: Customize ios hig design for production environments with multiple constraints and team-specific requirements.

## Resources

- Official ORM documentation
- Community best practices and patterns
- Related skills in this plugin pack
