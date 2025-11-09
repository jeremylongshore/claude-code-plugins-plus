#!/usr/bin/env node
/**
 * Generate Astro content collection from marketplace.json
 * Creates individual JSON files for each plugin in src/content/plugins
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load marketplace catalog (prefer extended metadata for site generation)
const extendedMarketplacePath = path.join(__dirname, '..', '.claude-plugin', 'marketplace.extended.json');
const marketplacePath = fs.existsSync(extendedMarketplacePath)
  ? extendedMarketplacePath
  : path.join(__dirname, '..', '.claude-plugin', 'marketplace.json');

const marketplaceData = JSON.parse(fs.readFileSync(marketplacePath, 'utf8'));

// Ensure content directory exists
const contentDir = path.join(__dirname, 'src', 'content', 'plugins');
if (!fs.existsSync(contentDir)) {
  fs.mkdirSync(contentDir, { recursive: true });
}

// Clear existing content
const existingFiles = fs.readdirSync(contentDir);
existingFiles.forEach(file => {
  if (file.endsWith('.json')) {
    fs.unlinkSync(path.join(contentDir, file));
  }
});

// Generate plugin files
let pluginCount = 0;
marketplaceData.plugins.forEach(plugin => {
  // Normalize category names
  let category = plugin.category || 'other';

  // Map categories to supported enum values
  const categoryMap = {
    'devops': 'devops',
    'ai-ml': 'ai-ml-assistance',
    'api-development': 'other',
    'testing': 'testing',
    'ai-agency': 'business-tools',
    'productivity': 'other',
    'security': 'security',
    'fullstack': 'frontend-development',
    'example': 'other',
    'design': 'other',
    'debugging': 'debugging',
    'code-quality': 'code-analysis',
    'automation': 'automation'
  };

  category = categoryMap[category] || 'other';

  // Process author data
  let authorData = { name: 'Claude Code Plugin Hub' };
  if (plugin.author) {
    authorData = {
      name: plugin.author.name || 'Claude Code Plugin Hub'
    };
    // Only add email if it exists, is not empty, and contains @
    if (plugin.author.email && typeof plugin.author.email === 'string' && plugin.author.email.includes('@') && plugin.author.email.trim().length > 3) {
      authorData.email = plugin.author.email.trim();
    }
    // Only add url if it exists, is not empty, and starts with http
    if (plugin.author.url && typeof plugin.author.url === 'string' && plugin.author.url.startsWith('http')) {
      authorData.url = plugin.author.url.trim();
    }
  }

  const pluginData = {
    name: plugin.name,
    description: plugin.description || '',
    version: plugin.version || '1.0.0',
    category: category,
    keywords: plugin.keywords || [],
    author: authorData,
    featured: plugin.featured || false,
    repository: plugin.repository || `https://github.com/jeremylongshore/claude-code-plugins/tree/main/${plugin.source}`,
    license: plugin.license || 'MIT',
    installation: `/plugin install ${plugin.name}@claude-code-plugins-plus`,
    features: plugin.features || [],
    requirements: plugin.requirements || [],
    screenshots: plugin.screenshots || []
  };

  // Write plugin file
  const filename = `${plugin.name}.json`;
  fs.writeFileSync(
    path.join(contentDir, filename),
    JSON.stringify(pluginData, null, 2)
  );
  pluginCount++;
});

console.log(`Generated ${pluginCount} plugin files in ${contentDir}`);
console.log('Content generation complete!');
