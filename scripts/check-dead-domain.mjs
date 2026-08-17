#!/usr/bin/env node

import { resolve } from 'node:path';

import { domainPolicyAllows, scanDeadDomainPolicy } from './dead-domain-policy.mjs';

function main(argv = process.argv.slice(2)) {
  const json = argv.includes('--json');
  const rootIndex = argv.indexOf('--root');
  const root = rootIndex === -1 ? process.cwd() : argv[rootIndex + 1];
  if (
    !root ||
    argv.some((arg, index) => arg !== '--json' && arg !== '--root' && index !== rootIndex + 1)
  ) {
    throw new Error('usage: check-dead-domain.mjs [--json] [--root <checkout>]');
  }
  const report = scanDeadDomainPolicy({ root: resolve(root) });
  if (json) {
    process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
  } else {
    for (const refusal of report.refused) {
      console.error(`REFUSE ${refusal.reasonCode}: ${refusal.path}`);
    }
    for (const path of report.actionable.paths) {
      console.error(`REFUSE RETIRED_DOMAIN_ON_ACTIONABLE_SURFACE: ${path}`);
    }
    for (const path of report.retained.paths) {
      console.log(`RETAIN ${path}`);
    }
    console.log(
      `dead-domain-policy: ${report.actionable.occurrences} actionable occurrence(s); ` +
        `${report.frozen_record.occurrences} frozen; ` +
        `${report.historical_snapshot.occurrences} historical; ` +
        `${report.provenance_mirror.occurrences} mirrored; ` +
        `${report.refused.length} refused path(s)`,
    );
  }
  if (!domainPolicyAllows(report)) process.exitCode = 1;
}

try {
  main();
} catch (error) {
  console.error(`dead-domain-policy: ${error.message}`);
  process.exitCode = 1;
}
