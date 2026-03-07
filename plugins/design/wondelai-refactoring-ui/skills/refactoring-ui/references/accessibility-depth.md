# Accessibility Deep Dive

Comprehensive WCAG 2.1 AA compliance checklist with practical implementation guidance.

## Accessibility Philosophy

Accessibility isn't just compliance—it improves UX for everyone:
- Keyboard navigation helps power users
- Good contrast helps in bright sunlight
- Clear focus states help everyone understand what's selected
- Proper headings help screen readers AND SEO

---

## WCAG 2.1 AA Checklist

### Perceivable

Users must be able to perceive content.

#### 1.1 Text Alternatives

**All images need alt text:**

```html
<!-- Decorative image (no alt) -->
<img src="divider.svg" alt="" role="presentation">

<!-- Informative image -->
<img src="chart.png" alt="Sales increased 40% from Q1 to Q2">

<!-- Functional image (button/link) -->
<button>
  <img src="search.svg" alt="Search">
</button>

<!-- Complex image (needs long description) -->
<figure>
  <img src="diagram.png" alt="System architecture overview" aria-describedby="diagram-desc">
  <figcaption id="diagram-desc">Detailed description of the system architecture...</figcaption>
</figure>
```

**Icons:**
```html
<!-- Icon with visible text (icon is decorative) -->
<button>
  <svg aria-hidden="true">...</svg>
  <span>Settings</span>
</button>

<!-- Icon-only button -->
<button aria-label="Settings">
  <svg aria-hidden="true">...</svg>
</button>
```

#### 1.3 Adaptable

**Semantic HTML structure:**

```html
<!-- Use semantic elements -->
<header>...</header>
<nav>...</nav>
<main>
  <article>
    <h1>Page Title</h1>
    <section>
      <h2>Section Title</h2>
    </section>
  </article>
</main>
<footer>...</footer>

<!-- Not this -->
<div class="header">...</div>
<div class="nav">...</div>
```

**Heading hierarchy:**
- One `<h1>` per page
- Don't skip levels (h1 → h3)
- Headings describe content structure

**Form labels:**
```html
<!-- Explicit label -->
<label for="email">Email</label>
<input id="email" type="email">

<!-- Implicit label -->
<label>
  Email
  <input type="email">
</label>

<!-- Hidden label (for visual designs without labels) -->
<label for="search" class="sr-only">Search</label>
<input id="search" type="search" placeholder="Search...">
```

#### 1.4 Distinguishable

**Color contrast requirements:**

| Content Type | Minimum Ratio | Tool |
|--------------|---------------|------|
| Normal text (<18px) | 4.5:1 | WebAIM Contrast Checker |
| Large text (≥18px or ≥14px bold) | 3:1 | |
| UI components & graphics | 3:1 | |

**Common contrast fixes:**

```css
/* Too light - fails */
.text-light { color: #9ca3af; } /* gray-400: 3.1:1 on white */

/* Passes AA */
.text-muted { color: #6b7280; } /* gray-500: 4.6:1 on white */

/* Passes AAA */
.text-strong { color: #374151; } /* gray-700: 9.1:1 on white */
```

**Don't rely on color alone:**

```html
<!-- Bad: only color indicates error -->
<input class="border-red-500">

<!-- Good: color + icon + text -->
<input class="border-red-500" aria-invalid="true" aria-describedby="error">
<p id="error" class="text-red-600">
  <svg aria-hidden="true">⚠️</svg>
  Email is required
</p>
```

**Text resize:**
- Content must be readable at 200% zoom
- Use relative units (rem, em) not px for text
- Test by zooming browser to 200%

---

### Operable

Users must be able to operate the interface.

#### 2.1 Keyboard Accessible

**All functionality must work with keyboard:**

| Key | Expected Behavior |
|-----|-------------------|
| Tab | Move to next focusable element |
| Shift+Tab | Move to previous focusable element |
| Enter | Activate links, buttons |
| Space | Activate buttons, toggle checkboxes |
| Arrows | Navigate within components (tabs, menus, radios) |
| Escape | Close modals, dropdowns, cancel actions |

