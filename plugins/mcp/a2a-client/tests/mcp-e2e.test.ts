import { createServer, type Server as HttpServer } from 'node:http';
import { once } from 'node:events';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { Role, type AgentCard, type Message, type Part } from '@a2a-js/sdk';
import type { Client as A2AClient } from '@a2a-js/sdk/client';
import {
  AgentEvent,
  DefaultRequestHandler,
  InMemoryTaskStore,
  JsonRpcTransportHandler,
  ServerCallContext,
  type AgentExecutor,
} from '@a2a-js/sdk/server';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { InMemoryTransport } from '@modelcontextprotocol/sdk/inMemory.js';
import { createA2AServer, type A2ARuntime } from '../src/index.js';
import {
  DEFAULT_MAX_RESPONSE_BYTES,
  DEFAULT_REQUEST_TIMEOUT_MS,
  type GuardConfig,
} from '../src/net-guard.js';

const localGuard: GuardConfig = {
  allowedHosts: new Set(),
  allowedDestinationOrigins: new Set(),
  allowPrivateHosts: true,
  allowTaskCancellation: false,
  authHeaderName: 'Authorization',
  authHeaderValue: '',
  requestTimeoutMs: DEFAULT_REQUEST_TIMEOUT_MS,
  maxResponseBytes: DEFAULT_MAX_RESPONSE_BYTES,
};

const openServers: HttpServer[] = [];

afterEach(async () => {
  await Promise.all(
    openServers
      .splice(0)
      .map(
        (server) =>
          new Promise<void>((resolve, reject) =>
            server.close((error) => (error ? reject(error) : resolve())),
          ),
      ),
  );
});

function replyMessage(contextId: string): Message {
  const parts: Part[] = [
    {
      content: { $case: 'text', value: 'reference-agent reply' },
      filename: '',
      mediaType: 'text/plain',
      metadata: undefined,
    },
  ];
  return {
    messageId: 'reply-1',
    contextId,
    taskId: '',
    role: Role.ROLE_AGENT,
    parts,
    metadata: undefined,
    extensions: [],
    referenceTaskIds: [],
  };
}

async function startReferenceAgent(
  advertisedBaseUrl?: string,
  requestCount?: { a2a: number },
): Promise<string> {
  let baseUrl = '';
  const card = (): AgentCard =>
    ({
      name: 'Reference Agent',
      description: 'Local official-SDK test agent',
      provider: undefined,
      version: '1.0.0',
      supportedInterfaces: [
        {
          url: `${advertisedBaseUrl ?? baseUrl}/a2a`,
          protocolBinding: 'JSONRPC',
          protocolVersion: '1.0',
          tenant: '',
        },
      ],
      capabilities: { streaming: false, pushNotifications: false, extensions: [] },
      defaultInputModes: ['text/plain'],
      defaultOutputModes: ['text/plain'],
      skills: [
        {
          id: 'echo',
          name: 'Echo',
          description: 'Returns a fixed message',
          tags: ['test'],
          examples: [],
          inputModes: ['text/plain'],
          outputModes: ['text/plain'],
          securityRequirements: [],
        },
      ],
      signatures: [],
      securitySchemes: {},
      securityRequirements: [],
    }) as unknown as AgentCard;

  const executor: AgentExecutor = {
    execute: async (context, eventBus) => {
      eventBus.publish(AgentEvent.message(replyMessage(context.contextId)));
      eventBus.finished();
    },
    cancelTask: async (_taskId, eventBus) => {
      eventBus.finished();
    },
  };
  const jsonRpcRef: { current?: JsonRpcTransportHandler } = {};

  const httpServer = createServer(async (request, response) => {
    if (request.method === 'GET' && request.url === '/.well-known/agent-card.json') {
      response.writeHead(200, { 'content-type': 'application/json' });
      response.end(JSON.stringify(card()));
      return;
    }
    if (request.method === 'POST' && request.url === '/a2a') {
      if (requestCount) requestCount.a2a += 1;
      if (!jsonRpcRef.current) throw new Error('reference agent not initialized');
      let body = '';
      for await (const chunk of request) body += String(chunk);
      const result = await jsonRpcRef.current.handle(body, new ServerCallContext());
      if (Symbol.asyncIterator in Object(result)) {
        response.writeHead(500);
        response.end('unexpected streaming response');
        return;
      }
      response.writeHead(200, { 'content-type': 'application/json' });
      response.end(JSON.stringify(result));
      return;
    }
    response.writeHead(404);
    response.end();
  });
  openServers.push(httpServer);
  httpServer.listen(0, '127.0.0.1');
  await once(httpServer, 'listening');
  const address = httpServer.address();
  if (address === null || typeof address === 'string')
    throw new Error('reference agent has no port');
  baseUrl = `http://127.0.0.1:${address.port}`;
  const requestHandler = new DefaultRequestHandler(card(), new InMemoryTaskStore(), executor);
  jsonRpcRef.current = new JsonRpcTransportHandler(requestHandler);
  return baseUrl;
}

