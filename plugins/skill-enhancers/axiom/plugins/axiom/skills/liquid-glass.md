---
name: liquid-glass
description: Use when implementing Liquid Glass effects, reviewing UI for Liquid Glass adoption, debugging visual artifacts, optimizing performance, or requesting expert review of Liquid Glass implementation - provides comprehensive design principles, API patterns, and troubleshooting guidance from WWDC 2025. Includes design review pressure handling and professional push-back frameworks
version: 1.1.0
last_updated: TDD-tested with design review pressure scenarios
apple_platforms: iOS 26+, iPadOS 26+, macOS Tahoe+, visionOS 3+
---

# Liquid Glass - Apple's New Material Design System

## When to Use This Skill

Use when:
- Implementing Liquid Glass effects in your app
- Reviewing existing UI for Liquid Glass adoption opportunities
- Debugging visual artifacts with Liquid Glass materials
- Optimizing Liquid Glass performance
- **Requesting expert review of Liquid Glass implementation**
- Understanding when to use Regular vs Clear variants
- Troubleshooting tinting, legibility, or adaptive behavior issues

## Example Prompts

These are real questions developers ask that this skill is designed to answer:

**1. "I just saw Liquid Glass in WWDC videos. How is it different from blur effects I've used before? Should I adopt it?"**
→ The skill explains Liquid Glass as a lensing-based material (not blur), shows design philosophy, and when adoption makes sense

**2. "I'm implementing Liquid Glass in my app but the lensing effect doesn't look quite right. It looks like a regular blur. What am I missing?"**
→ The skill covers the visual properties (lensing vs motion vs environment), Regular vs Clear variants, and debugging visual artifacts

**3. "Liquid Glass works great on iPhone but looks odd on iPad. Should I adjust the implementation differently for different screen sizes?"**
→ The skill demonstrates adaptive Liquid Glass patterns and platform-specific guidance (iOS 26+, macOS Tahoe+, visionOS 3+)

**4. "I need to use Liquid Glass but still need legible text on top. How do I ensure text contrast while using Liquid Glass?"**
→ The skill covers tinting strategies, adaptive color choices, and opacity patterns for maintaining readability across light/dark modes

**5. "We want to do a design review of our Liquid Glass implementation. What are the expert criteria for a good Liquid Glass implementation?"**
→ The skill provides the comprehensive review checklist and professional push-back frameworks for design review meetings

---

## What is Liquid Glass?

Liquid Glass is Apple's next-generation material design system introduced at WWDC 2025. It represents a significant evolution from previous materials (Aqua, iOS 7 blurs, Dynamic Island) by creating a new digital meta-material that:

- **Dynamically bends and shapes light** (lensing) rather than scattering it
- **Moves organically** like a lightweight liquid, responding to touch and app dynamism
- **Adapts automatically** to size, environment, content, and light/dark modes
- **Unifies design language** across all Apple platforms (iOS, iPadOS, macOS, visionOS)

**Core Philosophy**: Liquid Glass complements the evolution of rounded, immersive screens with rounded, floating forms that feel natural to touch interaction while letting content shine through.

---

## Visual Properties

### 1. Lensing (Primary Visual Characteristic)

Liquid Glass defines itself through **lensing** - the warping and bending of light that communicates presence, motion, and form.

**How it works**:
- Dynamically concentrates and shapes light in real-time
- Provides definition against background while feeling visually grounded
- Controls feel ultra-lightweight and transparent while visually distinguishable
- Elements materialize in/out by modulating light bending (not fading)

**Design Implication**: Unlike previous materials that scattered light, Liquid Glass uses instinctive visual cues from the natural world to provide separation.

### 2. Motion & Fluidity

Motion and visuals were designed as one unified experience:

- **Instant flex and energize** - Responds to interaction by flexing with light
- **Gel-like flexibility** - Communicates transient, malleable nature
- **Moves in tandem** with interaction - Aligns with dynamism of thinking and movement
- **Temporary lift** - Elements can lift into Liquid Glass on interaction (great for controls)
- **Dynamic morphing** - Continuously shape-shifts between app states as a singular floating plane
- **Lightweight transitions** - Menus pop open in-line, maintaining clear relationship to source

