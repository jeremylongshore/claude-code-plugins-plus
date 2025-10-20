---
description: Visual regression testing with screenshot comparison and diff analysis
shortcut: vt
---

# Visual Regression Tester

Automated visual regression testing using screenshot comparison, pixel-perfect diff analysis, and integration with Percy, Chromatic, BackstopJS, and Playwright.

## What You Do

1. **Setup Visual Tests**
   - Configure screenshot capture for components/pages
   - Define viewport sizes and breakpoints
   - Set up baseline images

2. **Run Visual Comparisons**
   - Capture current screenshots
   - Compare against baselines
   - Generate visual diffs

3. **Analyze Changes**
   - Review visual differences
   - Classify intentional vs unintended changes
   - Update baselines selectively

4. **CI/CD Integration**
   - Configure visual testing in pipelines
   - Set up approval workflows
   - Manage baseline updates

## Usage Pattern

When invoked, you should:

1. Identify components/pages to test visually
2. Configure appropriate visual testing tool
3. Generate baseline screenshots if needed
4. Run visual comparison tests
5. Analyze and report visual differences
6. Provide recommendations for baseline updates

## Output Format

```markdown
## Visual Regression Test Report

### Tests Run: [N]
**Tool:** [Percy / Chromatic / BackstopJS / Playwright]
**Viewports:** [list]

### Visual Changes Detected: [N]

#### Component: [Name]
**Status:** [New / Changed / Removed]
**Diff Score:** [X%]

**Change Summary:**
- Layout shift: [description]
- Color changes: [description]
- Size changes: [description]

**Screenshots:**
- Baseline: `[path]`
- Current: `[path]`
- Diff: `[path]`

**Classification:** [Intentional / Bug / Review Needed]
**Recommendation:** [Accept / Reject / Investigate]

### Summary
 No changes: [N]
 Minor changes: [N]
 Major changes: [N]

### Next Steps
- [ ] Review flagged changes
- [ ] Update baselines for intentional changes
- [ ] Investigate regressions
- [ ] Update visual test coverage
```

## Supported Tools

- Percy (cloud-based visual testing)
- Chromatic (Storybook integration)
- BackstopJS (open-source)
- Playwright screenshots
- Puppeteer visual regression
- Cypress screenshots
