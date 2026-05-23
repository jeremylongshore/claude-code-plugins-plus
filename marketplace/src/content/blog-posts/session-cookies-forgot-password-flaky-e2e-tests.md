---
title: "Session Cookie Auth, Forgot-Password Timeouts, and Killing Flaky E2E Tests"
description: "Why session cookies beat raw ID tokens, how dynamic imports caused 504 timeouts on forgot-password, and the 17-commit saga to stabilize a Playwright E2E test suite."
date: "2026-02-17"
tags: ["firebase", "authentication", "e2e-testing", "debugging", "session-management"]
featured: false
---
## The Auth Stack Was Wrong

Hustle (hustlestats.io) is a youth soccer statistics platform built on Next.js 15 and Firebase. The auth system worked — until it didn't. Users were getting logged out after one hour despite having a 14-day cookie. The forgot-password flow was timing out with 504 errors. And the Playwright E2E tests were failing randomly on every other run.

Three problems. Three different root causes. One painful week.

## Why Session Cookies Beat Raw ID Tokens

Firebase ID tokens expire in one hour. That's by design — they're short-lived credentials for API calls. But Hustle was storing raw ID tokens in cookies with a 14-day `maxAge`:

```typescript
// BEFORE: Storing raw ID token (expires in 1 hour)
response.cookies.set('__session', idToken, {
  maxAge: 60 * 60 * 24 * 14, // 14 days — but the token dies in 1 hour
  httpOnly: true,
  secure: useSecureCookie,
  sameSite: 'lax',
});
```

The cookie lasted 14 days. The token inside it lasted 1 hour. After that hour, `verifyIdToken()` threw an error, and the user got bounced to login.

The fix: use Firebase's `createSessionCookie()` API, which issues a server-side session token that actually lasts as long as you specify:

```typescript
// AFTER: Using proper Firebase session cookie
const expiresIn = 60 * 60 * 24 * 14 * 1000; // 14 days in milliseconds
const sessionCookie = await adminAuth.createSessionCookie(idToken, { expiresIn });

response.cookies.set('__session', sessionCookie, {
  maxAge: expiresIn / 1000,
  httpOnly: true,
  secure: useSecureCookie,
  sameSite: 'lax',
});
```

Server-side verification also changed — from `verifyIdToken()` to `verifySessionCookie()`. The session cookie is a different token type entirely, verified through a different code path in the Admin SDK.

## The 504 Timeout Root Cause

The forgot-password endpoint was timing out on Firebase Hosting. Intermittent 504 errors with no clear pattern.

Root cause: three dynamic imports with timeout wrappers on cold starts.

```typescript
// BEFORE: Dynamic imports on cold starts = ~20s overhead
const { adminAuth } = await withTimeout(
  import('@/lib/firebase/admin'), 10000, 'import firebase/admin'
);
const [{ sendEmail }, { emailTemplates }] = await Promise.all([
  withTimeout(import('@/lib/email'), 5000, 'import email'),
  withTimeout(import('@/lib/email-templates'), 5000, 'import email-templates'),
]);
```

Each dynamic `import()` on a cold start adds seconds of overhead. Three of them with timeout wrappers meant the function could take 20+ seconds before it even started doing real work. Firebase Hosting's proxy timeout killed it.

The fix was embarrassingly simple — static imports:

```typescript
// AFTER: Static imports
import { adminAuth } from '@/lib/firebase/admin';
import { sendEmail } from '@/lib/email';
import { emailTemplates } from '@/lib/email-templates';
```

These modules already handle lazy initialization internally. The dynamic import wrappers were adding latency for no benefit.

But the real fix went further: switch to client-side Firebase SDK for password reset entirely. `sendPasswordResetEmail()` runs directly in the browser — no Cloud Run dependency, no cold start, no timeout possible. The server-side endpoint became unnecessary.

## Universal Firebase Action Handler

Password reset emails from Firebase point to a configurable URL. The original setup had separate pages for `/verify-email` and `/reset-password`, which meant maintaining two pages and coordinating Firebase Console configuration.

The simplification: make `/verify-email` handle both modes inline. One page, zero redirects.

```typescript
function VerifyEmailContent() {
  const mode = searchParams.get('mode');
  const oobCode = searchParams.get('oobCode');

  if (mode === 'resetPassword') {
    return <ResetPasswordInline oobCode={oobCode} router={router} />;
  }
  return <VerifyEmailInline oobCode={oobCode} router={router} />;
}
```

