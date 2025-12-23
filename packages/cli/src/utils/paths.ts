import * as os from 'os';
import * as path from 'path';
import * as fs from 'fs-extra';

export interface ClaudePaths {
  configDir: string;
  pluginsDir: string;
  marketplacesDir: string;
  projectPluginDir?: string;
}

/**
 * Detect Claude Code installation paths across platforms
 * Supports Linux, macOS, and Windows
 */
export async function detectClaudePaths(): Promise<ClaudePaths> {
  const homeDir = os.homedir();
  const platform = os.platform();

  let configDir: string;

  // Detect global Claude config directory
  if (platform === 'win32') {
    configDir = path.join(homeDir, 'AppData', 'Roaming', 'Claude');
  } else {
    // Linux and macOS
    configDir = path.join(homeDir, '.claude');
  }

  // Verify config directory exists
  if (!await fs.pathExists(configDir)) {
    throw new Error(
      `Claude Code config directory not found at ${configDir}. ` +
      'Please ensure Claude Code is installed and has been run at least once.'
    );
  }

  const pluginsDir = path.join(configDir, 'plugins');
  const marketplacesDir = path.join(configDir, 'marketplaces');

  // Ensure directories exist
  await fs.ensureDir(pluginsDir);
  await fs.ensureDir(marketplacesDir);

  // Check for project-local plugin directory (.claude-plugin/)
  let projectPluginDir: string | undefined;
  const cwd = process.cwd();
  const localPluginDir = path.join(cwd, '.claude-plugin');

  if (await fs.pathExists(localPluginDir)) {
    projectPluginDir = localPluginDir;
  }

  return {
    configDir,
    pluginsDir,
    marketplacesDir,
    projectPluginDir,
  };
}

/**
 * Get the marketplace catalog path for claude-code-plugins-plus
 */
export function getMarketplaceCatalogPath(paths: ClaudePaths): string {
  return path.join(
    paths.marketplacesDir,
    'claude-code-plugins-plus',
    '.claude-plugin',
    'marketplace.json'
  );
}

/**
 * Check if the marketplace catalog is installed
 */
export async function isMarketplaceInstalled(paths: ClaudePaths): Promise<boolean> {
  const catalogPath = getMarketplaceCatalogPath(paths);
  return await fs.pathExists(catalogPath);
}
