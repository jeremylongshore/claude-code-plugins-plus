#!/usr/bin/env node
/**
 * Promptbook — UserPromptSubmit hook.
 * Increments the prompt counter and records timestamp for the active session.
 * Runs synchronously (<50ms) — completely silent.
 */
'use strict';

const fs = require('fs');
const path = require('path');
const { getDataDir, readStdin, readConfig, hasTrackingConsent, acquireLock, releaseLock, atomicWrite, appendLog, isValidSessionId } = require('./lib/io');

const DATA_DIR = getDataDir();

try {
  // Skip if this session was spawned by our own summary generation
  if (process.env.PROMPTBOOK_SKIP_HOOKS === '1') process.exit(0);
  if (!hasTrackingConsent(readConfig())) process.exit(0);

  const input = readStdin();
  if (!input || !input.session_id || !isValidSessionId(input.session_id)) process.exit(0);

  const sessionsDir = path.join(DATA_DIR, 'sessions');
  const sessionFile = path.join(sessionsDir, `${input.session_id}.json`);

  if (!fs.existsSync(sessionFile)) process.exit(0);

  acquireLock(sessionFile);
  try {
    const session = JSON.parse(fs.readFileSync(sessionFile, 'utf8'));
    session.prompt_count = (session.prompt_count || 0) + 1;

    if (!session.prompt_timestamps) session.prompt_timestamps = [];
    session.prompt_timestamps.push(new Date().toISOString());

    atomicWrite(sessionFile, session);
  } finally {
    releaseLock(sessionFile);
  }
} catch (err) {
  appendLog(DATA_DIR, 'hook-errors.log', `prompt-count: ${err.message}`);
  process.exit(0);
}
