/**
 * Promptbook — Language detection and project name derivation.
 */
'use strict';

const fs = require('fs');
const path = require('path');

const EXT_TO_LANGUAGE = {
  ts: 'TypeScript', tsx: 'TypeScript',
  js: 'JavaScript', jsx: 'JavaScript',
  py: 'Python',
  rs: 'Rust',
  go: 'Go',
  rb: 'Ruby',
  java: 'Java',
  swift: 'Swift',
  kt: 'Kotlin',
  css: 'CSS',
  html: 'HTML',
  sql: 'SQL',
  sh: 'Shell', bash: 'Shell', zsh: 'Shell',
  md: 'Markdown',
  json: 'JSON',
  yaml: 'YAML', yml: 'YAML',
  c: 'C', h: 'C',
  cpp: 'C++', cc: 'C++', cxx: 'C++', hpp: 'C++',
  cs: 'C#',
  php: 'PHP',
  r: 'R',
  scala: 'Scala',
  dart: 'Dart',
  lua: 'Lua',
  zig: 'Zig',
  ex: 'Elixir', exs: 'Elixir',
  erl: 'Erlang',
  hs: 'Haskell',
  ml: 'OCaml',
  vue: 'Vue',
  svelte: 'Svelte',
};

/**
 * Map a file extension to a human-readable language name.
 */
function mapExtToLanguage(ext) {
  if (!ext) return 'Unknown';
  return EXT_TO_LANGUAGE[ext.toLowerCase()] || 'Unknown';
}

/**
 * Get the most-used language from a file_extensions object.
 * Input: { ts: 5, css: 2, json: 1 } → "TypeScript"
 */
function getPrimaryLanguage(fileExtensions) {
  if (!fileExtensions || typeof fileExtensions !== 'object') return 'Unknown';
  const entries = Object.entries(fileExtensions);
  if (entries.length === 0) return 'Unknown';
  entries.sort((a, b) => b[1] - a[1]);
  return mapExtToLanguage(entries[0][0]);
}

/**
 * Derive project name from cwd, handling git worktrees.
 * If .git is a file (worktree), resolve the parent repo name.
 */
function deriveProjectName(cwd) {
  if (!cwd) return 'unknown';

  let projectName = path.basename(cwd);

  try {
    const gitPath = path.join(cwd, '.git');
    const stat = fs.statSync(gitPath);

    if (stat.isFile()) {
      // Git worktree: .git is a file containing "gitdir: /path/to/repo/.git/worktrees/<name>"
      const content = fs.readFileSync(gitPath, 'utf8');
      const match = content.match(/^gitdir:\s*(.+)/m);
      if (match) {
        const gitdir = match[1].trim();
        // Strip /.git/worktrees/<name> to get the parent repo path
        const parentMatch = gitdir.match(/^(.+)\/\.git\/worktrees\/.+$/);
        if (parentMatch) {
          const parentRepo = parentMatch[1];
          try {
            fs.statSync(parentRepo);
            projectName = path.basename(parentRepo);
          } catch { /* parent doesn't exist, keep original */ }
        }
      }
    }
  } catch { /* no .git or can't read — use basename */ }

  return projectName;
}

module.exports = {
  mapExtToLanguage,
  getPrimaryLanguage,
  deriveProjectName,
};