### 3. Adaptive Behavior

Liquid Glass **continuously adapts** without fixed light/dark appearance:

**Content-aware adaptation**:
- Shadows become more prominent when text scrolls underneath
- Tint and dynamic range shift to ensure legibility
- Independently switches light/dark to feel at home in any context
- Larger elements (menus, sidebars) simulate thicker material with deeper shadows and richer lensing

**Platform adaptation**:
- Nests perfectly into rounded corners of windows
- Forms distinct functional layer for controls/navigation
- Ambient environment (colorful content nearby) subtly spills onto surface
- Light reflects, scatters, and bleeds into shadows

---

## Implementation Guide

### Basic API Usage

#### SwiftUI: `glassEffect` Modifier

```swift
// Basic usage - applies glass within capsule shape
Text("Hello")
    .glassEffect()

// Custom shape
Text("Hello")
    .glassEffect(in: RoundedRectangle(cornerRadius: 12))

// Interactive elements (iOS - for controls/containers)
Button("Tap Me") {
    // action
}
.glassEffect()
.interactive() // Add for custom controls on iOS
```

**Automatic Adoption**: Simply recompiling with Xcode 26 brings Liquid Glass to standard controls automatically.

### Variants: Regular vs Clear

**CRITICAL DECISION**: Never mix Regular and Clear in the same interface.

#### Regular Variant (Default - Use Most Often)

**Characteristics**:
- Most versatile, use in 95% of cases
- Full visual and adaptive effects
- Provides legibility regardless of context
- Works in any size, over any content
- Anything can be placed on top

**When to use**: Navigation bars, tab bars, toolbars, buttons, menus, sidebars

```swift
// Regular is the default
NavigationView {
    // Content
}
.glassEffect() // Uses Regular variant
```

#### Clear Variant (Special Cases Only)

**Characteristics**:
- Permanently more transparent
- No adaptive behaviors
- Allows content richness to interact with glass
- **Requires dimming layer** for legibility

**Use ONLY when ALL three conditions are met**:
1. ✅ Element is over **media-rich content**
2. ✅ Content layer won't be negatively affected by **dimming layer**
3. ✅ Content above glass is **bold and bright**

```swift
// Clear variant with localized dimming for small footprints
ZStack {
    MediaRichBackground()
        .overlay(.black.opacity(0.3)) // Dimming layer

    BoldBrightControl()
        .glassEffect(.clear)
}
```

**⚠️ WARNING**: Using Clear without meeting all three conditions results in poor legibility.

---

## Layered System Architecture

Liquid Glass is composed of multiple layers working together:

### 1. Highlights Layer
- Light sources shine on material, producing highlights responding to geometry
- Lights move during interactions (lock/unlock), defining silhouette
- Some cases respond to device motion (feels aware of position in real world)

### 2. Shadows Layer
- Aware of background content
- Increases shadow opacity over text for separation
- Lowers shadow opacity over solid light backgrounds
- Ensures elements are always easy to spot

### 3. Internal Glow (Interaction Feedback)
- Material illuminates from within on interaction
- Glow starts under fingertips, spreads throughout element
- Spreads to nearby Liquid Glass elements
- Interacts with flexible properties - feels natural and fluid
- Makes interface feel alive and connected to physical world

### 4. Adaptive Tinting Layer
- Multiple layers adapt together to maintain hierarchy
- Windows losing focus visually recede (Mac/iPad)
- All behaviors come built-in automatically

---

## Design Principles & Best Practices

### ✅ DO: Reserve for Navigation Layer

**Correct Usage**:
```
[Content Layer - No Glass]
    ↓
[Navigation Layer - Liquid Glass]
    • Tab bars
    • Navigation bars
    • Toolbars
    • Floating controls
```

**Why**: Liquid Glass floats above content, creating clear hierarchy.

### ❌ DON'T: Use on Content Layer

**Wrong**:
```swift
// DON'T apply to table views, lists, or content
List(items) { item in
    Text(item.name)
}
.glassEffect() // ❌ Competes with navigation, muddy hierarchy
```

