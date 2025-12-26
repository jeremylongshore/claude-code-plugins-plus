import chalk from 'chalk';
import { existsSync } from 'fs';
import * as path from 'path';
import type { ClaudePaths } from '../utils/paths.js';

const MARKETPLACE_REPO = 'jeremylongshore/claude-code-plugins';
const MARKETPLACE_SLUG = 'claude-code-plugins-plus';

interface MarketplaceOptions {
  verify?: boolean;
}

/**
 * Guide user through marketplace setup
 */
export async function marketplaceCommand(
  paths: ClaudePaths,
  options: MarketplaceOptions
): Promise<void> {
  console.log(chalk.bold('\n📦 Claude Code Plugins Marketplace\n'));

  // Check if marketplace is already added
  const marketplacePath = path.join(paths.marketplacesDir, MARKETPLACE_SLUG);
  const isInstalled = existsSync(marketplacePath);

  if (isInstalled) {
    console.log(chalk.green('✓ Marketplace is already added!\n'));

    if (options.verify) {
      await verifyMarketplace(paths);
    } else {
      showMarketplaceInfo(true);
    }
  } else {
    console.log(chalk.yellow('⚠️  Marketplace not added yet\n'));
    showMarketplaceSetupGuide();
  }
}

/**
 * Verify marketplace installation and show status
 */
async function verifyMarketplace(paths: ClaudePaths): Promise<void> {
  console.log(chalk.bold('🔍 Marketplace Status:\n'));

  const marketplacePath = path.join(paths.marketplacesDir, MARKETPLACE_SLUG);
  const catalogPath = path.join(marketplacePath, '.claude-plugin', 'marketplace.json');

  console.log(chalk.gray('Installation:'));
  console.log(chalk.green('  ✓') + chalk.gray(' Marketplace added'));
  console.log(chalk.gray(`  Location: ${marketplacePath}\n`));

  // Check for catalog file
  if (existsSync(catalogPath)) {
    console.log(chalk.green('  ✓') + chalk.gray(' Catalog found'));
    console.log(chalk.gray(`  File: ${catalogPath}\n`));
  } else {
    console.log(chalk.yellow('  ⚠') + chalk.gray(' Catalog not found'));
    console.log(chalk.gray('  Try refreshing the marketplace\n'));
  }

  console.log(chalk.bold('📚 Available Commands:\n'));
  console.log(chalk.cyan('  ccpi search <query>') + chalk.gray('  - Search for plugins'));
  console.log(chalk.cyan('  ccpi install <name>') + chalk.gray('  - Install a plugin'));
  console.log(chalk.cyan('  ccpi list') + chalk.gray('            - List installed plugins'));
  console.log(chalk.cyan('  ccpi doctor') + chalk.gray('          - System diagnostics\n'));
}

/**
 * Show marketplace setup guide
 */
function showMarketplaceSetupGuide(): void {
  console.log(chalk.bold('📋 Setup Instructions:\n'));
  console.log(chalk.gray('1. Open Claude Code (terminal or desktop app)'));
  console.log(chalk.gray('2. Run this command:\n'));

  console.log(chalk.cyan(`   /plugin marketplace add ${MARKETPLACE_REPO}\n`));

  console.log(chalk.gray('3. Wait for confirmation (usually < 5 seconds)'));
  console.log(chalk.gray('4. Verify installation:\n'));

  console.log(chalk.cyan('   npx @intentsolutionsio/ccpi marketplace --verify\n'));

  console.log(chalk.gray('━'.repeat(60)));
  console.log(chalk.gray('💡 This gives you access to 258 plugins!'));
  console.log(chalk.gray('━'.repeat(60) + '\n'));

  showMarketplaceInfo(false);
}

/**
 * Show general marketplace information
 */
function showMarketplaceInfo(isInstalled: boolean): void {
  console.log(chalk.bold('ℹ️  About This Marketplace:\n'));

  console.log(chalk.gray('Repository:  ') + chalk.cyan(MARKETPLACE_REPO));
  console.log(chalk.gray('Slug:        ') + chalk.cyan(MARKETPLACE_SLUG));
  console.log(chalk.gray('Website:     ') + chalk.cyan('https://claudecodeplugins.io'));
  console.log(chalk.gray('Plugins:     ') + chalk.cyan('258 across 18 categories\n'));

  console.log(chalk.bold('📂 Plugin Categories:\n'));
  console.log(chalk.gray('  • Productivity  • Security      • DevOps'));
  console.log(chalk.gray('  • AI/ML         • Database      • API Development'));
  console.log(chalk.gray('  • Crypto        • Finance       • Performance'));
  console.log(chalk.gray('  • Business      • Life Sciences • MCP Servers'));
  console.log(chalk.gray('  • Google Cloud  • Vertex AI     • Firebase Genkit\n'));

  if (isInstalled) {
    console.log(chalk.bold('🚀 Next Steps:\n'));
    console.log(chalk.gray('1. Search for plugins:  ') + chalk.cyan('ccpi search <keyword>'));
    console.log(chalk.gray('2. Install a plugin:    ') + chalk.cyan('ccpi install <name>'));
    console.log(chalk.gray('3. Browse all plugins:  ') + chalk.cyan('https://claudecodeplugins.io\n'));
  } else {
    console.log(chalk.bold('🚀 After Setup:\n'));
    console.log(chalk.gray('Run `ccpi search <keyword>` to find plugins'));
    console.log(chalk.gray('Run `ccpi install <name>` to install them\n'));
  }
}

/**
 * Add marketplace command (wrapper around native Claude command)
 */
export async function addMarketplace(paths: ClaudePaths): Promise<void> {
  console.log(chalk.bold('\n📦 Adding Claude Code Plugins Marketplace\n'));

  // Check if already added
  const marketplacePath = path.join(paths.marketplacesDir, MARKETPLACE_SLUG);
  if (existsSync(marketplacePath)) {
    console.log(chalk.green('✓ Marketplace is already added!\n'));
    console.log(chalk.gray('Run:') + chalk.cyan(' ccpi marketplace --verify') + chalk.gray(' to check status\n'));
    return;
  }

  showMarketplaceSetupGuide();
}

/**
 * Remove marketplace command (wrapper)
 */
export async function removeMarketplace(paths: ClaudePaths): Promise<void> {
  console.log(chalk.bold('\n📦 Removing Claude Code Plugins Marketplace\n'));

  const marketplacePath = path.join(paths.marketplacesDir, MARKETPLACE_SLUG);
  if (!existsSync(marketplacePath)) {
    console.log(chalk.yellow('⚠️  Marketplace is not currently added\n'));
    return;
  }

  console.log(chalk.gray('To remove the marketplace, run this command in Claude Code:\n'));
  console.log(chalk.cyan(`   /plugin marketplace remove ${MARKETPLACE_SLUG}\n`));

  console.log(chalk.gray('━'.repeat(60)));
  console.log(chalk.yellow('⚠️  Warning: This will not uninstall plugins'));
  console.log(chalk.gray('Installed plugins will remain until manually removed'));
  console.log(chalk.gray('━'.repeat(60) + '\n'));
}
