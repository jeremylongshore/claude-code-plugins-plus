#!/usr/bin/env node
/**
 * Marketplace Catalog Generator
 *
 * Generates marketplace/src/data/catalog.json from marketplace.extended.json
 * with git timestamps, badges, and computed fields.
 *
 * Bead ID: claude-code-plugins-wey
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Paths
const ROOT = path.join(__dirname, '..');
const EXTENDED_JSON = path.join(ROOT, '.claude-plugin/marketplace.extended.json');
const OUTPUT_JSON = path.join(ROOT, 'marketplace/src/data/catalog.json');
const FEATURED_CONFIG = path.join(ROOT, 'marketplace/src/data/featured.json');

// Constants
const DAY_MS = 24 * 60 * 60 * 1000;
const NEW_THRESHOLD_DAYS = 14;
const ACTIVE_THRESHOLD_DAYS = 30;
const MAINTAINED_THRESHOLD_DAYS = 90;

/**
 * Get git last commit timestamp for a path
 */
function getLastCommitTimestamp(sourcePath) {
  try {
    const fullPath = path.join(ROOT, sourcePath);
    const timestamp = execSync(
      `git log -1 --format=%ct -- "${fullPath}"`,
      { cwd: ROOT, encoding: 'utf8' }
    ).trim();

    return timestamp ? parseInt(timestamp, 10) : null;
  } catch (error) {
    console.warn(`Warning: Could not get git timestamp for ${sourcePath}`);
    return null;
  }
}

/**
 * Calculate status based on last updated timestamp
 */
function calculateStatus(lastUpdatedEpoch) {
  if (!lastUpdatedEpoch) return 'unknown';

  const daysSinceUpdate = (Date.now() / 1000 - lastUpdatedEpoch) / (60 * 60 * 24);

  if (daysSinceUpdate < ACTIVE_THRESHOLD_DAYS) return 'active';
  if (daysSinceUpdate < MAINTAINED_THRESHOLD_DAYS) return 'maintained';
  return 'stale';
}

/**
 * Determine badges for a plugin
 */
function determineBadges(plugin, lastUpdatedEpoch, featuredList) {
  const badges = [];

  // Featured badge (from config)
  if (featuredList.includes(plugin.name)) {
    badges.push('featured');
  }

  // New badge (<14 days)
  if (lastUpdatedEpoch) {
    const daysSinceUpdate = (Date.now() / 1000 - lastUpdatedEpoch) / (60 * 60 * 24);
    if (daysSinceUpdate < NEW_THRESHOLD_DAYS) {
      badges.push('new');
    }
  }

  return badges;
}

/**
 * Generate install command for a plugin
 */
function generateInstallCommand(plugin) {
  return `/plugin install ${plugin.name}`;
}

/**
 * Extract slug from plugin name
 */
function extractSlug(name) {
  // Remove leading numbers and author prefix: "000-jeremy-plugin-name" -> "plugin-name"
  return name.replace(/^\d+-[^-]+-/, '').replace(/^\d+-/, '');
}

/**
 * Main generator function
 */
