#!/usr/bin/env node

/** MCP-to-A2A bridge. Remote agent cards are untrusted reports, never local authority. */

import { randomUUID } from 'node:crypto';
import { pathToFileURL } from 'node:url';
import { Role, type AgentCard, type Message, type Part } from '@a2a-js/sdk';
import {
  ClientFactory,
  ClientFactoryOptions,
  DefaultAgentCardResolver,
  JsonRpcTransportFactory,
  RestTransportFactory,
  type Client,
} from '@a2a-js/sdk/client';
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import { z } from 'zod';
import { auditCard, claimsOf } from './card-audit.js';
import {
  BlockedDestinationError,
  configFromEnv,
  createGuardedDispatcher,
  createGuardedFetch,
  type GuardConfig,
} from './net-guard.js';

const SERVER_INFO = { name: 'a2a-client', version: '0.1.0' } as const;
const CANCEL_CONFIRMATION_PREFIX = 'cancel ';

class ConfirmationRequiredError extends Error {
  readonly code = 'CONFIRMATION_REQUIRED';

  constructor(taskId: string) {
    super(`cancel_task requires confirmation exactly equal to "${CANCEL_CONFIRMATION_PREFIX}${taskId}"`);
    this.name = 'ConfirmationRequiredError';
  }
}

class CancellationDisabledError extends Error {
  readonly code = 'CANCELLATION_DISABLED';

  constructor() {
    super('cancel_task is disabled. Set A2A_ALLOW_TASK_CANCELLATION=1 to opt in explicitly.');
    this.name = 'CancellationDisabledError';
  }
}

export interface A2ARuntime {
  clientFor(baseUrl: string, cardPath?: string): Promise<Client>;
  cardFor(baseUrl: string, cardPath?: string): Promise<AgentCard>;
}

function runtimeFromConfig(guardConfig: GuardConfig): A2ARuntime {
  const dispatcher = createGuardedDispatcher(guardConfig);
  const guardedFetchFor = (baseUrl: string) =>
    createGuardedFetch(guardConfig, fetch, undefined, dispatcher, baseUrl);
  const factory = (baseUrl: string) => {
    const guardedFetch = guardedFetchFor(baseUrl);
    return new ClientFactory(
      ClientFactoryOptions.createFrom(ClientFactoryOptions.default, {
        transports: [
          new JsonRpcTransportFactory({ fetchImpl: guardedFetch }),
          new RestTransportFactory({ fetchImpl: guardedFetch }),
        ],
        cardResolver: new DefaultAgentCardResolver({ fetchImpl: guardedFetch }),
      }),
    );
  };

  return {
    clientFor: (baseUrl, cardPath) => factory(baseUrl).createFromUrl(baseUrl, cardPath),
    cardFor: (baseUrl, cardPath) =>
      new DefaultAgentCardResolver({ fetchImpl: guardedFetchFor(baseUrl) }).resolve(
        baseUrl,
        cardPath,
      ),
  };
}

function textMessage(text: string, taskId?: string, contextId?: string): Message {
  const parts: Part[] = [
    { content: { $case: 'text', value: text }, filename: '', mediaType: '', metadata: undefined },
  ];
  return {
    messageId: randomUUID(),
    contextId: contextId ?? '',
    taskId: taskId ?? '',
    role: Role.ROLE_USER,
    parts,
    metadata: undefined,
    extensions: [],
    referenceTaskIds: [],
  };
}

const RequiredTarget = { baseUrl: z.string().url(), cardPath: z.string().optional() };
const OptionalTarget = { baseUrl: z.string().url().optional(), cardPath: z.string().optional() };
const FetchAgentCardSchema = z.object(RequiredTarget);
const ValidateAgentCardSchema = z
  .object({ ...OptionalTarget, card: z.record(z.string(), z.unknown()).optional() })
  .refine((value) => value.baseUrl !== undefined || value.card !== undefined, {
    message: 'Either baseUrl or card is required',
  });
const SendMessageSchema = z.object({
  ...RequiredTarget,
  text: z.string().min(1),
  taskId: z.string().optional(),
  contextId: z.string().optional(),
});
const StreamMessageSchema = z.object({
  ...RequiredTarget,
  text: z.string().min(1),
  contextId: z.string().optional(),
  maxEvents: z.number().int().positive().max(500).optional().default(50),
});
const GetTaskSchema = z.object({
  ...RequiredTarget,
  taskId: z.string().min(1),
  historyLength: z.number().int().nonnegative().optional(),
});
const ListTasksSchema = z.object({
  ...RequiredTarget,
  contextId: z.string().optional(),
  pageSize: z.number().int().min(1).max(100).optional(),
});
const CancelTaskSchema = z.object({
  ...RequiredTarget,
  taskId: z.string().min(1),
  confirmation: z.string().min(1),
});

