# iOS HIG Design - Implementation Guide

Step-by-step methodology for designing native iOS interfaces following Apple's Human Interface Guidelines principles.

## The Three Pillars of iOS Design

Every design decision in an iOS app should answer to one of three foundational principles:

| Pillar | Definition | Design Question |
|--------|-----------|----------------|
| Clarity | Every element is purposeful and legible | "Does this serve the user's task or add noise?" |
| Deference | The interface supports the content, not the other way around | "Does the chrome distract from the content?" |
| Depth | Layering, motion, and spatial cues create hierarchy and meaning | "Does the visual depth communicate structure?" |

## Step 1: Navigation Architecture

iOS uses three primary navigation patterns. Choose based on your content type.

**1a. Tab bar navigation**
- Best for: 3-5 top-level destinations that are parallel and equally important
- Rules:
  - 3-5 tabs (fewer = consider a different pattern; more = consider a hamburger drawer)
  - Tabs persist regardless of where the user navigates within them
  - Use SF Symbols for icons, always paired with a label
  - The selected tab has a filled icon; unselected tabs have outline icons
- Example apps: Instagram, App Store, Clock

**1b. Navigation controller (push/pop)**
- Best for: hierarchical content where you drill down and come back
- Rules:
  - Back button always shows the name of the parent screen (not "Back")
  - Title bar shows the current screen's name
  - The left edge swipe gesture must always pop the current screen
  - Do not push modals onto a navigation stack — use sheets

**1c. Modal sheets**
- Best for: focused tasks that require the user's full attention
- Rules:
  - Small detent (half-sheet): quick info, pickers
  - Large detent (full-sheet): complex tasks, forms
  - Always provide a clear dismiss action (Done button or swipe down)
  - Do not use modals for navigation — only for focused tasks

## Step 2: Visual Design Fundamentals

**2a. Dynamic Type and accessibility**
- Never use hard-coded font sizes — use iOS text styles
- Required text styles and their use:
  - `largeTitle`: prominent screen titles (optional)
  - `title1` / `title2` / `title3`: section headers
  - `headline`: primary content labels (semibold)
  - `body`: default readable text
  - `callout`: slightly smaller body copy
  - `subheadline`: secondary labels
  - `footnote` / `caption1` / `caption2`: metadata, timestamps
- All text must scale when the user increases system font size (Dynamic Type)

**2b. Spacing and layout**
- Standard margins: 20pt from screen edges (use `safeAreaLayoutGuide`)
- List item height: minimum 44pt touch target
- Icon sizes: Tab bar icons at 25pt, navigation icons at 22pt, app icon at specific required sizes
- Use system spacing tokens, not arbitrary values

**2c. Color system**
- Always use semantic colors (not hex values):
  - `label` / `secondaryLabel` / `tertiaryLabel` / `quaternaryLabel`
  - `systemBackground` / `secondarySystemBackground` / `tertiarySystemBackground`
  - `separator` / `opaqueSeparator`
  - `systemRed`, `systemBlue`, `systemGreen`, etc. (auto-adjust for dark mode)
- Never use `UIColor.black` or `UIColor.white` directly — they break in dark mode

**2d. SF Symbols**
- Use SF Symbols for all standard icons
- Always pair symbols with labels (accessibility and clarity)
- Use symbol variants consistently: filled for selected states, outline for unselected
- Respect weight and scale: match symbol weight to surrounding text weight

## Step 3: Core Interaction Patterns

**3a. Swipe gestures**
- Swipe right on table rows: primary action (destructive or confirmatory)
- Swipe left on table rows: secondary actions (archive, flag, delete)
- Pull-to-refresh: standard for list content that updates
- Swipe to dismiss: sheets, full-screen modals (handle `interactiveDismissalRequiresConfirmation` for dirty forms)

**3b. Long press (context menus)**
- Long press should reveal a context menu (not custom UI) on all tappable content
- Context menu items must use SF Symbols + descriptive labels
- Destructive items must be marked `.destructive` (appear red)
- Context menus replace many use cases where a sheet was previously used

**3c. Haptics**
- Use UIFeedbackGenerator for meaningful moments:
  - `UIImpactFeedbackGenerator(.light)`: selection, subtle interactions
  - `UIImpactFeedbackGenerator(.medium)`: confirmations, actions
  - `UIImpactFeedbackGenerator(.heavy)`: significant actions
  - `UINotificationFeedbackGenerator(.success/.warning/.error)`: task outcomes
