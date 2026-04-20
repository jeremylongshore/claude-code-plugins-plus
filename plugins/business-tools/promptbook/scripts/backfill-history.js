#!/usr/bin/env node
/**
 * Promptbook — Historic Data Sync (Backfill)
 *
 * Scans local Claude Code JSONL transcripts and submits aggregate stats
 * as backfill Build Cards. Uses the same parsing logic as the live hooks.
 *
 * Never sends prompts, code, or file contents — only aggregate stats.
 *
 * Usage:
 *   node backfill-history.js [--days N] [--dry-run] [--json] [--project DIR]
 *                            [--before DATE] [--generate-summaries]
 *                            [--api-url URL]
 */
'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync, execFileSync } = require('child_process');
const { parseTranscript, parseSubagentTokens } = require('./lib/transcript');
const { getPrimaryLanguage, deriveProjectName } = require('./lib/language');
const { buildSummaryPrompt, generateFallbackTitle, generateFallbackSummary } = require('./lib/summary');

// --- CLI argument parsing ---
const args = process.argv.slice(2);
function getArg(name, defaultVal) {
  const idx = args.indexOf(`--${name}`);
  if (idx === -1) return defaultVal;
  if (typeof defaultVal === 'boolean') return true;
  return args[idx + 1] || defaultVal;
}
const DAYS = Number(getArg('days', '30'));
const DRY_RUN = getArg('dry-run', false);
const JSON_MODE = getArg('json', false);
const PROJECT_FILTER = getArg('project', '');
const BEFORE = getArg('before', '');
const GENERATE_SUMMARIES = getArg('generate-summaries', false);
const API_URL_ARG = getArg('api-url', '');
const BATCH_ID_ARG = getArg('batch-id', '');
let currentApiUrl = API_URL_ARG;
let currentApiKey = '';
let currentBatchId = BATCH_ID_ARG;

// --- Checkpoint helpers ---
const CHECKPOINT_PATH = path.join(os.homedir(), '.promptbook', 'backfill-summary-progress.json');

function loadCheckpoint(batchId) {
  try {
    if (!fs.existsSync(CHECKPOINT_PATH)) return new Set();
    const data = JSON.parse(fs.readFileSync(CHECKPOINT_PATH, 'utf8'));
    if (data.batch_id !== batchId) return new Set(); // different batch, start fresh
    return new Set(data.summarized_ids || []);
  } catch { return new Set(); }
}

function saveCheckpoint(batchId, summarizedIds) {
  try {
    const dir = path.dirname(CHECKPOINT_PATH);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(CHECKPOINT_PATH, JSON.stringify({
      batch_id: batchId,
      summarized_ids: [...summarizedIds],
      updated_at: new Date().toISOString(),
    }));
  } catch { /* best effort */ }
}

function clearCheckpoint() {
  try { if (fs.existsSync(CHECKPOINT_PATH)) fs.unlinkSync(CHECKPOINT_PATH); } catch { /* ok */ }
}

// --- Mark sessions as submitted in the live hook's retry queue ---
function markSessionsSubmitted(sessionIds) {
  const sessionsDir = path.join(os.homedir(), '.promptbook', 'sessions');
  if (!fs.existsSync(sessionsDir)) return;
  let marked = 0;
  for (const id of sessionIds) {
    const filePath = path.join(sessionsDir, `${id}.json`);
    try {
      if (!fs.existsSync(filePath)) continue;
      const session = JSON.parse(fs.readFileSync(filePath, 'utf8'));
      if (session.submitted_at) continue; // already marked
      session.submitted_at = new Date().toISOString();
      fs.writeFileSync(filePath, JSON.stringify(session, null, 2));
      marked++;
    } catch { /* best effort */ }
  }
  if (marked > 0) log(`  Marked ${marked} sessions as submitted in retry queue`);
}

