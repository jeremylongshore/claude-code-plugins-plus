import { Command } from 'commander';
import { detectClaudePaths } from './utils/paths.js';
import { installPlugin } from './commands/install.js';
import { upgradeCommand } from './commands/upgrade.js';
import { listPlugins } from './commands/list.js';
import { doctorCheck } from './commands/doctor.js';
import { marketplaceCommand, addMarketplace, removeMarketplace } from './commands/marketplace.js';
import { validateCommand } from './commands/validate.js';
import { getVersion } from './utils/version.js';
import chalk from 'chalk';
import ora from 'ora';

export function buildProgram() {
  const program = new Command();

  program
    .name('ccpi')
    .description('Claude Code Plugins - Install and manage plugins from claudecodeplugins.io')
    .version(getVersion());

  program
    .command('install [plugin]')
    .description('Install a plugin from the marketplace')
    .option('-y, --yes', 'Skip confirmation prompts')
    .option('--global', 'Install globally for all projects')
    .option('--all', 'Install ALL plugins from marketplace')
    .option('--skills', 'Install standalone skills (coming soon)')
    .option('--pack <name>', 'Install a plugin pack (devops, security, api, etc)')
    .option('--category <name>', 'Install all plugins in a category')
    .action(async (plugin: string | undefined, options) => {
      const spinner = ora('Detecting Claude Code installation...').start();

      try {
        const paths = await detectClaudePaths();
        spinner.succeed('Found Claude Code installation');

        await installPlugin(plugin, paths, options);
      } catch (error) {
        spinner.fail('Failed to detect Claude Code installation');
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        console.error(chalk.yellow('\nRun `ccpi doctor` for diagnostics'));
        process.exit(1);
      }
    });

  program
    .command('upgrade')
    .description('Check for and install plugin updates')
    .option('--check', 'Check for available updates without upgrading')
    .option('--all', 'Upgrade all plugins with available updates')
    .option('--plugin <name>', 'Upgrade a specific plugin')
    .action(async (options) => {
      try {
        const paths = await detectClaudePaths();
        await upgradeCommand(paths, options);
      } catch (error) {
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  program
    .command('list')
    .description('List installed plugins')
    .option('-a, --all', 'Show all available plugins (not just installed)')
    .action(async (options) => {
      try {
        const paths = await detectClaudePaths();
        await listPlugins(paths, options);
      } catch (error) {
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  program
    .command('doctor')
    .description('Run diagnostics on Claude Code installation and plugins')
    .option('--json', 'Output results as JSON')
    .action(async (options) => {
      await doctorCheck(options);
    });

  program
    .command('search <query>')
    .description('Search for plugins in the marketplace')
    .action(async (query: string) => {
      console.log(chalk.blue(`Searching marketplace for: ${query}`));
      console.log(chalk.yellow('🚧 Search functionality coming soon!'));
      console.log(chalk.gray('Visit https://claudecodeplugins.io to browse plugins'));
    });

  program
    .command('validate [path]')
    .description('Validate plugins, skills, and frontmatter')
    .option('--skills', 'Validate skills only')
    .option('--frontmatter', 'Validate frontmatter only')
    .option('--strict', 'Fail on warnings (for CI)')
    .option('--json', 'Output results as JSON')
    .action(async (targetPath: string | undefined, options) => {
      await validateCommand(targetPath, options);
    });

  program
    .command('analytics')
    .description('View plugin usage analytics')
    .option('--json', 'Output as JSON')
    .action(async () => {
      console.log(chalk.yellow('Analytics functionality coming soon!'));
      console.log(chalk.gray('This will show plugin usage, performance, and cost metrics'));
    });

  program
    .command('marketplace')
    .description('Manage marketplace connection')
    .option('--verify', 'Verify marketplace installation')
    .action(async (options) => {
      try {
        const paths = await detectClaudePaths();
        await marketplaceCommand(paths, options);
      } catch (error) {
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  program
    .command('marketplace-add')
    .description('Add the marketplace to Claude Code')
    .action(async () => {
      try {
        const paths = await detectClaudePaths();
        await addMarketplace(paths);
      } catch (error) {
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  program
    .command('marketplace-remove')
    .description('Remove the marketplace from Claude Code')
    .action(async () => {
      try {
        const paths = await detectClaudePaths();
        await removeMarketplace(paths);
      } catch (error) {
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  return program;
}

