import { vi, beforeEach, afterEach } from 'vitest';
import fs from 'fs/promises';
import path from 'path';
import { randomUUID } from 'crypto';
import { spawn, ChildProcess } from 'child_process';

/**
 * Test environment for isolated E2E testing
 */
export interface TestEnvironment {
  /** Unique test environment ID */
  id: string;
  /** Base path for test environment */
  basePath: string;
  /** Path to test marketplace catalog */
  catalogPath: string;
  /** Path to installed plugins */
  pluginsPath: string;
  /** Installed plugins */
  installedPlugins: Map<string, PluginMetadata>;
  /** Active MCP servers */
  mcpServers: Map<string, McpServer>;
  /** Cleanup function */
  cleanup: () => Promise<void>;
}

export interface PluginMetadata {
  name: string;
  version: string;
  description: string;
  author: {
    name: string;
    email: string;
  };
  license: string;
  manifestPath: string;
  installPath: string;
}

export interface Skill {
  name: string;
  description: string;
  allowedTools: string[];
  version: string;
  author: string;
  license: string;
  content: string;
  triggerPhrases: string[];
}

export interface McpServer {
  /** Server process */
  process: ChildProcess;
  /** Server name */
  name: string;
  /** Server port (if applicable) */
  port?: number;
  /** Registered tools */
  tools: Map<string, McpTool>;
  /** Server status */
  status: 'starting' | 'ready' | 'error' | 'stopped';
  /** Stop function */
  stop: () => Promise<void>;
}

export interface McpTool {
  name: string;
  description: string;
  inputSchema: Record<string, unknown>;
}

/**
 * Create an isolated test environment
 */
export async function createTestEnv(): Promise<TestEnvironment> {
  const id = randomUUID();
  const basePath = path.join('/tmp', `claude-e2e-test-${id}`);
  const catalogPath = path.join(basePath, 'marketplace.json');
  const pluginsPath = path.join(basePath, 'plugins');

  // Create directory structure
  await fs.mkdir(basePath, { recursive: true });
  await fs.mkdir(pluginsPath, { recursive: true });

  // Create empty catalog
  await fs.writeFile(
    catalogPath,
    JSON.stringify({
      name: 'test-marketplace',
      version: '1.0.0',
      plugins: []
    }, null, 2)
  );

  const installedPlugins = new Map<string, PluginMetadata>();
  const mcpServers = new Map<string, McpServer>();

  const cleanup = async () => {
    // Stop all MCP servers
    for (const server of mcpServers.values()) {
      await server.stop();
    }

    // Remove test directory unless E2E_KEEP_ARTIFACTS is set
    if (!process.env.E2E_KEEP_ARTIFACTS) {
      await fs.rm(basePath, { recursive: true, force: true });
    } else {
      console.log(`Test artifacts kept at: ${basePath}`);
    }
  };

  return {
    id,
    basePath,
    catalogPath,
    pluginsPath,
    installedPlugins,
    mcpServers,
    cleanup
  };
}

/**
 * Install a plugin into the test environment
 */
export async function installPlugin(
  env: TestEnvironment,
  pluginSourcePath: string
): Promise<PluginMetadata> {
  // Read plugin manifest
  const manifestPath = path.join(pluginSourcePath, '.claude-plugin', 'plugin.json');
  const manifestContent = await fs.readFile(manifestPath, 'utf-8');
  const manifest = JSON.parse(manifestContent);

  // Validate required fields
  if (!manifest.name || !manifest.version || !manifest.description) {
    throw new Error('Invalid plugin manifest: missing required fields');
  }

  // Check for duplicate installation
  if (env.installedPlugins.has(manifest.name)) {
    throw new Error(`Plugin ${manifest.name} is already installed`);
  }

  // Copy plugin files to test environment
  const installPath = path.join(env.pluginsPath, manifest.name);
  await copyDirectory(pluginSourcePath, installPath);

  const metadata: PluginMetadata = {
    name: manifest.name,
    version: manifest.version,
    description: manifest.description,
    author: manifest.author || { name: 'Unknown', email: '' },
    license: manifest.license || 'MIT',
    manifestPath: path.join(installPath, '.claude-plugin', 'plugin.json'),
    installPath
  };

  env.installedPlugins.set(manifest.name, metadata);

  return metadata;
}

/**
 * Uninstall a plugin from the test environment
 */
export async function uninstallPlugin(
  env: TestEnvironment,
  pluginName: string
): Promise<void> {
  const plugin = env.installedPlugins.get(pluginName);
  if (!plugin) {
    throw new Error(`Plugin ${pluginName} is not installed`);
  }

  // Remove plugin directory
  await fs.rm(plugin.installPath, { recursive: true, force: true });

  // Remove from installed plugins map
  env.installedPlugins.delete(pluginName);
}