// --- Helpers ---
function log(msg) {
  process.stderr.write(msg + '\n');
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function parseRetryAfterMs(response) {
  const header = response.headers.get('retry-after');
  if (!header) return null;

  const seconds = Number(header);
  if (Number.isFinite(seconds) && seconds > 0) {
    return seconds * 1000;
  }

  const dateMs = Date.parse(header);
  if (!Number.isNaN(dateMs)) {
    return Math.max(dateMs - Date.now(), 0);
  }

  return null;
}

function computeBackoffMs(attempt, response) {
  const retryAfterMs = response ? parseRetryAfterMs(response) : null;
  if (retryAfterMs !== null) {
    return retryAfterMs + Math.floor(Math.random() * 500);
  }

  const baseMs = Math.min(1000 * (2 ** attempt), 15000);
  return baseMs + Math.floor(Math.random() * 500);
}

async function fetchWithRetry(url, options, retryOptions = {}) {
  const {
    maxRetries = 4,
    retryStatuses = [429, 502, 503, 504],
    label = 'request',
  } = retryOptions;

  let lastError = null;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    let response = null;
    try {
      response = await fetch(url, options);
      if (!retryStatuses.includes(response.status)) {
        return response;
      }

      lastError = new Error(`${label} failed with HTTP ${response.status}`);
      if (attempt === maxRetries) {
        return response;
      }

      const delayMs = computeBackoffMs(attempt, response);
      log(`  ${label} rate-limited, retrying in ${Math.ceil(delayMs / 1000)}s...`);
      await sleep(delayMs);
    } catch (err) {
      lastError = err;
      if (attempt === maxRetries) throw err;

      const delayMs = computeBackoffMs(attempt, null);
      log(`  ${label} failed (${err.message}), retrying in ${Math.ceil(delayMs / 1000)}s...`);
      await sleep(delayMs);
    }
  }

  throw lastError || new Error(`${label} failed`);
}

async function startBatch(apiUrl, apiKey) {
  const response = await fetchWithRetry(`${apiUrl}/api/backfill/start`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`,
    },
    body: JSON.stringify({ days_scanned: DAYS }),
    signal: AbortSignal.timeout(30000),
  }, {
    maxRetries: 2,
    label: 'start batch',
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Failed to start backfill (HTTP ${response.status}): ${body}`);
  }

  const body = await response.json();
  if (!body.batch_id || typeof body.batch_id !== 'string') {
    throw new Error('Failed to start backfill: missing batch_id');
  }

  return body.batch_id;
}

async function updateBatchProgress(apiUrl, apiKey, batchId, update) {
  if (!batchId) return;

  try {
    await fetchWithRetry(`${apiUrl}/api/backfill/progress`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`,
      },
      body: JSON.stringify({ batch_id: batchId, ...update }),
      signal: AbortSignal.timeout(15000),
    }, {
      maxRetries: 2,
      label: 'progress update',
    });
  } catch {
    // Progress updates are best-effort so local scanning never blocks on them.
  }
}

async function finalizeBatchProgress(apiUrl, apiKey, batchId, update) {
  if (!batchId) return;

  let lastError = null;
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      const response = await fetchWithRetry(`${apiUrl}/api/backfill/progress`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${apiKey}`,
        },
        body: JSON.stringify({ batch_id: batchId, ...update }),
        signal: AbortSignal.timeout(15000),
      }, {
        maxRetries: 4,
        label: 'final progress update',
      });
      if (response.ok) return;
      lastError = new Error(`HTTP ${response.status}`);
    } catch (err) {
      lastError = err;
    }

    if (attempt < 2) {
      await new Promise(r => setTimeout(r, 1000));
    }
  }

  throw lastError || new Error('Failed to finalize backfill progress');
}

