import chokidar, { type FSWatcher } from 'chokidar';
import { readFile } from 'fs/promises';
import { EventEmitter } from 'events';
import { join } from 'path';
import type {
  WatcherConfig,
  ConversationData,
  AnalyticsEvent,
  PluginActivationEvent,
  SkillTriggerEvent,
  LLMCallEvent,
  ConversationCreatedEvent,
  ConversationUpdatedEvent,
} from './types.js';

/**
 * ConversationWatcher - Monitors Claude Code conversation files for analytics events
 */
export class ConversationWatcher extends EventEmitter {
  private watcher: FSWatcher | null = null;
  private config: Required<WatcherConfig>;
  private conversationCache: Map<string, ConversationData> = new Map();

  constructor(config: WatcherConfig) {
    super();
    this.config = {
      conversationsPath: config.conversationsPath,
      debounceMs: config.debounceMs ?? 500,
      ignoreInitial: config.ignoreInitial ?? true,
    };
  }

  /**
   * Start watching the conversations directory
   */
  start(): void {
    if (this.watcher) {
      console.warn('Watcher already started');
      return;
    }

    console.log(`Starting conversation watcher: ${this.config.conversationsPath}`);

    this.watcher = chokidar.watch(join(this.config.conversationsPath, '*.json'), {
      persistent: true,
      ignoreInitial: this.config.ignoreInitial,
      awaitWriteFinish: {
        stabilityThreshold: this.config.debounceMs,
        pollInterval: 100,
      },
    });

    this.watcher
      .on('add', (path: string) => this.handleFileAdded(path))
      .on('change', (path: string) => this.handleFileChanged(path))
      .on('error', (error: unknown) => this.handleError(error as Error));

    console.log('Conversation watcher started successfully');
  }

  /**
   * Stop watching
   */
  async stop(): Promise<void> {
    if (this.watcher) {
      await this.watcher.close();
      this.watcher = null;
      console.log('Conversation watcher stopped');
    }
  }

  /**
   * Handle new conversation file detected
   */
  private async handleFileAdded(filePath: string): Promise<void> {
    try {
      const conversation = await this.parseConversationFile(filePath);
      if (!conversation) return;

      this.conversationCache.set(conversation.id, conversation);

      const event: ConversationCreatedEvent = {
        type: 'conversation.created',
        timestamp: Date.now(),
        conversationId: conversation.id,
        title: conversation.title,
      };

      this.emit('event', event);
      this.emitPluginEvents(conversation);
    } catch (error) {
      console.error(`Error handling file added: ${filePath}`, error);
    }
  }

  /**
   * Handle conversation file changed
   */
  private async handleFileChanged(filePath: string): Promise<void> {
    try {
      const conversation = await this.parseConversationFile(filePath);
      if (!conversation) return;

      const cachedConversation = this.conversationCache.get(conversation.id);
      this.conversationCache.set(conversation.id, conversation);

      const event: ConversationUpdatedEvent = {
        type: 'conversation.updated',
        timestamp: Date.now(),
        conversationId: conversation.id,
        messageCount: conversation.messages.length,
      };

      this.emit('event', event);

      // Emit events for new messages/plugins
      this.emitPluginEvents(conversation, cachedConversation);
      this.emitLLMEvents(conversation, cachedConversation);
    } catch (error) {
      console.error(`Error handling file changed: ${filePath}`, error);
    }
  }

  /**
   * Parse conversation JSON file
   */
  private async parseConversationFile(filePath: string): Promise<ConversationData | null> {
    try {
      const content = await readFile(filePath, 'utf-8');
      const data = JSON.parse(content) as ConversationData;

      // Basic validation
      if (!data.id || !Array.isArray(data.messages)) {
        console.warn(`Invalid conversation file: ${filePath}`);
        return null;
      }

      return data;
    } catch (error) {
      if (error instanceof SyntaxError) {
        // JSON parsing error - file might be incomplete
        return null;
      }
      throw error;
    }
  }

  /**
   * Emit plugin activation events
   */
  private emitPluginEvents(
    conversation: ConversationData,
    previousConversation?: ConversationData
  ): void {
    const currentPlugins = new Set(conversation.metadata?.plugins ?? []);
    const previousPlugins = new Set(previousConversation?.metadata?.plugins ?? []);

    // Find newly activated plugins
    for (const pluginName of currentPlugins) {
      if (!previousPlugins.has(pluginName)) {
        const event: PluginActivationEvent = {
          type: 'plugin.activation',
          timestamp: Date.now(),
          conversationId: conversation.id,
          pluginName,
        };

        this.emit('event', event);
      }
    }

    // Check for skill triggers in messages
    this.emitSkillEvents(conversation, previousConversation);
  }

  /**
   * Emit skill trigger events
   */
  private emitSkillEvents(
    conversation: ConversationData,
    previousConversation?: ConversationData
  ): void {
    const previousMessageCount = previousConversation?.messages.length ?? 0;
    const newMessages = conversation.messages.slice(previousMessageCount);

    for (const message of newMessages) {
      if (message.metadata?.skill) {
        const event: SkillTriggerEvent = {
          type: 'skill.trigger',
          timestamp: message.timestamp ?? Date.now(),
          conversationId: conversation.id,
          skillName: message.metadata.skill,
          pluginName: message.metadata.plugin ?? 'unknown',
        };

        this.emit('event', event);
      }
    }
  }

  /**
   * Emit LLM call events
   */
  private emitLLMEvents(
    conversation: ConversationData,
    previousConversation?: ConversationData
  ): void {
    const previousMessageCount = previousConversation?.messages.length ?? 0;
    const newMessages = conversation.messages.slice(previousMessageCount);

    for (const message of newMessages) {
      if (message.role === 'assistant' && message.metadata?.tokens) {
        const event: LLMCallEvent = {
          type: 'llm.call',
          timestamp: message.timestamp ?? Date.now(),
          conversationId: conversation.id,
          model: conversation.metadata?.model ?? 'unknown',
          inputTokens: message.metadata.tokens.input,
          outputTokens: message.metadata.tokens.output,
          totalTokens: message.metadata.tokens.total,
        };

        this.emit('event', event);
      }
    }
  }

  /**
   * Handle watcher errors
   */
  private handleError(error: Error): void {
    console.error('Conversation watcher error:', error);
    this.emit('error', error);
  }

  /**
   * Get all tracked conversations
   */
  getConversations(): ConversationData[] {
    return Array.from(this.conversationCache.values());
  }

  /**
   * Get conversation by ID
   */
  getConversation(id: string): ConversationData | undefined {
    return this.conversationCache.get(id);
  }
}
