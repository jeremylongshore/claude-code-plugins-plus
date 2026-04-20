/**
 * Promptbook — JSONL transcript parser (replaces parse-transcript.py).
 * Single-pass line-by-line reader. No external dependencies.
 *
 * Extracts:
 * - Token usage (input, output, cache_creation, cache_read, total)
 * - Files touched (sanitized paths from Read/Write/Edit tools)
 * - Tool usage summary (counts per tool name)
 * - Compact session log for auto-summary generation
 */
'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');

const HOME = os.homedir();

/**
 * Sanitize a file path: make relative to cwd, strip home prefix, or basename.
 * Never exposes full absolute paths in output.
 */
function sanitizePath(filePath, cwd) {
  if (!filePath) return '';

  let normalized = path.normalize(filePath);

  // If absolute and inside cwd, make relative
  if (cwd && path.isAbsolute(normalized)) {
    try {
      const relative = path.relative(cwd, normalized);
      if (relative !== '..' && !relative.startsWith(`..${path.sep}`)) {
        return relative;
      }
    } catch { /* ignore */ }
  }

  // Strip home directory prefix
  if (HOME && normalized.startsWith(HOME + path.sep)) {
    return normalized.slice(HOME.length + 1);
  }

  // Absolute path outside cwd and home — use basename only
  if (path.isAbsolute(normalized)) {
    return path.basename(normalized);
  }

  // Strip leading ./
  return normalized.replace(/^\.\//, '');
}

/**
 * Remove control characters that break JSON encoding.
 */
function sanitizeText(text) {
  return text.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F]/g, ' ');
}

/**
 * Format extracted data into a budget-allocated compact log for auto-summary.
 *
 * Budget allocation (~4000 chars total):
 * - ~800 chars: structured metadata (files touched, tool counts)
 * - ~1200 chars: session conclusion (last 5-10 assistant blocks)
 * - ~2000 chars: sparse sample from earlier session for arc context
 */
function formatCompactLog(assistantLines, assistantFullBlocks, filesTouched, toolCounts) {
  const parts = [];

  // Zone 1: Metadata (~800 chars)
  const metaParts = [];
  if (filesTouched.size > 0) {
    metaParts.push('Files touched:');
    for (const fp of [...filesTouched].sort()) {
      metaParts.push(`  ${fp}`);
    }
  }
  if (Object.keys(toolCounts).length > 0) {
    const sorted = Object.entries(toolCounts).sort((a, b) => b[1] - a[1]);
    const toolsStr = sorted.map(([k, v]) => `${v} ${k}`).join(', ');
    metaParts.push(`Tool usage: ${toolsStr}`);
  }
  let metaText = metaParts.join('\n');
  if (metaText.length > 800) {
    metaText = metaText.slice(0, 800) + '\n...';
  }
  if (metaText) parts.push(metaText);

  // Zone 2: Session conclusion (~1200 chars)
  const conclusionBlocks = assistantFullBlocks.slice(-10);
  if (conclusionBlocks.length > 0) {
    const conclusionLines = [];
    let totalChars = 0;
    for (let i = conclusionBlocks.length - 1; i >= 0; i--) {
      const block = conclusionBlocks[i];
      if (totalChars + block.length > 1200) break;
      conclusionLines.unshift(`  - ${block}`);
      totalChars += block.length;
    }
    if (conclusionLines.length > 0) {
      parts.push('\nSession conclusion (what was completed):');
      parts.push(...conclusionLines);
    }
  }

  // Zone 3: Earlier session activity (~2000 chars)
  let earlierLines = assistantLines.length > 10 ? assistantLines.slice(0, -10) : [];
  if (earlierLines.length > 0) {
    if (earlierLines.length > 30) {
      const step = Math.max(1, Math.floor(earlierLines.length / 30));
      const sampled = [];
      for (let i = 0; i < earlierLines.length && sampled.length < 30; i += step) {
        sampled.push(earlierLines[i]);
      }
      earlierLines = sampled;
    }
    const sampledLines = [];
    let totalChars = 0;
    for (const line of earlierLines) {
      if (totalChars + line.length > 2000) break;
      sampledLines.push(`  - ${line}`);
      totalChars += line.length;
    }
    if (sampledLines.length > 0) {
      parts.push('\nEarlier session activity:');
      parts.push(...sampledLines);
    }
  }

  return parts.join('\n');
}