async function updateBuildSummary(apiUrl, apiKey, batchId, session) {
  const response = await fetchWithRetry(`${apiUrl}/api/backfill/summary`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      batch_id: batchId,
      session_id: session.session_id,
      title: session.title,
      summary: session.summary,
    }),
    signal: AbortSignal.timeout(30000),
  }, {
    maxRetries: 4,
    label: 'summary update',
  });

  if (!response.ok) {
    const body = await response.text();
    const err = new Error(`Failed to update summary (HTTP ${response.status}): ${body}`);
    err.statusCode = response.status;
    throw err;
  }
}

async function updateBuildSummaryStatus(apiUrl, apiKey, batchId, sessionId, status, errorCode) {
  const response = await fetchWithRetry(`${apiUrl}/api/backfill/summary`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      batch_id: batchId,
      session_id: sessionId,
      status,
      error_code: errorCode || null,
    }),
    signal: AbortSignal.timeout(30000),
  }, {
    maxRetries: 2,
    label: 'summary status update',
  });

  if (!response.ok) {
    const body = await response.text();
    const err = new Error(`Failed to update summary status (HTTP ${response.status}): ${body}`);
    err.statusCode = response.status;
    throw err;
  }
}

/**
 * Count real user prompts in a JSONL file.
 * Only counts type=user entries with actual text content (not empty tool results).
 */
function countPrompts(jsonlPath) {
  let count = 0;
  const content = fs.readFileSync(jsonlPath, 'utf8');
  for (const line of content.split('\n')) {
    if (!line.trim()) continue;
    let entry;
    try { entry = JSON.parse(line); } catch { continue; }
    if (entry.type !== 'user') continue;
    const msg = entry.message || {};
    const c = typeof msg === 'object' ? msg.content : undefined;
    if (typeof c === 'string' && c.trim().length > 0) {
      count++;
    } else if (Array.isArray(c)) {
      if (c.some(b => b && b.type === 'text' && typeof b.text === 'string' && b.text.trim().length > 0)) {
        count++;
      }
    }
  }
  return count;
}

/**
 * Extract timestamps from JSONL entries for session duration.
 */
function extractTimestamps(jsonlPath) {
  const timestamps = [];
  const content = fs.readFileSync(jsonlPath, 'utf8');
  for (const line of content.split('\n')) {
    if (!line.trim()) continue;
    let entry;
    try { entry = JSON.parse(line); } catch { continue; }
    const ts = entry.timestamp;
    if (ts && typeof ts === 'string') {
      const d = new Date(ts);
      if (!isNaN(d.getTime())) timestamps.push(d);
    }
  }
  return timestamps;
}

/**
 * Count lines changed from tool_use blocks in the JSONL (same logic as track-edits.js).
 */
function countLinesChanged(jsonlPath) {
  let linesChanged = 0;
  const content = fs.readFileSync(jsonlPath, 'utf8');
  for (const line of content.split('\n')) {
    if (!line.trim()) continue;
    let entry;
    try { entry = JSON.parse(line); } catch { continue; }
    if (entry.type !== 'assistant') continue;
    const msg = entry.message || {};
    const blocks = msg.content;
    if (!Array.isArray(blocks)) continue;
    for (const block of blocks) {
      if (!block || block.type !== 'tool_use') continue;
      const toolName = block.name || '';
      const toolInput = block.input || {};
      if (toolName === 'Write') {
        const c = toolInput.content || '';
        if (c) linesChanged += c.split('\n').length;
      } else if (toolName === 'Edit') {
        const newStr = toolInput.new_string || '';
        const oldStr = toolInput.old_string || '';
        if (newStr) {
          const diff = Math.abs(newStr.split('\n').length - (oldStr ? oldStr.split('\n').length : 0));
          linesChanged += diff || (newStr ? 1 : 0);
        }
      } else if (toolName === 'NotebookEdit') {
        const src = toolInput.new_source || '';
        linesChanged += src ? src.split('\n').length : 1;
      }
    }
  }
  return linesChanged;
}

/**
 * Find JSONL session files from the last N days.
 */
