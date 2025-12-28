/**
 * Event types emitted by the analytics daemon
 */

/**
 * Base event interface - all events extend this
 */
export interface BaseEvent {
  type: string;
  timestamp: number;
  conversationId: string;
}

/**
 * Plugin activation event
 * Emitted when a plugin is activated in a conversation
 */
export interface PluginActivationEvent extends BaseEvent {
  type: 'plugin.activation';
  pluginName: string;
  pluginVersion?: string;
  marketplace?: string;
}

/**
 * Skill trigger event
 * Emitted when an Agent Skill is triggered
 */
export interface SkillTriggerEvent extends BaseEvent {
  type: 'skill.trigger';
  skillName: string;
  pluginName: string;
  triggerPhrase?: string;
}

/**
 * LLM call event
 * Emitted when Claude API is called
 */
export interface LLMCallEvent extends BaseEvent {
  type: 'llm.call';
  model: string;
  inputTokens?: number;
  outputTokens?: number;
  totalTokens?: number;
}

/**
 * Cost update event
 * Emitted when API costs are calculated
 */
export interface CostUpdateEvent extends BaseEvent {
  type: 'cost.update';
  model: string;
  inputCost: number;
  outputCost: number;
  totalCost: number;
  currency: string;
}

/**
 * Rate limit warning event
 * Emitted when approaching or hitting rate limits
 */
export interface RateLimitWarningEvent extends BaseEvent {
  type: 'rate_limit.warning';
  service: string;
  limit: number;
  current: number;
  resetAt?: number;
}

/**
 * Conversation created event
 * Emitted when a new conversation file is detected
 */
export interface ConversationCreatedEvent extends BaseEvent {
  type: 'conversation.created';
  title?: string;
}

/**
 * Conversation updated event
 * Emitted when a conversation file is modified
 */
export interface ConversationUpdatedEvent extends BaseEvent {
  type: 'conversation.updated';
  messageCount: number;
}

/**
 * MCP tool call event
 * Emitted when an MCP tool is invoked
 */
export interface MCPToolCallEvent extends BaseEvent {
  type: 'mcp.tool_call';
  toolName: string;
  mcpServer?: string;
}

/**
 * Union type of all possible events
 */
export type AnalyticsEvent =
  | PluginActivationEvent
  | SkillTriggerEvent
  | LLMCallEvent
  | CostUpdateEvent
  | RateLimitWarningEvent
  | ConversationCreatedEvent
  | ConversationUpdatedEvent
  | MCPToolCallEvent;

/**
 * Conversation file structure (subset of actual conversation JSON)
 */
export interface ConversationData {
  id: string;
  title?: string;
  messages: ConversationMessage[];
  metadata?: {
    plugins?: string[];
    skills?: string[];
    model?: string;
  };
}

/**
 * Conversation message structure
 */
export interface ConversationMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: number;
  metadata?: {
    plugin?: string;
    skill?: string;
    tokens?: {
      input?: number;
      output?: number;
      total?: number;
    };
  };
}

/**
 * File watcher configuration
 */
export interface WatcherConfig {
  conversationsPath: string;
  debounceMs?: number;
  ignoreInitial?: boolean;
}

/**
 * WebSocket server configuration
 */
export interface ServerConfig {
  port: number;
  host?: string;
}