**Focus must be visible:**

```css
/* Don't remove focus outlines */
:focus {
  outline: none; /* ❌ Never do this without replacement */
}

/* Do provide visible focus */
:focus-visible {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}

/* Or use ring utility */
.focusable:focus-visible {
  @apply ring-2 ring-blue-500 ring-offset-2;
}
```

**Keyboard traps:**
- Modal dialogs should trap focus inside
- But must have a way to exit (Escape key, close button)

```jsx
// Focus trap for modals
function Modal({ isOpen, onClose, children }) {
  const modalRef = useRef();

  useEffect(() => {
    if (isOpen) {
      // Focus first focusable element
      const firstFocusable = modalRef.current.querySelector('button, input, a');
      firstFocusable?.focus();

      // Trap focus inside
      const handleTab = (e) => {
        if (e.key === 'Tab') {
          // ... trap logic
        }
        if (e.key === 'Escape') {
          onClose();
        }
      };

      document.addEventListener('keydown', handleTab);
      return () => document.removeEventListener('keydown', handleTab);
    }
  }, [isOpen]);

  // Return focus on close
}
```

**Skip links:**

```html
<body>
  <a href="#main-content" class="sr-only focus:not-sr-only">
    Skip to main content
  </a>
  <nav>...</nav>
  <main id="main-content">...</main>
</body>
```

#### 2.4 Navigable

**Page titles:**
- Unique, descriptive page titles
- Format: `Page Name | Site Name`

**Focus order:**
- Must follow logical reading order
- Don't use positive `tabindex` values (messes up order)
- Only use `tabindex="0"` (make focusable) or `tabindex="-1"` (programmatically focusable)

**Link purpose:**
```html
<!-- Bad -->
<a href="/article">Click here</a>
<a href="/article">Read more</a>

<!-- Good -->
<a href="/article">Read more about accessibility best practices</a>

<!-- Or with context -->
<a href="/article" aria-describedby="article-title">Read more</a>
```

---

### Understandable

Users must be able to understand content and operation.

#### 3.1 Readable

**Language declaration:**
```html
<html lang="en">
  <body>
    <p>This is English.</p>
    <p lang="fr">Ceci est français.</p>
  </body>
</html>
```

#### 3.2 Predictable

**Consistent navigation:**
- Same navigation in same location across pages
- Same elements behave the same way

**No unexpected changes:**
- Form inputs don't auto-submit on change
- No unexpected pop-ups
- Focus doesn't move unexpectedly

```html
<!-- Bad: changes page on select -->
<select onchange="window.location = this.value">...</select>

<!-- Good: requires explicit action -->
<select id="region">...</select>
<button onclick="navigate()">Go</button>
```

#### 3.3 Input Assistance

**Error identification:**
```html
<label for="email">Email</label>
<input
  id="email"
  type="email"
  aria-invalid="true"
  aria-describedby="email-error"
>
<p id="email-error" class="error">
  Please enter a valid email address (e.g., name@example.com)
</p>
```

**Required fields:**
```html
<label for="name">
  Name <span aria-hidden="true">*</span>
  <span class="sr-only">(required)</span>
</label>
<input id="name" required aria-required="true">
```

**Error prevention for critical actions:**
- Confirm destructive actions
- Allow review before submission
- Provide undo capability

---

### Robust

Content must work with current and future technologies.

#### 4.1 Compatible

**Valid HTML:**
- Unique IDs
- Complete start/end tags
- Proper nesting

**ARIA usage:**
```html
<!-- If you use ARIA, use it correctly -->

<!-- Roles -->
<div role="button" tabindex="0" onclick="...">Fake Button</div>
<!-- Better: just use <button> -->

<!-- States -->
<button aria-pressed="true">Bold</button>
<button aria-expanded="false" aria-controls="menu">Menu</button>

<!-- Live regions -->
<div aria-live="polite" aria-atomic="true">
  <!-- Screen reader announces changes here -->
</div>
```

