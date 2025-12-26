import chalk from 'chalk';
import ora from 'ora';
import { promises as fs } from 'fs';
import { existsSync } from 'fs';
import * as path from 'path';
import axios from 'axios';
import type { ClaudePaths } from '../utils/paths.js';

export interface InstallOptions {
  yes?: boolean;
  global?: boolean;
  all?: boolean;
  skills?: boolean;
  pack?: string;
  category?: string;
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

// Known plugin packs (curated collections)
const PLUGIN_PACKS: Record<string, string[]> = {
  'devops': [
    'terraform-specialist', 'kubernetes-architect', 'deployment-engineer',
    'devops-troubleshooter', 'hybrid-cloud-architect', 'docker-pro'
  ],
  'security': [
    'security-auditor', 'backend-security-coder', 'frontend-security-coder',
    'mobile-security-coder'
  ],
  'api': [
    'backend-architect', 'graphql-architect', 'fastapi-pro'
  ],
  'ai-ml': [
    'ai-engineer', 'ml-engineer', 'mlops-engineer', 'prompt-engineer'
  ],
  'frontend': [
    'frontend-developer', 'flutter-expert', 'mobile-developer', 'ui-ux-designer'
  ],
  'backend': [
    'python-pro', 'golang-pro', 'rust-pro', 'java-pro', 'typescript-pro',
    'csharp-pro', 'ruby-pro', 'php-pro', 'elixir-pro', 'scala-pro'
  ],
  'database': [
    'database-optimizer', 'database-admin', 'sql-pro', 'data-engineer'
  ],
  'testing': [
    'test-automator', 'debugger', 'error-detective', 'performance-engineer'
  ],
};

/**
 * Install a plugin or plugins from the marketplace (guided flow)
 */
export async function installPlugin(
  pluginName: string | undefined,
  paths: ClaudePaths,
  options: InstallOptions
): Promise<void> {
  // Handle bulk install options
  if (options.all) {
    await installAllPlugins(paths, options);
    return;
  }

  if (options.skills) {
    await installSkills(paths, options);
    return;
  }

  if (options.pack) {
    await installPack(options.pack, paths, options);
    return;
  }

  if (options.category) {
    await installByCategory(options.category, paths, options);
    return;
  }

  // Single plugin install
  if (!pluginName) {
    console.log(chalk.red('Error: Plugin name required\n'));
    console.log(chalk.gray('Usage:'));
    console.log(chalk.cyan('  ccpi install <plugin-name>'));
    console.log(chalk.cyan('  ccpi install --all'));
    console.log(chalk.cyan('  ccpi install --pack devops'));
    console.log(chalk.cyan('  ccpi install --category security\n'));
    process.exit(1);
  }

  console.log(chalk.bold(`\nInstalling ${chalk.cyan(pluginName)}...\n`));

  try {
    // Step 1: Check if marketplace is added
    const marketplaceInstalled = await checkMarketplaceInstalled(paths);

    if (!marketplaceInstalled) {
      console.log(chalk.yellow('Marketplace not added yet\n'));
      await guideMarketplaceSetup();
      return;
    }

    // Step 2: Verify plugin exists in catalog
    const plugin = await findPluginInCatalog(pluginName);

    if (!plugin) {
      console.log(chalk.red(`Plugin "${pluginName}" not found in marketplace\n`));
      console.log(chalk.gray('Search for plugins:'));
      console.log(chalk.cyan(`   npx @intentsolutionsio/ccpi search ${pluginName}`));
      console.log(chalk.gray('\nBrowse all plugins:'));
      console.log(chalk.cyan('   https://claudecodeplugins.io\n'));
      process.exit(1);
    }

    // Step 3: Check if already installed
    const alreadyInstalled = await checkPluginInstalled(paths, pluginName);

    if (alreadyInstalled) {
      console.log(chalk.yellow(`${plugin.name} is already installed\n`));
      console.log(chalk.gray('To reinstall or upgrade:'));
      console.log(chalk.cyan(`   /plugin uninstall ${pluginName}@${MARKETPLACE_SLUG}`));
      console.log(chalk.cyan(`   /plugin install ${pluginName}@${MARKETPLACE_SLUG}\n`));
      return;
    }

    // Step 4: Guide installation
    await guidePluginInstall(plugin, options);

  } catch (error) {
    console.log(chalk.red('\nInstallation failed\n'));
    if (error instanceof Error) {
      console.log(chalk.gray(error.message));
    }
    process.exit(1);
  }
}

/**
 * Install ALL plugins from the marketplace
 */
async function installAllPlugins(paths: ClaudePaths, options: InstallOptions): Promise<void> {
  console.log(chalk.bold('\nInstall All Plugins\n'));

  const spinner = ora('Fetching catalog...').start();

  try {
    const catalog = await fetchCatalog();
    if (!catalog) {
      spinner.fail('Failed to fetch catalog');
      process.exit(1);
    }

    const plugins = catalog.plugins || [];
    spinner.succeed(`Found ${plugins.length} plugins`);

    console.log(chalk.yellow(`\nThis will install ALL ${plugins.length} plugins.\n`));
    console.log(chalk.gray('Run these commands in Claude Code:\n'));

    // Group by category for better organization
    const byCategory: Record<string, PluginMetadata[]> = {};
    for (const plugin of plugins) {
      const cat = plugin.category || 'other';
      if (!byCategory[cat]) {
        byCategory[cat] = [];
      }
      byCategory[cat].push(plugin);
    }

    const scope = options.global ? '--global' : '--project';

    // Show commands grouped by category
    for (const [category, categoryPlugins] of Object.entries(byCategory)) {
      console.log(chalk.bold.blue(`\n${category} (${categoryPlugins.length}):`));
      for (const plugin of categoryPlugins) {
        console.log(chalk.cyan(`  /plugin install ${plugin.name}@${MARKETPLACE_SLUG} ${scope}`));
      }
    }

    console.log(chalk.gray('\n' + '━'.repeat(60)));
    console.log(chalk.yellow('\nNote: This is a guided install - run each command in Claude Code'));
    console.log(chalk.gray('━'.repeat(60) + '\n'));

  } catch (error) {
    spinner.fail('Failed to fetch catalog');
    console.error(chalk.red(error instanceof Error ? error.message : String(error)));
    process.exit(1);
  }
}

/**
 * Install standalone skills (future feature)
 */
async function installSkills(_paths: ClaudePaths, _options: InstallOptions): Promise<void> {
  console.log(chalk.bold('\nInstall Standalone Skills\n'));
  console.log(chalk.yellow('Standalone skills installation coming soon!\n'));
  console.log(chalk.gray('Currently, skills are bundled with plugins.'));
  console.log(chalk.gray('The 500 Standalone Skills Initiative is in development.\n'));
  console.log(chalk.gray('For now, install plugins to get their skills:'));
  console.log(chalk.cyan('  ccpi install <plugin-name>\n'));
}

/**
 * Install a plugin pack
 */
async function installPack(packName: string, paths: ClaudePaths, options: InstallOptions): Promise<void> {
  console.log(chalk.bold(`\nInstalling Pack: ${packName}\n`));

  const packPlugins = PLUGIN_PACKS[packName.toLowerCase()];

  if (!packPlugins) {
    console.log(chalk.red(`Unknown pack: ${packName}\n`));
    console.log(chalk.gray('Available packs:'));
    for (const [name, plugins] of Object.entries(PLUGIN_PACKS)) {
      console.log(chalk.cyan(`  ${name}`) + chalk.gray(` (${plugins.length} plugins)`));
    }
    console.log('');
    process.exit(1);
  }

  console.log(chalk.gray(`This pack includes ${packPlugins.length} plugins:\n`));

  const scope = options.global ? '--global' : '--project';

  for (const pluginName of packPlugins) {
    console.log(chalk.cyan(`  /plugin install ${pluginName}@${MARKETPLACE_SLUG} ${scope}`));
  }

  console.log(chalk.gray('\n' + '━'.repeat(60)));
  console.log(chalk.gray('Run these commands in Claude Code to install the pack'));
  console.log(chalk.gray('━'.repeat(60) + '\n'));
}

/**
 * Install plugins by category
 */
async function installByCategory(category: string, paths: ClaudePaths, options: InstallOptions): Promise<void> {
  console.log(chalk.bold(`\nInstalling Category: ${category}\n`));

  const spinner = ora('Fetching catalog...').start();

  try {
    const catalog = await fetchCatalog();
    if (!catalog) {
      spinner.fail('Failed to fetch catalog');
      process.exit(1);
    }

    const plugins = (catalog.plugins || []).filter(
      (p: PluginMetadata) => p.category?.toLowerCase() === category.toLowerCase()
    );

    if (plugins.length === 0) {
      spinner.fail(`No plugins found in category: ${category}`);

      // Show available categories
      const categories = new Set<string>();
      for (const p of catalog.plugins || []) {
        if (p.category) {
          categories.add(p.category);
        }
      }

      console.log(chalk.gray('\nAvailable categories:'));
      for (const cat of Array.from(categories).sort()) {
        const count = (catalog.plugins || []).filter((p: PluginMetadata) => p.category === cat).length;
        console.log(chalk.cyan(`  ${cat}`) + chalk.gray(` (${count} plugins)`));
      }
      console.log('');
      process.exit(1);
    }

    spinner.succeed(`Found ${plugins.length} plugins in ${category}`);

    const scope = options.global ? '--global' : '--project';

    console.log(chalk.gray('\nRun these commands in Claude Code:\n'));
    for (const plugin of plugins) {
      console.log(chalk.cyan(`  /plugin install ${plugin.name}@${MARKETPLACE_SLUG} ${scope}`));
    }

    console.log(chalk.gray('\n' + '━'.repeat(60)));
    console.log(chalk.gray('Run these commands in Claude Code to install'));
    console.log(chalk.gray('━'.repeat(60) + '\n'));

  } catch (error) {
    spinner.fail('Failed to fetch catalog');
    console.error(chalk.red(error instanceof Error ? error.message : String(error)));
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
 * Fetch full catalog
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
 * Guide user through marketplace setup
 */
async function guideMarketplaceSetup(): Promise<void> {
  console.log(chalk.bold('First-time setup required\n'));
  console.log(chalk.gray('The Claude Code Plugins marketplace needs to be added to your Claude installation.\n'));

  console.log(chalk.bold('Step 1: Add Marketplace\n'));
  console.log(chalk.gray('Open Claude Code and run this command:\n'));
  console.log(chalk.cyan(`   /plugin marketplace add ${MARKETPLACE_REPO}\n`));

  console.log(chalk.gray('This will add access to all 259 plugins from https://claudecodeplugins.io\n'));

  console.log(chalk.bold('After adding the marketplace:\n'));
  console.log(chalk.gray('Run this command again to install your plugin:\n'));
  console.log(chalk.cyan(`   npx @intentsolutionsio/ccpi install <plugin-name>\n`));

  console.log(chalk.gray('━'.repeat(60)));
  console.log(chalk.gray('Tip: You only need to add the marketplace once!'));
  console.log(chalk.gray('━'.repeat(60) + '\n'));
}

/**
 * Guide user through plugin installation
 */
async function guidePluginInstall(plugin: PluginMetadata, options: InstallOptions): Promise<void> {
  console.log(chalk.green('Found: ') + chalk.cyan(plugin.name) + chalk.gray(` v${plugin.version}`));

  if (plugin.description) {
    console.log(chalk.gray(`  ${plugin.description}\n`));
  }

  console.log(chalk.bold('Installation Command:\n'));
  console.log(chalk.gray('Open Claude Code and run:\n'));

  const scope = options.global ? '--global' : '--project';
  const installCmd = `/plugin install ${plugin.name}@${MARKETPLACE_SLUG} ${scope}`;

  console.log(chalk.cyan(`   ${installCmd}\n`));

  console.log(chalk.gray('━'.repeat(60)));
  console.log(chalk.gray('Scope explanation:'));
  console.log(chalk.gray('  --global  : Available in all projects'));
  console.log(chalk.gray('  --project : Only available in current project'));
  console.log(chalk.gray('━'.repeat(60) + '\n'));

  console.log(chalk.bold('After Installation:\n'));
  console.log(chalk.gray('1. Plugin will be immediately available in Claude Code'));
  console.log(chalk.gray('2. Check for slash commands with:') + chalk.cyan(' /help'));
  console.log(chalk.gray('3. View plugin details:') + chalk.cyan(' /plugin list\n'));

  if (plugin.category) {
    console.log(chalk.gray(`Category: ${plugin.category}\n`));
  }

  console.log(chalk.bold('Verification:\n'));
  console.log(chalk.gray('After installation, verify with:\n'));
  console.log(chalk.cyan(`   npx @intentsolutionsio/ccpi doctor\n`));

  console.log(chalk.gray('━'.repeat(60)));
  console.log(chalk.green('Ready to install!'));
  console.log(chalk.gray('━'.repeat(60) + '\n'));
}