async function connectedClient(runtime?: A2ARuntime, guardConfig: GuardConfig = localGuard) {
  const [clientTransport, serverTransport] = InMemoryTransport.createLinkedPair();
  const server = createA2AServer(guardConfig, runtime);
  const client = new Client({ name: 'a2a-client-test', version: '1.0.0' }, { capabilities: {} });
  await server.connect(serverTransport);
  await client.connect(clientTransport);
  return { client, server };
}

function parsedText(result: unknown): Record<string, unknown> {
  if (result === null || typeof result !== 'object') throw new Error('expected tool result');
  const content = (result as { content?: unknown }).content;
  if (!Array.isArray(content)) throw new Error('expected content array');
  const first = content[0] as { type?: string; text?: string } | undefined;
  if (!first) throw new Error('expected tool content');
  if (first.type !== 'text') throw new Error('expected text tool result');
  return JSON.parse(first.text ?? '') as Record<string, unknown>;
}

describe('MCP handshake and A2A end-to-end path', () => {
  it('negotiates MCP, lists seven tools, and validates an inline card without baseUrl', async () => {
    const { client, server } = await connectedClient();
    try {
      const tools = await client.listTools();
      expect(tools.tools).toHaveLength(7);
      expect(tools.tools.map((tool) => tool.name)).toContain('cancel_task');
      const sendMessage = tools.tools.find((tool) => tool.name === 'send_message');
      const streamMessage = tools.tools.find((tool) => tool.name === 'stream_message');
      const getTask = tools.tools.find((tool) => tool.name === 'get_task');
      expect(sendMessage?.inputSchema.properties?.text).toMatchObject({ minLength: 1 });
      expect(streamMessage?.inputSchema.properties?.maxEvents).toMatchObject({ type: 'integer' });
      expect(getTask?.inputSchema.properties?.historyLength).toMatchObject({ type: 'integer' });

      const result = await client.callTool({
        name: 'validate_agent_card',
        arguments: { card: { name: 'intentionally incomplete' } },
      });
      expect(result.isError).not.toBe(true);
      expect(parsedText(result).structure).toBe('malformed');
    } finally {
      await client.close();
      await server.close();
    }
  });

  it('fetches a card and sends a message through the official A2A client/server stack', async () => {
    const baseUrl = await startReferenceAgent();
    const { client, server } = await connectedClient();
    try {
      const fetched = await client.callTool({
        name: 'fetch_agent_card',
        arguments: { baseUrl },
      });
      expect(fetched.isError, JSON.stringify(fetched)).not.toBe(true);
      expect(parsedText(fetched).structure).toBe('valid');

      const sent = await client.callTool({
        name: 'send_message',
        arguments: { baseUrl, text: 'hello' },
      });
      expect(sent.isError).not.toBe(true);
      expect(parsedText(sent).arm).toBe('message');
      expect(JSON.stringify(parsedText(sent))).toContain('reference-agent reply');
    } finally {
      await client.close();
      await server.close();
    }
  });

  it('refuses a card-advertised cross-origin message target by default', async () => {
    const requests = { a2a: 0 };
    const sinkUrl = await startReferenceAgent(undefined, requests);
    const cardUrl = await startReferenceAgent(sinkUrl);
    const { client, server } = await connectedClient();
    try {
      const result = await client.callTool({
        name: 'send_message',
        arguments: { baseUrl: cardUrl, text: 'do not route this elsewhere' },
      });
      expect(result.isError).toBe(true);
      expect((parsedText(result).error as { code: string }).code).toBe('DESTINATION_BLOCKED');
      expect(requests.a2a).toBe(0);
    } finally {
      await client.close();
      await server.close();
    }
  });

  it('allows a card-advertised cross-origin target only with a destination-origin opt-in', async () => {
    const requests = { a2a: 0 };
    const sinkUrl = await startReferenceAgent(undefined, requests);
    const cardUrl = await startReferenceAgent(sinkUrl);
    const { client, server } = await connectedClient(undefined, {
      ...localGuard,
      allowedDestinationOrigins: new Set([new URL(sinkUrl).origin]),
    });
    try {
      const result = await client.callTool({
        name: 'send_message',
        arguments: { baseUrl: cardUrl, text: 'explicitly routed' },
      });
      expect(result.isError, JSON.stringify(result)).not.toBe(true);
      expect(requests.a2a).toBe(1);
    } finally {
      await client.close();
      await server.close();
    }
  });

  it('returns structured tool errors and refuses disabled cancel_task before network I/O', async () => {
    const runtime: A2ARuntime = { cardFor: vi.fn(), clientFor: vi.fn() };
    const { client, server } = await connectedClient(runtime);
    try {
      const invalid = await client.callTool({ name: 'send_message', arguments: { text: '' } });
      expect(invalid.isError).toBe(true);
      expect((parsedText(invalid).error as { code: string }).code).toBe('INVALID_ARGUMENT');

      const cancel = await client.callTool({
        name: 'cancel_task',
        arguments: {
          baseUrl: 'https://agent.example',
          taskId: 'task-42',
          confirmation: 'cancel task-42',
        },
      });
      expect(cancel.isError).toBe(true);
      expect((parsedText(cancel).error as { code: string }).code).toBe('CANCELLATION_DISABLED');
      expect(runtime.clientFor).not.toHaveBeenCalled();
    } finally {
      await client.close();
      await server.close();
    }
  });

  it('requires the exact task-bound phrase after cancellation is enabled', async () => {
    const runtime: A2ARuntime = { cardFor: vi.fn(), clientFor: vi.fn() };
    const { client, server } = await connectedClient(runtime, {
      ...localGuard,
      allowTaskCancellation: true,
    });
    try {
      const result = await client.callTool({
        name: 'cancel_task',
        arguments: {
          baseUrl: 'https://agent.example',
          taskId: 'task-42',
          confirmation: 'cancel task-41',
        },
      });
      expect(result.isError).toBe(true);
      expect((parsedText(result).error as { code: string }).code).toBe('CONFIRMATION_REQUIRED');
      expect(runtime.clientFor).not.toHaveBeenCalled();
    } finally {
      await client.close();
      await server.close();
    }
  });

  it('preserves A2A protocol error codes in an MCP tool error result', async () => {
    const protocolError = Object.assign(new Error('remote task not found'), { code: -32_001 });
    const runtime: A2ARuntime = {
      cardFor: vi.fn(),
      clientFor: vi.fn(async () => {
        throw protocolError;
      }),
    };
    const { client, server } = await connectedClient(runtime);
    try {
      const result = await client.callTool({
        name: 'get_task',
        arguments: { baseUrl: 'https://agent.example', taskId: 'missing-task' },
      });
      expect(result.isError).toBe(true);
      expect(parsedText(result).error).toMatchObject({
        code: -32_001,
        message: 'remote task not found',
      });
    } finally {
      await client.close();
      await server.close();
    }
  });

  it('allows cancel_task only when the exact task-bound phrase is present', async () => {
    const cancelTask = vi.fn(async () => ({ id: 'task-42', status: { state: 5 } }));
    const runtime: A2ARuntime = {
      cardFor: vi.fn(),
      clientFor: vi.fn(async () => ({ cancelTask }) as unknown as A2AClient),
    };
    const { client, server } = await connectedClient(runtime, {
      ...localGuard,
      allowTaskCancellation: true,
    });
    try {
      const result = await client.callTool({
        name: 'cancel_task',
        arguments: {
          baseUrl: 'https://agent.example',
          taskId: 'task-42',
          confirmation: 'cancel task-42',
        },
      });
      expect(result.isError).not.toBe(true);
      expect(cancelTask).toHaveBeenCalledOnce();
    } finally {
      await client.close();
      await server.close();
    }
  });
});