function findJsonlFiles() {
  const claudeDir = path.join(os.homedir(), '.claude', 'projects');
  if (!fs.existsSync(claudeDir)) {
    log(`No Claude Code projects found at ${claudeDir}`);
    return [];
  }

  const afterCutoff = Date.now() - (DAYS * 86400 * 1000);
  const beforeCutoff = BEFORE ? new Date(BEFORE).getTime() : null;
  const files = [];

  for (const dirName of fs.readdirSync(claudeDir)) {
    const projectDir = path.join(claudeDir, dirName);
    if (!fs.statSync(projectDir).isDirectory()) continue;

    if (PROJECT_FILTER) {
      const decoded = dirName.split('-').filter(Boolean).pop() || dirName;
      if (!dirName.toLowerCase().includes(PROJECT_FILTER.toLowerCase()) &&
          decoded.toLowerCase() !== PROJECT_FILTER.toLowerCase()) {
        continue;
      }
    }

    for (const file of fs.readdirSync(projectDir)) {
      if (!file.endsWith('.jsonl')) continue;
      const filePath = path.join(projectDir, file);
      try {
        const stat = fs.statSync(filePath);
        if (!stat.isFile()) continue;
        const mtime = stat.mtimeMs;
        // Skip files modified in the last 3 minutes — likely in-progress sessions
        if (Date.now() - mtime < 3 * 60 * 1000) continue;
        if (mtime >= afterCutoff && (!beforeCutoff || mtime < beforeCutoff)) {
          files.push(filePath);
        }
      } catch { continue; }
    }
  }

  return files.sort((a, b) => fs.statSync(a).mtimeMs - fs.statSync(b).mtimeMs);
}

/**
 * Parse a single JSONL session file into a build record.
 * Uses the shared lib/ modules (same code as live hooks).
 */
function parseSession(jsonlPath) {
  const sessionId = path.basename(jsonlPath, '.jsonl');
  const projectDirName = path.basename(path.dirname(jsonlPath));

  // Decode the Claude Code directory name back to a real path, then use shared
  // deriveProjectName() which handles git worktrees.
  // Format: -Users-foo-Desktop-myproject → /Users/foo/Desktop/myproject
  const decodedPath = '/' + projectDirName.replace(/^-/, '').replace(/-/g, '/');
  const projectName = deriveProjectName(decodedPath);

  // Extract timestamps for session duration
  const timestamps = extractTimestamps(jsonlPath);
  if (timestamps.length < 2) return null;

  const startTime = new Date(Math.min(...timestamps.map(t => t.getTime())));
  const endTime = new Date(Math.max(...timestamps.map(t => t.getTime())));
  const buildTimeSeconds = Math.round((endTime - startTime) / 1000);

  if (buildTimeSeconds < 5) return null;

  // Count real user prompts (same logic as UserPromptSubmit hook)
  const promptCount = countPrompts(jsonlPath);

  // Parse transcript using shared lib (same code as session-end.js)
  const transcript = parseTranscript(jsonlPath, '');
  if (transcript.error) return null;
  if (!transcript.model) return null;

  // Aggregate subagent tokens before noise filter (same as session-end.js)
  let sessionTotalTokens = transcript.total_tokens || 0;
  let sessionInputTokens = transcript.input_tokens || 0;
  let sessionOutputTokens = transcript.output_tokens || 0;
  let sessionCacheCreation = transcript.cache_creation_input_tokens || 0;
  let sessionCacheRead = transcript.cache_read_input_tokens || 0;
  const fileExtensions = transcript.source_metadata?.file_extensions || {};
  const toolSummary = transcript.tool_usage_summary || {};
  const sourceMetadata = {
    file_extensions: fileExtensions,
    tool_usage_summary: toolSummary,
  };

  try {
    const subagentData = parseSubagentTokens(jsonlPath);
    if (subagentData) {
      sessionTotalTokens += subagentData.subagent_tokens;
      sessionInputTokens += subagentData.input_tokens;
      sessionOutputTokens += subagentData.output_tokens;
      sessionCacheCreation += subagentData.cache_creation_input_tokens;
      sessionCacheRead += subagentData.cache_read_input_tokens;
      sourceMetadata.subagent_count = subagentData.subagent_count;
      sourceMetadata.subagent_tokens = subagentData.subagent_tokens;
    }
  } catch { /* skip subagent aggregation errors */ }

  // Skip noise (same filter as session-end.js) — uses aggregated totals
  if (promptCount === 0 && buildTimeSeconds < 10 && sessionTotalTokens < 1000) return null;
  if (sessionTotalTokens === 0 && promptCount === 0) return null;

  // Count lines changed (same logic as track-edits.js)
  const linesChanged = countLinesChanged(jsonlPath);

  // Language detection using shared lib (same as session-end.js)
  const language = getPrimaryLanguage(fileExtensions);

  // Tool summary for fallback title generation
  const toolSummaryStr = Object.entries(toolSummary)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([k, v]) => `${v} ${k}`)
    .join(', ');

  return {
    session_id: sessionId,
    project_name: projectName,
    model: transcript.model,
    ai_tool: 'claude-code',
    start_time: startTime.toISOString(),
    end_time: endTime.toISOString(),
    build_time_seconds: buildTimeSeconds,
    prompt_count: promptCount,
    lines_changed: linesChanged || null,
    language,
    status: 'completed',
    total_tokens: sessionTotalTokens,
    input_tokens: sessionInputTokens,
    output_tokens: sessionOutputTokens,
    cache_creation_input_tokens: sessionCacheCreation,
    cache_read_input_tokens: sessionCacheRead,
    source: 'backfill',
    source_metadata: sourceMetadata,
    // Kept locally for summary generation — stripped before upload
    _compact_log: transcript.compact_log || '',
    _tool_summary_str: toolSummaryStr,
    _jsonl_path: jsonlPath,
  };
}

