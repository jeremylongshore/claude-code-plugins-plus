#!/usr/bin/env node
/**
 * check-mcp-plaintext-creds.mjs — refuse a live-shaped credential in plaintext
 * `env` in the repo-root MCP config (blueprint 727, Epic 1 bead 1.14).
 *
 * WHY THIS EXISTS
 * ---------------
 * The working-tree `/.mcp.json` (git-ignored, machine-local) carried a live
 * Whop API key in plaintext `env` for months — never published, but sitting
 * unencrypted on a box where multiple agent sessions run with filesystem
 * access (blueprint § 18.7). The value now lives SOPS-encrypted in
 * `.env.sops`, injected at server launch by `scripts/sops-env`. This
 * pre-flight is the delegable recurrence guard: an MCP config whose `env`
 * holds a live-shaped value fails loudly with the sanctioned fix.
 *
 * SCOPE
 * -----
 * Exactly the repo-root `.mcp.json`. Plugin directories ship example MCP
 * configs with placeholder values by design; those are graded by the skill
 * validator, not by this guard. A missing root config passes (CI checkouts
 * never contain the untracked file). Epic 4 bead 4.14 owns the stronger
 * refuse-to-start integration.
 *
 * WHAT COUNTS AS LIVE-SHAPED
 * --------------------------
 * Known provider prefixes (apik_, sk-, ghp_/gho_/ghs_, github_pat_, xoxb-/
 * xoxp-, AKIA, glpat-, AGE-SECRET-KEY-) — plus a fallback: any env value 20+
 * chars that is not a placeholder (${VAR} interpolation, YOUR_ prefixes,
 * REPLACE, CHANGEME, EXAMPLE, PLACEHOLDER, angle-bracketed hints) is treated
 * as a secret. Fail closed: when in doubt, it does not belong in plaintext.
 */

import { existsSync, readFileSync, realpathSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(__dirname, '..');

const LIVE_PREFIXES =
  /^(apik_|sk-|ghp_|gho_|ghs_|github_pat_|xox[bpsoar]-|AKIA|glpat-|AGE-SECRET-KEY-)/;
const PLACEHOLDER =
  /^(\$\{[^}]*\}|<[^>]*>|(YOUR|MY|EXAMPLE|SAMPLE|TEST|DUMMY|FAKE)[-_].*|REPLACE.*|CHANGE ?ME.*|PLACEHOLDER.*|TODO.*|xxx+|\.\.\.)$/i;

/** Classify one env value. Returns null when safe, else a reason string. */
export function classifyEnvValue(value) {
  if (typeof value !== 'string' || value.length === 0) return null;
  if (PLACEHOLDER.test(value.trim())) return null;
  if (LIVE_PREFIXES.test(value.trim())) return 'matches a known live credential prefix';
  if (value.trim().length >= 20 && !/\s/.test(value.trim()))
    return 'is a 20+ character opaque value that is not a recognized placeholder';
  return null;
}

/** Scan a parsed MCP config object. Returns violation strings. */
export function scanMcpConfig(config) {
  const violations = [];
  const servers = config?.mcpServers ?? {};
  for (const [name, server] of Object.entries(servers)) {
    for (const [key, value] of Object.entries(server?.env ?? {})) {
      const reason = classifyEnvValue(value);
      if (reason) {
        violations.push(
          `server "${name}" env ${key}: ${reason}. Move it to .env.sops and launch via ` +
            `scripts/sops-env (see blueprint 727 § 18.7 / bead E1.14).`,
        );
      }
    }
  }
  return violations;
}

const isMain = process.argv[1] && import.meta.url === new URL(`file://${process.argv[1]}`).href;
if (isMain) {
  // E4.14 refuse-to-start pre-flight: --all-local additionally scans this
  // machine's ~/.claude.json project registration for the repo — the config
  // that actually LAUNCHES the MCP servers, and where the § 18.7 plaintext
  // key historically lived. Wired into the pre-commit hook so work on this
  // box refuses to proceed while a plaintext key sits in either config.
  const ALL_LOCAL = process.argv.includes('--all-local');
  const targets = [{ path: join(REPO_ROOT, '.mcp.json'), label: 'root .mcp.json' }];
  if (ALL_LOCAL && process.env.HOME) {
    targets.push({
      path: join(process.env.HOME, '.claude.json'),
      label: "~/.claude.json (this repo's project mcpServers)",
      project: REPO_ROOT,
    });
  }
  let violations = [];
  let scanned = 0;
  for (const target of targets) {
    if (!existsSync(target.path)) continue;
    let config;
    try {
      config = JSON.parse(readFileSync(target.path, 'utf8'));
    } catch (err) {
      console.error(
        `mcp-plaintext-creds: STRUCTURAL — ${target.label} unparseable (${err.message})`,
      );
      process.exit(1);
    }
    if (target.project) {
      const projects = config?.projects ?? {};
      const key = Object.keys(projects).find((p) => {
        try {
          return realpathSync(p) === realpathSync(target.project);
        } catch {
          return p === target.project;
        }
      });
      config = { mcpServers: (key && projects[key]?.mcpServers) || {} };
    }
    scanned += 1;
    violations = violations.concat(scanMcpConfig(config).map((v) => `${target.label}: ${v}`));
  }
  if (scanned === 0) {
    console.log('mcp-plaintext-creds: OK (no MCP config present in this checkout)');
    process.exit(0);
  }
  for (const v of violations) console.error(`mcp-plaintext-creds: VIOLATION — ${v}`);
  if (violations.length > 0) {
    console.error(`mcp-plaintext-creds: FAIL — ${violations.length} plaintext credential(s).`);
    process.exit(1);
  }
  console.log(
    `mcp-plaintext-creds: OK (${scanned} config(s) hold no live-shaped plaintext env${ALL_LOCAL ? '; local pre-flight' : ''})`,
  );
}
