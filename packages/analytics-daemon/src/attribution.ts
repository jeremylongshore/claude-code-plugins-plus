/**
 * Attribution Module - Best-effort tracking of plugin/skill/MCP usage
 *
 * This module analyzes Claude conversation logs to detect:
 * - Plugin activations (plugins mentioned in context)
 * - Skill triggers (skill invocations in conversations)
 * - MCP tool calls (MCP server tool usage patterns)
 *
 * Note: This is best-effort attribution. It uses pattern matching and heuristics
 * to infer usage from conversation content. Not all usage may be detected.
 */

import { readFile, writeFile, mkdir } from 'fs/promises';
import { join } from 'path';
import { homedir } from 'os';
import { existsSync } from 'fs';
import type { ConversationData, ConversationMessage } from './types.js';

/**
 * Attribution statistics for a single entity (plugin/skill/MCP)
 */
export interface AttributionStats {
  name: string;
  type: 'plugin' | 'skill' | 'mcp';
  activationCount: number;
  lastActivated: number;
  conversationIds: Set<string>;
  metadata?: {
    pluginName?: string; // For skills, which plugin they belong to
    marketplace?: string; // For plugins, which marketplace
    mcpServer?: string; // For MCP tools, which server provides them
  };
}

/**
 * Complete attribution data store
 */
export interface AttributionData {
  plugins: Map<string, AttributionStats>;
  skills: Map<string, AttributionStats>;
  mcpTools: Map<string, AttributionStats>;
  lastUpdated: number;
}

/**
 * Attribution event emitted when new usage is detected
 */
export interface AttributionEvent {
  type: 'plugin' | 'skill' | 'mcp';
  name: string;
  conversationId: string;
  timestamp: number;
  metadata?: Record<string, unknown>;
}

/**
 * Serializable version of AttributionStats for JSON storage
 */
interface SerializableAttributionStats {
  name: string;
  type: 'plugin' | 'skill' | 'mcp';
  activationCount: number;
  lastActivated: number;
  conversationIds: string[];
  metadata?: {
    pluginName?: string;
    marketplace?: string;
    mcpServer?: string;
  };
}

/**
 * Serializable version of AttributionData for JSON storage
 */
interface SerializableAttributionData {
  plugins: SerializableAttributionStats[];
  skills: SerializableAttributionStats[];
  mcpTools: SerializableAttributionStats[];
  lastUpdated: number;
}

/**
 * Attribution Engine - Tracks plugin/skill/MCP usage across conversations
 */
export class AttributionEngine {
  private data: AttributionData;
  private storagePath: string;
  private callbacks: ((event: AttributionEvent) => void)[] = [];

  constructor(storagePath?: string) {
    this.storagePath = storagePath ?? join(homedir(), '.claude', 'analytics', 'attribution.json');
    this.data = {
      plugins: new Map(),
      skills: new Map(),
      mcpTools: new Map(),
      lastUpdated: Date.now(),
    };
  }

  /**
   * Initialize the attribution engine and load existing data
   */
  async initialize(): Promise<void> {
    await this.ensureStorageDirectory();
    await this.loadData();
  }

  /**
   * Register a callback for attribution events
   */
  onAttribution(callback: (event: AttributionEvent) => void): void {
    this.callbacks.push(callback);
  }

  /**
   * Analyze a conversation for plugin/skill/MCP usage
   * This is the main entry point for processing conversations
   */
  async analyzeConversation(conversation: ConversationData): Promise<void> {
    // Track plugins from metadata
    if (conversation.metadata?.plugins) {
      for (const pluginName of conversation.metadata.plugins) {
        this.trackPlugin(pluginName, conversation.id);
      }
    }

    // Track skills from metadata
    if (conversation.metadata?.skills) {
      for (const skillName of conversation.metadata.skills) {
        this.trackSkill(skillName, conversation.id);
      }
    }

    // Analyze messages for additional patterns
    for (const message of conversation.messages) {
      await this.analyzeMessage(message, conversation.id);
    }

    await this.saveData();
  }

  /**
   * Analyze a single message for attribution patterns
   */
  private async analyzeMessage(message: ConversationMessage, conversationId: string): Promise<void> {
    // Extract plugin usage from message metadata
    if (message.metadata?.plugin) {
      this.trackPlugin(message.metadata.plugin, conversationId);
    }

    // Extract skill usage from message metadata
    if (message.metadata?.skill) {
      this.trackSkill(message.metadata.skill, conversationId, message.metadata.plugin);
    }

    // Pattern matching on message content (best-effort)
    if (message.content) {
      this.detectPatternsInContent(message.content, conversationId);
    }
  }

