# Animation & Microinteractions

Guidelines for when and how to animate UI elements effectively.

## The Purpose of Animation

Animation should serve a function, not just look nice.

### Valid Reasons to Animate

| Purpose | Example |
|---------|---------|
| **Feedback** | Button press confirmation, form submission success |
| **Orientation** | Showing where something came from or went to |
| **Focus** | Drawing attention to important changes |
| **Teaching** | Demonstrating how something works |
| **Continuity** | Maintaining context during state changes |
| **Delight** | Occasional surprise (use sparingly) |

### Invalid Reasons to Animate

- "It looks cool"
- "The competition does it"
- "To show off our skills"
- Every state change
- To hide slow performance

---

## Timing & Duration

### Duration Guidelines

| Animation Type | Duration | Rationale |
|----------------|----------|-----------|
| Micro-feedback (hover, press) | 100-150ms | Must feel instant |
| Simple transitions (fade, slide) | 150-250ms | Noticeable but quick |
| Complex transitions (modal, navigation) | 250-350ms | Need time to follow |
| Entrances/Reveals | 200-400ms | Can be slightly longer |
| Decorative/Emphasis | 300-500ms | Purpose is to be noticed |

### The 200ms Rule

Most UI animations should be around 200ms:
- Faster than 100ms → Too fast to perceive
- Slower than 400ms → Feels sluggish, interrupts flow

**Exception:** Loading and progress indicators can be slower because they represent real waiting.

### Duration by Distance

Longer travel distance = longer duration (but not proportionally).

```
Small movement (8-16px):   100-150ms
Medium movement (50-100px): 150-250ms
Large movement (full screen): 250-350ms
```

---

## Easing Functions

Easing makes motion feel natural. Linear motion looks robotic.

### Common Easing Curves

| Easing | Use For | Feel |
|--------|---------|------|
| **ease-out** | Elements entering | Fast start, gentle stop |
| **ease-in** | Elements leaving | Gentle start, fast exit |
| **ease-in-out** | Elements moving within view | Smooth throughout |
| **linear** | Progress indicators, opacity changes | Mechanical (intentional) |

### When to Use Each

**Ease-out (default for entrances):**
```css
transition: transform 200ms ease-out;
```
- Modals appearing
- Notifications sliding in
- Dropdowns opening
- Tooltips appearing

**Ease-in (for exits):**
```css
transition: opacity 150ms ease-in;
```
- Modals dismissing
- Elements fading out
- Notifications leaving

**Ease-in-out (for on-screen movement):**
```css
transition: transform 250ms ease-in-out;
```
- Tab indicators sliding
- Carousel transitions
- Drawer/sidebar toggling

### Custom Cubic Bezier

For more personality, customize curves:

```css
/* Snappy entrance */
transition: transform 200ms cubic-bezier(0.34, 1.56, 0.64, 1);

/* Smooth overshoot */
transition: transform 300ms cubic-bezier(0.175, 0.885, 0.32, 1.275);
```

---

## Common Animation Patterns

### Button States

**Hover:**
```css
.btn {
  transition: background-color 100ms ease-out, transform 100ms ease-out;
}
.btn:hover {
  background-color: var(--btn-hover);
}
```

**Active/Pressed:**
```css
.btn:active {
  transform: scale(0.97);
}
```

**Loading state:**
```css
.btn.loading {
  opacity: 0.7;
  pointer-events: none;
}
.btn.loading .spinner {
  animation: spin 1s linear infinite;
}
```

### Modal Entrance/Exit

**Enter:**
```css
.modal {
  opacity: 0;
  transform: scale(0.95) translateY(-10px);
  transition: opacity 200ms ease-out, transform 200ms ease-out;
}
.modal.open {
  opacity: 1;
  transform: scale(1) translateY(0);
}
```

**Exit:**
```css
.modal.closing {
  opacity: 0;
  transform: scale(0.95);
  transition: opacity 150ms ease-in, transform 150ms ease-in;
}
```

### Dropdown/Menu

```css
.dropdown {
  opacity: 0;
  transform: translateY(-8px);
  pointer-events: none;
  transition: opacity 150ms ease-out, transform 150ms ease-out;
}
.dropdown.open {
  opacity: 1;
  transform: translateY(0);
  pointer-events: auto;
}
```

### Toast/Notification

```css
.toast {
  transform: translateX(100%);
  transition: transform 300ms ease-out;
}
.toast.visible {
  transform: translateX(0);
}
.toast.exiting {
  transform: translateX(100%);
  transition: transform 200ms ease-in;
}
```

