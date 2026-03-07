import { test, expect } from '@playwright/test';

/**
 * P3: Domain Redirects — Verifies all legacy domains 301 to tonsofskills.com
 */

test.describe('P3: Domain Redirects', () => {
  // These tests use direct fetch (no browser rendering) to check redirect headers
  test('claudecodeplugins.io redirects to tonsofskills.com', async ({ request }) => {
    const response = await request.get('https://claudecodeplugins.io', {
      maxRedirects: 0,
      failOnStatusCode: false,
    });
    expect(response.status()).toBe(301);
    const location = response.headers()['location'];
    expect(location).toContain('tonsofskills.com');
  });

  test('claudecodeskills.io redirects to tonsofskills.com', async ({ request }) => {
    const response = await request.get('https://claudecodeskills.io', {
      maxRedirects: 0,
      failOnStatusCode: false,
    });
    expect(response.status()).toBe(301);
    const location = response.headers()['location'];
    expect(location).toContain('tonsofskills.com');
  });

  test('claudecoworkskills.io redirects to tonsofskills.com/cowork', async ({ request }) => {
    const response = await request.get('https://claudecoworkskills.io', {
      maxRedirects: 0,
      failOnStatusCode: false,
    });
    expect(response.status()).toBe(301);
    const location = response.headers()['location'];
    expect(location).toContain('tonsofskills.com');
    expect(location).toContain('/cowork');
  });

  test('tonsofskills.com responds with 200 (primary)', async ({ request }) => {
    const response = await request.get('https://tonsofskills.com');
    expect(response.status()).toBe(200);
  });
});
