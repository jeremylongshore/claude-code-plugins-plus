/**
 * Analytics Event Types - Frontend
 * Mirrors backend event types from analytics-daemon
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
 */
export interface PluginActivationEvent extends BaseEvent {
  type: 'plugin.activation';
  pluginName: string;
  pluginVersion?: string;
  marketplace?: string;
}

/**
 * Skill trigger event
 */
export interface SkillTriggerEvent extends BaseEvent {
  type: 'skill.trigger';
  skillName: string;
  pluginName: string;
  triggerPhrase?: string;
}

/**
 * LLM call event
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
 */
export interface ConversationCreatedEvent extends BaseEvent {
  type: 'conversation.created';
  title?: string;
}

/**
 * Conversation updated event
 */
export interface ConversationUpdatedEvent extends BaseEvent {
  type: 'conversation.updated';
  messageCount: number;
}

/**
 * Server connected event (welcome message)
 */
export interface ServerConnectedEvent {
  type: 'server.connected';
  timestamp: number;
  message: string;
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
  | ServerConnectedEvent;

/**
 * WebSocket connection status
 */
export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected';

/**
 * WebSocket configuration
 */
export interface WebSocketConfig {
  url: string;
  reconnectDelay?: number;
  maxReconnectAttempts?: number;
}

/**
 * Active session data
 */
export interface ActiveSession {
  id: string;
  title: string;
  startTime: number;
  pluginUsage: Map<string, number>;
  costIncurred: number;
}

/**
 * Plugin usage statistics
 */
export interface PluginUsage {
  name: string;
  count: number;
  percentage: number;
}

/**
 * Cost breakdown by provider
 */
export interface CostByProvider {
  provider: string;
  model: string;
  cost: number;
}

/**
 * Rate limit tracking
 */
export interface RateLimit {
  name: string;
  current: number;
  limit: number;
  resetTime: number;
}

/**
 * Analytics state for Zustand store
 */
export interface AnalyticsState {
  activeSessions: ActiveSession[];
  pluginBreakdown: Map<string, number>;
  costByProvider: Map<string, number>;
  rateLimits: RateLimit[];

  // Actions
  addSession: (session: ActiveSession) => void;
  updatePluginUsage: (pluginName: string, count: number) => void;
  updateCost: (provider: string, cost: number) => void;
  updateRateLimit: (rateLimit: RateLimit) => void;
}
