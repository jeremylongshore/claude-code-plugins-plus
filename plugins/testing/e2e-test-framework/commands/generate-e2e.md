---
name: generate-e2e
description: Generate end-to-end browser tests for user workflows
shortcut: ee
---
# End-to-End Test Generator

Generate comprehensive browser-based E2E tests for complete user workflows using Playwright, Cypress, or Selenium.

## Purpose

Create automated tests that simulate real user interactions:
- Complete user journeys (signup → login → purchase)
- Multi-page workflows
- Form interactions and validations
- Navigation flows
- Browser-specific behaviors
- Mobile responsive testing

## Supported Frameworks

**Playwright** (Recommended)
- Multi-browser support (Chromium, Firefox, WebKit)
- Auto-wait for elements
- Network interception
- Mobile emulation
- Parallel execution

**Cypress**
- Time-travel debugging
- Real-time reloads
- Automatic waiting
- Network stubbing
- Screenshot/video capture

**Selenium WebDriver**
- Mature ecosystem
- Cross-browser support
- Remote execution (Selenium Grid)
- Mobile testing (Appium)

## Test Generation

When invoked, generate E2E tests with:

1. **User workflow analysis**
   - Identify key user journeys
   - Map page interactions
   - Define success criteria

2. **Page Object Model**
   - Create page classes
   - Define selectors
   - Implement action methods

3. **Test scenarios**
   - Happy path workflows
   - Error handling paths
   - Edge cases

4. **Assertions**
   - URL validation
   - Element presence
   - Content verification
   - State changes

## Example: Playwright Test

```typescript
import { test, expect } from '@playwright/test';

test.describe('User Registration Flow', () => {
  test('should complete full registration workflow', async ({ page }) => {
    // Navigate to signup
    await page.goto('https://example.com/signup');

    // Fill registration form
    await page.fill('[name="email"]', '[email protected]');
    await page.fill('[name="password"]', 'SecurePass123!');
    await page.fill('[name="confirmPassword"]', 'SecurePass123!');
    await page.check('[name="terms"]');

    // Submit and wait for navigation
    await page.click('button[type="submit"]');
    await page.waitForURL('**/verify-email');

    // Verify success message
    await expect(page.locator('.success-message')).toContainText(
      'Please check your email'
    );
  });

  test('should show validation errors for invalid data', async ({ page }) => {
    await page.goto('https://example.com/signup');

    // Submit empty form
    await page.click('button[type="submit"]');

    // Verify error messages
    await expect(page.locator('.error-email')).toBeVisible();
    await expect(page.locator('.error-password')).toBeVisible();
  });
});

test.describe('E-commerce Purchase Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('https://example.com/login');
    await page.fill('[name="email"]', '[email protected]');
    await page.fill('[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/dashboard');
  });

  test('should complete product purchase', async ({ page }) => {
    // Browse products
    await page.goto('https://example.com/products');
    await page.click('text=Add to Cart').first();

    // Verify cart badge
    await expect(page.locator('.cart-badge')).toHaveText('1');

    // Go to checkout
    await page.click('.cart-icon');
    await page.click('text=Checkout');

    // Fill shipping info
    await page.fill('[name="address"]', '123 Main St');
    await page.fill('[name="city"]', 'San Francisco');
    await page.fill('[name="zip"]', '94102');
    await page.click('text=Continue');

    // Enter payment (test mode)
    await page.fill('[name="cardNumber"]', '4242424242424242');
    await page.fill('[name="expiry"]', '12/25');
    await page.fill('[name="cvc"]', '123');
    await page.click('text=Place Order');

    // Verify success
    await page.waitForURL('**/order/confirmation');
    await expect(page.locator('.order-success')).toBeVisible();
    await expect(page.locator('.order-number')).toContainText('ORDER-');
  });
});
```

## Example: Cypress Test

```javascript
describe('User Dashboard Workflow', () => {
  beforeEach(() => {
    cy.login('[email protected]', 'password123');
  });

  it('should load dashboard with user data', () => {
    cy.visit('/dashboard');
    cy.get('.welcome-message').should('contain', 'Welcome, John');
    cy.get('.user-stats').should('be.visible');
  });

  it('should create new project', () => {
    cy.visit('/dashboard');
    cy.get('[data-testid="new-project"]').click();

    cy.get('[name="projectName"]').type('My New Project');
    cy.get('[name="description"]').type('Project description here');
    cy.get('button[type="submit"]').click();

    cy.url().should('include', '/projects/');
    cy.get('.project-title').should('contain', 'My New Project');
  });
});
```

## Page Object Model

```typescript
// pages/LoginPage.ts
export class LoginPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/login');
  }

  async login(email: string, password: string) {
    await this.page.fill('[name="email"]', email);
    await this.page.fill('[name="password"]', password);
    await this.page.click('button[type="submit"]');
  }

  async getErrorMessage() {
    return this.page.locator('.error-message').textContent();
  }
}

// Test using Page Object
test('login with page object', async ({ page }) => {
  const loginPage = new LoginPage(page);
  await loginPage.goto();
  await loginPage.login('[email protected]', 'password123');
  await expect(page).toHaveURL('/dashboard');
});
```

## Best Practices

- **Use data-testid attributes** - Stable selectors
- **Implement Page Objects** - Reusable page interactions
- **Handle waits properly** - Auto-wait or explicit waits
- **Test realistic scenarios** - Actual user workflows
- **Parallelize tests** - Faster execution
- **Capture screenshots on failure** - Debugging aid
- **Use fixtures** - Consistent test data
- **Test across browsers** - Chrome, Firefox, Safari
