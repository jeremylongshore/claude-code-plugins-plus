#!/usr/bin/env node

/**
 * Sugar MCP Server
 * Bridges Claude Code with Sugar's Python CLI for autonomous development
 *
 * @version 1.9.1
 * @author Steven Leggett <contact@roboticforce.io>
 * @license MIT
 */

import { spawn } from 'child_process';
import { promisify } from 'util';
import { access, constants } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const accessAsync = promisify(access);

/**
 * Sugar MCP Server
 * Handles communication between Claude Code and Sugar CLI
 */
class SugarMCPServer {
  constructor() {
    this.sugarCommand = null;
    this.projectRoot = process.env.SUGAR_PROJECT_ROOT || process.cwd();
    this.debug = process.env.SUGAR_DEBUG === 'true';
  }

  /**
   * Initialize the MCP server
   */
  async initialize() {
    this.log('Sugar MCP Server initializing...');
    this.log(`Project root: ${this.projectRoot}`);

    // Detect Sugar installation
    this.sugarCommand = await this.detectSugarCommand();

    if (!this.sugarCommand) {
      throw new Error(
        'Sugar CLI not found. Please install: pip install sugarai\\n' +
        'Then initialize: sugar init'
      );
    }

    this.log(`Sugar CLI found: ${this.sugarCommand}`);

    // Verify Sugar is initialized in project
    const sugarDir = join(this.projectRoot, '.sugar');
    try {
      await accessAsync(sugarDir, constants.F_OK);
      this.log('Sugar initialized in project ✓');
    } catch {
      this.log('Warning: Sugar not initialized in project. Run: sugar init');
    }

    this.log('Sugar MCP Server ready ✓');
  }

  /**
   * Detect Sugar CLI command location
   */
  async detectSugarCommand() {
    const candidates = [
      'sugar',
      '/usr/local/bin/sugar',
      join(process.env.HOME || '', '.local', 'bin', 'sugar'),
      join(this.projectRoot, 'venv', 'bin', 'sugar'),
      join(this.projectRoot, '.venv', 'bin', 'sugar')
    ];

    for (const cmd of candidates) {
      try {
        const result = await this.execCommand(cmd, ['--version']);
        if (result.success) {
          return cmd;
        }
      } catch {
        continue;
      }
    }

    return null;
  }

  /**
   * Execute command and return result
   */
  async execCommand(command, args, options = {}) {
    return new Promise((resolve) => {
      const proc = spawn(command, args, {
        cwd: options.cwd || this.projectRoot,
        env: { ...process.env, ...options.env },
        timeout: options.timeout || 30000
      });

      let stdout = '';
      let stderr = '';

      proc.stdout?.on('data', (data) => {
        stdout += data.toString();
      });

      proc.stderr?.on('data', (data) => {
        stderr += data.toString();
      });

      proc.on('close', (code) => {
        resolve({
          success: code === 0,
          code,
          stdout: stdout.trim(),
          stderr: stderr.trim()
        });
      });

      proc.on('error', (error) => {
        resolve({
          success: false,
          code: -1,
          stdout: '',
          stderr: error.message
        });
      });
    });
  }

  /**
   * Execute Sugar CLI command
   */
  async execSugar(args, options = {}) {
    return this.execCommand(this.sugarCommand, args, options);
  }

  /**
   * MCP Tool: Create Task
   */
  async createTask(params) {
    this.log('createTask called', params);

    const {
      title,
      type = 'feature',
      priority = 3,
      urgent = false,
      description = null,
      json_data = null
    } = params;

    if (!title) {
      return {
        success: false,
        error: 'Task title is required'
      };
    }

    const args = ['add', title];

    if (type) args.push('--type', type);
    if (priority) args.push('--priority', priority.toString());
    if (urgent) args.push('--urgent');

    if (json_data) {
      args.push('--json', '--description', JSON.stringify(json_data));
    } else if (description) {
      args.push('--description', description);
    }

    const result = await this.execSugar(args);

    if (result.success) {
      // Parse task ID from output
      const match = result.stdout.match(/Task (?:created|added).*?:\s*(.+)/i) ||
                    result.stdout.match(/ID:\s*(.+)/i);
      const taskId = match ? match[1].trim() : null;

      return {
        success: true,
        taskId,
        message: 'Task created successfully',
        output: result.stdout
      };
    } else {
      return {
        success: false,
        error: result.stderr || result.stdout,
        message: 'Failed to create task'
      };
    }
  }