async function generateCatalog() {
  console.log('🔨 Generating marketplace catalog...\n');

  // Load extended marketplace data
  console.log('📖 Reading marketplace.extended.json...');
  const extended = JSON.parse(fs.readFileSync(EXTENDED_JSON, 'utf8'));

  // Load or create featured list
  let featuredList = [];
  if (fs.existsSync(FEATURED_CONFIG)) {
    featuredList = JSON.parse(fs.readFileSync(FEATURED_CONFIG, 'utf8'));
  } else {
    console.log('⚠️  No featured.json found, creating empty list...');
    // Create default featured list with a few popular plugins
    featuredList = [
      'security-auditor',
      'python-pro',
      'devops-automation-pack',
      'test-automator',
      'backend-architect'
    ];
    fs.mkdirSync(path.dirname(FEATURED_CONFIG), { recursive: true });
    fs.writeFileSync(FEATURED_CONFIG, JSON.stringify(featuredList, null, 2));
  }

  // Process plugins
  console.log(`📦 Processing ${extended.plugins.length} plugins...\n`);

  const catalog = extended.plugins.map((plugin, index) => {
    const lastUpdatedEpoch = getLastCommitTimestamp(plugin.source);
    const status = calculateStatus(lastUpdatedEpoch);
    const badges = determineBadges(plugin, lastUpdatedEpoch, featuredList);
    const slug = extractSlug(plugin.name);

    // Progress indicator
    if ((index + 1) % 50 === 0 || index === extended.plugins.length - 1) {
      console.log(`  ✓ Processed ${index + 1}/${extended.plugins.length} plugins`);
    }

    return {
      // Core fields
      slug,
      name: plugin.name,
      displayName: plugin.name.replace(/^\d+-[^-]+-/, '').replace(/-/g, ' '),
      description: plugin.description,
      version: plugin.version,

      // Classification
      category: plugin.category,
      keywords: plugin.keywords || [],

      // Components
      hasSkills: (plugin.components?.skills || 0) > 0,
      skillCount: plugin.components?.skills || 0,
      commandCount: plugin.components?.commands || 0,

      // Installation
      installCommand: generateInstallCommand(plugin),
      sourcePath: plugin.source,

      // Timestamps & status
      lastUpdatedEpoch,
      lastUpdatedDate: lastUpdatedEpoch
        ? new Date(lastUpdatedEpoch * 1000).toISOString()
        : null,
      status,

      // Badges
      badges,
      isFeatured: badges.includes('featured'),
      isNew: badges.includes('new'),

      // Author
      author: plugin.author,

      // Metadata (for future use)
      type: plugin.category === 'mcp' ? 'mcp-server' : 'instruction-plugin'
    };
  });

  // Generate summary stats
  const stats = {
    totalPlugins: catalog.length,
    totalSkills: catalog.reduce((sum, p) => sum + p.skillCount, 0),
    totalCommands: catalog.reduce((sum, p) => sum + p.commandCount, 0),
    pluginsWithSkills: catalog.filter(p => p.hasSkills).length,
    byCategory: {},
    byStatus: {
      active: catalog.filter(p => p.status === 'active').length,
      maintained: catalog.filter(p => p.status === 'maintained').length,
      stale: catalog.filter(p => p.status === 'stale').length,
      unknown: catalog.filter(p => p.status === 'unknown').length
    },
    featured: catalog.filter(p => p.isFeatured).length,
    new: catalog.filter(p => p.isNew).length,
    generatedAt: new Date().toISOString()
  };

  // Calculate category counts
  catalog.forEach(plugin => {
    stats.byCategory[plugin.category] = (stats.byCategory[plugin.category] || 0) + 1;
  });

  // Create output
  const output = {
    meta: {
      version: '1.0.0',
      generated: stats.generatedAt,
      source: 'marketplace.extended.json',
      generator: 'scripts/generate-catalog.js'
    },
    stats,
    plugins: catalog
  };

  // Write output
  console.log(`\n💾 Writing catalog to ${OUTPUT_JSON}...`);
  fs.mkdirSync(path.dirname(OUTPUT_JSON), { recursive: true });
  fs.writeFileSync(OUTPUT_JSON, JSON.stringify(output, null, 2));

  // Summary
  console.log('\n✅ Catalog generation complete!\n');
  console.log('📊 Summary:');
  console.log(`   Total plugins: ${stats.totalPlugins}`);
  console.log(`   Total skills: ${stats.totalSkills}`);
  console.log(`   Plugins with skills: ${stats.pluginsWithSkills}`);
  console.log(`   Featured: ${stats.featured}`);
  console.log(`   New (<${NEW_THRESHOLD_DAYS}d): ${stats.new}`);
  console.log(`   Status breakdown:`);
  console.log(`     Active (<${ACTIVE_THRESHOLD_DAYS}d): ${stats.byStatus.active}`);
  console.log(`     Maintained (<${MAINTAINED_THRESHOLD_DAYS}d): ${stats.byStatus.maintained}`);
  console.log(`     Stale (≥${MAINTAINED_THRESHOLD_DAYS}d): ${stats.byStatus.stale}`);
  console.log(`\n📁 Output: ${OUTPUT_JSON}`);
  console.log(`📁 Featured config: ${FEATURED_CONFIG}\n`);
}

// Run
generateCatalog().catch(error => {
  console.error('❌ Error generating catalog:', error);
  process.exit(1);
});