**Why**: Makes elements compete, creates visual confusion.

### ❌ DON'T: Stack Glass on Glass

**Wrong**:
```swift
ZStack {
    NavigationBar()
        .glassEffect() // ❌

    FloatingButton()
        .glassEffect() // ❌ Glass on glass
}
```

**Correct**:
```swift
ZStack {
    NavigationBar()
        .glassEffect()

    FloatingButton()
        .foregroundStyle(.primary) // Use fills, transparency, vibrancy
        // Feels like thin overlay part of the material
}
```

### ✅ DO: Avoid Content Intersections in Steady State

**Wrong**: Content intersects with Liquid Glass when app launches

**Correct**: Reposition or scale content to maintain separation in steady states

**Why**: Prevents unwanted visual noise; intersections acceptable during scrolling/transitions.

---

## Scroll Edge Effects

Work in concert with Liquid Glass to maintain separation and legibility with scrolling content.

**How they work**:
- Content begins scrolling → effect gently dissolves content into background
- Lifts glass visually above moving content
- Floating elements (titles) remain clear
- Darker content triggers dark style → subtle dimming for contrast

### Hard Style Effect

Use when pinned accessory views exist (e.g., column headers):

```swift
ScrollView {
    // Content
}
.scrollEdgeEffect(.hard) // Uniform across toolbar + pinned accessories
```

**When to use**: Extra visual separation between floating elements in accessory view and scrolling content.

---

## Tinting & Color

### New Tinting System

Liquid Glass introduces **adaptive tinting** that respects material principles and maximizes legibility.

**How it works**:
1. Selecting color generates range of tones
2. Tones mapped to content brightness underneath element
3. Inspired by colored glass in reality
4. Changes hue, brightness, saturation based on background
5. Doesn't deviate too much from intended color

**Compatible with all glass behaviors** (morphing, adaptation, interaction).

```swift
Button("Primary Action") {
    // action
}
.tint(.red) // Adaptive tinting automatically applied
.glassEffect()
```

### Tinting Best Practices

**✅ DO: Use for Primary Actions**
```swift
// Good - Emphasizes primary action
Button("View Bag") {
    // action
}
.tint(.red)
.glassEffect()
```

**❌ DON'T: Tint Everything**
```swift
// Wrong - When everything is tinted, nothing stands out
VStack {
    Button("Action 1").tint(.blue).glassEffect()
    Button("Action 2").tint(.green).glassEffect()
    Button("Action 3").tint(.purple).glassEffect()
} // ❌ Confusing, no hierarchy
```

**Solution**: Use color in content layer instead, reserve tinting for primary UI actions.

### Solid Fills vs Tinting

**Solid fills break Liquid Glass character**:
```swift
// ❌ Opaque, breaks visual character
Button("Action") {}
    .background(.red) // Solid, opaque

// ✅ Transparent, grounded in environment
Button("Action") {}
    .tint(.red)
    .glassEffect()
```

---

## Legibility & Contrast

### Automatic Legibility Features

Small elements (navbars, tabbars):
- Constantly adapt appearance based on background
- Flip light/dark for discernibility

Large elements (menus, sidebars):
- Adapt based on context
- **Don't flip light/dark** (too distracting for large surface area)

Symbols/glyphs:
- Mirror glass behavior (flip light/dark)
- Maximize contrast automatically
- All content on Regular variant receives this treatment

### Custom Colors

Use selectively for distinct functional purpose:

```swift
// Selective tinting for emphasis
NavigationView {
    List {
        // Content
    }
    .toolbar {
        ToolbarItem {
            Button("Important") {}
                .tint(.orange) // Brings attention
        }
    }
}
```

**Applies to**: Labels, text, fully tinted buttons, time on lock screen, etc.

---

## Accessibility

Liquid Glass offers several accessibility features that modify material **without sacrificing its magic**:

### Reduced Transparency
- Makes Liquid Glass frostier
- Obscures more content behind it
- Applied automatically when system setting enabled

### Increased Contrast
- Makes elements predominantly black or white
- Highlights with contrasting border
- Applied automatically when system setting enabled

