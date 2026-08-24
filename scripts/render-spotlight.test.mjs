import assert from 'node:assert/strict';
import test from 'node:test';

import { renderBlock, renderDeepDive } from './render-spotlight.mjs';

test('renders only the supplied deep-dive assets in stable label order', () => {
  assert.equal(
    renderDeepDive({ onePager: '/brief.md', cfo: 'https://example.com/cfo', prd: '/prd.md' }),
    '> Deep dive: [PRD](https://tonsofskills.com/prd.md) · [One-pager](https://tonsofskills.com/brief.md) · [CFO brief](https://example.com/cfo)',
  );
});

test('omits the deep-dive row when an entry has no assets', () => {
  const rendered = renderBlock({
    week: '2026-W01',
    spotlight: { pluginSlug: 'example', author: 'Example', grade: 'A', link: '/plugins/example' },
  });
  assert.doesNotMatch(rendered, /Deep dive:/);
});

test('renders deep-dive links in the generated README block', () => {
  const rendered = renderBlock({
    week: '2026-W01',
    spotlight: {
      pluginSlug: 'example',
      author: 'Example',
      grade: 'A',
      link: '/plugins/example',
      assets: { adr: '/adr.md' },
    },
  });
  assert.match(rendered, /> Deep dive: \[ADR\]\(https:\/\/tonsofskills\.com\/adr\.md\)/);
});
