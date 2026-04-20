#!/usr/bin/env node
/**
 * Promptbook — Detached build submission + summary generation.
 * Spawned by session-end.js as a background process.
 *
 * Responsibilities:
 * 1. Flush retry queue (previously failed submissions)
 * 2. Submit current build to API
 * 3. Generate title/summary via Haiku (or fallback)
 * 4. PATCH the build card
 *
 * Session metadata comes via env vars; API credentials read from config file.
 */
'use strict';

const fs = require('fs');
const path = require('path');
const { execSync, execFileSync } = require('child_process');
const { atomicWrite, appendLog, readConfig, hasTrackingConsent } = require('./lib/io');
const {
  generateFallbackTitle, generateFallbackSummary,
  buildSummaryPrompt,
} = require('./lib/summary');

// --- Environment ---
const SESSION_ID = process.env.PROMPTBOOK_SESSION_ID;
const SESSION_FILE = process.env.PROMPTBOOK_SESSION_FILE;
const TRANSCRIPT_PATH = process.env.PROMPTBOOK_TRANSCRIPT_PATH || '';
const COMPACT_LOG_FILE = process.env.PROMPTBOOK_COMPACT_LOG_FILE || '';
const AUTO_SUMMARY = process.env.PROMPTBOOK_AUTO_SUMMARY !== 'false';
const CLAUDE_BIN = process.env.PROMPTBOOK_CLAUDE_BIN || '';
const PROMPT_COUNT = process.env.PROMPTBOOK_PROMPT_COUNT || '0';
const MODEL = process.env.PROMPTBOOK_MODEL || 'unknown';
const BUILD_TIME = process.env.PROMPTBOOK_BUILD_TIME || '0';
const TOTAL_TOKENS = process.env.PROMPTBOOK_TOTAL_TOKENS || '0';
const TOOL_SUMMARY = process.env.PROMPTBOOK_TOOL_SUMMARY || '';
const PROJECT_NAME = process.env.PROMPTBOOK_PROJECT_NAME || '';
const DATA_DIR = process.env.PROMPTBOOK_DATA_DIR;
const SCRIPTS_DIR = process.env.PROMPTBOOK_SCRIPTS_DIR;

// Read API credentials from config file (not env vars — env is visible via ps)
const config = readConfig();
const API_KEY = config?.api_key || '';
const API_URL = config?.api_url || '';

// Validate required values early
if (!SESSION_ID || !SESSION_FILE || !API_KEY || !API_URL || !DATA_DIR || !hasTrackingConsent(config)) {
  process.exit(0);
}

function log(message) {
  appendLog(DATA_DIR, 'submit.log', `session=${SESSION_ID} | ${message}`);
}

/** Validate that a string looks like a UUID (prevents path traversal in URL construction). */
const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
function isValidBuildId(id) {
  return typeof id === 'string' && UUID_RE.test(id);
}

/**
 * Read plugin version from plugin.json (plugin installs).
 * Falls back to hooks-hash file (bash/setup.sh installs).
 */
function getHooksVersion() {
  // Try plugin version first
  try {
    const pluginJsonPath = path.join(SCRIPTS_DIR, '..', '.claude-plugin', 'plugin.json');
    const data = JSON.parse(fs.readFileSync(pluginJsonPath, 'utf8'));
    if (data.version) return data.version;
  } catch { /* not a plugin install */ }

  // Fall back to hooks-hash (written by setup.sh for bash installs)
  try {
    const hashPath = path.join(DATA_DIR, 'hooks-hash');
    const hash = fs.readFileSync(hashPath, 'utf8').trim();
    if (hash) return hash;
  } catch { /* no hooks-hash file */ }

  return '';
}

/**
 * Submit a session to the Promptbook API.
 * Returns { ok, buildId, updateAvailable, status } or { ok: false, status }.
 */
