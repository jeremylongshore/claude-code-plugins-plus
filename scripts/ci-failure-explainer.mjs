#!/usr/bin/env node
/**
 * ci-failure-explainer.mjs
 *
 * DETERMINISTIC "why did CI fail + how to fix it" renderer for a contributor
 * PR comment. Given a set of FAILED CI checks (check-run name + its error
 * text), it emits a marker-anchored markdown comment mapping each recognised
 * failure signature to a concrete, repo-specific fix. NO LLM, no network, no
 * fork-code execution — a pure function of its input, so the same failures
 * always render byte-identical output.
 *
 * WHY THIS SHAPE (reuse, not reinvent): this deliberately reuses the mechanism
 * from @intentsolutions/jrig-cli (`@j-rig/core`):
 *   - the `CheckResult { id, severity, message, details }` finding record,
 *     where `details` is the "how to fix" slot
 *     (j-rig-binary-eval/packages/core/src/checks/types.ts),
 *   - the `summarize()` + report-formatting pattern (same file), and
 *   - the rollout-gate marker-pair idempotent-comment model
 *     (`<!-- key --> … <!-- /key -->`, patch-in-place, byte-stable —
 *     j-rig-binary-eval/packages/pr-comment/src/render.ts).
 * The SIGNATURE_CATALOG below is the `{code → handler}` dispatch pattern from
 * j-rig's intentional-mapping registry, keyed on THIS repo's CI signatures.
 *
 * The catalog is authored (there is no upstream signature→fix table to copy);
 * everything around it is the reused j-rig contract.
 *
 * Usage:
 *   node scripts/ci-failure-explainer.mjs --checks failed-checks.json
 *   node scripts/ci-failure-explainer.mjs --checks failed-checks.json --json
 *   cat failed-checks.json | node scripts/ci-failure-explainer.mjs --stdin
 *
 * Input JSON shape (array of failed checks):
 *   [ { "name": "eslint-check", "text": "…first ~N lines of the failing log…",
 *       "url": "https://github.com/…/job/123" }, … ]
 *
 * Output: markdown comment on stdout (or the PackageReport JSON with --json).
 * Exit code: always 0 — this is an advisory helper; producing no recognised
 * findings still emits a valid (generic) comment.
 */

import { readFileSync } from 'node:fs';

// The idempotence marker key. The workflow lists PR comments, finds the one
// carrying the OPENING marker for this key, and PATCHes it in place instead of
// posting a duplicate. Deliberately DISTINCT from pr-prescreen's
// `pr-prescreen-marker` so the two bots never clobber each other's comment.
export const MARKER_KEY = 'ci-failure-explainer';
export const MARKER_OPEN = `<!-- ${MARKER_KEY} -->`;
export const MARKER_CLOSE = `<!-- /${MARKER_KEY} -->`;

// ---------------------------------------------------------------------------
// j-rig CheckResult contract (reused shape)
// ---------------------------------------------------------------------------

/** @typedef {{ id: string, description?: string, severity: 'error'|'warning'|'pass', message: string, details?: string }} CheckResult */

/** Build the summary counts — mirrors @j-rig/core summarize(). */
export function summarize(results) {
  return {
    total: results.length,
    passed: results.filter((r) => r.severity === 'pass').length,
    warnings: results.filter((r) => r.severity === 'warning').length,
    errors: results.filter((r) => r.severity === 'error').length,
  };
}

// ---------------------------------------------------------------------------
// SIGNATURE CATALOG — the {signature → CheckResult} dispatch (MM-N pattern)
//
// Each entry: appliesTo(name, text) returns a truthy match (or null); toResult
// turns that match into a CheckResult whose `details` is the concrete fix. The
// FIRST matching entry per failed check wins (order = specificity). A check
// that matches nothing falls through to the generic explainer so a contributor
// always gets *something* actionable plus the log link.
// ---------------------------------------------------------------------------

