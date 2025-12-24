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

  // MCP server checks
  const mcpChecks = await runMCPChecks();
  results.push(mcpChecks);

  // Environment + API key checks
  const envChecks = await runEnvironmentChecks();
  results.push(envChecks);

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
      // Check catalog integrity
      const integrityCheck = await checkMarketplaceIntegrity(paths);
      checks.push(...integrityCheck);
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
 * Check marketplace catalog integrity
 */
async function checkMarketplaceIntegrity(paths: any): Promise<CheckResult[]> {
  const checks: CheckResult[] = [];
  const marketplaceSlug = 'claude-code-plugins-plus';
  const marketplacePath = `${paths.marketplacesDir}/${marketplaceSlug}`;

  try {
    // Check if both catalog files exist
    const catalogPath = `${marketplacePath}/.claude-plugin/marketplace.json`;
    const extendedPath = `${marketplacePath}/.claude-plugin/marketplace.extended.json`;

    const catalogExists = existsSync(catalogPath);
    const extendedExists = existsSync(extendedPath);

    if (!catalogExists || !extendedExists) {
      checks.push({
        name: 'Catalog Files',
        status: 'warn',
        message: `${catalogExists ? 'marketplace.json' : 'Missing marketplace.json'}${!catalogExists && !extendedExists ? ', ' : ''}${extendedExists ? 'marketplace.extended.json' : !catalogExists ? 'Missing marketplace.extended.json' : ''}`,
        details: 'Marketplace catalog files incomplete',
      });
      return checks;
    }

    // Validate JSON structure
    let catalog: any;
    let extended: any;

    try {
      const catalogContent = await fs.readFile(catalogPath, 'utf-8');
      catalog = JSON.parse(catalogContent);
    } catch (error) {
      checks.push({
        name: 'Catalog Structure',
        status: 'fail',
        message: 'marketplace.json is corrupted',
        details: error instanceof Error ? error.message : 'Invalid JSON',
      });
      return checks;
    }

    try {
      const extendedContent = await fs.readFile(extendedPath, 'utf-8');
      extended = JSON.parse(extendedContent);
    } catch (error) {
      checks.push({
        name: 'Extended Catalog Structure',
        status: 'fail',
        message: 'marketplace.extended.json is corrupted',
        details: error instanceof Error ? error.message : 'Invalid JSON',
      });
      return checks;
    }

    // Check sync status (plugin count comparison)
    const catalogCount = catalog.plugins?.length || 0;
    const extendedCount = extended.plugins?.length || 0;

    if (catalogCount !== extendedCount) {
      checks.push({
        name: 'Catalog Sync',
        status: 'warn',
        message: `Out of sync (${catalogCount} vs ${extendedCount} plugins)`,
        details: 'Run `pnpm run sync-marketplace` in repository to sync catalogs',
      });
    } else {
      checks.push({
        name: 'Catalog Sync',
        status: 'pass',
        message: `In sync (${catalogCount} plugins)`,
      });
    }

    // Validate plugin count is reasonable
    if (catalogCount > 0) {
      checks.push({
        name: 'Catalog Size',
        status: catalogCount >= 200 ? 'pass' : catalogCount >= 100 ? 'warn' : 'fail',
        message: `${catalogCount} plugins available`,
        details: catalogCount < 200 ? 'Catalog may be incomplete or outdated' : undefined,
      });
    }

    // Check for required fields in catalog
    const samplePlugin = catalog.plugins?.[0];
    if (samplePlugin) {
      const hasRequiredFields = samplePlugin.name && samplePlugin.version && samplePlugin.description;
      checks.push({
        name: 'Catalog Schema',
        status: hasRequiredFields ? 'pass' : 'warn',
        message: hasRequiredFields ? 'Valid structure' : 'Missing required fields',
        details: !hasRequiredFields ? 'Catalog may be corrupted or outdated' : undefined,
      });
    }

  } catch (error) {
    checks.push({
      name: 'Catalog Integrity',
      status: 'fail',
      message: 'Could not validate catalog',
      details: error instanceof Error ? error.message : undefined,
    });
  }

  return checks;
}

/**
 * Run MCP server health checks
 */
async function runMCPChecks(): Promise<DiagnosticResult> {
  const checks: CheckResult[] = [];

  try {
    const paths = await detectClaudePaths();
    const mcpServers = await detectMCPServers(paths);

    if (mcpServers.length === 0) {
      checks.push({
        name: 'MCP Servers',
        status: 'pass',
        message: 'No MCP servers configured',
        details: 'This is normal if you haven\'t installed MCP server plugins',
      });
      return {
        category: 'MCP Servers',
        checks,
      };
    }

    checks.push({
      name: 'MCP Servers Detected',
      status: 'pass',
      message: `${mcpServers.length} server(s) configured`,
    });

    // Check each MCP server
    for (const server of mcpServers) {
      const serverChecks = await checkMCPServer(server);
      checks.push(...serverChecks);
    }

  } catch (error) {
    checks.push({
      name: 'MCP Server Check',
      status: 'fail',
      message: 'Could not check MCP servers',
      details: error instanceof Error ? error.message : undefined,
    });
  }

  return {
    category: 'MCP Servers',
    checks,
  };
}