async function submitBuild(sessionFilePath) {
  try {
    const session = JSON.parse(fs.readFileSync(sessionFilePath, 'utf8'));

    // Strip sensitive/unnecessary fields before sending
    const payload = { ...session };
    delete payload.files_touched;
    delete payload.compact_log;
    delete payload.cwd;
    delete payload.prompt_timestamps;
    if (payload.source_metadata) {
      payload.source_metadata = { ...payload.source_metadata };
      delete payload.source_metadata.files_touched;
    }

    const pluginVersion = getHooksVersion();
    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${API_KEY}`,
    };
    if (pluginVersion) headers['X-Hooks-Hash'] = pluginVersion;

    const response = await fetch(`${API_URL}/api/builds`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(30000),
    });

    const body = await response.text();

    if (response.status === 201) {
      let parsed = {};
      try { parsed = JSON.parse(body); } catch { /* ignore */ }
      const buildId = isValidBuildId(parsed.id) ? parsed.id : '';
      if (!buildId) {
        appendLog(DATA_DIR, 'submit.log', `WARN: 201 but missing/invalid build ID — will retry`);
        return { ok: false, status: 201 };
      }
      return {
        ok: true,
        buildId,
        updateAvailable: parsed.update_available || false,
        status: 201,
      };
    }

    // 409 = duplicate session — treat as success (already submitted)
    if (response.status === 409) {
      let parsed = {};
      try { parsed = JSON.parse(body); } catch { /* ignore */ }
      const existingId = isValidBuildId(parsed.build_id) ? parsed.build_id : '';
      return { ok: true, buildId: existingId, updateAvailable: false, status: 409 };
    }

    return { ok: false, status: response.status, body };
  } catch (err) {
    return { ok: false, status: 0, body: err.message };
  }
}

/**
 * Flush the retry queue: submit previously failed sessions.
 * Session files with status "completed" and no submitted_at are candidates.
 */
async function flushRetryQueue() {
  try {
    const sessionsDir = path.join(DATA_DIR, 'sessions');
    if (!fs.existsSync(sessionsDir)) return;

    const files = fs.readdirSync(sessionsDir).filter(f => f.endsWith('.json') && f !== `${SESSION_ID}.json`);
    const candidates = [];

    for (const file of files) {
      try {
        const filePath = path.join(sessionsDir, file);
        const session = JSON.parse(fs.readFileSync(filePath, 'utf8'));
        if (session.status === 'completed' && !session.submitted_at) {
          // Skip sessions older than 30 days
          const age = Date.now() - new Date(session.start_time).getTime();
          if (age > 30 * 24 * 60 * 60 * 1000) {
            // Too stale — clean up
            try { fs.unlinkSync(filePath); } catch { /* ignore */ }
            continue;
          }
          candidates.push({ filePath, startTime: session.start_time });
        }
      } catch { /* skip corrupted files */ }
    }

    // Sort oldest first, limit to 5
    candidates.sort((a, b) => new Date(a.startTime) - new Date(b.startTime));
    const toRetry = candidates.slice(0, 5);

    for (const { filePath } of toRetry) {
      const result = await submitBuild(filePath);
      if (result.ok && result.status !== 409) {
        try {
          const session = JSON.parse(fs.readFileSync(filePath, 'utf8'));
          session.submitted_at = new Date().toISOString();
          atomicWrite(filePath, session);
          log(`RETRY OK: ${path.basename(filePath)} (HTTP ${result.status})`);
        } catch { /* ignore */ }

        // Publish retried build with fallback title/summary so it doesn't stay draft
        if (result.buildId) {
          await publishWithFallback(result.buildId, 'retry_fallback', 'retried_session');
        }
      } else if (result.ok && result.status === 409) {
        // Already submitted — mark so we don't retry again
        try {
          const session = JSON.parse(fs.readFileSync(filePath, 'utf8'));
          session.submitted_at = new Date().toISOString();
          atomicWrite(filePath, session);
          log(`RETRY SKIP: ${path.basename(filePath)} (duplicate)`);
        } catch { /* ignore */ }
      } else {
        log(`RETRY FAIL: ${path.basename(filePath)} (HTTP ${result.status})`);
        break; // Stop retrying if API is down
      }
    }
  } catch (err) {
    log(`RETRY ERROR: ${err.message}`);
  }
}

/**
 * Update the summary status on the server.
 */
async function updateSummaryStatus(buildId, status, errorCode) {
  try {
    const body = { status };
    if (errorCode) body.error_code = errorCode;

    await fetch(`${API_URL}/api/builds/${buildId}/summary-status`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_KEY}`,
      },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(5000),
    });
  } catch { /* silent */ }
}

/**
 * Publish the build with a deterministic fallback summary.
 */
