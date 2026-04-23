#!/usr/bin/env node
/**
 * Promptbook — SessionStart hook.
 * Creates a new session tracking file.
 *
 * Input (stdin JSON): { session_id, model, cwd, hook_event_name }
 */
'use strict';

const fs = require('fs');
const path = require('path');
const { getDataDir, readStdin, readConfig, hasTrackingConsent, appendLog, isValidSessionId } = require('./lib/io');
const { deriveProjectName } = require('./lib/language');

const DATA_DIR = getDataDir();

function main() {
  // Skip if this session was spawned by our own summary generation
  if (process.env.PROMPTBOOK_SKIP_HOOKS === '1') return;

  const config = readConfig();
  if (!hasTrackingConsent(config)) return;

  const input = readStdin();
  if (!input || !input.session_id || !isValidSessionId(input.session_id)) return;

  const sessionsDir = path.join(DATA_DIR, 'sessions');
  fs.mkdirSync(sessionsDir, { recursive: true });

  const sessionId = input.session_id;

  // Extract model — try multiple field paths (Claude Code format varies)
  let model = 'unknown';
  if (typeof input.model === 'string' && input.model) {
    model = input.model;
  } else if (input.model && typeof input.model === 'object') {
    model = input.model.id || input.model.name || input.model.display_name || input.model.model || 'unknown';
  } else {
    model = input.model_name || input.modelName || input.session_model || input.sessionModel || 'unknown';
  }
  if (!model || model === 'null') {
    model = 'unknown';
    appendLog(DATA_DIR, 'hook-errors.log', `WARN: SessionStart missing model field. Keys: ${Object.keys(input).sort().join(',')}`);
  }

  const cwd = input.cwd || '';
  const timestamp = new Date().toISOString();
  const projectName = deriveProjectName(cwd);

  // Capture git branch (useful for grouping worktree/parallel sessions)
  let gitBranch = null;
  if (cwd) {
    try {
      const { execSync } = require('child_process');
      gitBranch = execSync('git rev-parse --abbrev-ref HEAD', {
        cwd, encoding: 'utf8', timeout: 2000, stdio: ['pipe', 'pipe', 'pipe'],
      }).trim() || null;
    } catch { /* not a git repo or git not available */ }
  }

  // Write session file
  const session = {
    session_id: sessionId,
    project_name: projectName,
    model,
    ai_tool: 'claude-code',
    agent_type: input.agent_type || null,
    git_branch: gitBranch,
    start_time: timestamp,
    end_time: null,
    build_time_seconds: null,
    prompt_count: 0,
    lines_changed: 0,
    cwd,
    file_extensions: {},
    status: 'active',
  };

  const sessionFile = path.join(sessionsDir, `${sessionId}.json`);
  fs.writeFileSync(sessionFile, JSON.stringify(session, null, 2), 'utf8');
}

try {
  main();
} catch (err) {
  appendLog(DATA_DIR, 'hook-errors.log', `UNCAUGHT session-start: ${err.message}`);
}