/**
 * Generate a title and summary for a session using Haiku (or fallback).
 * Same logic as submit.js generateAndPublish().
 */
function generateSummary(session) {
  let compactLog = session._compact_log || '';
  if (!compactLog) {
    return {
      title: generateFallbackTitle(
        session.prompt_count, session.build_time_seconds,
        session.project_name, session._tool_summary_str
      ),
      summary: generateFallbackSummary(
        session.prompt_count, session.build_time_seconds,
        session.total_tokens, session.model, session._tool_summary_str
      ),
    };
  }

  // Truncate to ~4000 chars
  if (compactLog.length > 4000) {
    compactLog = compactLog.slice(0, 4000) + '\n... (truncated)';
  }

  // Try Haiku via claude CLI
  let claudeCmd = '';
  try {
    claudeCmd = execSync('which claude 2>/dev/null || where claude 2>nul', { encoding: 'utf8' }).trim();
  } catch { /* not found */ }

  if (claudeCmd) {
    try {
      const prompt = buildSummaryPrompt(compactLog, session.project_name, session.prompt_count);
      const response = execFileSync(claudeCmd, ['--print', '--model', 'haiku'], {
        input: prompt,
        encoding: 'utf8',
        timeout: 60000,
        env: { ...process.env, PROMPTBOOK_SKIP_HOOKS: '1' },
      });

      if (response) {
        const titleMatch = response.match(/^TITLE:\s*(.+)/im);
        const summaryMatch = response.match(/^SUMMARY:\s*(.+)/im);
        if (titleMatch || summaryMatch) {
          return {
            title: titleMatch ? titleMatch[1].trim() : '',
            summary: summaryMatch ? summaryMatch[1].trim() : '',
          };
        }
      }
    } catch (err) {
      log(`  Haiku failed for ${session.session_id.slice(0, 8)}...: ${err.message}`);
    }
  }

  // Fallback: deterministic title/summary (same as submit.js)
  return {
    title: generateFallbackTitle(
      session.prompt_count, session.build_time_seconds,
      session.project_name, session._tool_summary_str
    ),
    summary: generateFallbackSummary(
      session.prompt_count, session.build_time_seconds,
      session.total_tokens, session.model, session._tool_summary_str
    ),
  };
}

