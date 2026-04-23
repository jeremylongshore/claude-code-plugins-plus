/**
 * Promptbook — Summary generation utilities.
 * Fallback title/summary generation, formatting, and Haiku prompt templates.
 */
'use strict';

/**
 * Format seconds into human-readable duration.
 * "42s" / "14m" / "2h 15m"
 */
function formatDuration(seconds) {
  const secs = Math.round(Number(seconds) || 0);
  if (secs < 60) return `${secs}s`;
  if (secs < 3600) return `${Math.floor(secs / 60)}m`;
  const h = Math.floor(secs / 3600);
  const m = Math.floor((secs % 3600) / 60);
  return m > 0 ? `${h}h ${m}m` : `${h}h`;
}

/**
 * Format token count for display.
 * "238K" / "1.2M" / "500"
 */
function formatTokens(count) {
  const tok = Number(count) || 0;
  if (tok >= 1_000_000) {
    const m = Math.floor(tok / 1_000_000);
    const tenths = Math.floor((tok % 1_000_000) / 100_000);
    return `${m}.${tenths}M`;
  }
  if (tok >= 1000) return `${Math.floor(tok / 1000)}K`;
  return String(tok);
}

/**
 * Determine work style from dominant tool name.
 * Returns { style, verb, desc } or defaults.
 */
function getWorkStyle(dominantTool) {
  const styles = {
    Edit:   { style: 'refactor',       verb: 'Refactored',    desc: 'with heavy editing and code changes' },
    Write:  { style: 'build',          verb: 'Built',         desc: 'creating new files and components' },
    Read:   { style: 'exploration',    verb: 'Explored',      desc: 'reading and analyzing the codebase' },
    Grep:   { style: 'investigation',  verb: 'Investigated',  desc: 'searching and tracing code patterns' },
    Bash:   { style: 'debugging',      verb: 'Debugged',      desc: 'running commands and testing' },
    Agent:  { style: 'orchestration',  verb: 'Orchestrated',  desc: 'delegating across sub-agents' },
    Glob:   { style: 'exploration',    verb: 'Explored',      desc: 'scanning and navigating the codebase' },
  };
  return styles[dominantTool] || { style: 'session', verb: 'Worked on', desc: '' };
}

/**
 * Extract dominant tool name from a tool summary string like "48 Edit, 12 Read, 3 Bash".
 */
function getDominantTool(toolSummary) {
  if (!toolSummary) return '';
  const first = toolSummary.split(',')[0]?.trim();
  if (!first) return '';
  const parts = first.split(/\s+/);
  return parts.length >= 2 ? parts[1] : '';
}

/**
 * Generate a deterministic fallback title when Haiku is unavailable.
 */
function generateFallbackTitle(promptCount, buildTime, projectName, toolSummary) {
  const dominant = getDominantTool(toolSummary);
  const { style, verb } = getWorkStyle(dominant);

  const count = Number(promptCount) || 0;
  const time = Number(buildTime) || 0;

  if (count === 0) {
    if (style !== 'session') return `Agent ${style} of ${projectName}`;
    return `Autonomous session on ${projectName}`;
  }
  if (count === 1) return `One-shot ${style} on ${projectName}`;
  if (count >= 40) return `Marathon ${style} on ${projectName}`;
  if (count <= 4 && time < 300) return `Quick ${style} on ${projectName}`;
  return `${verb} ${projectName}`;
}

/**
 * Generate a deterministic fallback summary when Haiku is unavailable.
 */
function generateFallbackSummary(promptCount, buildTime, totalTokens, model, toolSummary) {
  const duration = formatDuration(buildTime);
  const tokens = formatTokens(totalTokens);
  const dominant = getDominantTool(toolSummary);
  const { desc } = getWorkStyle(dominant);
  const count = Number(promptCount) || 0;

  if (count === 0) {
    if (desc) return `Autonomous ${duration} agent session ${desc}. ${tokens} tokens processed using ${model}.`;
    return `Autonomous ${duration} agent session using ${model}. ${tokens} tokens processed.`;
  }
  if (desc) return `${duration} session ${desc}. ${tokens} tokens across ${count} prompts using ${model}.`;
  return `${duration} coding session using ${model}. ${tokens} tokens across ${count} prompts.`;
}