### Reduced Motion
- Decreases intensity of effects
- Disables elastic properties
- Applied automatically when system setting enabled

**Developer Action Required**: None - all features available automatically when using Liquid Glass.

---

## Performance Considerations

### View Hierarchy Impact

**Concern**: Liquid Glass rendering cost in complex view hierarchies

**Guidance**:
- Regular variant optimized for performance
- Larger elements (menus, sidebars) use more pronounced effects but managed by system
- Avoid excessive nesting of glass elements

**Optimization**:
```swift
// ❌ Avoid deep nesting
ZStack {
    GlassContainer1()
        .glassEffect()
    ZStack {
        GlassContainer2()
            .glassEffect()
        // More nesting...
    }
}

// ✅ Flatten hierarchy
VStack {
    GlassContainer1()
        .glassEffect()

    GlassContainer2()
        .glassEffect()
}
```

### Rendering Costs

**Adaptive behaviors have computational cost**:
- Light/dark switching
- Shadow adjustments
- Tint calculations
- Lensing effects

**System handles optimization**, but be mindful:
- Don't animate Liquid Glass elements unnecessarily
- Use Clear variant sparingly (requires dimming layer computation)
- Profile with Instruments if experiencing performance issues

---

## Testing Liquid Glass

### Visual Regression Testing

Capture screenshots in multiple states:

```swift
func testLiquidGlassAppearance() {
    let app = XCUIApplication()
    app.launch()

    // Test light mode
    XCTContext.runActivity(named: "Light Mode Glass") { _ in
        let screenshot = app.screenshot()
        // Compare with baseline
    }

    // Test dark mode
    app.launchArguments = ["-UIUserInterfaceStyle", "dark"]
    app.launch()

    XCTContext.runActivity(named: "Dark Mode Glass") { _ in
        let screenshot = app.screenshot()
        // Compare with baseline
    }
}
```

### Test Across Configurations

Critical test cases:
- ✅ Light mode vs dark mode
- ✅ Different color schemes (environment)
- ✅ Reduced Transparency enabled
- ✅ Increased Contrast enabled
- ✅ Reduced Motion enabled
- ✅ Dynamic Type (larger text sizes)
- ✅ Content scrolling (verify scroll edge effects)
- ✅ Right-to-left languages

### Accessibility Testing

```swift
func testLiquidGlassAccessibility() {
    // Enable accessibility features via launch arguments
    app.launchArguments += [
        "-UIAccessibilityIsReduceTransparencyEnabled", "1",
        "-UIAccessibilityButtonShapesEnabled", "1",
        "-UIAccessibilityIsReduceMotionEnabled", "1"
    ]

    // Verify glass still functional and legible
    XCTAssertTrue(glassElement.exists)
    XCTAssertTrue(glassElement.isHittable)
}
```

---

## Design Review Pressure: Defending Your Implementation

### The Problem

Under design review pressure, you'll face requests to:
- "Use Clear variant everywhere - Regular is too opaque"
- "Glass on all controls for visual cohesion"
- "More transparency to let content shine through"

These sound reasonable. **But they violate the framework.** Your job: defend using evidence, not opinion.

### Red Flags - Designer Requests That Violate Skill Guidelines

If you hear ANY of these, **STOP and reference the skill**:

- ❌ **"Use Clear everywhere"** – Clear requires three specific conditions, not design preference
- ❌ **"Glass looks better than fills"** – Correct layer (navigation vs content) trumps aesthetics
- ❌ **"Users won't notice the difference"** – Clear variant fails legibility tests in low-contrast scenarios
- ❌ **"Stack glass on glass for consistency"** – Explicitly prohibited; use fills instead
- ❌ **"Apply glass to Lists for sophistication"** – Lists are content layer; causes visual confusion

### How to Push Back Professionally

**Step 1: Show the Framework**

```
"I want to make this change, but let me show you Apple's guidance on Clear variant.
It requires THREE conditions:

1. Media-rich content background
2. Dimming layer for legibility
3. Bold, bright controls on top

Let me show which screens meet all three..."
```

**Step 2: Demonstrate the Risk**

Open the app on a device. Show:
- Clear variant in low-contrast scenario (unreadable)
- Regular variant in same scenario (legible)
- Reference WWDC 219 session

