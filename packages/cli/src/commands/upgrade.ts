import chalk from 'chalk';
import { promises as fs } from 'fs';
import { existsSync } from 'fs';
import * as path from 'path';
import axios from 'axios';
import type { ClaudePaths } from '../utils/paths.js';

interface UpgradeOptions {
  check?: boolean;
  all?: boolean;
  plugin?: string;
}

interface PluginMetadata {
  name: string;
  version: string;
  description: string;
  author: string;
  category?: string;
}

interface InstalledPlugin {
  version: string;
  scope?: string;
  installedAt?: string;
}

interface PluginUpdate {
  name: string;
  currentVersion: string;
  latestVersion: string;
  description?: string;
}

const MARKETPLACE_REPO = 'jeremylongshore/claude-code-plugins';
const MARKETPLACE_SLUG = 'claude-code-plugins-plus';
const CATALOG_URL = 'https://raw.githubusercontent.com/jeremylongshore/claude-code-plugins/main/.claude-plugin/marketplace.json';

/**
 * Main upgrade command handler
 */
export async function upgradeCommand(
  paths: ClaudePaths,
  options: UpgradeOptions
): Promise<void> {
  console.log(chalk.bold('\n🔄 Plugin Upgrade Manager\n'));

  try {
    // Check marketplace installation
    const marketplaceInstalled = await checkMarketplaceInstalled(paths);
    if (!marketplaceInstalled) {
      console.log(chalk.yellow('⚠️  Marketplace not added yet\n'));
      console.log(chalk.gray('Run this command to add the marketplace:\n'));
      console.log(chalk.cyan(`   npx @intentsolutionsio/ccpi marketplace\n`));
      process.exit(1);
    }

    // Get installed plugins
    const installedPlugins = await getInstalledPlugins(paths);

    if (Object.keys(installedPlugins).length === 0) {
      console.log(chalk.yellow('⚠️  No plugins installed\n'));
      console.log(chalk.gray('Install plugins with:\n'));
      console.log(chalk.cyan('   npx @intentsolutionsio/ccpi install <plugin-name>\n'));
      return;
    }

    // Get catalog
    const catalog = await fetchCatalog();
    if (!catalog) {
      console.log(chalk.red('❌ Failed to fetch catalog\n'));
      process.exit(1);
    }

    // Find available updates
    const updates = findAvailableUpdates(installedPlugins, catalog.plugins);

    if (updates.length === 0) {
      console.log(chalk.green('✓ All plugins are up to date!\n'));
      showInstalledPlugins(installedPlugins);
      return;
    }

    // Handle different modes
    if (options.check) {
      await showAvailableUpdates(updates);
    } else if (options.all) {
      await guideUpgradeAll(updates);
    } else if (options.plugin) {
      await guideUpgradePlugin(options.plugin, updates);
    } else {
      // Default: show updates with guidance
      await showAvailableUpdates(updates);
      console.log(chalk.gray('\n💡 To upgrade:\n'));
      console.log(chalk.cyan('   npx @intentsolutionsio/ccpi upgrade --all'));
      console.log(chalk.gray('   (Updates all plugins)\n'));
      console.log(chalk.cyan('   npx @intentsolutionsio/ccpi upgrade --plugin <name>'));
      console.log(chalk.gray('   (Updates specific plugin)\n'));
    }

  } catch (error) {
    console.log(chalk.red('\n❌ Upgrade check failed\n'));
    if (error instanceof Error) {
      console.log(chalk.gray(error.message));
    }
    process.exit(1);
  }
}

/**
 * Check if marketplace is installed
 */
async function checkMarketplaceInstalled(paths: ClaudePaths): Promise<boolean> {
  const marketplacePath = path.join(paths.marketplacesDir, MARKETPLACE_SLUG);
  return existsSync(marketplacePath);
}

/**
 * Get installed plugins from Claude config
 */
async function getInstalledPlugins(paths: ClaudePaths): Promise<Record<string, InstalledPlugin>> {
  const installedPluginsPath = path.join(paths.configDir, 'plugins', 'installed_plugins.json');

  if (!existsSync(installedPluginsPath)) {
    return {};
  }

  try {
    const content = await fs.readFile(installedPluginsPath, 'utf-8');
    const data = JSON.parse(content);
    return data.plugins || {};
  } catch {
    return {};
  }
}

/**
 * Fetch catalog from GitHub
 */
async function fetchCatalog(): Promise<{ plugins: PluginMetadata[] } | null> {
  try {
    const response = await axios.get(CATALOG_URL);
    return response.data;
  } catch {
    return null;
  }
}

/**
 * Compare versions and find updates
 */
function findAvailableUpdates(
  installed: Record<string, InstalledPlugin>,
  catalog: PluginMetadata[]
): PluginUpdate[] {
  const updates: PluginUpdate[] = [];

  for (const [name, installedData] of Object.entries(installed)) {
    const catalogPlugin = catalog.find(p => p.name === name);

    if (!catalogPlugin) {
      continue; // Plugin not in catalog (might be from different marketplace)
    }

    if (isNewerVersion(catalogPlugin.version, installedData.version)) {
      updates.push({
        name,
        currentVersion: installedData.version,
        latestVersion: catalogPlugin.version,
        description: catalogPlugin.description,
      });
    }
  }

  return updates;
}