  /**
   * MCP Tool: List Tasks
   */
  async listTasks(params = {}) {
    this.log('listTasks called', params);

    const {
      status = null,
      type = null,
      priority = null,
      limit = 20
    } = params;

    const args = ['list'];

    if (status) args.push('--status', status);
    if (type) args.push('--type', type);
    if (priority) args.push('--priority', priority.toString());
    if (limit) args.push('--limit', limit.toString());

    const result = await this.execSugar(args);

    if (result.success) {
      return {
        success: true,
        tasks: this.parseTasks(result.stdout),
        output: result.stdout
      };
    } else {
      return {
        success: false,
        error: result.stderr || result.stdout,
        tasks: []
      };
    }
  }

  /**
   * MCP Tool: View Task
   */
  async viewTask(params) {
    this.log('viewTask called', params);

    const { taskId } = params;

    if (!taskId) {
      return {
        success: false,
        error: 'Task ID is required'
      };
    }

    const result = await this.execSugar(['view', taskId]);

    if (result.success) {
      return {
        success: true,
        task: this.parseTaskDetails(result.stdout),
        output: result.stdout
      };
    } else {
      return {
        success: false,
        error: result.stderr || result.stdout
      };
    }
  }

  /**
   * MCP Tool: Update Task
   */
  async updateTask(params) {
    this.log('updateTask called', params);

    const {
      taskId,
      title = null,
      type = null,
      priority = null,
      status = null,
      description = null
    } = params;

    if (!taskId) {
      return {
        success: false,
        error: 'Task ID is required'
      };
    }

    const args = ['update', taskId];

    if (title) args.push('--title', title);
    if (type) args.push('--type', type);
    if (priority) args.push('--priority', priority.toString());
    if (status) args.push('--status', status);
    if (description) args.push('--description', description);

    const result = await this.execSugar(args);

    return {
      success: result.success,
      message: result.success ? 'Task updated successfully' : 'Failed to update task',
      output: result.stdout,
      error: result.stderr
    };
  }

  /**
   * MCP Tool: Get Status
   */
  async getStatus() {
    this.log('getStatus called');

    const result = await this.execSugar(['status']);

    if (result.success) {
      return {
        success: true,
        status: this.parseStatus(result.stdout),
        output: result.stdout
      };
    } else {
      return {
        success: false,
        error: result.stderr || result.stdout
      };
    }
  }

  /**
   * MCP Tool: Run Once
   */
  async runOnce(params = {}) {
    this.log('runOnce called', params);

    const { dryRun = false, validate = false } = params;

    const args = ['run', '--once'];
    if (dryRun) args.push('--dry-run');
    if (validate) args.push('--validate');

    // Longer timeout for execution
    const result = await this.execSugar(args, { timeout: 300000 });

    return {
      success: result.success,
      output: result.stdout,
      error: result.stderr
    };
  }

  /**
   * MCP Tool: Remove Task
   */
  async removeTask(params) {
    this.log('removeTask called', params);

    const { taskId } = params;

    if (!taskId) {
      return {
        success: false,
        error: 'Task ID is required'
      };
    }

    const result = await this.execSugar(['remove', taskId]);

    return {
      success: result.success,
      message: result.success ? 'Task removed successfully' : 'Failed to remove task',
      output: result.stdout,
      error: result.stderr
    };
  }

  /**
   * Parse task list output
   */
  parseTasks(output) {
    const tasks = [];
    const lines = output.split('\n');

    for (const line of lines) {
      // Try multiple patterns
      let match = line.match(/\[([^\]]+)\]\s+(.+?)\s+\((?:ID:|id:)?\s*([^)]+)\)/i);

