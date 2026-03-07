# WCAG 2.1 AA Checklist

Complete checklist for WCAG 2.1 Level AA compliance with testing guidance.

## Perceivable

Content must be presentable in ways users can perceive.

### 1.1 Text Alternatives

| Criterion | Requirement | How to Test |
|-----------|-------------|-------------|
| 1.1.1 Non-text Content | All images, icons, and visual content have text alternatives | Inspect alt attributes; use screen reader |

**Pass criteria:**
- [ ] Informative images have descriptive alt text
- [ ] Decorative images have empty alt (`alt=""`)
- [ ] Complex images (charts, diagrams) have extended descriptions
- [ ] Icons have accessible names
- [ ] CAPTCHA provides audio alternative

### 1.2 Time-based Media

| Criterion | Requirement | How to Test |
|-----------|-------------|-------------|
| 1.2.1 Audio/Video (prerecorded) | Captions and/or transcripts | Check video player for captions |
| 1.2.2 Captions | Synchronized captions for video | Watch with captions on |
| 1.2.3 Audio Description | Description of visual content | Check for AD track |
| 1.2.5 Audio Description (AA) | Audio description for all video | Verify AD available |

**Pass criteria:**
- [ ] Videos have synchronized captions
- [ ] Captions are accurate and complete
- [ ] Audio descriptions available for important visual content
- [ ] Transcripts available for audio-only content

### 1.3 Adaptable

| Criterion | Requirement | How to Test |
|-----------|-------------|-------------|
| 1.3.1 Info and Relationships | Semantic structure preserved | Inspect HTML; use screen reader |
| 1.3.2 Meaningful Sequence | Content order makes sense | Disable CSS; read in DOM order |
| 1.3.3 Sensory Characteristics | Don't rely on shape/color/position alone | Check instructions |
| 1.3.4 Orientation (AA) | Works in portrait and landscape | Rotate device |
| 1.3.5 Identify Input Purpose (AA) | Input fields have autocomplete | Check `autocomplete` attributes |

**Pass criteria:**
- [ ] Headings use proper h1-h6 hierarchy
- [ ] Lists use `<ul>`, `<ol>`, `<dl>` elements
- [ ] Forms have proper labels associated with inputs
- [ ] Tables have headers marked with `<th>`
- [ ] Reading order is logical without CSS
- [ ] Works in both orientations
- [ ] Input fields have appropriate autocomplete values

### 1.4 Distinguishable

| Criterion | Requirement | How to Test |
|-----------|-------------|-------------|
| 1.4.1 Use of Color | Color not sole means of info | View in grayscale |
| 1.4.2 Audio Control | Auto-playing audio can be stopped | Check for controls |
| 1.4.3 Contrast (Minimum) | 4.5:1 text, 3:1 large text | Use contrast checker |
| 1.4.4 Resize Text | Readable at 200% zoom | Zoom browser |
| 1.4.5 Images of Text | Use real text, not images | Inspect for text images |
| 1.4.10 Reflow (AA) | No horizontal scroll at 320px | Test at narrow width |
| 1.4.11 Non-text Contrast (AA) | 3:1 for UI components | Check buttons, inputs |
| 1.4.12 Text Spacing (AA) | Survives increased text spacing | Apply spacing override |
| 1.4.13 Content on Hover/Focus (AA) | Hoverable, dismissible, persistent | Test tooltips, menus |

**Pass criteria:**
- [ ] Normal text has 4.5:1 contrast ratio minimum
- [ ] Large text (18pt+) has 3:1 contrast ratio minimum
- [ ] UI components have 3:1 contrast
- [ ] Text resizes to 200% without loss
- [ ] No horizontal scrolling at 320px width
- [ ] Tooltips are dismissible, hoverable, persistent
- [ ] Color alone doesn't convey meaning

---

## Operable

Users must be able to operate the interface.

### 2.1 Keyboard Accessible

| Criterion | Requirement | How to Test |
|-----------|-------------|-------------|
| 2.1.1 Keyboard | All functionality works with keyboard | Navigate with Tab, Enter, Space |
| 2.1.2 No Keyboard Trap | Focus can always move away | Tab through everything |
| 2.1.4 Character Key Shortcuts (AA) | Single-key shortcuts can be disabled | Check for shortcut conflicts |

