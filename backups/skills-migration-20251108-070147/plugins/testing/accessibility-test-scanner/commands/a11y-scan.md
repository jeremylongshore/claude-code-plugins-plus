---
description: Scan for accessibility issues with WCAG 2.1/2.2 compliance and screen reader testing
shortcut: a11y
---

# Accessibility Test Scanner

Comprehensive accessibility testing with WCAG 2.1/2.2 validation, ARIA compliance, keyboard navigation testing, and screen reader compatibility checks.

## What You Do

1. **WCAG Compliance Scanning**
   - Check WCAG 2.1 Level A, AA, AAA compliance
   - Validate WCAG 2.2 new success criteria
   - Generate detailed compliance reports

2. **ARIA Validation**
   - Verify proper ARIA usage
   - Detect ARIA antipatterns
   - Validate landmark regions and roles

3. **Keyboard Navigation**
   - Test tab order and focus management
   - Verify keyboard shortcuts
   - Check focus indicators

4. **Screen Reader Testing**
   - Generate screen reader test scenarios
   - Validate semantic HTML
   - Check alt text and labels

5. **Color Contrast**
   - Validate color contrast ratios
   - Test for color blindness
   - Suggest accessible color palettes

## Usage Pattern

When invoked, you should:

1. Identify pages/components to test
2. Run automated accessibility audits (axe-core, Pa11y, Lighthouse)
3. Analyze results against WCAG criteria
4. Prioritize issues by severity and impact
5. Generate fix recommendations with code examples
6. Create accessibility test suite

## Output Format

```markdown
## Accessibility Audit Report

### Compliance Level: [A / AA / AAA]
**Pages Scanned:** [N]
**Issues Found:** [Critical: N, Serious: N, Moderate: N, Minor: N]

### Critical Issues (WCAG Level A)

#### Issue: [Description]
**WCAG Criterion:** [X.X.X - Name]
**Impact:** [High/Medium/Low]
**Affected Elements:** [N]
**Location:** `[selector or file:line]`

**Problem:**
[Detailed explanation]

**Fix:**
```html
<!-- Before -->
[problematic code]

<!-- After -->
[corrected code]
```

**Testing:**
- [ ] Screen reader: [how to verify]
- [ ] Keyboard: [how to verify]

### ARIA Issues
- Missing labels: [N]
- Invalid roles: [N]
- Incorrect relationships: [N]

### Keyboard Navigation
 Tab order: Logical
 Focus indicators: Missing on [N] elements
 Keyboard traps: Found [N]

### Color Contrast
 Normal text: Pass
 Small text: [N] failures
 UI components: [N] failures

### Recommendations
1. [Priority fix]
2. [Priority fix]
3. [Enhancement]

### Next Steps
- [ ] Fix critical WCAG A violations
- [ ] Address WCAG AA issues
- [ ] Set up automated a11y testing
- [ ] Manual screen reader testing
```

## Testing Tools Integration

- axe-core (automated testing)
- Pa11y (command-line testing)
- Lighthouse accessibility audit
- WAVE browser extension
- NVDA/JAWS screen reader scripts
- jest-axe / cypress-axe for automated tests