This eliminated the `/reset-password` route entirely and removed a redirect rule from `next.config.ts`. One fewer page to maintain, one fewer thing to break.

## Killing Flaky E2E Tests: 17 Commits

The Playwright test suite had a complete user journey test — registration, dashboard, athlete creation, the full MVP flow. It passed locally about 70% of the time. In CI, maybe 50%.

I'd rather have a hard failure than a test that passes twice and fails once. At least a hard failure points you somewhere.

Here's what was actually wrong, fixed across 17 commits:

### URL Matching Was Too Loose

```typescript
// BEFORE: Matches /dashboard/add-athlete, /dashboard/settings, etc.
await page.waitForURL(/\/dashboard/, { timeout: 30000 });

// AFTER: Only matches the dashboard root
await page.waitForURL(/\/dashboard\/?$/, { timeout: 30000 });
```

The loose regex caused tests to proceed prematurely when navigating through dashboard sub-routes. The `$` anchor was the entire fix.

### False Positive Error Detection

```typescript
// BEFORE: Catches Next.js dev tools [role="alert"] elements
const errorBanner = page.locator('[role="alert"]');
if (await errorBanner.isVisible({ timeout: 2000 })) {
  throw new Error(`Athlete creation failed: ${errorText}`);
}

// AFTER: Only catch visible error banners with actual content
const errorBanner = page.locator('.bg-red-50[role="alert"]');
if (await errorBanner.isVisible({ timeout: 2000 })) {
  const errorText = await errorBanner.textContent();
  if (errorText?.trim()) {
    throw new Error(`Athlete creation failed: ${errorText}`);
  }
}
```

Next.js dev tools inject `[role="alert"]` elements that aren't actual application errors. The test was catching framework noise and treating it as a failure.

### Navigation Method Incompatibility

Next.js `<Link>` components use client-side navigation that doesn't trigger Playwright's standard click handlers reliably. Fix: use `page.goto()` for navigation assertions instead of clicking links.

### Rate Limiting Tests Used Form Submissions

The rate limiting test submitted the login form 10 times in rapid succession. But form submissions trigger redirects, and Playwright lost track of the page state. Fix: use `fetch()` at the API level instead of form submissions. Test the rate limiter, not the form.

### Timeout Calibration

Turbopack in development mode is significantly slower than production builds. Dashboard heading renders took 3-5 seconds in dev versus sub-second in prod. Tests needed wider timeouts for dev server realities, not production assumptions.

### The Stabilization Commit

The final commit addressed 8 separate issues simultaneously: dashboard performance thresholds, navigation method, storage state propagation across 3 describe blocks, a missed URL regex, XSS test dialog handler filtering, rate limiting rewrite, player management `waitForTimeout` replacement, and Dream Gym onboarding detection with `networkidle` wait.

After that commit, the suite went from 50-70% pass rate to consistent green.

## Client-Side Auth as Primary

The biggest architectural lesson: stop treating server-side session cookies as the security boundary.

Firebase SDK's `onAuthStateChanged` listener handles auth state reliably in the browser. Session cookies became optional — nice for SSR personalization, but not the gatekeeper. If cookie creation fails, the login still succeeds and client-side `ProtectedRoute` handles access control.

```typescript
// Login: best-effort session cookie (non-blocking on failure)
try {
  const idToken = await user.getIdToken();
  await fetch('/api/auth/set-session', { method: 'POST', body: JSON.stringify({ idToken }) });
} catch (sessionError) {
  console.warn('Session cookie failed (non-fatal):', sessionError?.message);
}
router.push('/dashboard'); // Client-side ProtectedRoute takes over
```

This eliminated an entire class of auth failures. No more 504 timeouts on session creation killing the login flow. No more users locked out because cookie verification had a transient error.

## What I Learned

**Check your token types.** An ID token is not a session cookie. They have different lifetimes, different verification methods, and different intended uses. Using one where you need the other creates subtle, intermittent failures.

**Dynamic imports have hidden costs.** Cold start overhead from three dynamic imports exceeded the proxy timeout. Static imports with lazy initialization are almost always the right choice in serverless contexts.

**E2E flakiness is cumulative.** No single issue caused the test failures. It was loose regexes, framework noise, wrong navigation methods, and optimistic timeouts — all combining to create random failures. You have to fix all of them to get stability.

**Client-side auth simplifies everything.** Once `onAuthStateChanged` becomes the primary auth mechanism, server-side session management becomes optional. Fewer moving parts, fewer failure modes.