/**
 * Build the Haiku summary prompt for a session.
 * Returns the full prompt string ready to pipe to `claude --print --model haiku`.
 */
function buildSummaryPrompt(compactLog, projectName, promptCount) {
  // Sanitize project name to prevent prompt injection
  const safeName = (projectName || '').replace(/[^a-zA-Z0-9 _.-]/g, '');
  const count = Number(promptCount) || 0;

  if (count === 0) {
    return `You are writing a title and summary for an autonomous agent Build Card — a shareable card showing what an AI agent accomplished without human prompts. This appears in a public community feed.

Project: ${safeName}

Agent session log (no user prompts — the agent ran autonomously):

${compactLog}

Title rules:
- 50-80 characters, aim for 8-12 words, sentence case
- Frame as agent work: "Agent investigated...", "Autonomous refactor of...", "Agent debugged and fixed..."
- If the log shows file reads/searches but no edits, frame as research: "Agent analyzed...", "Explored and mapped..."
- If the log is very sparse, use the project name: "Autonomous session on ${safeName}"
- Be specific about WHAT the agent did based on the log evidence
- No quotes.

Summary rules:
- Under 120 characters (~20 words). One sentence. Start with a verb. Past tense.
- What the agent accomplished, not what it did. Outcome over process.
- The "Session conclusion" section shows what was completed — prioritize that over early activity
- If the log is sparse, write a minimal honest summary — e.g., "Explored the codebase and analyzed project structure."
- NEVER leave the title or summary blank
- NEVER invent features or changes that aren't evidenced in the session log

Privacy (strict):
- NEVER include: file paths, database table names, endpoint URLs, function names, internal architecture details, credentials, API keys, or code
- Describe what was done in plain language without exposing implementation internals

Format (exact):
TITLE: <title>
SUMMARY: <summary>`;
  }

  return `You are writing a title and summary for a Build Card — a shareable card showing what a developer built in a coding session. This appears in a public community feed.

Project: ${safeName}

Session log:

${compactLog}

Title rules:
- 50-80 characters, aim for 8-12 words, sentence case
- Start with an action verb (Built, Shipped, Rewrote, Added, Designed, Implemented) or name the artifact directly
- Describe the OUTCOME — what changed for users or the product, not the technical implementation
- Be specific: "Built a real-time notification system with read tracking" not "Added notifications"
- Sound like something you'd share with a friend, not a commit message. No quotes.

Summary rules:
- Under 120 characters (~20 words). One sentence. Start with a verb. Past tense.
- What shipped, not what happened. Outcome over process.
- The "Session conclusion" section shows what was completed — prioritize that over early session activity
- Ground every claim in evidence from the session log
- No marketing language, no superlatives, no filler

Sparse session handling:
- If the session log has concrete activity (file edits, tool usage, assistant actions), describe what happened specifically
- If the session log is very thin (few lines, no file edits), write a conservative summary grounded in whatever evidence exists — e.g., "Explored the codebase and planned the approach for [feature]" or "Investigated [area] and prototyped initial changes"
- NEVER leave the title or summary blank — a brief, honest summary is always better than nothing
- NEVER invent features or changes that aren't evidenced in the session log

Privacy (strict):
- NEVER include: file paths, database table names, endpoint URLs, function names, internal architecture details, credentials, API keys, or code
- Describe what was done in plain language without exposing implementation internals
- Focus on what was accomplished, not tools or process

Format (exact):
TITLE: <title>
SUMMARY: <summary>`;
}

module.exports = {
  formatDuration,
  formatTokens,
  generateFallbackTitle,
  generateFallbackSummary,
  buildSummaryPrompt,
  getDominantTool,
  getWorkStyle,
};