/**
 * Load a skill from a plugin
 */
export async function loadSkill(
  env: TestEnvironment,
  pluginName: string,
  skillName: string
): Promise<Skill> {
  const plugin = env.installedPlugins.get(pluginName);
  if (!plugin) {
    throw new Error(`Plugin ${pluginName} is not installed`);
  }

  const skillPath = path.join(
    plugin.installPath,
    'skills',
    skillName,
    'SKILL.md'
  );

  // Read skill file
  const skillContent = await fs.readFile(skillPath, 'utf-8');

  // Parse frontmatter
  const frontmatterMatch = skillContent.match(/^---\n([\s\S]+?)\n---/);
  if (!frontmatterMatch) {
    throw new Error(`Invalid skill: missing frontmatter in ${skillPath}`);
  }

  const frontmatter = parseFrontmatter(frontmatterMatch[1]);

  // Extract trigger phrases from description
  const triggerPhrases = extractTriggerPhrases(frontmatter.description || '');

  return {
    name: frontmatter.name || skillName,
    description: frontmatter.description || '',
    allowedTools: parseAllowedTools(frontmatter['allowed-tools'] || ''),
    version: frontmatter.version || '1.0.0',
    author: frontmatter.author || 'Unknown',
    license: frontmatter.license || 'MIT',
    content: skillContent,
    triggerPhrases
  };
}

/**
 * Simulate skill activation by trigger phrase
 */
export async function activateSkill(
  env: TestEnvironment,
  userInput: string
): Promise<Skill | null> {
  // Search all installed plugins for matching skills
  for (const plugin of env.installedPlugins.values()) {
    const skillsPath = path.join(plugin.installPath, 'skills');

    try {
      const skillDirs = await fs.readdir(skillsPath);

      for (const skillDir of skillDirs) {
        const skillPath = path.join(skillsPath, skillDir, 'SKILL.md');

        try {
          const skill = await loadSkill(env, plugin.name, skillDir);

          // Check if user input matches any trigger phrase
          for (const trigger of skill.triggerPhrases) {
            if (userInput.toLowerCase().includes(trigger.toLowerCase())) {
              return skill;
            }
          }
        } catch (error) {
          // Skill file might not exist or be invalid, continue
          continue;
        }
      }
    } catch (error) {
      // Plugin might not have skills directory, continue
      continue;
    }
  }

  return null;
}

/**
 * Start an MCP server for testing
 */
export async function startMcpServer(
  serverPath: string,
  serverName: string
): Promise<McpServer> {
  return new Promise((resolve, reject) => {
    // Spawn MCP server process
    const serverProcess = spawn('node', [serverPath], {
      stdio: ['pipe', 'pipe', 'pipe'],
      env: { ...process.env, NODE_ENV: 'test' }
    });

    const tools = new Map<string, McpTool>();
    let status: McpServer['status'] = 'starting';

    // Collect stdout for tool registration
    let stdoutBuffer = '';
    serverProcess.stdout.on('data', (data) => {
      stdoutBuffer += data.toString();

      // Parse JSON-RPC messages for tool registration
      const messages = stdoutBuffer.split('\n');
      for (const message of messages) {
        if (!message.trim()) continue;

        try {
          const parsed = JSON.parse(message);
          if (parsed.method === 'tools/list') {
            // Server has sent tools list
            for (const tool of parsed.params?.tools || []) {
              tools.set(tool.name, {
                name: tool.name,
                description: tool.description,
                inputSchema: tool.inputSchema
              });
            }
            status = 'ready';
          }
        } catch (e) {
          // Not JSON, ignore
        }
      }
    });

    // Handle errors
    serverProcess.stderr.on('data', (data) => {
      console.error(`MCP Server error: ${data.toString()}`);
    });

    serverProcess.on('error', (error) => {
      status = 'error';
      reject(error);
    });

    serverProcess.on('exit', (code) => {
      status = 'stopped';
      if (code !== 0) {
        reject(new Error(`MCP Server exited with code ${code}`));
      }
    });

    // Wait for server to be ready (timeout after 5s)
    const timeout = setTimeout(() => {
      if (status !== 'ready') {
        serverProcess.kill();
        reject(new Error('MCP Server startup timeout'));
      }
    }, 5000);

    // Check for ready status
    const readyCheck = setInterval(() => {
      if (status === 'ready') {
        clearInterval(readyCheck);
        clearTimeout(timeout);

        const stop = async () => {
          return new Promise<void>((resolve) => {
            serverProcess.on('exit', () => resolve());
            serverProcess.kill('SIGTERM');

            // Force kill after 2s if not stopped
            setTimeout(() => {
              if (status !== 'stopped') {
                serverProcess.kill('SIGKILL');
              }
            }, 2000);
          });
        };

        resolve({
          process: serverProcess,
          name: serverName,
          tools,
          status,
          stop
        });
      }
    }, 100);
  });
}