const TARGET_PROPERTIES = {
  baseUrl: { type: 'string', format: 'uri', description: 'Base URL of the remote A2A agent' },
  cardPath: {
    type: 'string',
    description: 'Agent-card path; defaults to /.well-known/agent-card.json',
  },
} as const;

export const TOOL_DEFINITIONS = [
  {
    name: 'fetch_agent_card',
    description:
      "Fetch a remote agent's card and report its claims and structural findings. Claims are never adopted as local authority.",
    inputSchema: { type: 'object', properties: TARGET_PROPERTIES, required: ['baseUrl'] },
  },
  {
    name: 'validate_agent_card',
    description: 'Validate a fetched or inline A2A agent card without adopting its claims.',
    inputSchema: {
      type: 'object',
      properties: {
        ...TARGET_PROPERTIES,
        card: { type: 'object', description: 'An already-fetched card to validate offline' },
      },
      anyOf: [{ required: ['baseUrl'] }, { required: ['card'] }],
    },
  },
  {
    name: 'send_message',
    description: 'Send a message and report whether the A2A response is a task or inline message.',
    inputSchema: {
      type: 'object',
      properties: {
        ...TARGET_PROPERTIES,
        text: { type: 'string', minLength: 1 },
        taskId: { type: 'string' },
        contextId: { type: 'string' },
      },
      required: ['baseUrl', 'text'],
    },
  },
  {
    name: 'stream_message',
    description: 'Send a message and collect at most maxEvents streamed A2A events.',
    inputSchema: {
      type: 'object',
      properties: {
        ...TARGET_PROPERTIES,
        text: { type: 'string', minLength: 1 },
        contextId: { type: 'string' },
        maxEvents: { type: 'integer', minimum: 1, maximum: 500, default: 50 },
      },
      required: ['baseUrl', 'text'],
    },
  },
  {
    name: 'get_task',
    description: 'Retrieve an A2A task state, artifacts, and optional history.',
    inputSchema: {
      type: 'object',
      properties: {
        ...TARGET_PROPERTIES,
        taskId: { type: 'string', minLength: 1 },
        historyLength: { type: 'integer', minimum: 0 },
      },
      required: ['baseUrl', 'taskId'],
    },
  },
  {
    name: 'list_tasks',
    description: 'List A2A tasks, optionally scoped to a conversation context.',
    inputSchema: {
      type: 'object',
      properties: {
        ...TARGET_PROPERTIES,
        contextId: { type: 'string' },
        pageSize: { type: 'integer', minimum: 1, maximum: 100 },
      },
      required: ['baseUrl'],
    },
  },
  {
    name: 'cancel_task',
    description:
      'Destructive and default-off: requires A2A_ALLOW_TASK_CANCELLATION=1, host approval, and confirmation exactly equal to "cancel <taskId>".',
    inputSchema: {
      type: 'object',
      properties: {
        ...TARGET_PROPERTIES,
        taskId: { type: 'string', minLength: 1 },
        confirmation: {
          type: 'string',
          minLength: 1,
          description: 'Exact phrase: cancel <taskId>',
        },
      },
      required: ['baseUrl', 'taskId', 'confirmation'],
    },
  },
] as const;

type Handler = (args: unknown) => Promise<unknown>;

