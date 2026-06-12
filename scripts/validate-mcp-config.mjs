#!/usr/bin/env node
/**
 * validate-mcp-config.mjs — kernel mcp-config validation (ADVISORY by default)
 *
 * Validates every `.mcp.json` file under `plugins/` AND every inline
 * `mcpServers` object block inside `plugins/.../.claude-plugin/plugin.json`
 * against the Spec Authority Kernel's authoring/v1 mcp-config composition
 * (@intentsolutions/core, pinned EXACTLY in package.json — same pin discipline
 * as kernel-shadow-validation.mjs; the schema is read straight out of
 * node_modules so the comparison is always against the pinned contract).
 *
 * CONTRACT SHAPE: the kernel mcp-config contract is a PER-SERVER ENTRY shape
 * (base requires name/command/args/transport/env; the IS overlay adds
 * description/version/enabled). On-disk `.mcp.json` files keyed as
 * `{"mcpServers": {"<server-name>": {…}}}` carry the name as the MAP KEY, so
 * this harness projects each entry to `{name: <key>, …entry}` before
 * validating (noted per finding as `projection: key->name`).
 *
 * MODE: ADVISORY by default — the corpus has never been validated against
 * this contract, so the first run is a findings BASELINE, not a gate.
 *   default  : report all findings, exit 0
 *   --strict : exit 1 when any finding exists (the future flip — NOT wired
 *              into CI; DR-049 soak gates that)
 *   --json   : machine-readable report to stdout
 *
 * Exit codes: 0 advisory success (findings or not) / 1 only on --strict with
 * findings, or on a harness error (kernel missing, unreadable schema).
 */

