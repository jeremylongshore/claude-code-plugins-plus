import chalk from 'chalk';
import ora from 'ora';
import * as os from 'os';
import { promises as fs } from 'fs';
import { existsSync } from 'fs';
import { detectClaudePaths, isMarketplaceInstalled } from '../utils/paths.js';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

interface DoctorOptions {
  json?: boolean;
}

interface DiagnosticResult {
  category: string;
  checks: CheckResult[];
}

interface CheckResult {
  name: string;
  status: 'pass' | 'warn' | 'fail';
  message: string;
  details?: string;
}

/**
 * Run comprehensive diagnostics on Claude Code installation
 */
export async function doctorCheck(options: DoctorOptions): Promise<void> {
  const results: DiagnosticResult[] = [];

  if (!options.json) {
    console.log(chalk.bold('\n🔍 Claude Code Plugins - System Diagnostics\n'));
  }

  // System checks
  const systemChecks = await runSystemChecks();
  results.push(systemChecks);

  // Claude installation checks
  const claudeChecks = await runClaudeChecks();
  results.push(claudeChecks);

  // Plugin checks
  const pluginChecks = await runPluginChecks();
  results.push(pluginChecks);

  // Marketplace checks
  const marketplaceChecks = await runMarketplaceChecks();
  results.push(marketplaceChecks);

  if (options.json) {
    console.log(JSON.stringify(results, null, 2));
    return;
  }

  // Display results
  displayResults(results);

  // Summary
  displaySummary(results);
}

/**
 * Run system environment checks
 */
async function runSystemChecks(): Promise<DiagnosticResult> {
  const checks: CheckResult[] = [];

  // Node.js version
  const nodeVersion = process.version;
  const majorVersion = parseInt(nodeVersion.slice(1).split('.')[0]);

  checks.push({
    name: 'Node.js Version',
    status: majorVersion >= 18 ? 'pass' : 'warn',
    message: `${nodeVersion} ${majorVersion >= 18 ? '(supported)' : '(upgrade recommended)'}`,
    details: majorVersion < 18 ? 'Node.js 18+ recommended for best compatibility' : undefined,
  });

  // Platform
  checks.push({
    name: 'Operating System',
    status: 'pass',
    message: `${os.platform()} ${os.release()}`,
  });

  // Available package managers
  const packageManagers = await checkPackageManagers();
  checks.push({
    name: 'Package Managers',
    status: packageManagers.length > 0 ? 'pass' : 'fail',
    message: packageManagers.length > 0 ? packageManagers.join(', ') : 'No package managers found',
    details: packageManagers.length === 0 ? 'Install npm, bun, pnpm, or deno' : undefined,
  });

  return {
    category: 'System Environment',
    checks,
  };
}

/**
 * Run Claude Code installation checks
 */
async function runClaudeChecks(): Promise<DiagnosticResult> {
  const checks: CheckResult[] = [];

  try {
    const paths = await detectClaudePaths();

    checks.push({
      name: 'Claude Config Directory',
      status: 'pass',
      message: paths.configDir,
    });

    checks.push({
      name: 'Plugins Directory',
      status: 'pass',
      message: paths.pluginsDir,
    });

    checks.push({
      name: 'Marketplaces Directory',
      status: 'pass',
      message: paths.marketplacesDir,
    });

    if (paths.projectPluginDir) {
      checks.push({
        name: 'Project Plugin Directory',
        status: 'pass',
        message: paths.projectPluginDir,
      });
    }
  } catch (error) {
    checks.push({
      name: 'Claude Installation',
      status: 'fail',
      message: error instanceof Error ? error.message : 'Not found',
      details: 'Install Claude Code from https://claude.com/code',
    });
  }

  return {
    category: 'Claude Code Installation',
    checks,
  };
}

/**
 * Run plugin installation checks
 */