/**
 * Detect MCP servers from Claude settings
 */
async function detectMCPServers(paths: any): Promise<any[]> {
  const servers: any[] = [];

  try {
    // Check for MCP settings in Claude config
    const settingsPath = `${paths.configDir}/settings.json`;

    if (!existsSync(settingsPath)) {
      return servers;
    }

    const settingsContent = await fs.readFile(settingsPath, 'utf-8');
    const settings = JSON.parse(settingsContent);

    // MCP servers are typically in settings.mcp.servers or settings.mcpServers
    const mcpConfig = settings.mcp?.servers || settings.mcpServers || {};

    for (const [name, config] of Object.entries(mcpConfig)) {
      servers.push({
        name,
        config: config as any,
      });
    }

  } catch (error) {
    // Settings file might not exist or be invalid - not an error
  }

  return servers;
}

/**
 * Check individual MCP server health
 */
async function checkMCPServer(server: any): Promise<CheckResult[]> {
  const checks: CheckResult[] = [];
  const serverName = server.name;
  const config = server.config;

  try {
    // Check if server command/path exists
    const command = config.command || config.cmd;
    const args = config.args || [];

    if (!command) {
      checks.push({
        name: `${serverName}`,
        status: 'warn',
        message: 'No command configured',
        details: 'MCP server configuration missing command',
      });
      return checks;
    }

    // Check if command is executable (basic validation)
    let isAccessible = false;
    try {
      // Try to check if command exists
      if (command.startsWith('/') || command.startsWith('./')) {
        // Absolute or relative path
        isAccessible = existsSync(command);
      } else {
        // Command in PATH - try to execute with --version or --help
        try {
          await execAsync(`${command} --version`, { timeout: 2000 });
          isAccessible = true;
        } catch {
          try {
            await execAsync(`${command} --help`, { timeout: 2000 });
            isAccessible = true;
          } catch {
            // Command might not support --version or --help, assume it exists
            isAccessible = true;
          }
        }
      }
    } catch {
      isAccessible = false;
    }

    if (!isAccessible && (command.startsWith('/') || command.startsWith('./'))) {
      checks.push({
        name: `${serverName}`,
        status: 'fail',
        message: 'Command not found',
        details: `MCP server command "${command}" does not exist`,
      });
      return checks;
    }

    // Server appears configured correctly
    checks.push({
      name: `${serverName}`,
      status: 'pass',
      message: 'Configured',
      details: `Command: ${command}${args.length > 0 ? ' ' + args.join(' ') : ''}`,
    });

  } catch (error) {
    checks.push({
      name: `${serverName}`,
      status: 'warn',
      message: 'Could not validate',
      details: error instanceof Error ? error.message : undefined,
    });
  }

  return checks;
}

/**
 * Run environment variable and API key checks for installed plugins
 */
async function runEnvironmentChecks(): Promise<DiagnosticResult> {
  const checks: CheckResult[] = [];

  try {
    const paths = await detectClaudePaths();
    const installedPluginsPath = `${paths.configDir}/plugins/installed_plugins.json`;

    if (!existsSync(installedPluginsPath)) {
      checks.push({
        name: 'Environment Variables',
        status: 'pass',
        message: 'No plugins installed to check',
      });
      return {
        category: 'Environment & API Keys',
        checks,
      };
    }

    // Read installed plugins
    const fileContent = await fs.readFile(installedPluginsPath, 'utf-8');
    const data = JSON.parse(fileContent);
    const pluginNames: string[] = [];

    if (data.plugins) {
      pluginNames.push(...Object.keys(data.plugins));
    }

    if (pluginNames.length === 0) {
      checks.push({
        name: 'Environment Variables',
        status: 'pass',
        message: 'No plugins to check',
      });
      return {
        category: 'Environment & API Keys',
        checks,
      };
    }

    // Check common API keys
    const apiKeyChecks = checkCommonAPIKeys(pluginNames);
    checks.push(...apiKeyChecks);

    // Check plugin-specific requirements
    const pluginEnvChecks = checkPluginSpecificEnv(pluginNames);
    checks.push(...pluginEnvChecks);

  } catch (error) {
    checks.push({
      name: 'Environment Check',
      status: 'fail',
      message: 'Could not check environment variables',
      details: error instanceof Error ? error.message : undefined,
    });
  }

  return {
    category: 'Environment & API Keys',
    checks,
  };
}

/**
 * Check common API keys used by AI/Cloud plugins
 */
