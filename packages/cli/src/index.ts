#!/usr/bin/env node

import { Command } from 'commander';
import chalk from 'chalk';
import ora from 'ora';
import { detectClaudePaths } from './utils/paths.js';
import { installPlugin } from './commands/install.js';
import { listPlugins } from './commands/list.js';
import { doctorCheck } from './commands/doctor.js';
import { getVersion } from './utils/version.js';

const program = new Command();

program
  .name('ccp')
  .description('Claude Code Plugins - Install and manage plugins from claudecodeplugins.io')
  .version(getVersion());

// Install command
program
  .command('install <plugin>')
  .description('Install a plugin from the marketplace')
  .option('-y, --yes', 'Skip confirmation prompts')
  .option('--global', 'Install globally for all projects')
  .action(async (plugin: string, options) => {
    const spinner = ora('Detecting Claude Code installation...').start();

    try {
      const paths = await detectClaudePaths();
      spinner.succeed('Found Claude Code installation');

      await installPlugin(plugin, paths, options);
    } catch (error) {
      spinner.fail('Failed to detect Claude Code installation');
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      console.error(chalk.yellow('\nRun `ccp doctor` for diagnostics'));
      process.exit(1);
    }
  });

// List command
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

// Doctor command
program
  .command('doctor')
  .description('Run diagnostics on Claude Code installation and plugins')
  .option('--json', 'Output results as JSON')
  .action(async (options) => {
    await doctorCheck(options);
  });

// Search command
program
  .command('search <query>')
  .description('Search for plugins in the marketplace')
  .action(async (query: string) => {
    console.log(chalk.blue(`Searching marketplace for: ${query}`));
    console.log(chalk.yellow('🚧 Search functionality coming soon!'));
    console.log(chalk.gray('Visit https://claudecodeplugins.io to browse plugins'));
  });

// Analytics command (placeholder for Epic C)
program
  .command('analytics')
  .description('View plugin usage analytics')
  .option('--json', 'Output as JSON')
  .action(async (options) => {
    console.log(chalk.yellow('🚧 Analytics functionality coming soon!'));
    console.log(chalk.gray('This will show plugin usage, performance, and cost metrics'));
  });

program.parse();