/** Extract distinct markdownlint rule codes (MD012, MD022, …) from log text. */
function markdownRules(text) {
  const codes = new Set();
  for (const m of text.matchAll(/\bMD\d{3}\b/g)) codes.add(m[0]);
  return [...codes].sort();
}

/** Extract the "MISSING required document: <path>" targets from log text. */
function missingDocs(text) {
  const docs = new Set();
  for (const m of text.matchAll(/MISSING required document:\s*(\S+)/g)) docs.add(m[1]);
  return [...docs].sort();
}

export const SIGNATURE_CATALOG = [
  {
    id: 'deps:lockfile-stale',
    appliesTo: (_name, text) => /ERR_PNPM_OUTDATED_LOCKFILE/.test(text),
    toResult: () => ({
      id: 'deps:lockfile-stale',
      severity: 'error',
      message:
        'pnpm-lock.yaml is out of date with a changed package.json (frozen-lockfile install failed).',
      details:
        'Run `pnpm install --lockfile-only` locally, then commit the updated `pnpm-lock.yaml`. ' +
        'Do NOT hand-edit the lockfile. This one fix typically clears eslint-check AND cli-smoke-tests, ' +
        'which both fail early when dependencies cannot install.',
    }),
  },
  {
    id: 'docs:submission-missing',
    appliesTo: (_name, text) => /MISSING required document/.test(text),
    toResult: (_m, text) => {
      const docs = missingDocs(text);
      return {
        id: 'docs:submission-missing',
        severity: 'error',
        message:
          docs.length > 0
            ? `New plugin is missing required submission doc(s): ${docs.join(', ')}.`
            : 'New plugin is missing required submission documents for its tier.',
        details:
          'Add the tier-required docs (micro → `docs/PRD.md`; standard → + `docs/ADR.md`; ' +
          'pack → + `docs/ONE-PAGER.md`). Templates live in `templates/skill-docs/`; the tier ' +
          'matrix + standard are in `000-docs/700-DR-GUID-skill-submission-standard.md`.',
      };
    },
  },
  {
    id: 'docs:markdownlint',
    appliesTo: (name, text) => /markdownlint/i.test(name) || markdownRules(text).length > 0,
    toResult: (_m, text) => {
      const rules = markdownRules(text);
      return {
        id: 'docs:markdownlint',
        severity: 'error',
        message:
          rules.length > 0
            ? `Markdown style violations: ${rules.join(', ')}.`
            : 'Markdown style violations (markdownlint).',
        details:
          'Fix the flagged lines (common ones: MD022 blank lines around headings, MD032 blank ' +
          'lines around lists, MD012 no consecutive blanks, MD047 end file with one newline). ' +
          'Run `npx markdownlint-cli2 "<your-changed-file>.md"` locally to see + fix them.',
      };
    },
  },
  {
    id: 'style:prettier',
    appliesTo: (name) => /format-check/i.test(name),
    toResult: () => ({
      id: 'style:prettier',
      severity: 'error',
      message: 'Files are not Prettier-formatted (format-check).',
      details: 'Run `pnpm run format` and commit the result.',
    }),
  },
  {
    id: 'lint:eslint',
    appliesTo: (name) => /eslint/i.test(name),
    toResult: () => ({
      id: 'lint:eslint',
      severity: 'error',
      message: 'ESLint reported problems (eslint-check).',
      details:
        'Run `pnpm lint` locally to see them. If the log shows ERR_PNPM_OUTDATED_LOCKFILE, ' +
        'fix the lockfile first (see the lockfile item) — eslint fails early when deps cannot install.',
    }),
  },
  {
    id: 'validate:marketplace',
    appliesTo: (name, text) => /^validate$/i.test(name) || /validate-skills-schema/.test(text),
    toResult: () => ({
      id: 'validate:marketplace',
      severity: 'error',
      message: 'A SKILL.md / plugin.json failed the marketplace-tier validator.',
      details:
        'Run `python3 scripts/validate-skills-schema.py --marketplace <your-plugin-dir>` locally. ' +
        'The 8 required frontmatter fields (name, description, allowed-tools, version, author, ' +
        'license, compatibility, tags) plus the required body sections must all be present.',
    }),
  },
];

