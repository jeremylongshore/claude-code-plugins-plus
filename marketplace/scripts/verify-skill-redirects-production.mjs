import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const redirects = JSON.parse(
  readFileSync(new URL('../src/data/skill-redirects.json', import.meta.url), 'utf8'),
).redirects;
const base = (process.argv[2] || 'https://tonsofskills.com').replace(/\/$/, '');

for (const redirect of redirects) {
  for (const suffix of ['', '/']) {
    const response = await fetch(`${base}/skills/${redirect.from}${suffix}`, {
      method: 'HEAD',
      redirect: 'manual',
    });
    assert.equal(response.status, 301, `${redirect.from}${suffix}: expected 301`);
    assert.equal(
      response.headers.get('location'),
      `/skills/${redirect.to}/`,
      `${redirect.from}${suffix}: wrong Location`,
    );
  }
}

console.log(`verified ${redirects.length * 2} production redirect variants at ${base}`);