async function publishWithFallback(buildId, summaryStatus, errorCode) {
  await updateSummaryStatus(buildId, summaryStatus, errorCode);

  const title = generateFallbackTitle(PROMPT_COUNT, BUILD_TIME, PROJECT_NAME, TOOL_SUMMARY);
  const summary = generateFallbackSummary(PROMPT_COUNT, BUILD_TIME, TOTAL_TOKENS, MODEL, TOOL_SUMMARY);

  log(`FALLBACK: publishing with deterministic summary: title="${title}"`);

  try {
    const response = await fetch(`${API_URL}/api/builds/${buildId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_KEY}`,
      },
      body: JSON.stringify({ title, summary, status: 'published' }),
      signal: AbortSignal.timeout(10000),
    });

    if (response.status === 200) {
      log('PUBLISHED: fallback summary applied');
    } else {
      log(`PATCH FAIL (HTTP ${response.status}): ${await response.text()}`);
    }
  } catch (err) {
    log(`PATCH ERROR: ${err.message}`);
  }
}

/**
 * Generate summary via Haiku and publish the build.
 */
async function generateAndPublish(buildId) {
  // Read compact log
  let compactLog = '';
  if (COMPACT_LOG_FILE && fs.existsSync(COMPACT_LOG_FILE)) {
    compactLog = fs.readFileSync(COMPACT_LOG_FILE, 'utf8');
    try { fs.unlinkSync(COMPACT_LOG_FILE); } catch { /* ignore */ }
    log('SOURCE: pre-extracted compact log file');
  } else if (TRANSCRIPT_PATH && fs.existsSync(TRANSCRIPT_PATH)) {
    // Re-parse transcript as fallback
    try {
      const { parseTranscript } = require('./lib/transcript');
      const result = parseTranscript(TRANSCRIPT_PATH, '', true);
      compactLog = result.compact_log || '';
      log('SOURCE: transcript fallback');
    } catch { /* ignore */ }
  }

  if (!compactLog) {
    log('SKIP: empty compact log');
    await publishWithFallback(buildId, 'skipped_empty_log', 'empty_compact_log');
    return;
  }

  // Truncate to ~4000 chars
  if (compactLog.length > 4000) {
    const originalLen = compactLog.length;
    compactLog = compactLog.slice(0, 4000) + '\n... (truncated)';
    log(`TRUNCATED: compact log was ${originalLen} chars, trimmed to 4000`);
  }

  // Resolve claude CLI
  let claudeCmd = '';
  if (CLAUDE_BIN && fs.existsSync(CLAUDE_BIN)) {
    claudeCmd = CLAUDE_BIN;
  } else {
    try {
      claudeCmd = execSync('which claude 2>/dev/null || where claude 2>nul', { encoding: 'utf8' }).trim();
    } catch { /* not found */ }
  }

  if (!claudeCmd) {
    log('SKIP: claude CLI not found');
    await publishWithFallback(buildId, 'skipped_no_claude', 'no_claude_cli');
    return;
  }

  // Build prompt and call Haiku
  const prompt = buildSummaryPrompt(compactLog, PROJECT_NAME, PROMPT_COUNT);
  log(`START: calling claude --print --model haiku | prompt_chars=${prompt.length} compact_log_chars=${compactLog.length}`);

  let response = '';
  try {
    response = execFileSync(claudeCmd, ['--print', '--model', 'haiku'], {
      input: prompt,
      encoding: 'utf8',
      timeout: 60000,
      env: { ...process.env, PROMPTBOOK_SKIP_HOOKS: '1' },
    });
  } catch (err) {
    log(`FAIL: claude CLI error: ${err.message}`);
    await publishWithFallback(buildId, 'patch_failed', 'claude_cli_error');
    return;
  }

  if (!response) {
    log('FAIL: empty response from claude');
    await publishWithFallback(buildId, 'patch_failed', 'empty_claude_response');
    return;
  }

  log(`RAW: ${response.split('\n').slice(0, 3).join(' | ')}`);
  log(`HAIKU_COST_EST: input_chars=${prompt.length} output_chars=${response.length} est_input_tokens=${Math.floor(prompt.length / 4)} est_output_tokens=${Math.floor(response.length / 4)}`);

  // Parse title and summary
  const titleMatch = response.match(/^TITLE:\s*(.+)/im);
  const summaryMatch = response.match(/^SUMMARY:\s*(.+)/im);
  const title = titleMatch ? titleMatch[1].trim() : '';
  const summary = summaryMatch ? summaryMatch[1].trim() : '';

  if (!title && !summary) {
    log(`FAIL: could not parse title/summary from response: ${response.split('\n').slice(0, 3).join(' | ')}`);
    await publishWithFallback(buildId, 'patch_failed', 'unparseable_claude_response');
    return;
  }

  log(`OK: title="${title}"`);

  // PATCH the build card
  try {
    const patchResponse = await fetch(`${API_URL}/api/builds/${buildId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_KEY}`,
      },
      body: JSON.stringify({ title, summary, status: 'published' }),
      signal: AbortSignal.timeout(10000),
    });

    if (patchResponse.status === 200) {
      await updateSummaryStatus(buildId, 'generated');
      log('PUBLISHED: title + summary applied, card is now public');
    } else {
      const body = await patchResponse.text();
      await updateSummaryStatus(buildId, 'patch_failed', `patch_http_${patchResponse.status}`);
      log(`PATCH FAIL (HTTP ${patchResponse.status}): ${body}`);
    }
  } catch (err) {
    log(`PATCH ERROR: ${err.message}`);
  }
}