- Do NOT use haptics for animation frames or continuous interactions — only discrete events

## Step 4: Lists and Tables

Lists are the most common iOS UI pattern. Apply these rules:

**4a. UITableView / List style in SwiftUI**
- Use grouped or inset-grouped style for settings-style content
- Use plain style for content lists
- Section headers are `.title2` or `.headline` weight
- Accessory views: disclosure indicator for navigating deeper, checkmark for selection

**4b. Cell design**
- Primary label: `.headline` or `.body`
- Secondary label: `.subheadline` or `.caption1` in `.secondaryLabel` color
- Icon/image: 29pt for settings icons, 40pt for avatars
- Touch target: minimum 44pt height

**4c. Empty states**
- Every list must handle an empty state
- Components: centered illustration (SF Symbol or custom), title (`.title2`), body text, optional CTA button
- Use `.systemTeal` or brand accent for CTA in empty states

## Step 5: Forms and Input

**5a. Text field design**
- Use `UITextField` for single-line input, `UITextView` for multi-line
- Always label fields (never rely on placeholder alone — it disappears on input)
- Use appropriate keyboard types: `.emailAddress`, `.numberPad`, `.phonePad`, `.URL`
- Enable autocorrect and autocapitalize appropriately per field type

**5b. Form validation**
- Validate inline, not just on submission
- Show errors inline below the field, not in a separate alert
- Error text: `.footnote` size, `systemRed` color
- Success state: optional checkmark icon in `systemGreen`

**5c. Return key behavior**
- Set `returnKeyType` to match next step: `.next` when more fields follow, `.done` when last field
- Use `UITextFieldDelegate` / `onSubmit` to advance focus programmatically

## Step 6: Accessibility Requirements

Accessibility is not optional — App Store review can reject apps with severe accessibility failures.

**6a. VoiceOver**
- Every interactive element must have a meaningful `accessibilityLabel`
- Custom controls must implement `accessibilityTraits` correctly
- Decorative images must have `accessibilityElementsHidden = true` or empty label

**6b. Touch target sizes**
- Minimum 44×44pt for all interactive elements
- If visual element is smaller (e.g., a 22pt icon), expand the tap area using padding or `contentEdgeInsets`

**6c. Color contrast**
- Text must meet WCAG AA contrast ratio: 4.5:1 for body text, 3:1 for large text
- Do not rely on color alone to convey information

## Step 7: Safe Areas and Device Adaptation

**7a. Safe area insets**
- Always use `safeAreaLayoutGuide` for content that should not be obscured by Dynamic Island, Home Indicator, or notch
- Bottom content must respect the Home Indicator safe area
- Never place interactive elements under the Dynamic Island

**7b. Dynamic Island integration**
- Use Live Activities for real-time updates that appear in the Dynamic Island
- Activities must use `ActivityKit` and follow `StandbyWidget` design guidelines

**7c. iPad layout**
- iPad must support split view and slide over (test in both orientations)
- On iPad, tab bar becomes a sidebar (SwiftUI's `NavigationSplitView` handles this automatically)
- Pointer support: hover effects and cursor changes for all interactive elements

## Common Pitfalls

| Mistake | Consequence | Fix |
|---------|------------|-----|
| Hard-coded colors | Breaks dark mode | Use semantic colors exclusively |
| Hard-coded font sizes | Breaks Dynamic Type | Use text style constants, never point values |
| Missing empty states | Poor experience on first install | Design and implement empty state for every list |
| Touch targets < 44pt | Accessibility failures, App Store rejection | Pad interactive targets to 44×44pt minimum |
| Custom navigation that breaks swipe-back | Destroys native feel, user frustration | Always preserve left-edge swipe gesture |

## Quick-Start Checklist

- [ ] Navigation pattern chosen (tab bar, nav controller, or modal) and justified
- [ ] All colors use semantic iOS color tokens
- [ ] All fonts use Dynamic Type text styles
- [ ] All interactive elements have 44×44pt minimum touch targets
- [ ] SF Symbols used for all standard icons
- [ ] Context menus implemented for all tappable content cells
- [ ] Empty states designed and implemented for all lists
- [ ] VoiceOver labels added to all interactive elements
- [ ] Dark mode tested in Simulator (Appearance override)
- [ ] Safe area insets respected on all screens