function checkCommonAPIKeys(pluginNames: string[]): CheckResult[] {
  const checks: CheckResult[] = [];

  // Define common API keys and their plugins
  const apiKeys: Array<{
    key: string;
    name: string;
    requiredBy: string[];
    signupUrl?: string;
  }> = [
    {
      key: 'ANTHROPIC_API_KEY',
      name: 'Anthropic API',
      requiredBy: ['ai-sdk-agents', 'make-scenario-builder', 'geepers-agents'],
      signupUrl: 'https://console.anthropic.com/',
    },
    {
      key: 'OPENAI_API_KEY',
      name: 'OpenAI API',
      requiredBy: ['openai-', 'gpt-', 'chatgpt-'],
      signupUrl: 'https://platform.openai.com/',
    },
    {
      key: 'GOOGLE_APPLICATION_CREDENTIALS',
      name: 'Google Cloud',
      requiredBy: ['jeremy-genkit-', 'jeremy-vertex-', 'jeremy-adk-', 'jeremy-gcp-'],
      signupUrl: 'https://console.cloud.google.com/',
    },
    {
      key: 'GOOGLE_AI_API_KEY',
      name: 'Google AI',
      requiredBy: ['gemini-', 'google-ai-'],
      signupUrl: 'https://makersuite.google.com/',
    },
    {
      key: 'GITHUB_TOKEN',
      name: 'GitHub',
      requiredBy: ['github-', 'git-'],
      signupUrl: 'https://github.com/settings/tokens',
    },
  ];

  for (const apiKey of apiKeys) {
    // Check if any installed plugin requires this key
    const requiresKey = pluginNames.some(plugin =>
      apiKey.requiredBy.some(pattern => plugin.includes(pattern))
    );

    if (requiresKey) {
      const isSet = !!process.env[apiKey.key];

      checks.push({
        name: apiKey.name,
        status: isSet ? 'pass' : 'warn',
        message: isSet ? `${apiKey.key} is set` : `${apiKey.key} not found`,
        details: !isSet ? `Set ${apiKey.key} in your environment. Get key from: ${apiKey.signupUrl}` : undefined,
      });
    }
  }

  return checks;
}

/**
 * Check plugin-specific environment requirements
 */
function checkPluginSpecificEnv(pluginNames: string[]): CheckResult[] {
  const checks: CheckResult[] = [];

  // Check for database-related plugins
  const dbPlugins = pluginNames.filter(p =>
    p.includes('postgres') || p.includes('mysql') || p.includes('mongodb') ||
    p.includes('redis') || p.includes('database')
  );

  if (dbPlugins.length > 0) {
    const hasDbUrl = !!(
      process.env.DATABASE_URL ||
      process.env.POSTGRES_URL ||
      process.env.MONGODB_URL ||
      process.env.REDIS_URL
    );

    checks.push({
      name: 'Database Configuration',
      status: hasDbUrl ? 'pass' : 'warn',
      message: hasDbUrl
        ? 'Database connection string detected'
        : 'No database connection strings found',
      details: !hasDbUrl
        ? `Plugins requiring databases: ${dbPlugins.join(', ')}. Set DATABASE_URL or plugin-specific connection strings.`
        : undefined,
    });
  }

  // Check for payment/billing plugins
  const paymentPlugins = pluginNames.filter(p =>
    p.includes('stripe') || p.includes('paypal') || p.includes('payment')
  );

  if (paymentPlugins.length > 0) {
    const hasPaymentKey = !!(process.env.STRIPE_API_KEY || process.env.PAYPAL_CLIENT_ID);

    checks.push({
      name: 'Payment Provider',
      status: hasPaymentKey ? 'pass' : 'warn',
      message: hasPaymentKey
        ? 'Payment API keys detected'
        : 'No payment API keys found',
      details: !hasPaymentKey
        ? `Plugins: ${paymentPlugins.join(', ')}. Set STRIPE_API_KEY or PAYPAL_CLIENT_ID.`
        : undefined,
    });
  }

  // Check for cloud provider plugins
  const awsPlugins = pluginNames.filter(p => p.includes('aws-') || p.includes('amazon-'));
  if (awsPlugins.length > 0 && !process.env.AWS_ACCESS_KEY_ID) {
    checks.push({
      name: 'AWS Credentials',
      status: 'warn',
      message: 'AWS credentials not found',
      details: `Plugins: ${awsPlugins.join(', ')}. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY.`,
    });
  }

  const azurePlugins = pluginNames.filter(p => p.includes('azure-'));
  if (azurePlugins.length > 0 && !process.env.AZURE_CLIENT_ID) {
    checks.push({
      name: 'Azure Credentials',
      status: 'warn',
      message: 'Azure credentials not found',
      details: `Plugins: ${azurePlugins.join(', ')}. Set AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID.`,
    });
  }

  return checks;
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