/**
 * Write a message directly to the user's terminal (even from a detached process).
 */
function writeToTerminal(msg) {
  try {
    const fd = fs.openSync('/dev/tty', 'w');
    fs.writeSync(fd, msg);
    fs.closeSync(fd);
    return;
  } catch { /* not Unix or no tty */ }
  if (process.platform === 'win32') {
    try {
      const fd = fs.openSync('CON', 'w');
      fs.writeSync(fd, msg);
      fs.closeSync(fd);
      return;
    } catch { /* no console */ }
  }
}

// --- Main ---
async function main() {
  log(`--- ${new Date().toISOString()} | session=${SESSION_ID} ---`);

  // 1. Flush retry queue first
  await flushRetryQueue();

  // 2. Submit current build
  const result = await submitBuild(SESSION_FILE);

  if (result.ok && result.status !== 409) {
    log(`OK: build_id=${result.buildId}`);

    // Mark as submitted
    try {
      const session = JSON.parse(fs.readFileSync(SESSION_FILE, 'utf8'));
      session.submitted_at = new Date().toISOString();
      atomicWrite(SESSION_FILE, session);
    } catch { /* ignore */ }

    if (result.buildId) {
      const siteUrl = API_URL.replace(/\/api.*/, '').replace(/\/$/, '');
      writeToTerminal(`\n  \x1b[32m\u2713\x1b[0m Progress recorded \u2192 \x1b[4m${siteUrl}/build/${result.buildId}\x1b[0m\n\n`);

      if (result.updateAvailable) {
        const updateCmd = process.env.CLAUDE_PLUGIN_ROOT
          ? '/plugin update promptbook'
          : 'bash <(curl -sL promptbook.gg/setup.sh)';
        writeToTerminal(`  \x1b[33m\u2191\x1b[0m Promptbook update available \u2014 run: \x1b[4m${updateCmd}\x1b[0m\n\n`);
      }

      // 3. Generate summary and publish
      if (AUTO_SUMMARY) {
        await generateAndPublish(result.buildId);
      } else {
        // Auto-summary disabled — publish immediately with deterministic fallback
        await publishWithFallback(result.buildId, 'disabled', 'auto_summary_off');
      }
    }
  } else if (result.ok && result.status === 409) {
    log('SKIP: duplicate session (already submitted)');
    // Mark as submitted so we don't retry
    try {
      const session = JSON.parse(fs.readFileSync(SESSION_FILE, 'utf8'));
      session.submitted_at = new Date().toISOString();
      atomicWrite(SESSION_FILE, session);
    } catch { /* ignore */ }

    // Still show terminal link if we have the existing build ID
    if (result.buildId) {
      const siteUrl = API_URL.replace(/\/api.*/, '').replace(/\/$/, '');
      writeToTerminal(`\n  \x1b[32m\u2713\x1b[0m Progress recorded \u2192 \x1b[4m${siteUrl}/build/${result.buildId}\x1b[0m\n\n`);
    }
  } else {
    log(`FAIL (HTTP ${result.status}): ${result.body || 'unknown error'}`);
    // Don't mark as submitted — will be retried on next session end
  }

  // Cleanup compact log if still around
  if (COMPACT_LOG_FILE && fs.existsSync(COMPACT_LOG_FILE)) {
    try { fs.unlinkSync(COMPACT_LOG_FILE); } catch { /* ignore */ }
  }
}

main().catch(err => {
  log(`UNCAUGHT: ${err.message}`);
});