**Step 3: Offer Compromise**

```
"Clear can work beautifully in these 6 hero sections where all three conditions apply.
Regular handles everything else with automatic legibility. Best of both worlds."
```

**Step 4: Document the Decision**

If overruled (designer insists on Clear everywhere):

```
Slack message to PM + designer:

"Design review decided to use Clear variant across all controls.
Important: Clear variant requires legibility testing in low-contrast scenarios
(bright sunlight, dark content). If we see accessibility issues after launch,
we'll need an expedited follow-up. I'm flagging this proactively."
```

**Why this works:**
- You're not questioning their taste (you like Clear too)
- You're raising accessibility/legibility risk
- You're offering a solution that preserves their vision in hero sections
- You're documenting the decision (protects you post-launch)

### Real-World Example: App Store Launch Blocker (36-Hour Deadline)

**Scenario:**
- 36 hours to launch
- Chief designer says: "Clear variant everywhere"
- Client watching the review meeting
- You already implemented Regular per the skill

**What to do:**

```swift
// In the meeting, demo side-by-side:

// Regular variant (current implementation)
NavigationBar()
    .glassEffect() // Automatic legibility

// Clear variant (requested)
NavigationBar()
    .glassEffect(.clear) // Requires dimming layer below

// Show the three-condition checklist
// Demonstrate which screens pass/fail
// Offer: Clear in hero sections, Regular elsewhere
```

**Result:**
- 30-minute compromise demo
- 90 minutes to implement changes
- Launch on schedule with optimal legibility
- No post-launch accessibility complaints

### When to Accept the Design Decision (Even If You Disagree)

Sometimes designers have valid reasons to override the skill. Accept if:

- [ ] They understand the three-condition framework
- [ ] They're willing to accept legibility risks
- [ ] You document the decision in writing
- [ ] They commit to monitoring post-launch feedback

**Document in Slack:**

```
"Design review decided to use Clear variant [in these locations].
We understand this requires:
- All three conditions met: [list them]
- Potential legibility issues in low-contrast scenarios
- Accessibility testing across brightness levels

Monitoring plan:
- Gather user feedback first 48 hours
- Run accessibility audit
- Have fallback to Regular variant ready for push if needed"
```

This protects both of you and shows you're not blocking - just de-risking.

---

## Expert Review Checklist