### Skeleton Loading

```css
.skeleton {
  background: linear-gradient(
    90deg,
    #f0f0f0 25%,
    #e0e0e0 50%,
    #f0f0f0 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
```

---

## Loading States

### Types of Loading Indicators

| Type | Use When | Example |
|------|----------|---------|
| **Spinner** | Unknown duration, short wait expected | Button submission |
| **Progress bar** | Known progress, longer operations | File upload |
| **Skeleton** | Loading content layout | Feed items |
| **Pulse/Shimmer** | Refreshing existing content | Pull to refresh |

### Spinner Guidelines

- Don't show immediately (wait 300-500ms)
- If wait < 1 second, spinner may not be needed
- Position in context (where content will appear)
- Provide cancel option for long operations

```jsx
// Delay spinner to avoid flash for fast operations
const [showSpinner, setShowSpinner] = useState(false);

useEffect(() => {
  if (isLoading) {
    const timer = setTimeout(() => setShowSpinner(true), 400);
    return () => clearTimeout(timer);
  }
  setShowSpinner(false);
}, [isLoading]);
```

### Progress Bar Guidelines

- Show percentage when meaningful
- Don't let it jump backwards
- Consider indeterminate state if progress unknown
- Complete to 100% before hiding

### Skeleton Screen Guidelines

- Match layout of actual content
- Use consistent bone shapes
- Animate subtly (shimmer, not bounce)
- Replace with content immediately when loaded

---

## Microinteractions

Small animations that provide feedback and delight.

### Effective Microinteractions

**Toggle switches:**
```css
.toggle-thumb {
  transition: transform 150ms ease-out;
}
.toggle.on .toggle-thumb {
  transform: translateX(20px);
}
```

**Checkbox check:**
```css
.checkmark {
  stroke-dasharray: 20;
  stroke-dashoffset: 20;
  transition: stroke-dashoffset 200ms ease-out;
}
.checkbox.checked .checkmark {
  stroke-dashoffset: 0;
}
```

**Like/Heart animation:**
```css
.heart {
  transform: scale(1);
  transition: transform 150ms ease-out;
}
.heart.liked {
  animation: pop 300ms ease-out;
}
@keyframes pop {
  0% { transform: scale(1); }
  50% { transform: scale(1.2); }
  100% { transform: scale(1); }
}
```

**Input focus:**
```css
.input {
  border-color: #ccc;
  transition: border-color 150ms ease-out, box-shadow 150ms ease-out;
}
.input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}
```

### When Microinteractions Help

- Confirming user action occurred
- Showing state change clearly
- Making interface feel responsive
- Guiding attention to changes

### When to Skip

- Repetitive actions (every keystroke)
- Performance-critical paths
- Accessibility mode (respect reduce-motion)

---

## Accessibility Considerations

### Respect User Preferences

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

### Provide Alternatives

- Don't rely on animation alone to convey information
- Ensure state changes are visible without animation
- Allow users to disable animations in app settings

### Avoid Problematic Animations

| Avoid | Reason |
|-------|--------|
| Flashing/strobing | Can trigger seizures |
| Parallax scrolling | Causes motion sickness |
| Auto-playing video | Distracting, accessibility |
| Infinite loops | Drains attention, battery |

---

## Performance Guidelines

### GPU-Accelerated Properties

Animate these for smooth 60fps:
- `transform` (translate, scale, rotate)
- `opacity`

Avoid animating (causes reflow/repaint):
- `width`, `height`
- `top`, `left`, `right`, `bottom`
- `margin`, `padding`
- `border-width`
- `font-size`

### Use will-change Sparingly

```css
/* Only for elements about to animate */
.modal {
  will-change: transform, opacity;
}

/* Remove after animation */
.modal.static {
  will-change: auto;
}
```

### Batch Animations

Start animations together, not staggered excessively:
- 0-50ms stagger: feels cohesive
- 100ms+ stagger: feels slow, sequential

### Test on Low-end Devices

What's smooth on your MacBook may stutter on a budget Android phone. Test on real devices or throttle CPU in DevTools.

---

## Animation Checklist

Before shipping an animation:

- [ ] Does it serve a purpose (not just decoration)?
- [ ] Is duration appropriate for the action?
- [ ] Does easing feel natural?
- [ ] Does it work with `prefers-reduced-motion`?
- [ ] Is it GPU-accelerated (transform/opacity)?
- [ ] Does it perform well on low-end devices?
- [ ] Can the interface function without it?