---

## Focus Management

### When to Manage Focus

| Scenario | Focus Action |
|----------|--------------|
| Modal opens | Focus first element inside modal |
| Modal closes | Return focus to trigger element |
| Error occurs | Focus error message or first invalid field |
| New content loads | Focus heading or first new element |
| Item deleted | Focus previous/next item or container |

### Implementation

```jsx
// Store trigger reference
const triggerRef = useRef();

function openModal() {
  triggerRef.current = document.activeElement;
  setIsOpen(true);
}

function closeModal() {
  setIsOpen(false);
  // Return focus after state update
  setTimeout(() => triggerRef.current?.focus(), 0);
}
```

### Roving Tabindex (for component groups)

```jsx
// Tab panels, menu items, radio groups
function Tabs({ tabs }) {
  const [activeIndex, setActiveIndex] = useState(0);

  const handleKeyDown = (e) => {
    if (e.key === 'ArrowRight') {
      setActiveIndex((activeIndex + 1) % tabs.length);
    }
    if (e.key === 'ArrowLeft') {
      setActiveIndex((activeIndex - 1 + tabs.length) % tabs.length);
    }
  };

  return (
    <div role="tablist" onKeyDown={handleKeyDown}>
      {tabs.map((tab, i) => (
        <button
          key={tab.id}
          role="tab"
          tabIndex={i === activeIndex ? 0 : -1}
          aria-selected={i === activeIndex}
          ref={i === activeIndex ? (el) => el?.focus() : null}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
```

---

## Screen Reader Considerations

### Announce Dynamic Changes

```html
<!-- Live region for status messages -->
<div aria-live="polite" class="sr-only" id="status"></div>

<script>
function showSuccess(message) {
  document.getElementById('status').textContent = message;
}
</script>
```

### Hide Decorative Content

```html
<!-- Hidden from screen readers -->
<svg aria-hidden="true">...</svg>
<span aria-hidden="true">•</span>
```

### Provide Context

```html
<!-- Ambiguous button -->
<button>Delete</button>

<!-- Clear button -->
<button aria-label="Delete comment by John">Delete</button>

<!-- Or use aria-describedby -->
<button aria-describedby="comment-123-author">Delete</button>
<span id="comment-123-author" class="sr-only">comment by John</span>
```

---

## Testing Tools

### Automated Testing

| Tool | What It Catches |
|------|-----------------|
| axe DevTools | ~30% of WCAG issues |
| WAVE | Similar to axe, visual overlay |
| Lighthouse | Basic accessibility audit |
| ESLint a11y plugin | Catches issues in JSX |

### Manual Testing Required

Automated tools miss ~70% of issues. Manual testing needed for:
- Keyboard navigation flow
- Screen reader experience
- Focus management
- Meaningful alt text
- Logical heading structure

### Testing Checklist

- [ ] Navigate entire page with keyboard only
- [ ] Test with screen reader (VoiceOver, NVDA)
- [ ] Check color contrast with tool
- [ ] Zoom to 200% and verify usability
- [ ] Test with high contrast mode
- [ ] Verify focus indicators visible
- [ ] Check heading structure with outline tool
- [ ] Run axe DevTools audit
- [ ] Test forms with validation errors

---

## Common Fixes Quick Reference

| Issue | Fix |
|-------|-----|
| Missing alt text | Add descriptive alt or `alt=""` for decorative |
| Low contrast | Use gray-600+ for text on white |
| Missing focus style | Add `focus-visible` ring/outline |
| Click-only interaction | Add keyboard handler + focusability |
| Missing form labels | Add `<label>` with `for` attribute |
| Heading skip | Use h1→h2→h3 in order |
| Color-only indicator | Add icon/text alongside color |
| Modal focus trap | Trap focus, allow Escape to close |
| Auto-playing media | Add pause control, don't autoplay |
| Motion | Respect `prefers-reduced-motion` |
