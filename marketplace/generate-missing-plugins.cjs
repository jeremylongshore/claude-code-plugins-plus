#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// Get repository root (go up one level from marketplace/)
const repoRoot = path.join(__dirname, '..');
const extendedMarketplacePath = path.join(repoRoot, '.claude-plugin', 'marketplace.extended.json');
const marketplaceJsonPath = fs.existsSync(extendedMarketplacePath)
  ? extendedMarketplacePath
  : path.join(repoRoot, '.claude-plugin', 'marketplace.json');

// Read marketplace.json
const marketplaceData = JSON.parse(
  fs.readFileSync(marketplaceJsonPath, 'utf8')
);

// Categories to process
const categories = ['crypto', 'database', 'performance', 'security', 'testing'];

// Find plugins in these categories
const pluginsToProcess = marketplaceData.plugins.filter(p => {
  const source = p.source || '';
  return categories.some(cat => source.includes(`/${cat}/`));
});

console.log(`Found ${pluginsToProcess.length} plugins to process`);

// Map categories from source paths to valid schema categories
function mapCategory(pluginCategory, sourcePath) {
  const categoryMap = {
    'crypto': 'other',
    'database': 'database',
    'performance': 'performance',
    'security': 'security',
    'testing': 'testing'
  };

  // Extract category from source path
  for (const [key, value] of Object.entries(categoryMap)) {
    if (sourcePath.includes(`/${key}/`)) {
      return value;
    }
  }

  return pluginCategory || 'other';
}

// Create marketplace/src/content/plugins directory if it doesn't exist
const outputDir = path.join(__dirname, 'src/content/plugins');
if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true });
}

let created = 0;
let skipped = 0;

// Process each plugin
pluginsToProcess.forEach(plugin => {
  const filename = `${plugin.name}.json`;
  const outputPath = path.join(outputDir, filename);

  // Skip if file already exists
  if (fs.existsSync(outputPath)) {
    console.log(`⏭️  Skipped ${filename} (already exists)`);
    skipped++;
    return;
  }

  // Map the category
  const category = mapCategory(plugin.category, plugin.source);

  // Create author object without email (email is optional and must be valid)
  const author = { name: (plugin.author && plugin.author.name) || 'Jeremy Longshore' };

  // Create the JSON object
  const marketplaceJson = {
    name: plugin.name,
    description: plugin.description,
    version: plugin.version || '1.0.0',
    category: category,
    keywords: plugin.keywords || [],
    author: author,
    featured: plugin.featured || false,
    repository: plugin.repository || `https://github.com/jeremylongshore/claude-code-plugins/tree/main/${plugin.source}`,
    license: plugin.license || 'MIT',
    installation: `/plugin install ${plugin.name}@claude-code-plugins-plus`,
    features: [],
    requirements: [],
    screenshots: []
  };

  // Write the file
  fs.writeFileSync(outputPath, JSON.stringify(marketplaceJson, null, 2) + '\n');
  console.log(`✅ Created ${filename}`);
  created++;
});

console.log(`\n📊 Summary:`);
console.log(`   Created: ${created}`);
console.log(`   Skipped: ${skipped}`);
console.log(`   Total: ${pluginsToProcess.length}`);