When reviewing Liquid Glass implementation (your code or others'), check:

### 1. Material Appropriateness
- [ ] Is Liquid Glass used only on navigation layer (not content)?
- [ ] Are standard controls getting glass automatically via Xcode 26 recompile?
- [ ] Is glass avoided on glass situations?

### 2. Variant Selection
- [ ] Is Regular variant used for most cases?
- [ ] If Clear variant used, do all three conditions apply?
  - [ ] Over media-rich content?
  - [ ] Dimming layer acceptable?
  - [ ] Content above is bold and bright?
- [ ] Are Regular and Clear never mixed in same interface?

### 3. Legibility & Contrast
- [ ] Are primary actions selectively tinted (not everything)?
- [ ] Is color used in content layer for overall app color scheme?
- [ ] Are solid fills avoided on glass elements?
- [ ] Do elements maintain legibility on various backgrounds?

### 4. Layering & Hierarchy
- [ ] Are content intersections avoided in steady states?
- [ ] Are elements on top of glass using fills/transparency (not glass)?
- [ ] Is visual hierarchy clear (navigation layer vs content layer)?

### 5. Scroll Edge Effects
- [ ] Are scroll edge effects applied where Liquid Glass meets scrolling content?
- [ ] Is hard style used for pinned accessory views?

### 6. Accessibility
- [ ] Does implementation work with Reduced Transparency?
- [ ] Does implementation work with Increased Contrast?
- [ ] Does implementation work with Reduced Motion?
- [ ] Are interactive elements hittable in all configurations?

### 7. Performance
- [ ] Is view hierarchy reasonably flat?
- [ ] Are glass elements animated only when necessary?
- [ ] Is Clear variant used sparingly?

---

## Common Mistakes & Solutions

### Mistake 1: Using Glass Everywhere

**Wrong**:
```swift
List(landmarks) { landmark in
    LandmarkRow(landmark)
        .glassEffect() // ❌
}
.glassEffect() // ❌
```

**Correct**:
```swift
NavigationView {
    List(landmarks) { landmark in
        LandmarkRow(landmark) // No glass
    }
}
.toolbar {
    ToolbarItem {
        Button("Add") {}
            .glassEffect() // ✅ Navigation layer only
    }
}
```

**Why**: Content layer should defer to Liquid Glass navigation layer.

### Mistake 2: Clear Variant Without Dimming

**Wrong**:
```swift
ZStack {
    VideoPlayer(player: player)

    PlayButton()
        .glassEffect(.clear) // ❌ No dimming, poor legibility
}
```

**Correct**:
```swift
ZStack {
    VideoPlayer(player: player)
        .overlay(.black.opacity(0.4)) // Dimming layer

    PlayButton()
        .glassEffect(.clear) // ✅
}
```

### Mistake 3: Over-Tinting

**Wrong**: All buttons tinted different colors

**Correct**: Primary action tinted, others use standard appearance

### Mistake 4: Static Material Expectations

**Wrong**: Assuming glass always looks the same (e.g., hardcoded shadows, fixed opacity)

**Correct**: Embrace adaptive behavior, test across light/dark modes and backgrounds

---

## Troubleshooting

### Visual Artifacts

**Issue**: Glass appears too transparent or invisible

**Check**:
1. Are you using Clear variant? (Switch to Regular if inappropriate)
2. Is background content extremely light or dark? (Glass adapts - this may be correct behavior)
3. Is Reduced Transparency enabled? (Check accessibility settings)

**Issue**: Glass appears opaque or has harsh edges

**Check**:
1. Are you using solid fills on glass? (Remove, use tinting)
2. Is Increased Contrast enabled? (Expected behavior)
3. Is custom shape too complex? (Simplify geometry)

### Dark Mode Issues

**Issue**: Glass doesn't flip to dark style on dark backgrounds

**Check**:
1. Is element large (menu, sidebar)? (Large elements don't flip - by design)
2. Is background actually dark? (Use Color Picker to verify)
3. Are you overriding appearance? (Remove `.preferredColorScheme()` if unintended)

**Issue**: Content on glass not legible in dark mode

**Fix**:
```swift
// Let SwiftUI handle contrast automatically
Text("Label")
    .foregroundStyle(.primary) // ✅ Adapts automatically

// Don't hardcode colors
Text("Label")
    .foregroundColor(.black) // ❌ Won't adapt to dark mode
```

### Performance Issues

**Issue**: Scrolling feels janky with Liquid Glass

**Debug**:
1. Profile with Instruments (see `swiftui-performance` skill)
2. Check for excessive view body updates
3. Simplify view hierarchy under glass
4. Verify not applying glass to content layer (major performance hit)

**Issue**: Animations stuttering

**Check**:
1. Are you animating glass shape changes? (Expensive)
2. Profile with SwiftUI Instrument for long view updates
3. Consider reducing glass usage if critical path

---

## Migration from Previous Materials

### From UIBlurEffect / NSVisualEffectView

**Before** (UIKit):
```swift
let blurEffect = UIBlurEffect(style: .systemMaterial)
let blurView = UIVisualEffectView(effect: blurEffect)
view.addSubview(blurView)
```

**After** (SwiftUI with Liquid Glass):
```swift
ZStack {
    // Content
}
.glassEffect()
```

**Benefits**:
- Automatic adaptation (no manual style switching)
- Built-in interaction feedback
- Platform-appropriate appearance
- Accessibility features included

### From Custom Materials

If you've built custom translucent effects:

1. **Try Liquid Glass first** - may provide desired effect automatically
2. **Evaluate Regular vs Clear** - Clear may match custom transparency needs
3. **Test across configurations** - Liquid Glass adapts automatically
4. **Measure performance** - Likely improvement over custom implementations

**When to keep custom materials**:
- Specific artistic effect not achievable with Liquid Glass
- Backward compatibility with iOS < 26 required
- Non-standard UI paradigm incompatible with Liquid Glass principles

---

## API Reference

### SwiftUI Modifiers

#### `glassEffect(in:isInteractive:)`

Applies Liquid Glass effect to view.

```swift
func glassEffect<S: Shape>(
    in shape: S = Capsule(),
    isInteractive: Bool = false
) -> some View
```

**Parameters**:
- `shape`: Shape defining glass bounds (default: `Capsule()`)
- `isInteractive`: On iOS, enables interactive mode for custom controls (default: `false`)

**Returns**: View with Liquid Glass effect applied

**Availability**: iOS 26+, iPadOS 26+, macOS Tahoe+, visionOS 3+

**Example**:
```swift
// Default capsule shape
Text("Hello").glassEffect()

// Custom shape
Text("Hello").glassEffect(in: RoundedRectangle(cornerRadius: 16))

// Interactive (iOS)
Button("Tap") {}.glassEffect(isInteractive: true)
```

#### `glassEffect(_:in:isInteractive:)`

Applies specific Liquid Glass variant.

```swift
func glassEffect<S: Shape>(
    _ variant: GlassVariant,
    in shape: S = Capsule(),
    isInteractive: Bool = false
) -> some View
```

**Parameters**:
- `variant`: `.regular` or `.clear`
- `shape`: Shape defining glass bounds
- `isInteractive`: Interactive mode for custom controls (iOS)

**Example**:
```swift
Text("Hello").glassEffect(.clear, in: Circle())
```

#### `scrollEdgeEffect(_:)`

Configures scroll edge appearance with Liquid Glass.

```swift
func scrollEdgeEffect(_ style: ScrollEdgeStyle) -> some View
```

**Parameters**:
- `style`: `.automatic`, `.soft`, or `.hard`

**Example**:
```swift
ScrollView {
    // Content
}
.scrollEdgeEffect(.hard) // For pinned accessories
```

### Types

#### `GlassVariant`

```swift
enum GlassVariant {
    case regular  // Default - full adaptive behavior
    case clear    // More transparent, no adaptation
}
```

#### `ScrollEdgeStyle`

```swift
enum ScrollEdgeStyle {
    case automatic  // System determines style
    case soft       // Gradual fade
    case hard       // Uniform effect across toolbar height
}
```

---

## WWDC 2025 References

**Primary Session**:
- [Meet Liquid Glass - WWDC25 Session 219](https://developer.apple.com/videos/play/wwdc2025/219/)
  - Design principles and visual properties
  - Adaptive behavior and platform integration
  - Variants and usage guidelines

**Related Sessions**:
- [Build a SwiftUI app with the new design - WWDC25 Session 323](https://developer.apple.com/videos/play/wwdc2025/323/)
  - Practical implementation patterns

- [What's new in SwiftUI - WWDC25 Session 256](https://developer.apple.com/videos/play/wwdc2025/256/)
  - API overview and integration with SwiftUI ecosystem

**Documentation**:
- [Landmarks: Building an app with Liquid Glass](https://developer.apple.com/documentation/SwiftUI/Landmarks-Building-an-app-with-Liquid-Glass)
- [Applying Liquid Glass to custom views](https://developer.apple.com/documentation/SwiftUI/Applying-Liquid-Glass-to-custom-views)

**Sample Code**:
- Landmarks tutorial series (WWDC 2025)

---

## Version History

- **1.1.0**: Added "Design Review Pressure: Defending Your Implementation" section from TDD pressure testing. Includes red flags for designer requests that violate guidelines, 4-step push-back framework with demo and documentation steps, real-world App Store launch example (36-hour deadline), and guidance on when to accept design overrides. Enables developers to professionally defend Regular vs Clear variant decisions under deadline and client pressure
- **1.0.0 (WWDC 2025)**: Initial skill based on Liquid Glass introduction at WWDC 2025, covering design principles, implementation patterns, variants, troubleshooting, and expert review capabilities.

---

**Last Updated**: WWDC 2025
**Minimum Platform**: iOS 26, iPadOS 26, macOS Tahoe, visionOS 3
**Xcode Version**: Xcode 26+
