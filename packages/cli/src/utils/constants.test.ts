import { describe, expect, test } from 'vitest';
import { CATALOG_URL, MARKETPLACE_REPO } from './constants.js';

describe('marketplace constants', () => {
  test('pin the canonical repository catalog rather than an unserved website route', () => {
    expect(MARKETPLACE_REPO).toBe('jeremylongshore/claude-code-plugins-plus-skills');
    expect(CATALOG_URL).toBe(
      'https://raw.githubusercontent.com/jeremylongshore/claude-code-plugins-plus-skills/main/.claude-plugin/marketplace.json',
    );
  });
});
