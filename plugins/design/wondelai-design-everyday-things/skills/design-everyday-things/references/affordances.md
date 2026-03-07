# Affordances: Designing for Action

An affordance is a relationship between an object and a person that determines how the object could possibly be used. A chair affords sitting. A handle affords pulling. A button affords pressing. Affordances exist in the physical properties of the object relative to the capabilities of the user, whether or not the user perceives them. The central design challenge is making affordances visible and unmistakable.

## Affordance Types

| Type | Definition | Key Characteristic | Example |
|------|------------|-------------------|---------|
| **Real affordance** | An action the object genuinely supports | Exists in the physics/code | A physical button can be pressed; a text input accepts keystrokes |
| **Perceived affordance** | An action the user believes is possible | Exists in the user's mind | A raised, shadowed rectangle looks pressable even if it is decorative |
| **Hidden affordance** | An action that exists but is not visible | Discoverable only by accident or instruction | Right-click context menus, multi-finger trackpad gestures |
| **False affordance** | An appearance of action that does not exist | Misleads the user | Underlined blue text that is not a link; a card with a shadow that is not clickable |
| **Anti-affordance** | A deliberate prevention of action | Communicates "you cannot do this" | A grayed-out disabled button; a railing that prevents falling |

### The Critical Distinction

Real affordances are properties of the system. Perceived affordances are properties of the user's interpretation. Good design aligns these two: every real affordance should be perceived, and no false affordance should exist.

---

## Digital Affordance Patterns

### Buttons

| Property | Affords | Signal |
|----------|---------|--------|
| Raised appearance / shadow | Pressing / clicking | Drop shadow, gradient, border |
| Color contrast with background | Attention and interaction | Primary color, high contrast |
| Hover state change | "I respond to interaction" | Background darkens, cursor changes |
| Active/pressed state | "Your click registered" | Slight depression, color shift |
| Disabled state (grayed) | "Not available right now" | Reduced opacity, no cursor change |

### Links

| Property | Affords | Signal |
|----------|---------|--------|
| Color differentiation | Navigation | Blue or brand-accent color |
| Underline | "I am clickable text" | Text decoration underline |
| Cursor change to pointer | "Click me" | CSS cursor: pointer |
| Visited state color | "You have been here" | Purple or muted color |

### Text Inputs

| Property | Affords | Signal |
|----------|---------|--------|
| Border / outline | "Type here" | Visible rectangular boundary |
| Placeholder text | "This is what goes here" | Light gray sample text |
| Focus ring | "You are editing this" | Blue outline on focus |
| Blinking cursor | "I am ready for input" | Text insertion cursor |
| Label above/beside | "This field is for X" | Descriptive text |

### Sliders

| Property | Affords | Signal |
|----------|---------|--------|
| Handle / thumb | Dragging | Circular or rectangular grab target |
| Track | Range of movement | Horizontal or vertical line |
| Fill color | Current value | Colored portion of the track |
| Min/max labels | Boundaries | Text or numbers at each end |

### Drag Targets

| Property | Affords | Signal |
|----------|---------|--------|
| Grip dots or lines | "Grab and move me" | Six-dot handle icon |
| Cursor change to grab | "Draggable" | CSS cursor: grab |
| Lift animation on drag start | "I am being moved" | Shadow increase, slight scale up |
| Drop zone highlight | "Drop it here" | Border change, background tint |

---

## Physical vs. Digital Affordances

| Dimension | Physical | Digital |
|-----------|----------|---------|
| **Perception** | Seen, felt, heard directly | Seen on screen; no physical texture |
| **Constraint** | Physics prevents wrong use | Only code prevents wrong use |
| **Discoverability** | Explore by touch and manipulation | Explore by clicking, hovering, scrolling |
| **Feedback** | Immediate tactile response | Must be programmed explicitly |
| **Cultural learning** | Handles, knobs, buttons are universal | UI conventions are learned (hamburger menu, swipe gestures) |
| **Cost of error** | May cause physical harm | Rarely dangerous, but data loss possible |