/**
 * Simple semver comparison (handles x.y.z format)
 */
function isNewerVersion(latest: string, current: string): boolean {
  const parseVersion = (v: string) => {
    const parts = v.replace(/^v/, '').split('.').map(Number);
    return { major: parts[0] || 0, minor: parts[1] || 0, patch: parts[2] || 0 };
  };

  const latestParsed = parseVersion(latest);
  const currentParsed = parseVersion(current);

  if (latestParsed.major > currentParsed.major) return true;
  if (latestParsed.major < currentParsed.major) return false;
  if (latestParsed.minor > currentParsed.minor) return true;
  if (latestParsed.minor < currentParsed.minor) return false;
  return latestParsed.patch > currentParsed.patch;
}

/**
 * Show available updates
 */
async function showAvailableUpdates(updates: PluginUpdate[]): Promise<void> {
  console.log(chalk.bold(`📦 ${updates.length} update(s) available:\n`));

  for (const update of updates) {
    console.log(chalk.cyan(`  ${update.name}`));
    console.log(chalk.gray(`    Current: ${update.currentVersion} → Latest: ${update.latestVersion}`));
    if (update.description) {
      console.log(chalk.gray(`    ${update.description}`));
    }
    console.log('');
  }
}

/**
 * Guide user to upgrade all plugins
 */
async function guideUpgradeAll(updates: PluginUpdate[]): Promise<void> {
  console.log(chalk.bold(`🚀 Upgrading ${updates.length} plugin(s)...\n`));

  console.log(chalk.gray('Follow these steps in Claude Code:\n'));

  for (let i = 0; i < updates.length; i++) {
    const update = updates[i];
    console.log(chalk.bold(`${i + 1}. ${update.name}`) + chalk.gray(` (${update.currentVersion} → ${update.latestVersion})`));
    console.log('');
    console.log(chalk.gray('   Step 1: Uninstall current version:'));
    console.log(chalk.cyan(`   /plugin uninstall ${update.name}@${MARKETPLACE_SLUG}`));
    console.log('');
    console.log(chalk.gray('   Step 2: Install latest version:'));
    console.log(chalk.cyan(`   /plugin install ${update.name}@${MARKETPLACE_SLUG}`));
    console.log('');
    console.log(chalk.gray('━'.repeat(60)));
  }

  console.log(chalk.gray('\n💡 Note: Claude Code currently requires manual uninstall + reinstall for upgrades'));
  console.log(chalk.gray('   A native /plugin upgrade command may be added in the future.\n'));

  console.log(chalk.bold('📋 Version Pinning:\n'));
  console.log(chalk.gray('To pin a plugin to a specific version, keep the current version installed.'));
  console.log(chalk.gray('Only upgrade when you\'re ready for the latest features.\n'));
}

/**
 * Guide user to upgrade specific plugin
 */
async function guideUpgradePlugin(pluginName: string, updates: PluginUpdate[]): Promise<void> {
  const update = updates.find(u => u.name === pluginName);

  if (!update) {
    console.log(chalk.yellow(`⚠️  No update available for "${pluginName}"\n`));
    console.log(chalk.gray('Plugin is either up to date or not installed.\n'));
    console.log(chalk.gray('Check all updates with:\n'));
    console.log(chalk.cyan('   npx @intentsolutionsio/ccpi upgrade --check\n'));
    return;
  }

  console.log(chalk.bold(`🚀 Upgrading ${update.name}...\n`));
  console.log(chalk.gray(`Current: ${update.currentVersion} → Latest: ${update.latestVersion}\n`));

  if (update.description) {
    console.log(chalk.gray(`${update.description}\n`));
  }

  console.log(chalk.bold('📋 Upgrade Steps:\n'));
  console.log(chalk.gray('Step 1: Uninstall current version:\n'));
  console.log(chalk.cyan(`   /plugin uninstall ${update.name}@${MARKETPLACE_SLUG}\n`));

  console.log(chalk.gray('Step 2: Install latest version:\n'));
  console.log(chalk.cyan(`   /plugin install ${update.name}@${MARKETPLACE_SLUG}\n`));

  console.log(chalk.gray('━'.repeat(60)));
  console.log(chalk.gray('💡 Tip: Your plugin configuration will be preserved'));
  console.log(chalk.gray('━'.repeat(60) + '\n'));
}

/**
 * Show currently installed plugins
 */
function showInstalledPlugins(installed: Record<string, InstalledPlugin>): void {
  const count = Object.keys(installed).length;
  console.log(chalk.gray(`📋 ${count} plugin(s) installed:\n`));

  for (const [name, data] of Object.entries(installed)) {
    console.log(chalk.cyan(`  ${name}`) + chalk.gray(` v${data.version}`));
  }
  console.log('');
}
