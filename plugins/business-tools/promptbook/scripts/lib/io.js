/**
 * Promptbook — Shared I/O utilities for hook scripts.
 * Zero external dependencies — Node.js built-ins only.
 */
'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');

/**
 * Resolve the data directory — always ~/.promptbook.
 * Both plugin and bash installs share this location.
 */
function getDataDir() {
  return path.join(os.homedir(), '.promptbook');
}

/**
 * Read and parse JSON from stdin (synchronous, cross-platform).
 * Returns null on any failure — never throws.
 */
function readStdin() {
  try {
    // Guard against hanging on TTY stdin (no piped data)
    if (process.stdin.isTTY) return null;
    const raw = fs.readFileSync(0, 'utf8');
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

/**
 * Read config.json from ~/.promptbook/config.json.
 * Returns { api_key, api_url, auto_summary, telemetry_consent } or null.
 */
function readConfig() {
  try {
    const configPath = path.join(os.homedir(), '.promptbook', 'config.json');
    const raw = fs.readFileSync(configPath, 'utf8');
    const config = JSON.parse(raw);
    return {
      api_key: config.api_key || '',
      api_url: config.api_url || '',
      auto_summary: config.auto_summary !== false,
      telemetry_consent: config.telemetry_consent === true,
    };
  } catch {
    return null;
  }
}

function hasTrackingConsent(config) {
  return !!(config && config.api_key && config.api_url && config.telemetry_consent === true);
}

/**
 * Write data to a file atomically (write tmp, then rename).
 * Includes one retry for Windows EPERM on rename.
 */
function atomicWrite(filePath, data) {
  const tmp = `${filePath}.tmp.${process.pid}`;
  const content = typeof data === 'string' ? data : JSON.stringify(data, null, 2);
  fs.writeFileSync(tmp, content, 'utf8');
  try {
    fs.renameSync(tmp, filePath);
  } catch (err) {
    // Windows can throw EPERM if the target is briefly locked — retry once
    if (err.code === 'EPERM') {
      try {
        // Small delay then retry
        const start = Date.now();
        while (Date.now() - start < 50) { /* spin */ }
        fs.renameSync(tmp, filePath);
      } catch {
        // Last resort: overwrite directly
        fs.writeFileSync(filePath, content, 'utf8');
        try { fs.unlinkSync(tmp); } catch { /* ignore */ }
      }
    } else {
      throw err;
    }
  }
}

/**
 * Acquire a file lock using mkdir (atomic on all filesystems).
 * Returns true if acquired, false if timed out (caller should proceed anyway).
 */
function acquireLock(sessionFile, maxAttempts = 500) {
  const lockDir = `${sessionFile}.lock`;

  // Clean up stale locks older than 60s (e.g., from a crashed process)
  try {
    const stat = fs.statSync(lockDir);
    if (stat.isDirectory() && Date.now() - stat.mtimeMs > 60000) {
      try { fs.rmdirSync(lockDir); } catch { /* ignore */ }
    }
  } catch { /* lock doesn't exist yet — good */ }

  for (let i = 0; i < maxAttempts; i++) {
    try {
      fs.mkdirSync(lockDir);
      return true;
    } catch {
      // Lock exists — wait 10ms and retry
      const start = Date.now();
      while (Date.now() - start < 10) { /* spin wait — setTimeout is async */ }
    }
  }
  // Timed out after ~5s — proceed without lock to avoid losing data
  return false;
}

/**
 * Release the file lock. Silent on failure.
 */
function releaseLock(sessionFile) {
  const lockDir = `${sessionFile}.lock`;
  try { fs.rmdirSync(lockDir); } catch { /* ignore */ }
}

/**
 * Append a timestamped line to a log file. Never throws.
 */
function appendLog(dataDir, filename, message) {
  try {
    const logPath = path.join(dataDir, filename);
    const line = `${new Date().toISOString()} ${message}\n`;
    fs.appendFileSync(logPath, line, 'utf8');
  } catch { /* never throw from logging */ }
}

/**
 * Read and parse a session JSON file. Returns null on failure.
 */
function readSession(sessionsDir, sessionId) {
  try {
    const filePath = path.join(sessionsDir, `${sessionId}.json`);
    return JSON.parse(fs.readFileSync(filePath, 'utf8'));
  } catch {
    return null;
  }
}

/**
 * Validate that a session ID is safe for use in filenames.
 * Claude Code session IDs are UUIDs — reject anything else
 * to prevent path traversal via crafted session_id values.
 */
const SESSION_ID_RE = /^[a-zA-Z0-9_-]+$/;
function isValidSessionId(id) {
  return typeof id === 'string' && id.length > 0 && id.length <= 128 && SESSION_ID_RE.test(id);
}

module.exports = {
  getDataDir,
  readStdin,
  readConfig,
  hasTrackingConsent,
  atomicWrite,
  acquireLock,
  releaseLock,
  appendLog,
  readSession,
  isValidSessionId,
};