/**
 * Invoke an MCP tool
 */
export async function invokeMcpTool(
  server: McpServer,
  toolName: string,
  params: Record<string, unknown>
): Promise<unknown> {
  if (!server.tools.has(toolName)) {
    throw new Error(`Tool ${toolName} not found on server ${server.name}`);
  }

  return new Promise((resolve, reject) => {
    const requestId = randomUUID();
    const request = {
      jsonrpc: '2.0',
      id: requestId,
      method: 'tools/call',
      params: {
        name: toolName,
        arguments: params
      }
    };

    // Send request to server
    server.process.stdin?.write(JSON.stringify(request) + '\n');

    // Wait for response
    const responseHandler = (data: Buffer) => {
      const response = data.toString();
      try {
        const parsed = JSON.parse(response);
        if (parsed.id === requestId) {
          server.process.stdout?.off('data', responseHandler);

          if (parsed.error) {
            reject(new Error(parsed.error.message));
          } else {
            resolve(parsed.result);
          }
        }
      } catch (e) {
        // Not JSON or not our response, ignore
      }
    };

    server.process.stdout?.on('data', responseHandler);

    // Timeout after 10s
    setTimeout(() => {
      server.process.stdout?.off('data', responseHandler);
      reject(new Error('MCP tool invocation timeout'));
    }, 10000);
  });
}

/**
 * Helper: Copy directory recursively
 */
async function copyDirectory(src: string, dest: string): Promise<void> {
  await fs.mkdir(dest, { recursive: true });

  const entries = await fs.readdir(src, { withFileTypes: true });

  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);

    if (entry.isDirectory()) {
      await copyDirectory(srcPath, destPath);
    } else {
      await fs.copyFile(srcPath, destPath);
    }
  }
}

/**
 * Helper: Parse YAML frontmatter
 */
function parseFrontmatter(yaml: string): Record<string, string> {
  const result: Record<string, string> = {};
  const lines = yaml.split('\n');

  for (const line of lines) {
    const colonIndex = line.indexOf(':');
    if (colonIndex === -1) continue;

    const key = line.substring(0, colonIndex).trim();
    let value = line.substring(colonIndex + 1).trim();

    // Handle multiline strings (|)
    if (value === '|') {
      // Next lines are the value until we hit a new key
      continue;
    }

    result[key] = value;
  }

  return result;
}

/**
 * Helper: Parse allowed-tools string
 */
function parseAllowedTools(toolsString: string): string[] {
  return toolsString
    .split(',')
    .map(tool => tool.trim())
    .filter(tool => tool.length > 0);
}

/**
 * Helper: Extract trigger phrases from description
 */
function extractTriggerPhrases(description: string): string[] {
  const triggers: string[] = [];

  // Look for quoted phrases
  const quotedMatches = description.match(/"([^"]+)"/g);
  if (quotedMatches) {
    triggers.push(...quotedMatches.map(m => m.replace(/"/g, '')));
  }

  // Look for common trigger patterns
  const patterns = [
    /trigger with ([\w\s]+)/gi,
    /use when ([\w\s]+)/gi,
    /activate on ([\w\s]+)/gi
  ];

  for (const pattern of patterns) {
    const matches = description.matchAll(pattern);
    for (const match of matches) {
      triggers.push(match[1].trim());
    }
  }

  return triggers;
}

/**
 * Global setup: Clean up any leftover test environments
 */
beforeEach(async () => {
  // Cleanup old test directories (older than 1 hour)
  try {
    const tmpDir = '/tmp';
    const entries = await fs.readdir(tmpDir, { withFileTypes: true });
    const oneHourAgo = Date.now() - 3600000;

    for (const entry of entries) {
      if (entry.isDirectory() && entry.name.startsWith('claude-e2e-test-')) {
        const dirPath = path.join(tmpDir, entry.name);
        const stats = await fs.stat(dirPath);

        if (stats.mtimeMs < oneHourAgo) {
          await fs.rm(dirPath, { recursive: true, force: true });
        }
      }
    }
  } catch (error) {
    // Ignore cleanup errors
  }
});

/**
 * Global teardown: Log test environment info
 */
afterEach(() => {
  if (process.env.E2E_DEBUG) {
    console.log('Test completed');
  }
});
