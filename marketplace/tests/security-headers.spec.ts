import { expect, test } from '@playwright/test';

// The policy module is plain ESM and intentionally shared with Astro config.
// @ts-expect-error JavaScript policy module has no separate declaration file.
import { securityHeadersForPath } from '../scripts/security-policy.mjs';

const pages = [
  '/',
  '/skills/',
  '/plugins/skill-creator/',
  '/docs/',
  '/explore/',
  '/chats/',
  '/terms/',
  '/privacy/',
  '/acceptable-use/',
];

for (const path of pages) {
  test(`${path} emits the reviewed CSP without runtime violations`, async ({ page }) => {
    await page.addInitScript(() => {
      const violations: string[] = [];
      Object.defineProperty(window, '__cspViolations', { value: violations });
      document.addEventListener('securitypolicyviolation', (event) => {
        violations.push(`${event.effectiveDirective}: ${event.blockedURI}`);
      });
    });
    const response = await page.goto(path, { waitUntil: 'networkidle' });
    expect(response?.status()).toBe(200);
    expect(response?.headers()['content-security-policy']).toBe(
      securityHeadersForPath(path)['Content-Security-Policy'],
    );
    const violations = await page.evaluate(
      // @ts-expect-error test-only property installed above.
      () => window.__cspViolations as string[],
    );
    expect(violations).toEqual([]);
  });
}
