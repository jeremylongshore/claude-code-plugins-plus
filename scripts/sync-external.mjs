#!/usr/bin/env node
/**
 * External Plugin Sync Engine
 *
 * Syncs plugins from external repositories defined in sources.yaml.
 * Runs daily via GitHub Actions to keep community plugins fresh.
 *
 * Usage:
 *   node scripts/sync-external.mjs [options]
 *
 * Options:
 *   --force        Force sync even if no changes detected
 *   --dry-run      Show what would be synced without making changes
 *   --source=NAME  Sync only the specified source
 *   --verbose      Show detailed output
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import https from 'https';
import yaml from 'js-yaml';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT_DIR = path.resolve(__dirname, '..');
const SOURCES_FILE = path.join(ROOT_DIR, 'sources.yaml');

// Parse command line arguments
const args = process.argv.slice(2);
const options = {
  force: args.includes('--force'),
  dryRun: args.includes('--dry-run'),
  verbose: args.includes('--verbose'),
  source: args.find(a => a.startsWith('--source='))?.split('=')[1] || null,
};

// Colors for terminal output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  dim: '\x1b[2m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  red: '\x1b[31m',
  cyan: '\x1b[36m',
};

function log(message, color = '') {
  console.log(`${color}${message}${colors.reset}`);
}

function logVerbose(message) {
  if (options.verbose) {
    console.log(`${colors.dim}  ${message}${colors.reset}`);
  }
}

/**
 * Fetch file content from GitHub API
 */
async function fetchFromGitHub(repo, filePath, branch = 'main') {
  const url = `https://api.github.com/repos/${repo}/contents/${filePath}?ref=${branch}`;

  return new Promise((resolve, reject) => {
    const headers = {
      'User-Agent': 'claude-code-plugins-sync',
      'Accept': 'application/vnd.github.v3+json',
    };

    // Add auth token if available
    if (process.env.GITHUB_TOKEN) {
      headers['Authorization'] = `token ${process.env.GITHUB_TOKEN}`;
    }

    https.get(url, { headers }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        if (res.statusCode === 200) {
          try {
            const json = JSON.parse(data);
            if (json.content) {
              // Decode base64 content
              const content = Buffer.from(json.content, 'base64').toString('utf8');
              resolve({ content, sha: json.sha, path: json.path });
            } else if (Array.isArray(json)) {
              // Directory listing
              resolve({ type: 'directory', files: json });
            } else {
              reject(new Error(`Unexpected response format for ${filePath}`));
            }
          } catch (e) {
            reject(new Error(`Failed to parse response: ${e.message}`));
          }
        } else if (res.statusCode === 404) {
          resolve(null); // File not found
        } else {
          reject(new Error(`GitHub API error ${res.statusCode}: ${data}`));
        }
      });
    }).on('error', reject);
  });
}

/**
 * Recursively fetch directory contents from GitHub
 */
async function fetchDirectory(repo, dirPath, branch = 'main') {
  const result = await fetchFromGitHub(repo, dirPath, branch);

  if (!result || result.type !== 'directory') {
    return [];
  }

  const files = [];

  for (const item of result.files) {
    if (item.type === 'file') {
      const fileContent = await fetchFromGitHub(repo, item.path, branch);
      if (fileContent) {
        files.push({
          path: item.path.replace(`${dirPath}/`, ''),
          content: fileContent.content,
          sha: fileContent.sha,
        });
      }
    } else if (item.type === 'dir') {
      const subFiles = await fetchDirectory(repo, item.path, branch);
      files.push(...subFiles.map(f => ({
        ...f,
        path: `${item.name}/${f.path}`,
      })));
    }
  }

  return files;
}

/**
 * Check if a path matches any of the glob patterns
 */
function matchesPattern(filePath, patterns) {
  if (!patterns || patterns.length === 0) return true;

  return patterns.some(pattern => {
    // Convert glob pattern to regex
    const regex = new RegExp(
      '^' + pattern
        .replace(/\*\*/g, '<<<DOUBLESTAR>>>')
        .replace(/\*/g, '[^/]*')
        .replace(/<<<DOUBLESTAR>>>/g, '.*')
        .replace(/\?/g, '.') + '$'
    );
    return regex.test(filePath);
  });
}

/**
 * Sync a single source
 */