**Pass criteria:**
- [ ] All interactive elements are focusable
- [ ] All actions can be performed via keyboard
- [ ] Focus is never trapped
- [ ] Single-key shortcuts can be disabled or remapped
- [ ] Tab order follows logical sequence

### 2.2 Enough Time

| Criterion | Requirement | How to Test |
|-----------|-------------|-------------|
| 2.2.1 Timing Adjustable | Users can extend/disable time limits | Check for timeouts |
| 2.2.2 Pause, Stop, Hide | Auto-updating content can be controlled | Check carousels, animations |

**Pass criteria:**
- [ ] Session timeouts have 20-second warning
- [ ] Users can extend time limits
- [ ] Auto-playing content has pause control
- [ ] Animations can be stopped

### 2.3 Seizures

| Criterion | Requirement | How to Test |
|-----------|-------------|-------------|
| 2.3.1 Three Flashes | No content flashes >3 times/second | Measure flash rate |

**Pass criteria:**
- [ ] No flashing content above threshold
- [ ] Animations don't cause seizure risk

### 2.4 Navigable

| Criterion | Requirement | How to Test |
|-----------|-------------|-------------|
| 2.4.1 Bypass Blocks | Skip links to bypass repeated content | Check for skip link |
| 2.4.2 Page Titled | Pages have descriptive titles | Check `<title>` element |
| 2.4.3 Focus Order | Focus sequence is logical | Tab through page |
| 2.4.4 Link Purpose | Link text describes destination | Read links out of context |
| 2.4.5 Multiple Ways (AA) | Multiple ways to find pages | Check nav, search, sitemap |
| 2.4.6 Headings and Labels (AA) | Headings and labels are descriptive | Review all headings |
| 2.4.7 Focus Visible (AA) | Focus indicator is visible | Tab through interface |

**Pass criteria:**
- [ ] Skip link present at top of page
- [ ] Page titles are unique and descriptive
- [ ] Tab order follows visual order
- [ ] Link text is meaningful ("Read more about X" not "Click here")
- [ ] Multiple navigation methods available
- [ ] All headings are descriptive
- [ ] Focus indicator is clearly visible

### 2.5 Input Modalities

| Criterion | Requirement | How to Test |
|-----------|-------------|-------------|
| 2.5.1 Pointer Gestures (AA) | Complex gestures have simple alternatives | Check for alternatives |
| 2.5.2 Pointer Cancellation (AA) | Actions on up-event, cancelable | Test click/drag behavior |
| 2.5.3 Label in Name (AA) | Accessible name contains visible label | Compare visible/accessible names |
| 2.5.4 Motion Actuation (AA) | Motion-based actions have alternatives | Check for non-motion options |

**Pass criteria:**
- [ ] Pinch, swipe have tap alternatives
- [ ] Click actions happen on release (up-event)
- [ ] Dragging outside target cancels action
- [ ] Accessible names include visible text
- [ ] Shake/tilt actions have button alternatives

---

## Understandable

Content must be understandable to users.

### 3.1 Readable

| Criterion | Requirement | How to Test |
|-----------|-------------|-------------|
| 3.1.1 Language of Page | Page language specified | Check `<html lang="">` |
| 3.1.2 Language of Parts (AA) | Foreign text marked with lang | Check multilingual content |

**Pass criteria:**
- [ ] HTML has lang attribute
- [ ] Foreign language passages have lang attribute

### 3.2 Predictable

| Criterion | Requirement | How to Test |
|-----------|-------------|-------------|
| 3.2.1 On Focus | Focus doesn't cause unexpected changes | Tab through all elements |
| 3.2.2 On Input | Input doesn't cause unexpected changes | Fill forms without submitting |
| 3.2.3 Consistent Navigation (AA) | Navigation is consistent across pages | Compare pages |
| 3.2.4 Consistent Identification (AA) | Same functions have same labels | Compare repeated elements |

**Pass criteria:**
- [ ] Focus doesn't trigger context changes
- [ ] Selecting options doesn't submit forms
- [ ] Navigation is in same location on all pages
- [ ] Same icons/labels used for same functions

