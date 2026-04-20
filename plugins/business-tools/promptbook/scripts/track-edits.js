#!/usr/bin/env node
/**
 * Promptbook — PostToolUse hook (matcher: Edit|Write|NotebookEdit).
 * Counts lines changed and tracks file extensions for language detection.
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

  const toolName = input.tool_name || '';
  const toolInput = (input.tool_input && typeof input.tool_input === 'object') ? input.tool_input : {};
  let lines = 0;
  let filePath = '';

  if (toolName === 'Write') {
    const content = toolInput.content || '';
    if (content) lines = content.split('\n').length;
    filePath = toolInput.file_path || '';
  } else if (toolName === 'Edit') {
    const newString = toolInput.new_string || '';
    const oldString = toolInput.old_string || '';
    if (newString) {
      const newLines = newString.split('\n').length;
      const oldLines = oldString ? oldString.split('\n').length : 0;
      lines = Math.abs(newLines - oldLines);
      if (lines === 0 && newString) lines = 1;
    }
    filePath = toolInput.file_path || '';
  } else if (toolName === 'NotebookEdit') {
    const newSource = toolInput.new_source || '';
    lines = newSource ? newSource.split('\n').length : 1;
    if (lines === 0) lines = 1;
    filePath = toolInput.notebook_path || toolInput.file_path || '';
  }

  // Extract file extension
  let fileExt = '';
  if (filePath) {
    const ext = path.extname(filePath).replace(/^\./, '');
    if (ext && ext !== filePath) fileExt = ext;
  }

  // Update session file
  acquireLock(sessionFile);
  try {
    const session = JSON.parse(fs.readFileSync(sessionFile, 'utf8'));
    session.lines_changed = (session.lines_changed || 0) + lines;

    if (fileExt) {
      if (!session.file_extensions) session.file_extensions = {};
      session.file_extensions[fileExt] = (session.file_extensions[fileExt] || 0) + 1;
    }

    atomicWrite(sessionFile, session);
  } finally {
    releaseLock(sessionFile);
  }
} catch (err) {
  appendLog(DATA_DIR, 'hook-errors.log', `track-edits: ${err.message}`);
  process.exit(0);
}