  /**
   * Detect usage patterns in message content (best-effort heuristics)
   *
   * Security Note: All regex patterns are designed to be ReDoS-safe:
   * - No nested quantifiers (e.g., no (a+)+ patterns)
   * - Simple character classes [a-z0-9-] with single quantifiers
   * - Linear time complexity O(n) where n is input length
   */
  private detectPatternsInContent(content: string, conversationId: string): void {
    // Limit content size to prevent DoS on extremely large messages
    const MAX_CONTENT_LENGTH = 100000; // 100KB
    const safeContent = content.length > MAX_CONTENT_LENGTH
      ? content.slice(0, MAX_CONTENT_LENGTH)
      : content;

    // Detect plugin references
    // Pattern: /plugin install <plugin-name>
    const pluginInstallPattern = /\/plugin\s+install\s+([a-z0-9-]+)/gi;
    let match;
    while ((match = pluginInstallPattern.exec(safeContent)) !== null) {
      this.trackPlugin(match[1], conversationId);
    }

    // Detect skill triggers
    // Pattern: Invoking skill "<skill-name>" or "Using skill: <skill-name>"
    const skillTriggerPattern = /(?:invoking|using|activating)\s+skill[:\s]+["\']?([a-z0-9-]+)["\']?/gi;
    while ((match = skillTriggerPattern.exec(safeContent)) !== null) {
      this.trackSkill(match[1], conversationId);
    }

    // Detect MCP tool calls
    // Pattern: MCP tool "tool_name" or Using MCP: tool_name
    const mcpToolPattern = /(?:MCP\s+tool|Using\s+MCP)[:\s]+["\']?([a-z0-9_-]+)["\']?/gi;
    while ((match = mcpToolPattern.exec(safeContent)) !== null) {
      this.trackMCPTool(match[1], conversationId);
    }

    // Detect MCP server references
    // Pattern: @server/tool_name (MCP protocol format)
    const mcpServerPattern = /@([a-z0-9-]+)\/([a-z0-9_-]+)/gi;
    while ((match = mcpServerPattern.exec(safeContent)) !== null) {
      const serverName = match[1];
      const toolName = match[2];
      this.trackMCPTool(toolName, conversationId, serverName);
    }
  }

  /**
   * Track plugin usage
   */
  private trackPlugin(pluginName: string, conversationId: string, marketplace?: string): void {
    let stats = this.data.plugins.get(pluginName);

    if (!stats) {
      stats = {
        name: pluginName,
        type: 'plugin',
        activationCount: 0,
        lastActivated: 0,
        conversationIds: new Set(),
        metadata: { marketplace },
      };
      this.data.plugins.set(pluginName, stats);
    }

    // Update stats
    stats.activationCount++;
    stats.lastActivated = Date.now();
    stats.conversationIds.add(conversationId);

    // Emit event
    this.emitAttribution({
      type: 'plugin',
      name: pluginName,
      conversationId,
      timestamp: Date.now(),
      metadata: { marketplace },
    });
  }

  /**
   * Track skill usage
   */
  private trackSkill(skillName: string, conversationId: string, pluginName?: string): void {
    let stats = this.data.skills.get(skillName);

    if (!stats) {
      stats = {
        name: skillName,
        type: 'skill',
        activationCount: 0,
        lastActivated: 0,
        conversationIds: new Set(),
        metadata: { pluginName },
      };
      this.data.skills.set(skillName, stats);
    }

    // Update stats
    stats.activationCount++;
    stats.lastActivated = Date.now();
    stats.conversationIds.add(conversationId);

    // Emit event
    this.emitAttribution({
      type: 'skill',
      name: skillName,
      conversationId,
      timestamp: Date.now(),
      metadata: { pluginName },
    });
  }

  /**
   * Track MCP tool usage
   */
  private trackMCPTool(toolName: string, conversationId: string, mcpServer?: string): void {
    let stats = this.data.mcpTools.get(toolName);

    if (!stats) {
      stats = {
        name: toolName,
        type: 'mcp',
        activationCount: 0,
        lastActivated: 0,
        conversationIds: new Set(),
        metadata: { mcpServer },
      };
      this.data.mcpTools.set(toolName, stats);
    }

    // Update stats
    stats.activationCount++;
    stats.lastActivated = Date.now();
    stats.conversationIds.add(conversationId);

    // Emit event
    this.emitAttribution({
      type: 'mcp',
      name: toolName,
      conversationId,
      timestamp: Date.now(),
      metadata: { mcpServer },
    });
  }

  /**
   * Emit attribution event to all callbacks
   */
  private emitAttribution(event: AttributionEvent): void {
    for (const callback of this.callbacks) {
      try {
        callback(event);
      } catch (error) {
        console.error('Error in attribution callback:', error);
      }
    }
  }

  /**
   * Get all attribution statistics
   */
  getStats(): AttributionData {
    return {
      plugins: new Map(this.data.plugins),
      skills: new Map(this.data.skills),
      mcpTools: new Map(this.data.mcpTools),
      lastUpdated: this.data.lastUpdated,
    };
  }

  /**
   * Get statistics for a specific plugin
   */
  getPluginStats(pluginName: string): AttributionStats | undefined {
    return this.data.plugins.get(pluginName);
  }

  /**
   * Get statistics for a specific skill
   */
  getSkillStats(skillName: string): AttributionStats | undefined {
    return this.data.skills.get(skillName);
  }

  /**
   * Get statistics for a specific MCP tool
   */
  getMCPToolStats(toolName: string): AttributionStats | undefined {
    return this.data.mcpTools.get(toolName);
  }

  /**
   * Get top N most used items of a specific type
   */
  getTopUsed(type: 'plugin' | 'skill' | 'mcp', limit = 10): AttributionStats[] {
    const map = this.data[type === 'plugin' ? 'plugins' : type === 'skill' ? 'skills' : 'mcpTools'];
    return Array.from(map.values())
      .sort((a, b) => b.activationCount - a.activationCount)
      .slice(0, limit);
  }

  /**
   * Get recently used items of a specific type
   */
  getRecentlyUsed(type: 'plugin' | 'skill' | 'mcp', limit = 10): AttributionStats[] {
    const map = this.data[type === 'plugin' ? 'plugins' : type === 'skill' ? 'skills' : 'mcpTools'];
    return Array.from(map.values())
      .sort((a, b) => b.lastActivated - a.lastActivated)
      .slice(0, limit);
  }

  /**
   * Save attribution data to disk
   */
  private async saveData(): Promise<void> {
    try {
      const serializable: SerializableAttributionData = {
        plugins: Array.from(this.data.plugins.values()).map(stat => ({
          ...stat,
          conversationIds: Array.from(stat.conversationIds),
        })),
        skills: Array.from(this.data.skills.values()).map(stat => ({
          ...stat,
          conversationIds: Array.from(stat.conversationIds),
        })),
        mcpTools: Array.from(this.data.mcpTools.values()).map(stat => ({
          ...stat,
          conversationIds: Array.from(stat.conversationIds),
        })),
        lastUpdated: Date.now(),
      };

      await writeFile(this.storagePath, JSON.stringify(serializable, null, 2), 'utf-8');
    } catch (error) {
      console.error('Failed to save attribution data:', error);
    }
  }

  /**
   * Load attribution data from disk
   */
  private async loadData(): Promise<void> {
    try {
      if (!existsSync(this.storagePath)) {
        return; // No existing data to load
      }

      const content = await readFile(this.storagePath, 'utf-8');
      const serializable: SerializableAttributionData = JSON.parse(content);

      // Reconstruct Maps with Sets
      this.data.plugins = new Map(
        serializable.plugins.map(stat => [
          stat.name,
          { ...stat, conversationIds: new Set(stat.conversationIds) }
        ])
      );

      this.data.skills = new Map(
        serializable.skills.map(stat => [
          stat.name,
          { ...stat, conversationIds: new Set(stat.conversationIds) }
        ])
      );

      this.data.mcpTools = new Map(
        serializable.mcpTools.map(stat => [
          stat.name,
          { ...stat, conversationIds: new Set(stat.conversationIds) }
        ])
      );

      this.data.lastUpdated = serializable.lastUpdated;
    } catch (error) {
      console.error('Failed to load attribution data:', error);
    }
  }

  /**
   * Ensure storage directory exists
   */
  private async ensureStorageDirectory(): Promise<void> {
    const dir = join(homedir(), '.claude', 'analytics');
    if (!existsSync(dir)) {
      await mkdir(dir, { recursive: true });
    }
  }

  /**
   * Reset all attribution data (useful for testing)
   */
  async reset(): Promise<void> {
    this.data = {
      plugins: new Map(),
      skills: new Map(),
      mcpTools: new Map(),
      lastUpdated: Date.now(),
    };
    await this.saveData();
  }
}