### 3.3 Input Assistance

| Criterion | Requirement | How to Test |
|-----------|-------------|-------------|
| 3.3.1 Error Identification | Errors clearly identified | Submit invalid forms |
| 3.3.2 Labels or Instructions | Labels and instructions provided | Review all forms |
| 3.3.3 Error Suggestion (AA) | Suggestions for fixing errors | Trigger errors |
| 3.3.4 Error Prevention (AA) | Confirmation for legal/financial actions | Test critical submissions |

**Pass criteria:**
- [ ] Errors are clearly described in text
- [ ] Error messages explain how to fix
- [ ] All inputs have visible labels
- [ ] Required fields are indicated
- [ ] Legal/financial submissions are reversible or confirmed

---

## Robust

Content must work with assistive technologies.

### 4.1 Compatible

| Criterion | Requirement | How to Test |
|-----------|-------------|-------------|
| 4.1.1 Parsing | Valid HTML | Run HTML validator |
| 4.1.2 Name, Role, Value | ARIA used correctly | Inspect with accessibility tools |
| 4.1.3 Status Messages (AA) | Status updates announced | Test with screen reader |

**Pass criteria:**
- [ ] HTML is valid (no duplicate IDs, proper nesting)
- [ ] Custom controls have appropriate roles
- [ ] States (expanded, selected) are programmatically set
- [ ] Status messages use aria-live regions

---

## Testing Tools

### Automated Testing

| Tool | What It Catches | Use For |
|------|-----------------|---------|
| axe DevTools | ~30% of issues | Quick scan |
| WAVE | Similar to axe | Visual overlay |
| Lighthouse | Basic accessibility | CI/CD integration |
| Pa11y | CLI-based | Automated testing |

### Manual Testing Required

| Area | How to Test |
|------|-------------|
| Keyboard navigation | Unplug mouse, use only keyboard |
| Screen reader | VoiceOver (Mac), NVDA (Windows) |
| Zoom | Browser zoom to 200%, 400% |
| Color contrast | WebAIM Contrast Checker |
| Color blindness | Sim Daltonism, Chrome DevTools |

### Screen Reader Testing

**VoiceOver (Mac):**
1. Enable: Cmd + F5
2. Navigate: VO (Ctrl + Opt) + arrows
3. Rotor: VO + U (headings, links, forms)

**NVDA (Windows):**
1. Download free from nvaccess.org
2. Navigate: Arrow keys, Tab
3. Elements list: NVDA + F7

---

## Quick Reference: Common Failures

| Issue | Failure | Fix |
|-------|---------|-----|
| Missing alt text | 1.1.1 | Add descriptive alt or `alt=""` |
| Low contrast | 1.4.3 | Increase to 4.5:1 (text) or 3:1 (large/UI) |
| No focus indicator | 2.4.7 | Add visible :focus-visible styles |
| Keyboard inaccessible | 2.1.1 | Make interactive, add tabindex=0 |
| Missing form labels | 1.3.1, 3.3.2 | Add `<label>` with `for` attribute |
| No skip link | 2.4.1 | Add "Skip to content" link |
| Missing page title | 2.4.2 | Add descriptive `<title>` |
| Color-only meaning | 1.4.1 | Add icon or text alongside |
| No lang attribute | 3.1.1 | Add `<html lang="en">` |
| Ambiguous links | 2.4.4 | Use descriptive link text |

---

## Testing Checklist Summary

Before launch, verify:

**Automated scan:**
- [ ] axe DevTools shows 0 issues
- [ ] Lighthouse accessibility score >90

**Keyboard:**
- [ ] All functionality works with keyboard
- [ ] Focus visible on all elements
- [ ] No keyboard traps
- [ ] Skip link works

**Screen reader:**
- [ ] All content announced correctly
- [ ] Form fields have labels
- [ ] Images have alt text
- [ ] Headings create logical outline

**Visual:**
- [ ] All text meets contrast requirements
- [ ] Works at 200% zoom
- [ ] Works at 320px width (mobile)
- [ ] Color not sole indicator
