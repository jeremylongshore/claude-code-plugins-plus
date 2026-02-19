#!/usr/bin/env node
/**
 * build-cowork-zips.mjs
 *
 * Generates downloadable zip files for Claude Cowork users who cannot use CLI.
 * Reads marketplace.extended.json, zips each plugin individually, creates
 * category bundles, a mega-zip, and a manifest.json with metadata.
 *
 * Output: marketplace/public/downloads/
 *   plugins/      - Individual plugin zips
 *   bundles/      - Category bundle zips
 *   claude-code-plugins-all.zip - Everything
 *   manifest.json - Sizes, counts, checksums
 */

import { createWriteStream, existsSync, lstatSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { createHash } from 'node:crypto';
import { createRequire } from 'node:module';

const ROOT = resolve(dirname(new URL(import.meta.url).pathname), '..');

// Resolve archiver from marketplace/node_modules where it's installed,
// since this script lives at root scripts/ but archiver is a marketplace dep
const require = createRequire(join(ROOT, 'marketplace', 'package.json'));
const archiver = require('archiver');
const EXTENDED_JSON = join(ROOT, '.claude-plugin', 'marketplace.extended.json');
const OUTPUT_DIR = join(ROOT, 'marketplace', 'public', 'downloads');
const PLUGINS_DIR = join(ROOT, 'plugins');

// Categories to skip (MCP plugins need node_modules, not suitable for zip)
const SKIP_CATEGORIES = new Set(['mcp']);
// Directories to skip inside plugin folders
const SKIP_DIRS = new Set(['node_modules', '.git', 'dist', '__pycache__', '.pytest_cache']);
const SKIP_FILES = new Set(['.DS_Store', 'Thumbs.db', '.env', '.env.local']);
// Patterns for sensitive files that should never be included in downloads
const SKIP_PATTERNS = [/^id_rsa/, /credentials/i, /secrets?\./i, /token\./i, /\.key$/, /\.pem$/];

// Human-friendly category names
const CATEGORY_LABELS = {
  'ai-ml': 'AI & Machine Learning',
  'ai-agency': 'AI Agents & Agency',
  'api-development': 'API Development',
  'automation': 'Automation',
  'business-tools': 'Business Tools',
  'code-quality': 'Code Quality',
  'community': 'Community',
  'crypto': 'Crypto & Web3',
  'database': 'Database',
  'data-engineering': 'Data Engineering',
  'design': 'Design',
  'devops': 'DevOps & Infrastructure',
  'enterprise': 'Enterprise',
  'examples': 'Examples & Templates',
  'finance': 'Finance',
  'fullstack': 'Full-Stack Development',
  'jeremy-genkit': 'Google Genkit',
  'jeremy-google-adk': 'Google ADK',
  'jeremy-vertex-ai': 'Vertex AI',
  'packages': 'Packages',
  'performance': 'Performance',
  'productivity': 'Productivity',
  'saas-packs': 'SaaS Integrations',
  'security': 'Security',
  'skill-enhancers': 'Skill Enhancers',
  'testing': 'Testing',
};

function sha256File(filePath) {
  const data = readFileSync(filePath);
  return createHash('sha256').update(data).digest('hex');
}

function fileSize(filePath) {
  return statSync(filePath).size;
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function countSkills(pluginDir) {
  const skillsDir = join(pluginDir, 'skills');
  if (!existsSync(skillsDir)) return 0;
  let count = 0;
  try {
    for (const entry of readdirSync(skillsDir, { withFileTypes: true })) {
      if (entry.isDirectory()) {
        const skillMd = join(skillsDir, entry.name, 'SKILL.md');
        if (existsSync(skillMd)) count++;
      }
    }
  } catch (err) { console.warn(`  Warning: Could not count skills in ${skillsDir}: ${err.message}`); }
  return count;
}

function countCommands(pluginDir) {
  const cmdDir = join(pluginDir, 'commands');
  if (!existsSync(cmdDir)) return 0;
  try {
    return readdirSync(cmdDir).filter(f => f.endsWith('.md')).length;
  } catch (err) { console.warn(`  Warning: Could not count commands in ${cmdDir}: ${err.message}`); return 0; }
}

function countAgents(pluginDir) {
  const agentDir = join(pluginDir, 'agents');
  if (!existsSync(agentDir)) return 0;
  try {
    return readdirSync(agentDir).filter(f => f.endsWith('.md')).length;
  } catch (err) { console.warn(`  Warning: Could not count agents in ${agentDir}: ${err.message}`); return 0; }
}

function shouldInclude(entryName) {
  if (SKIP_DIRS.has(entryName) || SKIP_FILES.has(entryName) || entryName.startsWith('.')) return false;
  if (SKIP_PATTERNS.some(p => p.test(entryName))) return false;
  return true;
}

/**
 * Validate that a resolved path is within the allowed plugins directory.
 * Prevents path traversal attacks from malicious catalog entries.
 */
function isWithinPluginsDir(resolvedPath) {
  const normalized = resolve(resolvedPath);
  return normalized.startsWith(PLUGINS_DIR + '/') || normalized === PLUGINS_DIR;
}

/**
 * Recursively add files from a directory to an archive, skipping symlinks.
 */
function addDirToArchive(archive, dirPath, archivePrefix, archiveName) {
  for (const entry of readdirSync(dirPath, { withFileTypes: true })) {
    if (!shouldInclude(entry.name)) continue;
    const fullPath = join(dirPath, entry.name);
    const archivePath = archivePrefix ? `${archivePrefix}/${entry.name}` : entry.name;

    // Skip symlinks to prevent directory traversal
    try {
      const stats = lstatSync(fullPath);
      if (stats.isSymbolicLink()) continue;
    } catch (err) { console.warn(`  Warning: Could not stat ${fullPath}: ${err.message}`); continue; }

    if (entry.isDirectory()) {
      addDirToArchive(archive, fullPath, archivePath, archiveName);
    } else if (entry.isFile()) {
      archive.file(fullPath, { name: `${archiveName}/${archivePath}` });
    }
  }
}

/**
 * Create a zip from a directory, returning the output path.
 */
async function zipDirectory(sourceDir, outputPath, archiveName) {
  mkdirSync(dirname(outputPath), { recursive: true });

  const output = createWriteStream(outputPath);
  const archive = archiver('zip', { zlib: { level: 6 } });

  const done = new Promise((res, rej) => {
    output.on('close', res);
    output.on('error', rej);
    archive.on('error', rej);
    archive.on('warning', (err) => {
      if (err.code !== 'ENOENT') rej(err);
    });
  });

  archive.pipe(output);
  addDirToArchive(archive, sourceDir, '', archiveName);

  try {
    await archive.finalize();
    await done;
  } catch (err) {
    output.destroy();
    throw err;
  }

  return outputPath;
}

/**
 * Create a zip from multiple directories (for bundles).
 */
async function zipMultipleDirs(entries, outputPath) {
  mkdirSync(dirname(outputPath), { recursive: true });

  const output = createWriteStream(outputPath);
  const archive = archiver('zip', { zlib: { level: 6 } });

  const done = new Promise((res, rej) => {
    output.on('close', res);
    output.on('error', rej);
    archive.on('error', rej);
    archive.on('warning', (err) => {
      if (err.code !== 'ENOENT') rej(err);
    });
  });

  archive.pipe(output);

  for (const { sourceDir, archiveName } of entries) {
    addDirToArchive(archive, sourceDir, '', archiveName);
  }

  try {
    await archive.finalize();
    await done;
  } catch (err) {
    output.destroy();
    throw err;
  }

  return outputPath;
}

async function main() {
  console.log('=== Building Cowork Download Zips ===\n');

  // Read catalog
  const catalog = JSON.parse(readFileSync(EXTENDED_JSON, 'utf-8'));
  const plugins = catalog.plugins || [];

  console.log(`Found ${plugins.length} plugins in catalog\n`);

  // Create output directories
  mkdirSync(join(OUTPUT_DIR, 'plugins'), { recursive: true });
  mkdirSync(join(OUTPUT_DIR, 'bundles'), { recursive: true });

  const manifest = {
    generated: new Date().toISOString(),
    version: catalog.metadata?.version || '1.0.0',
    plugins: [],
    bundles: [],
    megaZip: null,
  };

  // Group plugins by category
  const byCategory = new Map();
  const allEntries = []; // For mega-zip

  let skippedCount = 0;
  let builtCount = 0;
  const failedBuilds = [];

  // Phase 1: Individual plugin zips
  console.log('Phase 1: Building individual plugin zips...');

  for (const plugin of plugins) {
    const { name, source, category } = plugin;
    if (!source) continue;

    // Resolve plugin directory with path traversal protection
    const pluginDir = resolve(ROOT, source);
    if (!isWithinPluginsDir(pluginDir)) {
      console.warn(`  SKIP: ${name} - path outside plugins directory: ${source}`);
      skippedCount++;
      continue;
    }
    if (!existsSync(pluginDir)) {
      console.warn(`  SKIP: ${name} - directory not found: ${source}`);
      skippedCount++;
      continue;
    }

    // Detect category from directory structure if not in JSON
    const dirParts = source.replace(/^\.?\/?plugins\//, '').split('/');
    const dirCategory = dirParts.length > 1 ? dirParts[0] : (category || 'uncategorized');

    // Skip MCP plugins
    if (SKIP_CATEGORIES.has(dirCategory)) {
      console.log(`  SKIP (MCP): ${name}`);
      skippedCount++;
      continue;
    }

    const zipName = `${name}.zip`;
    const zipPath = join(OUTPUT_DIR, 'plugins', zipName);

    try {
      await zipDirectory(pluginDir, zipPath, name);
      const size = fileSize(zipPath);
      const checksum = sha256File(zipPath);
      const skills = countSkills(pluginDir);
      const commands = countCommands(pluginDir);
      const agents = countAgents(pluginDir);

      manifest.plugins.push({
        name,
        category: dirCategory,
        fileName: zipName,
        path: `/downloads/plugins/${zipName}`,
        size,
        sizeFormatted: formatBytes(size),
        checksum,
        skills,
        commands,
        agents,
      });

      // Track for category bundles
      if (!byCategory.has(dirCategory)) {
        byCategory.set(dirCategory, []);
      }
      byCategory.get(dirCategory).push({ sourceDir: pluginDir, archiveName: name });
      allEntries.push({ sourceDir: pluginDir, archiveName: name });

      builtCount++;
      if (builtCount % 50 === 0) {
        console.log(`  Progress: ${builtCount}/${plugins.length} plugins built...`);
      }
    } catch (err) {
      console.error(`  ERROR: ${name} - ${err.message}`);
      failedBuilds.push({ name, error: err.message });
    }
  }

  console.log(`  Built ${builtCount} plugin zips, skipped ${skippedCount}\n`);

  // Phase 2: Category bundle zips
  console.log('Phase 2: Building category bundle zips...');

  for (const [category, entries] of byCategory.entries()) {
    const bundleName = `${category}.zip`;
    const bundlePath = join(OUTPUT_DIR, 'bundles', bundleName);

    try {
      await zipMultipleDirs(entries, bundlePath);
      const size = fileSize(bundlePath);
      const checksum = sha256File(bundlePath);

      const totalSkills = entries.reduce((sum, e) => {
        return sum + countSkills(e.sourceDir);
      }, 0);

      manifest.bundles.push({
        category,
        label: CATEGORY_LABELS[category] || category,
        fileName: bundleName,
        path: `/downloads/bundles/${bundleName}`,
        size,
        sizeFormatted: formatBytes(size),
        checksum,
        pluginCount: entries.length,
        totalSkills,
      });

      console.log(`  ${category}: ${entries.length} plugins (${formatBytes(size)})`);
    } catch (err) {
      console.error(`  ERROR: ${category} bundle - ${err.message}`);
      failedBuilds.push({ name: `bundle:${category}`, error: err.message });
    }
  }

  // Sort bundles by plugin count desc
  manifest.bundles.sort((a, b) => b.pluginCount - a.pluginCount);

  console.log(`  Built ${manifest.bundles.length} category bundles\n`);

  // Phase 3: Mega-zip
  console.log('Phase 3: Building mega-zip...');

  const megaPath = join(OUTPUT_DIR, 'claude-code-plugins-all.zip');
  try {
    await zipMultipleDirs(allEntries, megaPath);
    const size = fileSize(megaPath);
    const checksum = sha256File(megaPath);
    const totalSkills = manifest.plugins.reduce((sum, p) => sum + p.skills, 0);

    manifest.megaZip = {
      fileName: 'claude-code-plugins-all.zip',
      path: '/downloads/claude-code-plugins-all.zip',
      size,
      sizeFormatted: formatBytes(size),
      checksum,
      pluginCount: allEntries.length,
      totalSkills,
    };

    console.log(`  Mega-zip: ${allEntries.length} plugins (${formatBytes(size)})\n`);
  } catch (err) {
    console.error(`  ERROR: mega-zip - ${err.message}`);
    failedBuilds.push({ name: 'mega-zip', error: err.message });
  }

  // Write manifest
  writeFileSync(join(OUTPUT_DIR, 'manifest.json'), JSON.stringify(manifest, null, 2));
  console.log(`Manifest written to downloads/manifest.json`);

  // Also write enriched cowork manifest for the Astro pages
  const coworkManifest = {
    generated: manifest.generated,
    version: manifest.version,
    totalPlugins: manifest.plugins.length,
    totalSkills: manifest.plugins.reduce((sum, p) => sum + p.skills, 0),
    totalCommands: manifest.plugins.reduce((sum, p) => sum + p.commands, 0),
    totalAgents: manifest.plugins.reduce((sum, p) => sum + p.agents, 0),
    megaZip: manifest.megaZip,
    bundles: manifest.bundles,
    plugins: manifest.plugins,
  };

  const coworkManifestPath = join(ROOT, 'marketplace', 'src', 'data', 'cowork-manifest.json');
  mkdirSync(dirname(coworkManifestPath), { recursive: true });
  writeFileSync(coworkManifestPath, JSON.stringify(coworkManifest, null, 2));
  console.log(`Cowork manifest written to marketplace/src/data/cowork-manifest.json`);

  // Summary
  console.log('\n=== Cowork Zips Complete ===');
  console.log(`  Individual zips: ${manifest.plugins.length}`);
  console.log(`  Category bundles: ${manifest.bundles.length}`);
  console.log(`  Mega-zip: ${manifest.megaZip?.sizeFormatted || 'N/A'}`);
  console.log(`  Total skills: ${coworkManifest.totalSkills}`);

  if (failedBuilds.length > 0) {
    console.error(`\n  ${failedBuilds.length} build(s) FAILED:`);
    for (const f of failedBuilds) {
      console.error(`    - ${f.name}: ${f.error}`);
    }
    process.exit(1);
  }
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