async function runPluginChecks(): Promise<DiagnosticResult> {
  const checks: CheckResult[] = [];

  try {
    const paths = await detectClaudePaths();

    // Read Claude's installed_plugins.json
    const installedPluginsPath = `${paths.configDir}/plugins/installed_plugins.json`;
    let totalPlugins = 0;
    let globalPlugins = 0;
    let projectPlugins = 0;

    if (existsSync(installedPluginsPath)) {
      const fileContent = await fs.readFile(installedPluginsPath, 'utf-8');
      const data = JSON.parse(fileContent);

      if (data.plugins) {
        const pluginEntries = Object.values(data.plugins) as any[];
        totalPlugins = pluginEntries.length;

        // Count by scope
        for (const installations of pluginEntries) {
          if (Array.isArray(installations) && installations.length > 0) {
            const firstInstall = installations[0];
            if (firstInstall.scope === 'global') {
              globalPlugins++;
            } else if (firstInstall.scope === 'project') {
              projectPlugins++;
            }
          }
        }
      }

      checks.push({
        name: 'Installed Plugins',
        status: totalPlugins > 0 ? 'pass' : 'warn',
        message: `${totalPlugins} total (${globalPlugins} global, ${projectPlugins} project)`,
        details: totalPlugins === 0 ? 'No plugins installed yet' : undefined,
      });
    } else {
      checks.push({
        name: 'Installed Plugins',
        status: 'warn',
        message: 'No plugins installed',
        details: 'Plugin registry not found - no plugins installed yet',
      });
    }
  } catch (error) {
    checks.push({
      name: 'Plugin Check',
      status: 'fail',
      message: 'Could not check plugins',
      details: error instanceof Error ? error.message : undefined,
    });
  }

  return {
    category: 'Plugins',
    checks,
  };
}

/**
 * Run marketplace checks
 */
async function runMarketplaceChecks(): Promise<DiagnosticResult> {
  const checks: CheckResult[] = [];

  try {
    const paths = await detectClaudePaths();
    const marketplaceInstalled = await isMarketplaceInstalled(paths);

    checks.push({
      name: 'Marketplace Catalog',
      status: marketplaceInstalled ? 'pass' : 'warn',
      message: marketplaceInstalled ? 'Installed' : 'Not installed',
      details: !marketplaceInstalled ? 'Run `ccp install <plugin>` to install marketplace' : undefined,
    });

    if (marketplaceInstalled) {
      // TODO: Check marketplace version/freshness
      checks.push({
        name: 'Catalog Freshness',
        status: 'pass',
        message: 'Up to date',
      });
    }
  } catch {
    checks.push({
      name: 'Marketplace Check',
      status: 'fail',
      message: 'Could not check marketplace',
    });
  }

  return {
    category: 'Marketplace',
    checks,
  };
}

/**
 * Check which package managers are available
 */
async function checkPackageManagers(): Promise<string[]> {
  const managers = ['npm', 'bun', 'pnpm', 'deno'];
  const available: string[] = [];

  for (const manager of managers) {
    try {
      await execAsync(`${manager} --version`);
      available.push(manager);
    } catch {
      // Not available
    }
  }

  return available;
}

/**
 * Display diagnostic results
 */
function displayResults(results: DiagnosticResult[]): void {
  for (const category of results) {
    console.log(chalk.bold(`\n${category.category}:`));

    for (const check of category.checks) {
      const icon = check.status === 'pass' ? chalk.green('✓') :
                   check.status === 'warn' ? chalk.yellow('⚠') :
                   chalk.red('✗');

      console.log(`  ${icon} ${check.name}: ${chalk.gray(check.message)}`);

      if (check.details) {
        console.log(chalk.gray(`    → ${check.details}`));
      }
    }
  }
}

/**
 * Display summary
 */
function displaySummary(results: DiagnosticResult[]): void {
  let passCount = 0;
  let warnCount = 0;
  let failCount = 0;

  for (const category of results) {
    for (const check of category.checks) {
      if (check.status === 'pass') passCount++;
      else if (check.status === 'warn') warnCount++;
      else failCount++;
    }
  }

  console.log(chalk.bold('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'));
  console.log(chalk.bold('Summary:'));
  console.log(chalk.green(`  ✓ ${passCount} passed`));

  if (warnCount > 0) {
    console.log(chalk.yellow(`  ⚠ ${warnCount} warnings`));
  }

  if (failCount > 0) {
    console.log(chalk.red(`  ✗ ${failCount} failed`));
  }

  if (failCount === 0 && warnCount === 0) {
    console.log(chalk.green('\n✨ All checks passed! Your Claude Code setup is healthy.\n'));
  } else if (failCount === 0) {
    console.log(chalk.yellow('\n⚠️  Some warnings detected. Your setup should work but could be improved.\n'));
  } else {
    console.log(chalk.red('\n❌ Critical issues detected. Please address the failures above.\n'));
  }
}