async function syncSource(source, config) {
  log(`\n📦 Syncing: ${source.name}`, colors.cyan);
  log(`   From: ${source.repo}/${source.source_path}`, colors.dim);
  log(`   To:   ${source.target_path}`, colors.dim);

  const changes = [];
  const branch = config.default_branch || 'main';

  try {
    // Fetch source directory contents
    const files = await fetchDirectory(source.repo, source.source_path, branch);

    if (files.length === 0) {
      log(`   ⚠️  No files found at source path`, colors.yellow);
      return { source: source.name, changes: [], error: 'No files found' };
    }

    logVerbose(`Found ${files.length} files in source`);

    // Filter files based on include/exclude patterns
    const filteredFiles = files.filter(file => {
      const included = matchesPattern(file.path, source.include);
      const excluded = matchesPattern(file.path, source.exclude);
      return included && !excluded;
    });

    logVerbose(`${filteredFiles.length} files after filtering`);

    // Process each file
    for (const file of filteredFiles) {
      const targetPath = path.join(ROOT_DIR, source.target_path, 'skills', source.name, file.path);
      const targetDir = path.dirname(targetPath);

      // Check if file exists and compare
      let needsUpdate = false;
      let reason = 'new';

      if (fs.existsSync(targetPath)) {
        const existingContent = fs.readFileSync(targetPath, 'utf8');
        if (existingContent !== file.content) {
          needsUpdate = true;
          reason = 'modified';
        }
      } else {
        needsUpdate = true;
      }

      if (needsUpdate || options.force) {
        if (options.dryRun) {
          log(`   📝 Would ${reason === 'new' ? 'create' : 'update'}: ${file.path}`, colors.yellow);
        } else {
          // Create directory if needed
          if (!fs.existsSync(targetDir)) {
            fs.mkdirSync(targetDir, { recursive: true });
          }

          // Write file
          fs.writeFileSync(targetPath, file.content);
          log(`   ✅ ${reason === 'new' ? 'Created' : 'Updated'}: ${file.path}`, colors.green);
        }

        changes.push({ path: file.path, action: reason });
      } else {
        logVerbose(`Unchanged: ${file.path}`);
      }
    }

    // Write .source.json with provenance info
    if (changes.length > 0 && !options.dryRun) {
      const sourceJsonPath = path.join(ROOT_DIR, source.target_path, '.source.json');
      const sourceJson = {
        synced_from: {
          repo: source.repo,
          path: source.source_path,
          branch: branch,
        },
        last_sync: new Date().toISOString(),
        author: source.author,
        license: source.license,
        files_synced: changes.length,
      };
      fs.writeFileSync(sourceJsonPath, JSON.stringify(sourceJson, null, 2));
      logVerbose(`Written .source.json`);
    }

    if (changes.length === 0) {
      log(`   ✓ No changes detected`, colors.dim);
    }

    return { source: source.name, changes, error: null };

  } catch (error) {
    log(`   ❌ Error: ${error.message}`, colors.red);
    return { source: source.name, changes: [], error: error.message };
  }
}

/**
 * Main sync function
 */
async function main() {
  log('\n🔄 External Plugin Sync', colors.bright + colors.blue);
  log('=' .repeat(50), colors.blue);

  if (options.dryRun) {
    log('DRY RUN MODE - No changes will be made\n', colors.yellow);
  }

  // Load sources.yaml
  if (!fs.existsSync(SOURCES_FILE)) {
    log(`❌ sources.yaml not found at ${SOURCES_FILE}`, colors.red);
    process.exit(1);
  }

  const sourcesContent = fs.readFileSync(SOURCES_FILE, 'utf8');
  const { sources, config } = yaml.load(sourcesContent);

  if (!sources || sources.length === 0) {
    log('❌ No sources defined in sources.yaml', colors.red);
    process.exit(1);
  }

  log(`Found ${sources.length} source(s) to sync`, colors.dim);

  // Filter sources if --source option provided
  const sourcesToSync = options.source
    ? sources.filter(s => s.name === options.source)
    : sources;

  if (options.source && sourcesToSync.length === 0) {
    log(`❌ Source "${options.source}" not found in sources.yaml`, colors.red);
    process.exit(1);
  }

  // Sync each source
  const results = [];
  for (const source of sourcesToSync) {
    const result = await syncSource(source, config);
    results.push(result);
  }

  // Summary
  log('\n' + '='.repeat(50), colors.blue);
  log('📊 Sync Summary', colors.bright + colors.blue);

  const totalChanges = results.reduce((acc, r) => acc + r.changes.length, 0);
  const errors = results.filter(r => r.error);

  if (totalChanges > 0) {
    log(`✅ ${totalChanges} file(s) ${options.dryRun ? 'would be ' : ''}synced`, colors.green);
  } else {
    log('✓ All sources up to date', colors.dim);
  }

  if (errors.length > 0) {
    log(`⚠️  ${errors.length} source(s) had errors`, colors.yellow);
    errors.forEach(e => log(`   - ${e.source}: ${e.error}`, colors.red));
  }

  // Output for GitHub Actions
  if (process.env.GITHUB_OUTPUT) {
    const outputFile = process.env.GITHUB_OUTPUT;
    fs.appendFileSync(outputFile, `changes=${totalChanges}\n`);
    fs.appendFileSync(outputFile, `sources=${results.map(r => r.source).join(',')}\n`);
    fs.appendFileSync(outputFile, `has_changes=${totalChanges > 0}\n`);
  }

  log('\n');
  process.exit(errors.length > 0 ? 1 : 0);
}

// Run
main().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});