function handlers(runtime: A2ARuntime, guardConfig: GuardConfig): Record<string, Handler> {
  return {
    fetch_agent_card: async (raw) => {
      const args = FetchAgentCardSchema.parse(raw);
      const card = await runtime.cardFor(args.baseUrl, args.cardPath);
      const audit = auditCard(card);
      return {
        note: 'Claims are reported, not adopted. No capability is enabled by this result.',
        structure: audit.structure,
        missingFields: audit.missingFields,
        signatureStatus: audit.signatureStatus,
        claims: claimsOf(card),
        findings: audit.findings,
      };
    },
    validate_agent_card: async (raw) => {
      const args = ValidateAgentCardSchema.parse(raw);
      const card =
        args.card !== undefined
          ? (args.card as unknown as AgentCard)
          : await runtime.cardFor(args.baseUrl!, args.cardPath);
      const audit = auditCard(card);
      return {
        structure: audit.structure,
        missingFields: audit.missingFields,
        signatureStatus: audit.signatureStatus,
        findings: audit.findings,
        operatorDecisionsRequired: audit.operatorDecisionsRequired,
      };
    },
    send_message: async (raw) => {
      const args = SendMessageSchema.parse(raw);
      const client = await runtime.clientFor(args.baseUrl, args.cardPath);
      const result = await client.sendMessage({
        tenant: '',
        message: textMessage(args.text, args.taskId, args.contextId),
        configuration: undefined,
        metadata: undefined,
      });
      return {
        protocolVersion: client.protocolVersion,
        arm: 'status' in result ? 'task' : 'message',
        result,
      };
    },
    stream_message: async (raw) => {
      const args = StreamMessageSchema.parse(raw);
      const client = await runtime.clientFor(args.baseUrl, args.cardPath);
      const events: unknown[] = [];
      let truncated = false;
      for await (const event of client.sendMessageStream({
        tenant: '',
        message: textMessage(args.text, undefined, args.contextId),
        configuration: undefined,
        metadata: undefined,
      })) {
        events.push(event);
        if (events.length >= args.maxEvents) {
          truncated = true;
          break;
        }
      }
      return { protocolVersion: client.protocolVersion, eventCount: events.length, truncated, events };
    },
    get_task: async (raw) => {
      const args = GetTaskSchema.parse(raw);
      const client = await runtime.clientFor(args.baseUrl, args.cardPath);
      return client.getTask({ tenant: '', id: args.taskId, historyLength: args.historyLength });
    },
    list_tasks: async (raw) => {
      const args = ListTasksSchema.parse(raw);
      const client = await runtime.clientFor(args.baseUrl, args.cardPath);
      return client.listTasks({
        tenant: '',
        contextId: args.contextId ?? '',
        status: 0,
        pageSize: args.pageSize,
        pageToken: '',
        historyLength: undefined,
        statusTimestampAfter: undefined,
      });
    },
    cancel_task: async (raw) => {
      const args = CancelTaskSchema.parse(raw);
      if (!guardConfig.allowTaskCancellation) throw new CancellationDisabledError();
      if (args.confirmation !== `${CANCEL_CONFIRMATION_PREFIX}${args.taskId}`) {
        throw new ConfirmationRequiredError(args.taskId);
      }
      const client = await runtime.clientFor(args.baseUrl, args.cardPath);
      const task = await client.cancelTask({ tenant: '', id: args.taskId, metadata: undefined });
      return {
        task,
        note: 'Cancellation is a request. Treat it as pending until the returned state is CANCELED.',
      };
    },
  };
}

interface StructuredError {
  ok: false;
  error: {
    code: string | number;
    message: string;
    details?: unknown;
  };
}

function structuredError(error: unknown): StructuredError {
  if (error instanceof z.ZodError) {
    return {
      ok: false,
      error: { code: 'INVALID_ARGUMENT', message: 'Invalid tool arguments', details: error.issues },
    };
  }
  if (
    error instanceof BlockedDestinationError ||
    error instanceof ConfirmationRequiredError ||
    error instanceof CancellationDisabledError
  ) {
    return { ok: false, error: { code: error.code, message: error.message } };
  }

  const record = error !== null && typeof error === 'object' ? (error as Record<string, unknown>) : {};
  const code =
    typeof record.code === 'string' || typeof record.code === 'number'
      ? record.code
      : 'A2A_REQUEST_FAILED';
  const message = error instanceof Error ? error.message : String(error);
  return { ok: false, error: { code, message } };
}

function toolResult(value: unknown, isError = false) {
  return {
    isError,
    content: [{ type: 'text' as const, text: JSON.stringify(value, null, 2) }],
  };
}

export function createA2AServer(
  guardConfig: GuardConfig = configFromEnv(),
  runtime: A2ARuntime = runtimeFromConfig(guardConfig),
): Server {
  const server = new Server(SERVER_INFO, { capabilities: { tools: {} } });
  const toolHandlers = handlers(runtime, guardConfig);

  server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: [...TOOL_DEFINITIONS] }));
  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const handler = toolHandlers[request.params.name];
    if (!handler) {
      return toolResult(
        { ok: false, error: { code: 'UNKNOWN_TOOL', message: `Unknown tool: ${request.params.name}` } },
        true,
      );
    }
    try {
      return toolResult(await handler(request.params.arguments));
    } catch (error) {
      return toolResult(structuredError(error), true);
    }
  });
  return server;
}

export async function main(): Promise<void> {
  await createA2AServer().connect(new StdioServerTransport());
  console.error('a2a-client MCP server running on stdio');
}

const launchedDirectly = process.argv[1]
  ? import.meta.url === pathToFileURL(process.argv[1]).href
  : false;
if (launchedDirectly) {
  main().catch((error: unknown) => {
    console.error('Fatal error in main():', error);
    process.exitCode = 1;
  });
}