### Implications for Digital Design

Physical objects get affordances "for free" from their material properties. Digital interfaces must manufacture every affordance through visual design. This means:

1. Every interactive element needs deliberate visual treatment.
2. Non-interactive elements must be visually distinct from interactive ones.
3. New interaction patterns (gestures, voice) start with zero perceived affordance and need onboarding.

---

## The Flat Design Problem: When Affordances Disappear

Flat design (the removal of skeuomorphic visual cues like shadows, gradients, and borders) creates a systematic affordance crisis. When buttons look like labels and labels look like buttons, users cannot distinguish interactive elements from static content.

### What Flat Design Removes

| Removed Cue | Affordance Lost | User Impact |
|-------------|----------------|-------------|
| Drop shadows on buttons | "This is pressable" | Users do not recognize buttons |
| Borders on inputs | "Type here" | Users do not know where to click to type |
| Underlines on links | "This navigates" | Users cannot find links in body text |
| Gradients and bevels | "This is interactive" | All elements look equally flat and static |
| Visual depth / layering | "This is above/below that" | Users lose sense of hierarchy |

### Recovering Affordances in Flat Design

- Use **color contrast** to distinguish interactive elements from static ones.
- Add **hover and focus states** that reveal interactivity.
- Use **consistent spacing** to create clickable regions.
- Apply **subtle shadows or borders** (flat design does not mean zero visual depth).
- Always provide **cursor changes** on interactive elements.
- Pair **icons with labels** so meaning is not ambiguous.

---

## Touch vs. Mouse Affordances

| Factor | Mouse | Touch |
|--------|-------|-------|
| **Hover state** | Available and essential | Does not exist; cannot preview interactivity |
| **Precision** | High (single pixel) | Low (finger covers ~44px) |
| **Right-click** | Common interaction | Not available natively |
| **Drag and drop** | Natural with mouse | Conflicts with scroll gesture |
| **Cursor feedback** | Changes shape to signal affordance | No cursor exists |
| **Target size** | Minimum ~24px | Minimum 44x44px (Apple HIG) or 48x48dp (Material) |

### Touch-Specific Affordance Strategies

- Make all touch targets at least 44x44 points.
- Use visual weight (size, color, shadow) instead of hover states to signal interactivity.
- Provide haptic feedback (vibration) on interaction to replace the tactile click of a mouse button.
- Avoid relying on gestures as the only way to access critical actions; always provide a visible alternative.
- Show visual hints for swipeable content (partial next-card visible, dots indicator).

---

## Affordance Audit Checklist

Use this checklist to evaluate any screen or physical product.

### Interactive Elements

- [ ] Every button is visually distinguishable from non-interactive text and containers.
- [ ] Every link has at least two signals (color + underline, or color + cursor change).
- [ ] Every text input has a visible boundary (border, background contrast, or underline).
- [ ] Every slider has a visible handle and track.
- [ ] Every draggable element has a grip indicator.
- [ ] All touch targets are at least 44x44 points (mobile) or 24x24 pixels (desktop).

### Non-Interactive Elements

- [ ] Static text does not use the same color as links.
- [ ] Decorative images do not have clickable appearance (no pointer cursor, no hover effect).
- [ ] Section headers are not styled like buttons.
- [ ] Cards and containers that are not clickable do not have hover lift effects.

### Hidden Affordances

- [ ] Any gesture-based interaction also has a visible control alternative.
- [ ] Keyboard shortcuts are documented in the interface (tooltip, menu, help).
- [ ] Right-click menus duplicate functionality available through visible controls.
- [ ] Swipeable content shows a visual hint that more content exists.

### False Affordances

- [ ] No underlined text that is not a link.
- [ ] No colored text that looks like a link but is not.
- [ ] No card shadows or hover effects on non-interactive containers.
- [ ] No cursor: pointer on non-interactive elements.

---

## Before/After Examples of Affordance Improvements

