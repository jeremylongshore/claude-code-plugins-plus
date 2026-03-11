# Clerk CI Integration - Implementation Guide

Detailed implementation examples and code patterns.

## Instructions

### Step 1: GitHub Actions Workflow
```yaml
# .github/workflows/test.yml
name: Test

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: ${{ secrets.CLERK_PUBLISHABLE_KEY_TEST }}
  CLERK_SECRET_KEY: ${{ secrets.CLERK_SECRET_KEY_TEST }}

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Type check
        run: npm run typecheck

      - name: Run unit tests
        run: npm test

      - name: Run integration tests
        run: npm run test:integration
        env:
          CLERK_SECRET_KEY: ${{ secrets.CLERK_SECRET_KEY_TEST }}

      - name: Build
        run: npm run build
```

### Step 2: E2E Testing with Playwright
```yaml
# .github/workflows/e2e.yml
name: E2E Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  e2e:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright
        run: npx playwright install --with-deps

      - name: Build application
        run: npm run build
        env:
          NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: ${{ secrets.CLERK_PUBLISHABLE_KEY_TEST }}

      - name: Run E2E tests
        run: npx playwright test
        env:
          NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: ${{ secrets.CLERK_PUBLISHABLE_KEY_TEST }}
          CLERK_SECRET_KEY: ${{ secrets.CLERK_SECRET_KEY_TEST }}
          CLERK_TEST_USER_EMAIL: ${{ secrets.CLERK_TEST_USER_EMAIL }}
          CLERK_TEST_USER_PASSWORD: ${{ secrets.CLERK_TEST_USER_PASSWORD }}

      - name: Upload test results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
```

### Step 3: Test User Setup
```typescript
// scripts/setup-test-user.ts
import { clerkClient } from '@clerk/nextjs/server'

async function setupTestUser() {
  const client = await clerkClient()

  // Check if test user exists
  const { data: users } = await client.users.getUserList({
    emailAddress: ['test@example.com']
  })

  if (users.length === 0) {
    // Create test user
    const user = await client.users.createUser({
      emailAddress: ['test@example.com'],
      password: process.env.CLERK_TEST_USER_PASSWORD,
      firstName: 'Test',
      lastName: 'User'
    })
    console.log('Created test user:', user.id)
  } else {
    console.log('Test user already exists:', users[0].id)
  }
}

setupTestUser()
```

### Step 4: Playwright Test Configuration
```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',

  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  webServer: {
    command: 'npm run start',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
})
```

### Step 5: Authentication Test Helpers
```typescript
// e2e/helpers/auth.ts
import { Page } from '@playwright/test'

export async function signIn(page: Page) {
  await page.goto('/sign-in')

  await page.fill('input[name="identifier"]', process.env.CLERK_TEST_USER_EMAIL!)
  await page.click('button:has-text("Continue")')

  await page.fill('input[name="password"]', process.env.CLERK_TEST_USER_PASSWORD!)
  await page.click('button:has-text("Continue")')

  // Wait for redirect to dashboard
  await page.waitForURL('/dashboard')
}

export async function signOut(page: Page) {
  await page.click('[data-clerk-user-button]')
  await page.click('button:has-text("Sign out")')
  await page.waitForURL('/')
}
```

### Step 6: Sample E2E Tests
```typescript
// e2e/auth.spec.ts
import { test, expect } from '@playwright/test'
import { signIn, signOut } from './helpers/auth'

test.describe('Authentication', () => {
  test('user can sign in and access dashboard', async ({ page }) => {
    await signIn(page)
    await expect(page).toHaveURL('/dashboard')
    await expect(page.locator('h1')).toContainText('Dashboard')
  })

  test('user can sign out', async ({ page }) => {
    await signIn(page)
    await signOut(page)
    await expect(page).toHaveURL('/')
  })

  test('unauthenticated user is redirected', async ({ page }) => {
    await page.goto('/dashboard')
    await expect(page).toHaveURL(/\/sign-in/)
  })
})
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Secret not found | Missing GitHub secret | Add secret in repo settings |
| Test user not found | User not created | Run setup script first |
| Timeout on sign-in | Slow response | Increase timeout, check network |
| Build fails | Missing env vars | Check all NEXT_PUBLIC vars set |