import { readFileSync, existsSync, readdirSync, statSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

import Ajv2020 from 'ajv/dist/2020.js';
import addFormats from 'ajv-formats';

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(__dirname, '..');

const SCHEMA_DIR = join(
  REPO_ROOT,
  'node_modules',
  '@intentsolutions',
  'core',
  'schemas',
  'authoring',
  'v1',
);

// The composed mcp-config contract is a pure allOf of $ref'd layers. ajv
// resolves $ref by $id, so every layer must be registered; marketplace-tier
// supplies the universalFolds $def the composition references. (Same loading
// pattern as kernel-shadow-validation.mjs.)
const SCHEMA_FILES = [
  'upstream-base/mcp-config.v1.json',
  'is-overlay/mcp-config.v1.json',
  'marketplace-tier.schema.json',
  'mcp-config.schema.json', // the composition (validated against)
];

const COMPOSED_SCHEMA_ID =
  'https://github.com/jeremylongshore/intent-eval-core/schemas/authoring/v1/mcp-config.schema.json';

const args = process.argv.slice(2);
const STRICT = args.includes('--strict');
const JSON_OUT = args.includes('--json');

function die(msg) {
  console.error(`[validate-mcp-config] HARNESS ERROR: ${msg}`);
  process.exit(1);
}

function buildKernelValidator() {
  const ajv = new Ajv2020({ allErrors: true, strict: false });
  addFormats(ajv);
  for (const rel of SCHEMA_FILES) {
    const p = join(SCHEMA_DIR, rel);
    if (!existsSync(p)) {
      die(`kernel schema layer missing: ${p}. Run pnpm install (@intentsolutions/core pinned).`);
    }
    ajv.addSchema(JSON.parse(readFileSync(p, 'utf8')));
  }
  const validate = ajv.getSchema(COMPOSED_SCHEMA_ID);
  if (!validate) {
    die(`could not resolve composed schema by $id ${COMPOSED_SCHEMA_ID}`);
  }
  return validate;
}

/** Recursively collect files under dir whose basename matches `names`. */
function collectFiles(dir, names, out = []) {
  let entries;
  try {
    entries = readdirSync(dir);
  } catch {
    return out;
  }
  for (const entry of entries) {
    if (entry === 'node_modules' || entry === '.git') continue;
    const p = join(dir, entry);
    let st;
    try {
      st = statSync(p);
    } catch {
      continue;
    }
    if (st.isDirectory()) {
      collectFiles(p, names, out);
    } else if (names.has(entry)) {
      out.push(p);
    }
  }
  return out;
}

function relTo(p) {
  return relative(REPO_ROOT, p);
}

function main() {
  const validate = buildKernelValidator();
  const pluginsDir = join(REPO_ROOT, 'plugins');
  if (!existsSync(pluginsDir)) die(`plugins directory not found at ${pluginsDir}`);

  const mcpJsonFiles = collectFiles(pluginsDir, new Set(['.mcp.json']));
  const pluginJsonFiles = collectFiles(pluginsDir, new Set(['plugin.json'])).filter((p) =>
    p.includes(`${join('.claude-plugin')}`),
  );

  const findings = []; // { file, server, source, errors: [...] }
  let filesScanned = 0;
  let serversValidated = 0;
  let serversPassed = 0;
  let parseFailures = 0;
  let stringRefBlocks = 0;

  /** Validate one mcpServers object block from `file` (source = '.mcp.json' | 'plugin.json'). */
  function validateServersBlock(file, servers, source) {
    if (servers === null || typeof servers !== 'object' || Array.isArray(servers)) {
      findings.push({
        file: relTo(file),
        server: null,
        source,
        errors: ['mcpServers is not an object map'],
      });
      return;
    }
    for (const [serverName, config] of Object.entries(servers)) {
      serversValidated += 1;
      if (config === null || typeof config !== 'object' || Array.isArray(config)) {
        findings.push({
          file: relTo(file),
          server: serverName,
          source,
          errors: ['server entry is not an object'],
        });
        continue;
      }
      // Projection: the kernel per-server contract requires `name` inside the
      // entry; on-disk configs carry it as the map key.
      const candidate = { name: serverName, ...config };
      const ok = validate(candidate) === true;
      if (ok) {
        serversPassed += 1;
      } else {
        findings.push({
          file: relTo(file),
          server: serverName,
          source,
          projection: 'key->name',
          errors: (validate.errors || []).map(
            (e) =>
              `${e.instancePath || '/'} ${e.message}${e.params ? ` ${JSON.stringify(e.params)}` : ''}`,
          ),
        });
      }
    }
  }

  // 1) plugins/**/.mcp.json — the whole document is {"mcpServers": {...}} (or,
  //    rarely, a bare server map).
  for (const file of mcpJsonFiles) {
    filesScanned += 1;
    let doc;
    try {
      doc = JSON.parse(readFileSync(file, 'utf8'));
    } catch (e) {
      parseFailures += 1;
      findings.push({
        file: relTo(file),
        server: null,
        source: '.mcp.json',
        errors: [`JSON parse error: ${e.message}`],
      });
      continue;
    }
    const servers =
      doc && typeof doc === 'object' && !Array.isArray(doc) && doc.mcpServers
        ? doc.mcpServers
        : doc;
    validateServersBlock(file, servers, '.mcp.json');
  }

  // 2) mcpServers blocks inside plugin.json — only inline OBJECT blocks are
  //    validated; string/array forms are file references (the referenced
  //    .mcp.json files are already covered by the glob above).
  for (const file of pluginJsonFiles) {
    let doc;
    try {
      doc = JSON.parse(readFileSync(file, 'utf8'));
    } catch (e) {
      parseFailures += 1;
      findings.push({
        file: relTo(file),
        server: null,
        source: 'plugin.json',
        errors: [`JSON parse error: ${e.message}`],
      });
      continue;
    }
    if (!doc || typeof doc !== 'object' || !('mcpServers' in doc)) continue;
    filesScanned += 1;
    if (typeof doc.mcpServers === 'string' || Array.isArray(doc.mcpServers)) {
      stringRefBlocks += 1; // file reference — covered via the .mcp.json glob
      continue;
    }
    validateServersBlock(file, doc.mcpServers, 'plugin.json');
  }

  const report = {
    mode: STRICT ? 'strict' : 'advisory',
    kernelPackage: '@intentsolutions/core',
    composedSchema: COMPOSED_SCHEMA_ID,
    projection: 'mcpServers map key projected to per-entry `name` before validation',
    totals: {
      mcpJsonFiles: mcpJsonFiles.length,
      pluginJsonWithMcpServers: filesScanned - mcpJsonFiles.length,
      stringRefBlocks,
      serversValidated,
      serversPassed,
      serversFailed: serversValidated - serversPassed,
      parseFailures,
      findings: findings.length,
    },
    findings,
    generatedAt: new Date().toISOString(),
  };

  if (JSON_OUT) {
    console.log(JSON.stringify(report, null, 2));
  } else {
    console.log('');
    console.log('═══════════════════════════════════════════════════════════════');
    console.log(`  MCP CONFIG VALIDATION (kernel authoring/v1 · ${report.mode.toUpperCase()})`);
    console.log('═══════════════════════════════════════════════════════════════');
    console.log(`  .mcp.json files               : ${mcpJsonFiles.length}`);
    console.log(`  plugin.json inline mcpServers : ${filesScanned - mcpJsonFiles.length}`);
    console.log(
      `  string-ref mcpServers blocks  : ${stringRefBlocks} (covered via .mcp.json glob)`,
    );
    console.log(`  server entries validated      : ${serversValidated}`);
    console.log(`  PASS                          : ${serversPassed}`);
    console.log(`  FAIL                          : ${serversValidated - serversPassed}`);
    console.log(`  parse failures                : ${parseFailures}`);
    console.log('  ───────────────────────────────────────────────────────────');
    for (const f of findings) {
      console.log(`  ✗ ${f.file}${f.server ? ` [${f.server}]` : ''}`);
      for (const e of f.errors.slice(0, 8)) console.log(`      ${e}`);
      if (f.errors.length > 8) console.log(`      … and ${f.errors.length - 8} more`);
    }
    if (findings.length === 0)
      console.log('  No findings — corpus conforms to the kernel contract.');
    console.log('═══════════════════════════════════════════════════════════════');
    console.log(
      STRICT
        ? '  STRICT mode: exiting non-zero on findings.'
        : '  ADVISORY ONLY — findings reported, exit 0 (use --strict to gate).',
    );
    console.log('');
  }

  // GitHub Step Summary (matches the kernel-shadow advisory pattern).
  if (process.env.GITHUB_STEP_SUMMARY) {
    const lines = [];
    lines.push('## MCP config validation (advisory · kernel authoring/v1)');
    lines.push('');
    lines.push('| metric | value |');
    lines.push('| --- | --- |');
    lines.push(`| .mcp.json files | ${mcpJsonFiles.length} |`);
    lines.push(`| plugin.json inline mcpServers | ${filesScanned - mcpJsonFiles.length} |`);
    lines.push(`| server entries validated | ${serversValidated} |`);
    lines.push(`| PASS | ${serversPassed} |`);
    lines.push(`| FAIL | ${serversValidated - serversPassed} |`);
    lines.push(`| findings | ${findings.length} |`);
    lines.push('');
    if (findings.length > 0) {
      lines.push(`<details><summary>Findings (first 40 of ${findings.length})</summary>`);
      lines.push('');
      lines.push('| file | server | first error |');
      lines.push('| --- | --- | --- |');
      for (const f of findings.slice(0, 40)) {
        lines.push(`| \`${f.file}\` | ${f.server || ''} | ${f.errors[0] || ''} |`);
      }
      lines.push('');
      lines.push('</details>');
    }
    lines.push('');
    try {
      writeFileSync(process.env.GITHUB_STEP_SUMMARY, lines.join('\n') + '\n', { flag: 'a' });
    } catch (e) {
      console.error(`[validate-mcp-config] could not write step summary: ${e.message}`);
    }
  }

  if (STRICT && findings.length > 0) process.exit(1);
  process.exit(0);
}

main();