/**
 * Parse a transcript JSONL file synchronously (line-by-line).
 * Returns { input_tokens, output_tokens, total_tokens, cache_creation_input_tokens,
 *   cache_read_input_tokens, files_touched, tool_usage_summary, compact_log,
 *   source_metadata, model }
 *
 * @param {string} transcriptPath - Path to the JSONL file
 * @param {string} cwd - Session working directory (for path sanitization)
 * @param {boolean} compactOnly - If true, skip token tracking, return compact_log only
 */
function parseTranscript(transcriptPath, cwd = '', compactOnly = false) {
  if (!fs.existsSync(transcriptPath)) {
    return { error: `Transcript not found: ${transcriptPath}` };
  }

  // Token tracking
  let totalOutputTokens = 0;
  let sumFreshInput = 0;
  let sumCacheCreation = 0;
  let sumCacheRead = 0;

  // Model extraction
  let model = '';

  // Shared tracking
  const filesTouched = new Set();
  const toolCounts = {};
  const fileExtensions = {};

  // Compact log data
  const assistantLines = [];
  const assistantFullBlocks = [];

  // Read file using chunked buffer to avoid loading entire file into memory.
  // Still synchronous (required for hook performance) but memory-efficient for large transcripts.
  const fd = fs.openSync(transcriptPath, 'r');
  const CHUNK_SIZE = 64 * 1024; // 64KB chunks
  const buf = Buffer.alloc(CHUNK_SIZE);
  let leftover = '';

  function processLine(line) {
    const trimmed = line.trim();
    if (!trimmed) return;

    let entry;
    try {
      entry = JSON.parse(trimmed);
    } catch {
      return;
    }

    if (entry.type !== 'assistant') return;

    const message = entry.message || {};

    // Model extraction (first assistant message wins)
    if (!model) {
      const m = message.model;
      if (m && typeof m === 'string') model = m;
    }

    // Token tracking (full mode only)
    if (!compactOnly) {
      const usage = message.usage;
      if (usage) {
        totalOutputTokens += usage.output_tokens || 0;
        const inp = usage.input_tokens || 0;
        const cc = usage.cache_creation_input_tokens || 0;
        const cr = usage.cache_read_input_tokens || 0;
        sumFreshInput += inp;
        sumCacheCreation += cc;
        sumCacheRead += cr;
      }
    }

    // Content blocks: tool usage, file paths, assistant text
    const contentBlocks = message.content;
    if (!Array.isArray(contentBlocks)) return;

    for (const block of contentBlocks) {
      if (!block || typeof block !== 'object') continue;

      if (block.type === 'text') {
        const text = sanitizeText((block.text || '').trim());
        if (text) {
          const firstLine = text.split('\n')[0].trim();
          if (firstLine.length > 10) {
            assistantLines.push(firstLine);
          }
          if (text.length > 10) {
            assistantFullBlocks.push(text.slice(0, 300));
          }
        }
      } else if (block.type === 'tool_use') {
        const toolName = block.name || '';
        if (toolName) {
          toolCounts[toolName] = (toolCounts[toolName] || 0) + 1;
        }

        const toolInput = block.input || {};
        if (['Read', 'Write', 'Edit', 'NotebookEdit'].includes(toolName) && typeof toolInput === 'object') {
          const filePath = toolInput.file_path || toolInput.notebook_path || '';
          const sanitized = sanitizePath(filePath, cwd);
          if (sanitized) {
            filesTouched.add(sanitized);
            if (!compactOnly) {
              const ext = path.extname(sanitized).toLowerCase().replace(/^\./, '');
              if (ext) {
                fileExtensions[ext] = (fileExtensions[ext] || 0) + 1;
              }
            }
          }
        }
      }
    }
  }

  // Chunked read loop
  let bytesRead;
  while ((bytesRead = fs.readSync(fd, buf, 0, CHUNK_SIZE)) > 0) {
    const chunk = leftover + buf.toString('utf8', 0, bytesRead);
    const lines = chunk.split('\n');
    leftover = lines.pop(); // last element may be incomplete
    for (const line of lines) {
      processLine(line);
    }
  }
  if (leftover) processLine(leftover);
  fs.closeSync(fd);

  const compactLog = formatCompactLog(assistantLines, assistantFullBlocks, filesTouched, toolCounts);

  if (compactOnly) {
    const result = { compact_log: compactLog };
    if (model) result.model = model;
    return result;
  }

  const totalTokens = sumFreshInput + sumCacheCreation + totalOutputTokens;
  const sortedFiles = [...filesTouched].sort();

  const result = {
    input_tokens: sumFreshInput,
    output_tokens: totalOutputTokens,
    total_tokens: totalTokens,
    cache_creation_input_tokens: sumCacheCreation,
    cache_read_input_tokens: sumCacheRead,
    files_touched: sortedFiles,
    tool_usage_summary: toolCounts,
    compact_log: compactLog,
    source_metadata: {
      files_touched: sortedFiles,
      file_count: sortedFiles.length,
      file_extensions: fileExtensions,
      tool_usage_summary: toolCounts,
    },
  };
  if (model) result.model = model;
  return result;
}