### Example 1: Flat Submit Button

**Before**: A gray text label "Submit" with no border, no shadow, no background color. Users do not realize it is clickable.

**After**: A filled blue rectangle with white text "Submit", a subtle shadow, and a darkened hover state. Users immediately recognize it as a button.

**Principle applied**: Perceived affordance aligned with real affordance through visual treatment.

### Example 2: Hidden Navigation

**Before**: A three-line hamburger icon in the top corner. New users do not know it contains navigation. Engagement with secondary pages is low.

**After**: A visible horizontal navigation bar with text labels for the top 4 sections, plus a "More" dropdown for the rest. Engagement with secondary pages increases by 50% or more.

**Principle applied**: Hidden affordance converted to visible affordance.

### Example 3: Non-Obvious Text Input

**Before**: A thin bottom-border line with a small floating label. Users click randomly around the area unsure where the input field actually is.

**After**: A fully bordered rectangle with a label above, placeholder text inside, and a clear focus ring. Users click into the input immediately.

**Principle applied**: Real affordance made perceivable through boundary signifiers.

### Example 4: Gesture-Only Delete

**Before**: On mobile, the only way to delete a list item is to swipe left. Users who do not know the gesture cannot delete items.

**After**: Swipe-to-delete still works, but each item also has a visible trash icon on tap or a long-press menu. All users can access the delete function.

**Principle applied**: Hidden affordance supplemented with visible alternative.

---

## Common Affordance Failures by Platform

### Web

| Failure | Impact | Fix |
|---------|--------|-----|
| Ghost buttons (transparent with thin border) | Low click-through rates | Use filled buttons for primary actions |
| Cards without hover state that are clickable | Users miss clickable content | Add hover elevation or background change |
| Dropdown triggers that look like labels | Users do not know to click | Add a chevron icon and border |

### Mobile (iOS / Android)

| Failure | Impact | Fix |
|---------|--------|-----|
| Small touch targets | Frequent mis-taps, frustration | Minimum 44pt / 48dp targets |
| Swipe-only actions | Core functionality is invisible | Provide visible button alternative |
| Bottom sheet handle with no label | Users do not know to drag up | Add "Swipe up for details" text or an upward chevron |

### Desktop Applications

| Failure | Impact | Fix |
|---------|--------|-----|
| Toolbar with icon-only buttons | Users memorize slowly, new users lost | Add text labels below icons |
| Resizable panels without grab edges | Users cannot resize | Show a dotted grab edge or resize cursor on hover |
| Menu items with no keyboard shortcut listed | Power users cannot accelerate | Show shortcut text next to every menu item |

---

## Accessibility and Affordances

Affordances must work for all users, including those who use assistive technologies.

| User Group | Affordance Consideration |
|-----------|------------------------|
| **Screen reader users** | Every interactive element must have an accessible role (button, link, input) and a descriptive label. Visual affordances are invisible; semantic affordances must replace them. |
| **Keyboard-only users** | Every interactive element must be focusable and operable with Enter or Space. Focus rings are the keyboard equivalent of hover states: they are affordance signifiers. |
| **Low-vision users** | Interactive elements need sufficient color contrast (WCAG 4.5:1 for text, 3:1 for UI components). Size thresholds increase. |
| **Motor-impaired users** | Touch targets must be larger (WCAG recommends 44x44 CSS pixels). Drag-and-drop must have a click-based alternative. |
| **Cognitive disabilities** | Affordances must be explicit, not implied. Labels are better than icons alone. Consistent placement is essential. |

### Accessibility Affordance Checklist

- [ ] All interactive elements have correct ARIA roles or native HTML semantics.
- [ ] Focus order follows visual order.
- [ ] Focus rings are visible and high-contrast.
- [ ] Interactive elements are reachable and operable via keyboard.
- [ ] Color is not the only affordance signal (shape, border, or icon accompanies color).
- [ ] Touch targets meet minimum size requirements.
- [ ] Drag interactions have non-drag alternatives.