/**
 * Turn a list of failed checks into a j-rig-shaped PackageReport.
 * @param {{name: string, text?: string, url?: string}[]} failedChecks
 * @param {string} nowIso  timestamp (injected so the function stays pure/testable)
 */
export function explain(failedChecks, nowIso) {
  /** @type {CheckResult[]} */
  const results = [];
  for (const check of failedChecks) {
    const name = check.name ?? '(unknown check)';
    const text = check.text ?? '';
    const entry = SIGNATURE_CATALOG.find((e) => e.appliesTo(name, text));
    if (entry) {
      results.push(entry.toResult(name, text));
    } else {
      // Generic fallback — never leave a failed check unexplained.
      results.push({
        id: `check:${name}`,
        severity: 'error',
        message: `\`${name}\` failed.`,
        details: check.url
          ? `Open the check log for the specific error: ${check.url}`
          : 'Open the failing check’s log for the specific error.',
      });
    }
  }
  // De-dupe by id (e.g. eslint + cli-smoke both trace to the lockfile) so the
  // contributor sees each fix once.
  const seen = new Set();
  const deduped = results.filter((r) => (seen.has(r.id) ? false : seen.add(r.id)));
  return {
    skill_name: null,
    timestamp: nowIso,
    results: deduped,
    summary: summarize(deduped),
  };
}

/**
 * Render the report as a marker-anchored markdown PR comment (reuses the
 * rollout-gate idempotence model — the workflow patches the comment carrying
 * MARKER_OPEN in place). Pure: same report → byte-identical body.
 */
export function renderComment(report) {
  const lines = [];
  lines.push(MARKER_OPEN);
  lines.push('## Why this PR’s checks failed — and how to fix each one');
  lines.push('');
  lines.push(
    '_Deterministic summary from the failing checks. Advisory, not a required gate; ' +
      'fix these and push to re-run._',
  );
  lines.push('');
  if (report.results.length === 0) {
    lines.push('No recognised failures to explain — open the checks tab for details.');
  } else {
    for (const r of report.results) {
      lines.push(`### \`${r.id}\``);
      lines.push(`**${r.message}**`);
      if (r.details) {
        lines.push('');
        lines.push(r.details);
      }
      lines.push('');
    }
  }
  lines.push(MARKER_CLOSE);
  return lines.join('\n');
}

// ---------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------

function main() {
  const args = process.argv.slice(2);
  const asJson = args.includes('--json');
  const useStdin = args.includes('--stdin');
  const checksIdx = args.indexOf('--checks');
  let raw;
  if (useStdin) {
    raw = readFileSync(0, 'utf-8');
  } else if (checksIdx !== -1 && args[checksIdx + 1]) {
    raw = readFileSync(args[checksIdx + 1], 'utf-8');
  } else {
    console.error('Usage: ci-failure-explainer.mjs --checks <file.json> | --stdin  [--json]');
    process.exit(2);
  }
  let failedChecks;
  try {
    failedChecks = JSON.parse(raw);
    if (!Array.isArray(failedChecks)) throw new Error('input must be a JSON array');
  } catch (e) {
    console.error(`ci-failure-explainer: bad input JSON: ${e.message}`);
    process.exit(2);
  }
  // Timestamp is stamped by the CLI (impure boundary), never inside explain().
  const report = explain(failedChecks, new Date().toISOString());
  process.stdout.write(asJson ? JSON.stringify(report, null, 2) : renderComment(report));
  process.stdout.write('\n');
}

// Only run main() when invoked directly, so tests can import the pure fns.
import { fileURLToPath } from 'node:url';
if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  main();
}