/**
 * Parse all subagent transcripts next to a parent session and return aggregate token counts.
 * Subagent transcripts live at {projectDir}/{sessionId}/subagents/agent-*.jsonl
 *
 * @param {string} transcriptPath - Parent transcript path (e.g. ~/.claude/projects/{proj}/{sessionId}.jsonl)
 * @returns {{ subagent_count, subagent_tokens, input_tokens, output_tokens, cache_creation_input_tokens, cache_read_input_tokens } | null}
 */
function parseSubagentTokens(transcriptPath) {
  if (!transcriptPath) return null;

  // Derive subagents dir: /path/to/{sessionId}.jsonl → /path/to/{sessionId}/subagents/
  const sessionId = path.basename(transcriptPath, '.jsonl');
  const subagentsDir = path.join(path.dirname(transcriptPath), sessionId, 'subagents');

  if (!fs.existsSync(subagentsDir)) return null;

  let files;
  try {
    files = fs.readdirSync(subagentsDir).filter(f => /^agent-.*\.jsonl$/.test(f));
  } catch { return null; }

  if (files.length === 0) return null;

  let totalInput = 0;
  let totalOutput = 0;
  let totalCacheCreation = 0;
  let totalCacheRead = 0;

  for (const file of files) {
    try {
      const content = fs.readFileSync(path.join(subagentsDir, file), 'utf8');
      for (const line of content.split('\n')) {
        if (!line.trim()) continue;
        let entry;
        try { entry = JSON.parse(line); } catch { continue; }
        if (entry.type !== 'assistant') continue;
        const usage = (entry.message || {}).usage;
        if (!usage) continue;
        totalInput += usage.input_tokens || 0;
        totalOutput += usage.output_tokens || 0;
        totalCacheCreation += usage.cache_creation_input_tokens || 0;
        totalCacheRead += usage.cache_read_input_tokens || 0;
      }
    } catch { /* skip corrupted files */ }
  }

  const subagentTokens = totalInput + totalCacheCreation + totalOutput;
  if (subagentTokens === 0) return null;

  return {
    subagent_count: files.length,
    subagent_tokens: subagentTokens,
    input_tokens: totalInput,
    output_tokens: totalOutput,
    cache_creation_input_tokens: totalCacheCreation,
    cache_read_input_tokens: totalCacheRead,
  };
}

module.exports = { parseTranscript, parseSubagentTokens, sanitizePath };
