import chalk from 'chalk';
import ora from 'ora';
import { promises as fs } from 'fs';
import { existsSync } from 'fs';
import * as path from 'path';
import axios from 'axios';
import { exec } from 'child_process';
import { promisify } from 'util';
import type { ClaudePaths } from '../utils/paths.js';

const execAsync = promisify(exec);

interface InstallOptions {
  yes?: boolean;
  global?: boolean;
}

interface PluginMetadata {
  name: string;
  version: string;
  description: string;
  author: string;
  category?: string;
}

const MARKETPLACE_REPO = 'jeremylongshore/claude-code-plugins';
const MARKETPLACE_SLUG = 'claude-code-plugins-plus';
const CATALOG_URL = 'https://raw.githubusercontent.com/jeremylongshore/claude-code-plugins/main/.claude-plugin/marketplace.json';

/**
 * Install a plugin from the marketplace (guided flow)
 */
export async function installPlugin(
  pluginName: string,
  paths: ClaudePaths,
  options: InstallOptions
): Promise<void> {
  console.log(chalk.bold(`\n🔍 Installing ${chalk.cyan(pluginName)}...\n`));

  try {
    // Step 1: Check if marketplace is added
    const marketplaceInstalled = await checkMarketplaceInstalled(paths);

    if (!marketplaceInstalled) {
      console.log(chalk.yellow('⚠️  Marketplace not added yet\n'));
      await guideMarketplaceSetup(paths);
      return;
    }

    // Step 2: Verify plugin exists in catalog
    const plugin = await findPluginInCatalog(pluginName);

    if (!plugin) {
      console.log(chalk.red(`❌ Plugin "${pluginName}" not found in marketplace\n`));
      console.log(chalk.gray('💡 Search for plugins:'));
      console.log(chalk.cyan(`   npx @claude-code-plugins/ccp search ${pluginName}`));
      console.log(chalk.gray('\n📚 Browse all plugins:'));
      console.log(chalk.cyan('   https://claudecodeplugins.io\n'));
      process.exit(1);
    }

    // Step 3: Check if already installed
    const alreadyInstalled = await checkPluginInstalled(paths, pluginName);

    if (alreadyInstalled) {
      console.log(chalk.yellow(`⚠️  ${plugin.name} is already installed\n`));
      console.log(chalk.gray('💡 To reinstall or upgrade:'));
      console.log(chalk.cyan(`   /plugin uninstall ${pluginName}@${MARKETPLACE_SLUG}`));
      console.log(chalk.cyan(`   /plugin install ${pluginName}@${MARKETPLACE_SLUG}\n`));
      return;
    }

    // Step 4: Guide installation
    await guidePluginInstall(plugin, options);

  } catch (error) {
    console.log(chalk.red('\n❌ Installation failed\n'));
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
 * Check if plugin is already installed
 */
async function checkPluginInstalled(paths: ClaudePaths, pluginName: string): Promise<boolean> {
  const installedPluginsPath = path.join(paths.configDir, 'plugins', 'installed_plugins.json');

  if (!existsSync(installedPluginsPath)) {
    return false;
  }

  try {
    const content = await fs.readFile(installedPluginsPath, 'utf-8');
    const data = JSON.parse(content);

    if (!data.plugins) {
      return false;
    }

    // Check if plugin exists in registry
    return pluginName in data.plugins;
  } catch {
    return false;
  }
}

/**
 * Find plugin in online catalog
 */
async function findPluginInCatalog(pluginName: string): Promise<PluginMetadata | null> {
  try {
    const response = await axios.get(CATALOG_URL);
    const catalog = response.data;

    const plugin = catalog.plugins?.find((p: PluginMetadata) => p.name === pluginName);
    return plugin || null;
  } catch {
    return null;
  }
}

/**
 * Guide user through marketplace setup
 */
async function guideMarketplaceSetup(paths: ClaudePaths): Promise<void> {
  console.log(chalk.bold('📦 First-time setup required\n'));
  console.log(chalk.gray('The Claude Code Plugins marketplace needs to be added to your Claude installation.\n'));

  console.log(chalk.bold('📋 Step 1: Add Marketplace\n'));
  console.log(chalk.gray('Open Claude Code and run this command:\n'));
  console.log(chalk.cyan(`   /plugin marketplace add ${MARKETPLACE_REPO}\n`));

  console.log(chalk.gray('This will add access to all 258 plugins from https://claudecodeplugins.io\n'));

  console.log(chalk.bold('✅ After adding the marketplace:\n'));
  console.log(chalk.gray('Run this command again to install your plugin:\n'));
  console.log(chalk.cyan(`   npx @claude-code-plugins/ccp install <plugin-name>\n`));

  console.log(chalk.gray('━'.repeat(60)));
  console.log(chalk.gray('💡 Tip: You only need to add the marketplace once!'));
  console.log(chalk.gray('━'.repeat(60) + '\n'));
}

/**
 * Guide user through plugin installation
 */
async function guidePluginInstall(plugin: PluginMetadata, options: InstallOptions): Promise<void> {
  console.log(chalk.green('✓') + chalk.gray(' Found: ') + chalk.cyan(plugin.name) + chalk.gray(` v${plugin.version}`));

  if (plugin.description) {
    console.log(chalk.gray(`  ${plugin.description}\n`));
  }

  console.log(chalk.bold('📋 Installation Command:\n'));
  console.log(chalk.gray('Open Claude Code and run:\n'));

  const scope = options.global ? '--global' : '--project';
  const installCmd = `/plugin install ${plugin.name}@${MARKETPLACE_SLUG} ${scope}`;

  console.log(chalk.cyan(`   ${installCmd}\n`));

  console.log(chalk.gray('━'.repeat(60)));
  console.log(chalk.gray('Scope explanation:'));
  console.log(chalk.gray('  --global  : Available in all projects'));
  console.log(chalk.gray('  --project : Only available in current project'));
  console.log(chalk.gray('━'.repeat(60) + '\n'));

  console.log(chalk.bold('📚 After Installation:\n'));
  console.log(chalk.gray('1. Plugin will be immediately available in Claude Code'));
  console.log(chalk.gray('2. Check for slash commands with:') + chalk.cyan(' /help'));
  console.log(chalk.gray('3. View plugin details:') + chalk.cyan(' /plugin list\n'));

  if (plugin.category) {
    console.log(chalk.gray(`📂 Category: ${plugin.category}\n`));
  }

  console.log(chalk.bold('🔍 Verification:\n'));
  console.log(chalk.gray('After installation, verify with:\n'));
  console.log(chalk.cyan(`   npx @claude-code-plugins/ccp doctor\n`));

  console.log(chalk.gray('━'.repeat(60)));
  console.log(chalk.green('✨ Ready to install!'));
  console.log(chalk.gray('━'.repeat(60) + '\n'));
}
