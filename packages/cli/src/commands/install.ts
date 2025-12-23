import chalk from 'chalk';
import ora from 'ora';
import * as fs from 'fs-extra';
import * as path from 'path';
import axios from 'axios';
import type { ClaudePaths } from '../utils/paths.js';
import { getMarketplaceCatalogPath, isMarketplaceInstalled } from '../utils/paths.js';

interface InstallOptions {
  yes?: boolean;
  global?: boolean;
}

interface PluginMetadata {
  name: string;
  version: string;
  description: string;
  author: string;
}

/**
 * Install a plugin from the marketplace
 */
export async function installPlugin(
  pluginName: string,
  paths: ClaudePaths,
  options: InstallOptions
): Promise<void> {
  const spinner = ora(`Installing ${chalk.cyan(pluginName)}...`).start();

  try {
    // Check if marketplace is installed
    if (!await isMarketplaceInstalled(paths)) {
      spinner.warn('Marketplace not found locally');
      console.log(chalk.yellow('\nInstalling marketplace first...'));
      await installMarketplace(paths);
    }

    // Load marketplace catalog
    const catalogPath = getMarketplaceCatalogPath(paths);
    const catalog = await fs.readJSON(catalogPath);

    // Find plugin in catalog
    const plugin = catalog.plugins?.find((p: PluginMetadata) => p.name === pluginName);

    if (!plugin) {
      spinner.fail(`Plugin ${chalk.red(pluginName)} not found in marketplace`);
      console.log(chalk.gray('\nRun `ccp search <query>` to find available plugins'));
      console.log(chalk.gray('Or visit https://claudecodeplugins.io'));
      process.exit(1);
    }

    spinner.text = `Installing ${chalk.cyan(plugin.name)} v${plugin.version}...`;

    // Determine installation directory
    const installDir = options.global || !paths.projectPluginDir
      ? path.join(paths.pluginsDir, pluginName)
      : path.join(paths.projectPluginDir, 'plugins', pluginName);

    // Check if already installed
    if (await fs.pathExists(installDir)) {
      spinner.warn(`${plugin.name} is already installed`);

      if (!options.yes) {
        console.log(chalk.yellow('\nUse `ccp upgrade` to update existing plugins'));
      }

      return;
    }

    // Copy plugin files from marketplace
    const marketplacePluginPath = path.join(
      paths.marketplacesDir,
      'claude-code-plugins-plus',
      'plugins'
    );

    // Find plugin directory (could be in any category)
    const pluginSource = await findPluginInMarketplace(marketplacePluginPath, pluginName);

    if (!pluginSource) {
      spinner.fail(`Plugin source files not found for ${pluginName}`);
      process.exit(1);
    }

    // Copy plugin files
    await fs.ensureDir(path.dirname(installDir));
    await fs.copy(pluginSource, installDir);

    spinner.succeed(`${chalk.green('✓')} Installed ${chalk.cyan(plugin.name)} v${plugin.version}`);

    console.log(chalk.gray(`\nInstalled to: ${installDir}`));

    if (plugin.description) {
      console.log(chalk.gray(`Description: ${plugin.description}`));
    }

    console.log(chalk.blue('\n📚 Usage:'));
    console.log(chalk.gray('  Plugin is now available in Claude Code'));
    console.log(chalk.gray('  Check the plugin README for specific commands and features'));

  } catch (error) {
    spinner.fail('Installation failed');
    throw error;
  }
}

/**
 * Install the marketplace catalog from GitHub
 */
async function installMarketplace(paths: ClaudePaths): Promise<void> {
  const spinner = ora('Downloading marketplace catalog...').start();

  try {
    const marketplaceDir = path.join(paths.marketplacesDir, 'claude-code-plugins-plus');

    // Clone or download marketplace
    // For now, we'll download the catalog JSON directly
    const catalogUrl = 'https://raw.githubusercontent.com/jeremylongshore/claude-code-plugins/main/.claude-plugin/marketplace.json';

    const response = await axios.get(catalogUrl);

    await fs.ensureDir(path.join(marketplaceDir, '.claude-plugin'));
    await fs.writeJSON(
      getMarketplaceCatalogPath(paths),
      response.data,
      { spaces: 2 }
    );

    spinner.succeed('Marketplace catalog installed');
  } catch (error) {
    spinner.fail('Failed to install marketplace');
    throw error;
  }
}

/**
 * Find plugin directory in marketplace (search across categories)
 */
async function findPluginInMarketplace(
  marketplacePluginsPath: string,
  pluginName: string
): Promise<string | null> {
  try {
    // Check if marketplace plugins directory exists
    if (!await fs.pathExists(marketplacePluginsPath)) {
      return null;
    }

    // Search through category directories
    const categories = await fs.readdir(marketplacePluginsPath);

    for (const category of categories) {
      const categoryPath = path.join(marketplacePluginsPath, category);
      const stats = await fs.stat(categoryPath);

      if (stats.isDirectory()) {
        const pluginPath = path.join(categoryPath, pluginName);

        if (await fs.pathExists(pluginPath)) {
          return pluginPath;
        }
      }
    }

    return null;
  } catch {
    return null;
  }
}