/**
 * Upload sessions to the backfill batch endpoint.
 */
async function uploadBatch(sessions, apiUrl, apiKey, batchId) {
  const chunkSize = 50;
  let uploadedCount = 0;
  const insertedIds = [];

  for (let i = 0; i < sessions.length; i += chunkSize) {
    const chunk = sessions.slice(i, i + chunkSize);

    // Strip internal fields before upload
    const cleaned = chunk.map(s => {
      const { _compact_log, _tool_summary_str, _jsonl_path, ...rest } = s;
      return rest;
    });

    try {
      const response = await fetchWithRetry(`${apiUrl}/api/backfill/upload`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${apiKey}`,
        },
        body: JSON.stringify({ batch_id: batchId, days_scanned: DAYS, sessions: cleaned }),
        signal: AbortSignal.timeout(30000),
      }, {
        maxRetries: 5,
        label: 'backfill upload',
      });

      if (!response.ok) {
        const body = await response.text();
        log(`  Upload failed (HTTP ${response.status}): ${body}`);
        if ([401, 403, 500].includes(response.status)) {
          log('  Stopping due to server error.');
          throw new Error(`Upload failed with HTTP ${response.status}`);
        }
        throw new Error(`Upload failed with HTTP ${response.status}`);
      }

      const body = await response.json();
      uploadedCount += body.uploaded || 0;
      if (Array.isArray(body.inserted_ids)) {
        insertedIds.push(...body.inserted_ids);
      }
      log(`  Uploaded ${body.uploaded || 0} sessions (${body.duplicates || 0} duplicates)`);
    } catch (err) {
      log(`  Upload failed: ${err.message}`);
      throw err;
    }

    // Brief pause between chunks smooths burstiness even with server-side retries.
    if (i + chunkSize < sessions.length) {
      await sleep(1000);
    }
  }

  return { uploadedCount, insertedIds };
}

// --- Main ---
async function main() {
  // Load config
  let apiUrl = API_URL_ARG;
  let apiKey = '';
  let batchId = BATCH_ID_ARG;
  const needsConfig = !DRY_RUN && !JSON_MODE;

  if (needsConfig || !apiUrl) {
    const configPath = path.join(os.homedir(), '.promptbook', 'config.json');
    if (!fs.existsSync(configPath)) {
      if (needsConfig) {
        log('Error: ~/.promptbook/config.json not found. Run the Promptbook setup first.');
        process.exit(1);
      }
    } else {
      const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
      apiUrl = apiUrl || config.api_url || '';
      apiKey = config.api_key || '';
      if (config.telemetry_consent !== true) {
        log('Error: Promptbook consent not found in ~/.promptbook/config.json. Run the plugin setup again to continue.');
        process.exit(1);
      }
    }
    if (needsConfig && (!apiUrl || !apiKey)) {
      log('Error: config.json missing api_url or api_key');
      process.exit(1);
    }
  }

  currentApiUrl = apiUrl;
  currentApiKey = apiKey;

  if (!DRY_RUN && !JSON_MODE) {
    batchId = batchId || await startBatch(apiUrl, apiKey);
    currentBatchId = batchId;
    await updateBatchProgress(apiUrl, apiKey, batchId, { status: 'scanning' });
  }

  // Find sessions
  if (!JSON_MODE) log(`Scanning for sessions from the last ${DAYS} days...`);
  const jsonlFiles = findJsonlFiles();
  if (!JSON_MODE) log(`Found ${jsonlFiles.length} session files`);
  if (!DRY_RUN && !JSON_MODE) {
    await updateBatchProgress(apiUrl, apiKey, batchId, {
      status: 'scanning',
      found_count: jsonlFiles.length,
    });
  }

  if (jsonlFiles.length === 0) {
    if (!DRY_RUN && !JSON_MODE) {
      await updateBatchProgress(apiUrl, apiKey, batchId, {
        status: 'completed',
        found_count: 0,
        candidate_count: 0,
        session_count: 0,
        skipped_count: 0,
        summarized_count: 0,
        finished_at: new Date().toISOString(),
      });
      await finalizeBatchProgress(apiUrl, apiKey, batchId, {
        status: 'completed',
        found_count: 0,
        candidate_count: 0,
        session_count: 0,
        skipped_count: 0,
        summarized_count: 0,
        finished_at: new Date().toISOString(),
      });
      process.stdout.write(batchId);
    }
    if (JSON_MODE) process.stdout.write('[]');
    else log('Nothing to backfill.');
    return;
  }

  // Parse all sessions
  const sessions = [];
  let skipped = 0;
  for (const filePath of jsonlFiles) {
    try {
      const session = parseSession(filePath);
      if (session) sessions.push(session);
      else skipped++;
    } catch (err) {
      skipped++;
      log(`  Skipped corrupt file ${path.basename(filePath)}: ${err.message}`);
    }
  }

  if (!JSON_MODE) log(`Parsed ${sessions.length} sessions (${skipped} skipped)`);
  if (!DRY_RUN && !JSON_MODE) {
    await updateBatchProgress(apiUrl, apiKey, batchId, {
      status: 'uploading',
      candidate_count: sessions.length,
      skipped_count: skipped,
      summarized_count: 0,
    });
  }

  // --json mode
  if (JSON_MODE) {
    const cleaned = sessions.map(s => {
      const { _compact_log, _tool_summary_str, _jsonl_path, ...rest } = s;
      return rest;
    });
    process.stdout.write(JSON.stringify(cleaned));
    return;
  }

  // --dry-run mode
  if (DRY_RUN) {
    for (let i = 0; i < sessions.length; i++) {
      const s = sessions[i];
      log(`  [${i + 1}/${sessions.length}] ${s.project_name}: ` +
        `${s.prompt_count} prompts, ${s.total_tokens.toLocaleString()} tokens, ` +
        `${s.build_time_seconds}s, ${s.lines_changed || 0} lines, model=${s.model}`);
    }
    log(`\nDone: ${sessions.length} sessions found, ${skipped} empty/invalid`);
    return;
  }

  // Upload
  if (sessions.length === 0) {
    await finalizeBatchProgress(apiUrl, apiKey, batchId, {
      status: 'completed',
      session_count: 0,
      candidate_count: 0,
      skipped_count: skipped,
      summarized_count: 0,
      finished_at: new Date().toISOString(),
    });
    process.stdout.write(batchId);
    log('No sessions to upload.');
    return;
  }

  await updateBatchProgress(apiUrl, apiKey, batchId, {
    status: 'uploading',
    summarized_count: 0,
  });

  const { uploadedCount, insertedIds } = await uploadBatch(sessions, apiUrl, apiKey, batchId);

  // Mark all uploaded sessions in the live hook's retry queue so they don't
  // get re-submitted on next session end (which delays the terminal success message)
  markSessionsSubmitted(sessions.map(s => s.session_id));

  let summarizedCount = 0;
  let summaryFailures = 0;
  // Load checkpoint to check for resumable work from a previous crashed run
  const priorCheckpoint = GENERATE_SUMMARIES ? loadCheckpoint(batchId) : new Set();
  const hasResumableWork = priorCheckpoint.size > 0;

  if (GENERATE_SUMMARIES && (uploadedCount > 0 || hasResumableWork)) {
    // On fresh run: only summarize newly inserted sessions (skip duplicates)
    // On resume: summarize ALL parsed sessions (insertedIds will be empty since they're duplicates)
    const insertedSet = new Set(insertedIds);
    const toSummarize = hasResumableWork && uploadedCount === 0
      ? sessions  // resume: try all parsed sessions, checkpoint will skip already-done ones
      : sessions.filter(s => insertedSet.has(s.session_id));

    // Skip sessions already summarized in a previous run
    const alreadySummarized = new Set(priorCheckpoint);
    const remaining = toSummarize.filter(s => !alreadySummarized.has(s.session_id));
    summarizedCount = alreadySummarized.size;

    await updateBatchProgress(apiUrl, apiKey, batchId, {
      status: 'summarizing',
      session_count: uploadedCount,
      candidate_count: sessions.length,
      skipped_count: skipped,
      summarized_count: summarizedCount,
    });

    if (remaining.length < toSummarize.length) {
      log(`Resuming summaries: ${alreadySummarized.size} already done, ${remaining.length} remaining`);
    } else {
      log(`Generating summaries for ${remaining.length} sessions (${sessions.length - toSummarize.length} duplicates skipped)...`);
    }

    for (let i = 0; i < remaining.length; i++) {
      const s = remaining[i];
      const result = generateSummary(s);
      if (result) {
        s.title = result.title;
        s.summary = result.summary;
        try {
          await updateBuildSummary(apiUrl, apiKey, batchId, s);
          summarizedCount++;
          alreadySummarized.add(s.session_id);
          if (!JSON_MODE) {
            const label = result.title.length > 50 ? result.title.slice(0, 50) + '...' : result.title;
            log(`  [${summarizedCount}/${toSummarize.length}] ${label}`);
          }
        } catch (err) {
          if (err.statusCode === 404) {
            log(`  Summary skipped for ${s.session_id.slice(0, 8)}...: build not found in batch`);
            alreadySummarized.add(s.session_id); // don't retry 404s
          } else {
            summaryFailures++;
            try {
              await updateBuildSummaryStatus(apiUrl, apiKey, batchId, s.session_id, 'patch_failed', 'summary_update_failed');
            } catch (statusErr) {
              log(`  Failed to mark summary error for ${s.session_id.slice(0, 8)}...: ${statusErr.message}`);
            }
            log(`  Summary update failed for ${s.session_id.slice(0, 8)}...: ${err.message}`);
          }
        }
      }

      // Checkpoint every 5 summaries so crashes don't lose progress
      if ((i + 1) % 5 === 0 || i + 1 === remaining.length) {
        saveCheckpoint(batchId, alreadySummarized);
        if (!DRY_RUN && !JSON_MODE) {
          await updateBatchProgress(apiUrl, apiKey, batchId, {
            status: 'summarizing',
            summarized_count: summarizedCount,
            error_count: summaryFailures,
          });
        }
      }
    }

    // Only clear checkpoint if all summaries succeeded — preserve resume state on partial failure
    if (summaryFailures === 0) {
      clearCheckpoint();
    } else {
      log(`  ${summaryFailures} summary failures — checkpoint preserved for resume`);
    }
  }

  // Builds are auto-published on upload — mark batch as completed
  await finalizeBatchProgress(apiUrl, apiKey, batchId, {
    status: 'completed',
    session_count: uploadedCount,
    candidate_count: sessions.length,
    skipped_count: skipped,
    summarized_count: GENERATE_SUMMARIES ? summarizedCount : 0,
    error_count: summaryFailures,
    finished_at: new Date().toISOString(),
  });
  log(`Batch ${batchId}: ${uploadedCount} sessions published`);
  if (GENERATE_SUMMARIES && summarizedCount > 0) {
    log(`  ${summarizedCount} summaries enhanced with Haiku`);
  }
  process.stdout.write(batchId);
}

main().catch(err => {
  if (currentApiUrl && currentApiKey && currentBatchId) {
    void finalizeBatchProgress(currentApiUrl, currentApiKey, currentBatchId, {
      status: 'failed',
      error_count: 1,
      last_error: err.message,
      finished_at: new Date().toISOString(),
    }).catch(() => {});
  }
  log(`Fatal: ${err.message}`);
  process.exit(1);
});
