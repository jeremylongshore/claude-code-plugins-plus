import { dirname, join } from 'node:path';
import { readFile, stat } from 'node:fs/promises';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';

const pluginRoot = join(dirname(fileURLToPath(import.meta.url)), '..');
const execFileAsync = promisify(execFile);

describe('published stdio entrypoint', () => {
  it('starts the built dist/index.js and completes the MCP handshake', async () => {
    const transport = new StdioClientTransport({
      command: process.execPath,
      args: [join(pluginRoot, 'dist/index.js')],
      cwd: pluginRoot,
      stderr: 'pipe',
    });
    const client = new Client({ name: 'entrypoint-test', version: '1.0.0' }, { capabilities: {} });
    try {
      await client.connect(transport);
      const tools = await client.listTools();
      expect(tools.tools).toHaveLength(7);
      expect(tools.tools.map((tool) => tool.name)).toContain('fetch_agent_card');
    } finally {
      await client.close();
    }
  });
});

describe('host cancellation gate', () => {
  it('registers an executable PreToolUse hook that asks for approval', async () => {
    const hookPath = join(pluginRoot, 'hooks/hooks.json');
    const scriptPath = join(pluginRoot, 'scripts/confirm-cancel-task.sh');
    const hook = JSON.parse(await readFile(hookPath, 'utf8')) as {
      hooks: { PreToolUse: Array<{ matcher: string }> };
    };
    const matcher = new RegExp(hook.hooks.PreToolUse[0].matcher);
    expect(matcher.test('mcp__a2a-client__cancel_task')).toBe(true);
    expect(matcher.test('mcp__plugin_a2a-client_a2a-client__cancel_task')).toBe(true);
    expect(matcher.test('mcp__plugin_other_a2a-client__cancel_task')).toBe(false);
    expect(matcher.test('mcp__plugin_a2a-client_a2a-client__send_message')).toBe(false);
    expect((await stat(scriptPath)).mode & 0o111).not.toBe(0);

    const { stdout } = await execFileAsync(scriptPath);
    const decision = JSON.parse(stdout) as {
      hookSpecificOutput: { permissionDecision: string };
    };
    expect(decision.hookSpecificOutput.permissionDecision).toBe('ask');
  });
});

describe('plugin MCP environment wiring', () => {
  it('inherits optional operator settings instead of overriding them with empty strings', async () => {
    const mcp = JSON.parse(await readFile(join(pluginRoot, '.mcp.json'), 'utf8')) as {
      mcpServers: {
        'a2a-client': {
          name: string;
          transport: string;
          enabled: boolean;
          env: Record<string, string>;
        };
      };
    };
    const server = mcp.mcpServers['a2a-client'];
    expect(server).toMatchObject({ name: 'a2a-client', type: 'stdio', enabled: true });
    const env = server.env;
    expect(env.A2A_ALLOWED_HOSTS).toBe('${A2A_ALLOWED_HOSTS:-}');
    expect(env.A2A_ALLOWED_DESTINATIONS).toBe('${A2A_ALLOWED_DESTINATIONS:-}');
    expect(env.A2A_ALLOW_TASK_CANCELLATION).toBe('${A2A_ALLOW_TASK_CANCELLATION:-}');
    expect(env.A2A_REQUEST_TIMEOUT_MS).toBe('${A2A_REQUEST_TIMEOUT_MS:-30000}');
    expect(env.A2A_MAX_RESPONSE_BYTES).toBe('${A2A_MAX_RESPONSE_BYTES:-2097152}');
  });
});
