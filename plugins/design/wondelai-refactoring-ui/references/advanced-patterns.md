# Advanced Design Patterns

Extended reference for complex scenarios. Load only when deeper guidance needed.

## Table of Contents
1. [Empty States](#empty-states)
2. [Form Design](#form-design)
3. [Image Treatment](#image-treatment)
4. [Icon Usage](#icon-usage)
5. [Interaction States](#interaction-states)
6. [Color Psychology](#color-psychology)
7. [Border Radius System](#border-radius-system)

---

## Empty States

Empty states are opportunities, not afterthoughts.

**Good empty states include:**
- Illustration or icon (not generic)
- Clear explanation of what goes here
- Primary action to remedy emptiness
- Optional secondary actions

```
❌ "No items"
✅ "No projects yet. Create your first project to get started."
   [+ Create Project]
```

**Match the tone.** A todo app empty state can be playful; an enterprise dashboard should be professional.

---

## Form Design

### Input Sizing

Match input width to expected content:
- Email/URL: Full width or ~400px
- Phone: ~200px
- ZIP code: ~100px
- Street address: Full width
- City: ~200px
- State dropdown: ~150px

### Placeholder vs. Label

**Never use placeholder as the only label.** Placeholders disappear on focus. Always have a visible label.

Placeholders work for:
- Format hints: "MM/DD/YYYY"
- Examples: "e.g., john@example.com"
- Optional clarification

### Input States

```
Default:     border-gray-300
Focus:       border-blue-500 ring-2 ring-blue-200
Error:       border-red-500 ring-2 ring-red-200
Disabled:    bg-gray-100 text-gray-400
Success:     border-green-500 (sparingly)
```

### Button Hierarchy

One primary action per view. Everything else is secondary or tertiary.

```
Primary:    Solid color, high contrast (bg-blue-600 text-white)
Secondary:  Outlined or muted (border border-gray-300)
Tertiary:   Text only (text-blue-600 hover:underline)
Danger:     Red but not screaming (bg-red-600 for confirm, text-red-600 for trigger)
```

### Form Layout

- One column for simple forms
- Two columns ONLY when inputs are related (First/Last name, City/State)
- Labels above inputs on mobile, beside on desktop (optional)
- Group related fields with subtle boundaries or spacing

---

## Image Treatment

### Background Images

**Problem:** Text over images is often unreadable.

**Solutions:**
1. Semi-transparent overlay: `bg-black/50`
2. Gradient overlay: `bg-gradient-to-t from-black/80 to-transparent`
3. Text shadow: `text-shadow: 0 2px 4px rgba(0,0,0,0.5)`
4. Solid color box behind text
5. Choose images with natural dark/simple areas for text

### User Avatars

- Always have a fallback (initials, generic icon)
- Consistent size per context (32px list, 48px card, 96px profile)
- Round for people, square with border-radius for companies/products
- Border adds polish: `ring-2 ring-white` for overlapping avatars

### Hero Images

- Don't stretch—use `object-cover`
- Consider `aspect-ratio` for consistency
- Compress appropriately (WebP, quality 80%)

---

## Icon Usage

### Sizing

Icons should feel balanced with adjacent text:
- 12-14px text: 16px icon
- 16px text: 20px icon  
- 18-20px text: 24px icon

### Icon + Text Pairing

Always align icon center with text baseline or center. Add consistent gap (8px typical).

```html
<span class="flex items-center gap-2">
  <IconSettings class="w-5 h-5" />
  <span>Settings</span>
</span>
```

### When to Use Icons

- Navigation items
- Common actions (edit, delete, share)
- Status indicators
- Feature lists (with caution—don't overdo)

### When NOT to Use Icons

- Don't add icons just to fill space
- Skip icons on buttons with clear text ("Submit", "Continue")
- Avoid decorative-only icons that add no meaning

---

## Interaction States

Every interactive element needs visible state changes:

### Hover
- Subtle background change
- Slight shadow increase
- Color shift (darken primary by 10%)

### Active/Pressed
- Darker than hover
- Slight scale down (`scale-95`)
- Reduce shadow

### Focus
- Obvious ring (critical for accessibility)
- Don't rely on color alone
- `focus-visible` for keyboard-only focus

### Loading
- Disable interaction
- Show spinner or skeleton
- Maintain layout size (prevent shift)

```css
/* Example button states */
.btn {
  @apply bg-blue-600 hover:bg-blue-700 active:bg-blue-800;
  @apply focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2;
  @apply disabled:opacity-50 disabled:cursor-not-allowed;
}
```

---

## Color Psychology

Use color purposefully:

| Color | Association | Use for |
|-------|-------------|---------|
| Blue | Trust, calm, professional | Primary actions, links, corporate |
| Green | Success, growth, go | Success states, positive actions |
| Red | Error, danger, urgency | Errors, destructive actions, alerts |
| Yellow/Orange | Warning, attention | Warnings, highlights |
| Purple | Premium, creative | Premium features, creative apps |
| Gray | Neutral, professional | Text, backgrounds, borders |

### Avoid

- Red for non-destructive primary buttons
- Green for errors (colorblind users)
- Low-saturation colors for important actions
- More than 3 accent colors per interface

---

## Border Radius System

Stay consistent. Pick a system:

**Sharp/Modern:**
```
none: 0
sm: 2px
md: 4px
lg: 6px
full: 9999px (pills/circles)
```

**Soft/Friendly:**
```
none: 0
sm: 4px
md: 8px
lg: 12px
xl: 16px
full: 9999px
```

### Rules

- Nested elements: inner radius = outer radius - padding
- Small elements get smaller radius (badges, tags)
- Large elements can have larger radius (cards, modals)
- Images inside cards: match card radius or use `overflow-hidden`

---

## Text Wrapping & Truncation

### When to Truncate

- Navigation items
- Table cells with fixed widths
- Card titles (with hover to reveal)

```css
.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
```

### When NOT to Truncate

- Body text
- Important information
- Search results
- Error messages

### Multi-line Truncation

```css
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
```

---

## Responsive Breakpoints

Standard breakpoints (Tailwind default):

```
sm:  640px  (landscape phones)
md:  768px  (tablets)
lg:  1024px (laptops)
xl:  1280px (desktops)
2xl: 1536px (large screens)
```

### Mobile-First Principles

1. Design for mobile first, add complexity for larger screens
2. Stack on mobile, side-by-side on desktop
3. Full-width inputs on mobile, constrained on desktop
4. Larger touch targets on mobile (44px minimum)
5. Hide secondary navigation in hamburger on mobile

---

## Modal and Overlay Patterns

### Modal Sizing

| Content Type | Width | Height |
|--------------|-------|--------|
| Confirmation dialog | 400-500px | Auto (minimal) |
| Form modal | 500-600px | Auto |
| Content modal | 600-800px | 70-80vh max |
| Full-screen modal | 100vw | 100vh |

### Modal Structure

```
┌─────────────────────────────────────────────┐
│  Title                              ✕ Close │
├─────────────────────────────────────────────┤
│                                             │
│  Modal content here                         │
│                                             │
├─────────────────────────────────────────────┤
│                     Cancel    Primary Action│
└─────────────────────────────────────────────┘
```

### Backdrop

```css
.backdrop {
  background: rgba(0, 0, 0, 0.5);
  /* Or with blur */
  backdrop-filter: blur(4px);
}
```

### Modal Transitions

```css
/* Fade + Scale */
.modal {
  opacity: 0;
  transform: scale(0.95);
  transition: opacity 200ms ease-out, transform 200ms ease-out;
}
.modal.open {
  opacity: 1;
  transform: scale(1);
}
```

---

## Dropdown and Menu Design

### Dropdown Positioning

- Default: Below trigger, left-aligned
- Flip: Above if no space below
- Constrain to viewport

```css
.dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: 4px;
}
```

### Menu Styling

```css
.menu {
  min-width: 180px;
  max-height: 300px;
  overflow-y: auto;
  background: white;
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.15);
}

.menu-item {
  padding: 8px 12px;
  cursor: pointer;
}

.menu-item:hover {
  background: #f3f4f6;
}

.menu-divider {
  height: 1px;
  background: #e5e7eb;
  margin: 4px 0;
}
```

### Menu Item Types

| Type | Visual |
|------|--------|
| Standard | Text label |
| With icon | Icon + Label |
| With shortcut | Label + Shortcut |
| With description | Label + Description |
| Destructive | Red text |
| Disabled | Grayed out |

---

## Navigation Patterns

### Top Navigation

```
┌─────────────────────────────────────────────────┐
│  Logo    Nav Item   Nav Item   Nav Item    CTA  │
└─────────────────────────────────────────────────┘
```

- Sticky on scroll (optional)
- Collapse to hamburger on mobile
- Clear active state

### Side Navigation

```
┌──────────────┬──────────────────────────────────┐
│  Logo        │                                  │
│              │                                  │
│  Dashboard   │         Main Content             │
│  Projects    │                                  │
│  Settings    │                                  │
│              │                                  │
│  ─────────   │                                  │
│  Account     │                                  │
│  Logout      │                                  │
└──────────────┴──────────────────────────────────┘
```

- Collapsible to icons on desktop
- Full overlay on mobile
- Group related items

### Breadcrumbs

```
Home  >  Category  >  Subcategory  >  Current Page
```

- Clickable except current page
- Truncate middle items if too long
- Show on detail/nested pages

### Tabs

```css
.tabs {
  display: flex;
  border-bottom: 1px solid #e5e7eb;
}

.tab {
  padding: 12px 16px;
  border-bottom: 2px solid transparent;
}

.tab.active {
  border-bottom-color: #3b82f6;
  color: #3b82f6;
}
```

- Underline or pill style
- Horizontal scroll on mobile if many tabs
- Consider vertical tabs for settings
