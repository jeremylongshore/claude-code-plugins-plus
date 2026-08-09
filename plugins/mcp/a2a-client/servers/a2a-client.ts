#!/usr/bin/env node

/**
 * a2a-client — an MCP server that lets a Claude Code session speak Agent2Agent (A2A).
 *
 * Wraps the official @a2a-js/sdk client. This server conforms to the published A2A
 * specification; it defines no wire format of its own.
 *
 * Trust posture, deliberately: an agent card is an externally-authored manifest fetched
 * from outside the trust boundary. Every tool here REPORTS what a card claims and never
 * converts a claim into local authority — no capability is auto-enabled, no interface URL
 * is adopted as a default, no card-named URL is resolved on the card's say-so.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import {
  ClientFactory,
  ClientFactoryOptions,
  DefaultAgentCardResolver,
  JsonRpcTransportFactory,
  RestTransportFactory,
  createAuthenticatingFetchWithRetry,
  type AuthenticationHandler,
  type Client,
  type HttpHeaders,
} from '@a2a-js/sdk/client';
import { Role, type AgentCard, type Message, type Part } from '@a2a-js/sdk';
import { auditCard, claimsOf } from './card-audit.js';
import { z } from 'zod';
import { randomUUID } from 'node:crypto';

// ── Auth ────────────────────────────────────────────────────────────────────────
// Credentials belong to the operator and arrive through the environment. They are
// never read from an agent card, never logged, and never echoed in a tool result.

const AUTH_HEADER_NAME = process.env.A2A_AUTH_HEADER_NAME ?? 'Authorization';
const BEARER_TOKEN = process.env.A2A_BEARER_TOKEN ?? '';
const API_KEY = process.env.A2A_API_KEY ?? '';

function operatorHeaders(): HttpHeaders {
  if (BEARER_TOKEN) return { [AUTH_HEADER_NAME]: `Bearer ${BEARER_TOKEN}` };
  if (API_KEY) return { [AUTH_HEADER_NAME]: API_KEY };
  return {};
}

const authHandler: AuthenticationHandler = {
  headers: async () => operatorHeaders(),
  // No credential discovery and no re-auth negotiation: a 401/403 is surfaced to the
  // operator rather than answered with a guessed second credential.
  shouldRetryWithHeaders: async () => undefined,
};

const authenticatingFetch = createAuthenticatingFetchWithRetry(fetch, authHandler);

// ── Client construction ─────────────────────────────────────────────────────────
// A client is built per call from the card at the given base URL. Nothing is cached
// between calls, so a card cannot install itself as a durable default.

function factory(): ClientFactory {
  return new ClientFactory(
    ClientFactoryOptions.createFrom(ClientFactoryOptions.default, {
      transports: [
        new JsonRpcTransportFactory({ fetchImpl: authenticatingFetch }),
        new RestTransportFactory({ fetchImpl: authenticatingFetch }),
      ],
      cardResolver: new DefaultAgentCardResolver({ fetchImpl: authenticatingFetch }),
    }),
  );
}

async function clientFor(baseUrl: string, cardPath?: string): Promise<Client> {
  return factory().createFromUrl(baseUrl, cardPath);
}

async function cardFor(baseUrl: string, cardPath?: string): Promise<AgentCard> {
  return new DefaultAgentCardResolver({ fetchImpl: authenticatingFetch }).resolve(baseUrl, cardPath);
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

// ── Tool schemas ────────────────────────────────────────────────────────────────

const BaseTarget = { baseUrl: z.string().min(1), cardPath: z.string().optional() };

const FetchAgentCardSchema = z.object(BaseTarget);
const ValidateAgentCardSchema = z.object({ ...BaseTarget, card: z.unknown().optional() });
const SendMessageSchema = z.object({
  ...BaseTarget,
  text: z.string().min(1),
  taskId: z.string().optional(),
  contextId: z.string().optional(),
});
const StreamMessageSchema = z.object({
  ...BaseTarget,
  text: z.string().min(1),
  contextId: z.string().optional(),
  maxEvents: z.number().int().positive().max(500).optional().default(50),
});
const GetTaskSchema = z.object({
  ...BaseTarget,
  taskId: z.string().min(1),
  historyLength: z.number().int().nonnegative().optional(),
});
const ListTasksSchema = z.object({
  ...BaseTarget,
  contextId: z.string().optional(),
  pageSize: z.number().int().min(1).max(100).optional(),
});
const CancelTaskSchema = z.object({ ...BaseTarget, taskId: z.string().min(1) });

// ── Tool implementations ────────────────────────────────────────────────────────

async function fetchAgentCard(a: z.infer<typeof FetchAgentCardSchema>) {
  const card = await cardFor(a.baseUrl, a.cardPath);
  const audit = auditCard(card);
  return {
    note: 'Claims are reported, not adopted. No capability here is enabled by this result.',
    structure: audit.structure,
    missingFields: audit.missingFields,
    signatureStatus: audit.signatureStatus,
    claims: claimsOf(card),
    findings: audit.findings,
  };
}

async function validateAgentCard(a: z.infer<typeof ValidateAgentCardSchema>) {
  const card = (a.card as AgentCard | undefined) ?? (await cardFor(a.baseUrl, a.cardPath));
  const audit = auditCard(card);
  return {
    structure: audit.structure,
    missingFields: audit.missingFields,
    signatureStatus: audit.signatureStatus,
    findings: audit.findings,
    operatorDecisionsRequired: audit.operatorDecisionsRequired,
  };
}

async function sendMessage(a: z.infer<typeof SendMessageSchema>) {
  const client = await clientFor(a.baseUrl, a.cardPath);
  const result = await client.sendMessage({
    tenant: '',
    message: textMessage(a.text, a.taskId, a.contextId),
    configuration: undefined,
    metadata: undefined,
  });
  // SendMessageResult is a union: an agent may answer inline without creating a task.
  const arm = 'status' in result ? 'task' : 'message';
  return { protocolVersion: client.protocolVersion, arm, result };
}

async function streamMessage(a: z.infer<typeof StreamMessageSchema>) {
  const client = await clientFor(a.baseUrl, a.cardPath);
  const events: unknown[] = [];
  let truncated = false;
  for await (const event of client.sendMessageStream({
    tenant: '',
    message: textMessage(a.text, undefined, a.contextId),
    configuration: undefined,
    metadata: undefined,
  })) {
    events.push(event);
    if (events.length >= a.maxEvents) {
      truncated = true;
      break;
    }
  }
  return { protocolVersion: client.protocolVersion, eventCount: events.length, truncated, events };
}

async function getTask(a: z.infer<typeof GetTaskSchema>) {
  const client = await clientFor(a.baseUrl, a.cardPath);
  return client.getTask({ tenant: '', id: a.taskId, historyLength: a.historyLength });
}

async function listTasks(a: z.infer<typeof ListTasksSchema>) {
  const client = await clientFor(a.baseUrl, a.cardPath);
  return client.listTasks({
    tenant: '',
    contextId: a.contextId ?? '',
    status: 0,
    pageSize: a.pageSize,
    pageToken: '',
    historyLength: undefined,
    statusTimestampAfter: undefined,
  });
}

async function cancelTask(a: z.infer<typeof CancelTaskSchema>) {
  const client = await clientFor(a.baseUrl, a.cardPath);
  const task = await client.cancelTask({ tenant: '', id: a.taskId, metadata: undefined });
  return {
    task,
    note: 'Cancellation is a request. Treat it as pending until the returned state is CANCELED.',
  };
}

// ── Server wiring ───────────────────────────────────────────────────────────────

const server = new Server(
  { name: 'a2a-client', version: '0.1.0' },
  { capabilities: { tools: {} } },
);

const TARGET_PROPS = {
  baseUrl: { type: 'string', description: 'Base URL of the remote A2A agent' },
  cardPath: {
    type: 'string',
    description: 'Agent-card path. Defaults to /.well-known/agent-card.json',
  },
};

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: 'fetch_agent_card',
      description:
        "Fetch a remote agent's card and report its claims plus structural findings. Claims are reported, never adopted — nothing here enables a capability or changes local configuration.",
      inputSchema: { type: 'object', properties: { ...TARGET_PROPS }, required: ['baseUrl'] },
    },
    {
      name: 'validate_agent_card',
      description:
        'Validate an agent card against the required A2A fields and return a structure verdict, findings, and a count of decisions that require an operator.',
      inputSchema: {
        type: 'object',
        properties: {
          ...TARGET_PROPS,
          card: { type: 'object', description: 'An already-fetched card to validate offline' },
        },
        required: [],
      },
    },
    {
      name: 'send_message',
      description:
        'Send a message to a remote A2A agent. The response is a union — a Task, or an inline Message when the agent answers without creating one.',
      inputSchema: {
        type: 'object',
        properties: {
          ...TARGET_PROPS,
          text: { type: 'string', description: 'Message text' },
          taskId: { type: 'string', description: 'Continue an interrupted task' },
          contextId: { type: 'string', description: 'Group into an existing conversation' },
        },
        required: ['baseUrl', 'text'],
      },
    },
    {
      name: 'stream_message',
      description:
        'Send a message and collect streamed events. Falls back to non-streaming when the agent does not support streaming.',
      inputSchema: {
        type: 'object',
        properties: {
          ...TARGET_PROPS,
          text: { type: 'string', description: 'Message text' },
          contextId: { type: 'string' },
          maxEvents: { type: 'number', description: 'Event cap before truncating (default 50)' },
        },
        required: ['baseUrl', 'text'],
      },
    },
    {
      name: 'get_task',
      description: 'Retrieve the current state of a task, including status and artifacts.',
      inputSchema: {
        type: 'object',
        properties: {
          ...TARGET_PROPS,
          taskId: { type: 'string' },
          historyLength: { type: 'number' },
        },
        required: ['baseUrl', 'taskId'],
      },
    },
    {
      name: 'list_tasks',
      description: 'List tasks, optionally filtered to one conversation context.',
      inputSchema: {
        type: 'object',
        properties: { ...TARGET_PROPS, contextId: { type: 'string' }, pageSize: { type: 'number' } },
        required: ['baseUrl'],
      },
    },
    {
      name: 'cancel_task',
      description:
        'Request cancellation of a task. Success is not guaranteed; the agent may report the task is not cancelable.',
      inputSchema: {
        type: 'object',
        properties: { ...TARGET_PROPS, taskId: { type: 'string' } },
        required: ['baseUrl', 'taskId'],
      },
    },
  ],
}));

const HANDLERS: Record<string, (args: unknown) => Promise<unknown>> = {
  fetch_agent_card: (a) => fetchAgentCard(FetchAgentCardSchema.parse(a)),
  validate_agent_card: (a) => validateAgentCard(ValidateAgentCardSchema.parse(a)),
  send_message: (a) => sendMessage(SendMessageSchema.parse(a)),
  stream_message: (a) => streamMessage(StreamMessageSchema.parse(a)),
  get_task: (a) => getTask(GetTaskSchema.parse(a)),
  list_tasks: (a) => listTasks(ListTasksSchema.parse(a)),
  cancel_task: (a) => cancelTask(CancelTaskSchema.parse(a)),
};

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const handler = HANDLERS[request.params.name];
  if (!handler) throw new Error(`Unknown tool: ${request.params.name}`);
  try {
    const result = await handler(request.params.arguments);
    return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
  } catch (error) {
    if (error instanceof z.ZodError) {
      throw new Error(
        `Invalid arguments: ${error.issues.map((e) => `${e.path.join('.')}: ${e.message}`).join(', ')}`,
      );
    }
    // Surface protocol errors verbatim — a spec error paraphrased into prose loses its code.
    throw error;
  }
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('a2a-client MCP server running on stdio');
}

// Only auto-start under stdio; importing this module for tests must not connect.
if (process.env.A2A_CLIENT_NO_AUTOSTART !== '1') {
  main().catch((error) => {
    console.error('Fatal error in main():', error);
    process.exit(1);
  });
}