      if (!match) {
        // Try alternative format
        match = line.match(/(\w+)\s+\|\s+(.+?)\s+\|\s+(\S+)/);
      }

      if (match) {
        tasks.push({
          status: match[1].trim(),
          title: match[2].trim(),
          id: match[3].trim()
        });
      }
    }

    return tasks;
  }

  /**
   * Parse task details
   */
  parseTaskDetails(output) {
    // Return raw output for now
    // Could be enhanced to parse structured data
    return {
      raw: output,
      // TODO: Parse structured details if needed
    };
  }

  /**
   * Parse status output
   */
  parseStatus(output) {
    const status = {
      raw: output
    };

    // Try to extract key metrics
    const totalMatch = output.match(/Total Tasks?:\s*(\d+)/i);
    const pendingMatch = output.match(/Pending:\s*(\d+)/i);
    const activeMatch = output.match(/Active:\s*(\d+)/i);
    const completedMatch = output.match(/Completed:\s*(\d+)/i);
    const failedMatch = output.match(/Failed:\s*(\d+)/i);

    if (totalMatch) status.total = parseInt(totalMatch[1]);
    if (pendingMatch) status.pending = parseInt(pendingMatch[1]);
    if (activeMatch) status.active = parseInt(activeMatch[1]);
    if (completedMatch) status.completed = parseInt(completedMatch[1]);
    if (failedMatch) status.failed = parseInt(failedMatch[1]);

    return status;
  }

  /**
   * Logging utility
   */
  log(...args) {
    if (this.debug) {
      console.error('[Sugar MCP]', ...args);
    }
  }

  /**
   * Handle incoming MCP request
   */
  async handleRequest(request) {
    this.log('Handling request:', request.method);

    try {
      let response;

      switch (request.method) {
        case 'createTask':
          response = await this.createTask(request.params || {});
          break;
        case 'listTasks':
          response = await this.listTasks(request.params || {});
          break;
        case 'viewTask':
          response = await this.viewTask(request.params || {});
          break;
        case 'updateTask':
          response = await this.updateTask(request.params || {});
          break;
        case 'removeTask':
          response = await this.removeTask(request.params || {});
          break;
        case 'getStatus':
          response = await this.getStatus();
          break;
        case 'runOnce':
          response = await this.runOnce(request.params || {});
          break;
        default:
          response = {
            success: false,
            error: `Unknown method: ${request.method}`
          };
      }

      return {
        jsonrpc: '2.0',
        id: request.id,
        result: response
      };
    } catch (error) {
      return {
        jsonrpc: '2.0',
        id: request.id,
        error: {
          code: -32603,
          message: error.message
        }
      };
    }
  }
}

/**
 * Main entry point
 */
async function main() {
  const server = new SugarMCPServer();

  try {
    await server.initialize();

    // Handle stdin/stdout communication
    let buffer = '';

    process.stdin.setEncoding('utf8');
    process.stdin.on('data', async (chunk) => {
      buffer += chunk;

      // Process complete lines
      let newlineIndex;
      while ((newlineIndex = buffer.indexOf('\n')) !== -1) {
        const line = buffer.slice(0, newlineIndex);
        buffer = buffer.slice(newlineIndex + 1);

        if (line.trim()) {
          try {
            const request = JSON.parse(line);
            const response = await server.handleRequest(request);
            process.stdout.write(JSON.stringify(response) + '\n');
          } catch (error) {
            process.stdout.write(JSON.stringify({
              jsonrpc: '2.0',
              error: {
                code: -32700,
                message: 'Parse error: ' + error.message
              }
            }) + '\n');
          }
        }
      }
    });

    process.stdin.on('end', () => {
      server.log('Shutting down...');
      process.exit(0);
    });

    // Handle signals
    process.on('SIGINT', () => {
      server.log('Received SIGINT, shutting down...');
      process.exit(0);
    });

    process.on('SIGTERM', () => {
      server.log('Received SIGTERM, shutting down...');
      process.exit(0);
    });

  } catch (error) {
    console.error('Failed to initialize Sugar MCP Server:', error.message);
    process.exit(1);
  }
}

// Run if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

export { SugarMCPServer };
