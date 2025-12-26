import chalk from 'chalk';
import * as fs from 'fs-extra';
import * as path from 'path';
import type { ClaudePaths } from '../utils/paths.js';
import { getMarketplaceCatalogPath, isMarketplaceInstalled } from '../utils/paths.js';

interface ListOptions {
  all?: boolean;
}

interface PluginInfo {
  name: string;
  version: string;
  description?: string;
  installed: boolean;
  location?: string;
}

/**
 * List installed plugins or all available plugins
 */
export async function listPlugins(
  paths: ClaudePaths,
  options: ListOptions
): Promise<void> {
  if (options.all) {
    await listAllPlugins(paths);
  } else {
    await listInstalledPlugins(paths);
  }
}

/**
 * List installed plugins
 */
async function listInstalledPlugins(paths: ClaudePaths): Promise<void> {
  const plugins: PluginInfo[] = [];

  // Check global plugins directory
  if (await fs.pathExists(paths.pluginsDir)) {
    const globalPlugins = await getPluginsFromDir(paths.pluginsDir, 'global');
    plugins.push(...globalPlugins);
  }

  // Check project-local plugins
  if (paths.projectPluginDir) {
    const localPluginsDir = path.join(paths.projectPluginDir, 'plugins');
    if (await fs.pathExists(localPluginsDir)) {
      const localPlugins = await getPluginsFromDir(localPluginsDir, 'local');
      plugins.push(...localPlugins);
    }
  }

  if (plugins.length === 0) {
    console.log(chalk.yellow('No plugins installed'));
    console.log(chalk.gray('\nRun `ccpi install <plugin>` to install a plugin'));
    console.log(chalk.gray('Or visit https://claudecodeplugins.io to browse'));
    return;
  }

  console.log(chalk.bold('\nInstalled Plugins:\n'));

  for (const plugin of plugins) {
    console.log(chalk.cyan(`  ${plugin.name}`) + chalk.gray(` v${plugin.version}`));

    if (plugin.description) {
      console.log(chalk.gray(`    ${plugin.description}`));
    }

    console.log(chalk.gray(`    Location: ${plugin.location}\n`));
  }

  console.log(chalk.gray(`Total: ${plugins.length} plugin${plugins.length === 1 ? '' : 's'}`));
}

/**
 * List all available plugins from marketplace
 */
async function listAllPlugins(paths: ClaudePaths): Promise<void> {
  if (!await isMarketplaceInstalled(paths)) {
    console.log(chalk.yellow('Marketplace catalog not installed'));
    console.log(chalk.gray('Run `ccpi install <plugin>` to install the marketplace first'));
    return;
  }

  const catalogPath = getMarketplaceCatalogPath(paths);
  const catalog = await fs.readJSON(catalogPath);

  const plugins = catalog.plugins || [];

  console.log(chalk.bold(`\nAvailable Plugins (${plugins.length}):\n`));

  // Group by category if available
  const categorized: Record<string, any[]> = {};

  for (const plugin of plugins) {
    const category = plugin.category || 'Other';
    if (!categorized[category]) {
      categorized[category] = [];
    }
    categorized[category].push(plugin);
  }

  for (const [category, categoryPlugins] of Object.entries(categorized)) {
    console.log(chalk.bold.blue(`\n${category}:`));

    for (const plugin of categoryPlugins) {
      console.log(chalk.cyan(`  ${plugin.name}`) + chalk.gray(` v${plugin.version}`));

      if (plugin.description) {
        console.log(chalk.gray(`    ${plugin.description}`));
      }
    }
  }

  console.log(chalk.gray(`\n\nTotal: ${plugins.length} plugins available`));
  console.log(chalk.gray('Visit https://claudecodeplugins.io for more details'));
}

/**
 * Get plugins from a directory
 */
async function getPluginsFromDir(
  dir: string,
  location: string
): Promise<PluginInfo[]> {
  const plugins: PluginInfo[] = [];

  try {
    const entries = await fs.readdir(dir);

    for (const entry of entries) {
      const pluginDir = path.join(dir, entry);
      const stats = await fs.stat(pluginDir);

      if (stats.isDirectory()) {
        const pluginJsonPath = path.join(pluginDir, '.claude-plugin', 'plugin.json');

        if (await fs.pathExists(pluginJsonPath)) {
          try {
            const metadata = await fs.readJSON(pluginJsonPath);

            plugins.push({
              name: metadata.name || entry,
              version: metadata.version || 'unknown',
              description: metadata.description,
              installed: true,
              location,
            });
          } catch {
            // Skip invalid plugin.json files
          }
        }
      }
    }
  } catch {
    // Directory doesn't exist or can't be read
  }

  return plugins;
}
