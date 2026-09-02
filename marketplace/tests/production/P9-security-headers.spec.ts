import { expect, test } from '@playwright/test';

// @ts-expect-error JavaScript policy module has no separate declaration file.
import { MARKETPLACE_SECURITY_HEADERS } from '../../scripts/security-policy.mjs';

test('production emits the reviewed CSP on representative public surfaces', async ({ request }) => {
  for (const path of ['/', '/skills/', '/plugins/skill-creator/', '/docs/', '/explore/']) {
    const response = await request.get(path);
    expect(response.status(), path).toBe(200);
    expect(response.headers()['content-security-policy'], path).toBe(
      MARKETPLACE_SECURITY_HEADERS['Content-Security-Policy'],
    );
  }
});
