#!/usr/bin/env node

import { homedir } from 'os';
import { join } from 'path';
import { ConversationWatcher } from './watcher.js';
import { AnalyticsServer } from './server.js';
import { AnalyticsAPI } from './api.js';
import type { AnalyticsEvent } from './types.js';

/**
 * Claude Code Analytics Daemon
 *
 * Monitors ~/.claude/conversations/ for plugin usage, skill triggers, and LLM calls.
 * Broadcasts real-time events via WebSocket for dashboard consumption.
 * Provides HTTP API for querying session data.
 */

const DEFAULT_WS_PORT = 3456;
const DEFAULT_API_PORT = 3333;
const DEFAULT_HOST = 'localhost';

/**
 * Main daemon class
 */
class AnalyticsDaemon {
  private watcher: ConversationWatcher;
  private server: AnalyticsServer;
  private api: AnalyticsAPI;
  private conversationsPath: string;

  constructor() {
    // Detect conversations directory
    this.conversationsPath = join(homedir(), '.claude', 'conversations');

    // Initialize watcher
    this.watcher = new ConversationWatcher({
      conversationsPath: this.conversationsPath,
      debounceMs: 500,
      ignoreInitial: true,
    });

    // Initialize WebSocket server
    this.server = new AnalyticsServer({
      port: parseInt(process.env.CCP_ANALYTICS_PORT ?? String(DEFAULT_WS_PORT)),
      host: process.env.CCP_ANALYTICS_HOST ?? DEFAULT_HOST,
    });

    // Initialize HTTP API
    this.api = new AnalyticsAPI(this.watcher, this.server, {
      port: parseInt(process.env.CCP_API_PORT ?? String(DEFAULT_API_PORT)),
      host: process.env.CCP_API_HOST ?? DEFAULT_HOST,
    });

    // Wire up events
    this.watcher.on('event', (event: AnalyticsEvent) => {
      this.handleEvent(event);
    });

    this.watcher.on('error', (error: Error) => {
      console.error('Watcher error:', error);
    });
  }

  /**
   * Start the daemon
   */
  async start(): Promise<void> {
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('🔍 Claude Code Analytics Daemon');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log();

    try {
      // Start HTTP API server
      await this.api.start();
      console.log();

      // Start WebSocket server
      await this.server.start();
      console.log();

      // Start file watcher
      this.watcher.start();
      console.log();

      console.log('✓ Daemon started successfully');
      console.log(`  Watching: ${this.conversationsPath}`);
      console.log(`  WebSocket: ws://${this.server.getStatus().host}:${this.server.getStatus().port}`);
      console.log();
      console.log('Press Ctrl+C to stop');
      console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    } catch (error) {
      console.error('Failed to start daemon:', error);
      process.exit(1);
    }
  }

  /**
   * Stop the daemon
   */
  async stop(): Promise<void> {
    console.log('\nStopping daemon...');
    await this.watcher.stop();
    await this.server.stop();
    await this.api.stop();
    console.log('Daemon stopped');
  }

  /**
   * Handle analytics event
   */
  private handleEvent(event: AnalyticsEvent): void {
    // Log event for debugging
    console.log(`[${new Date(event.timestamp).toISOString()}] ${event.type}`);

    // Broadcast to connected clients
    this.server.broadcast(event);

    // Additional event-specific handling
    switch (event.type) {
      case 'plugin.activation':
        console.log(`  Plugin: ${event.pluginName}`);
        break;
      case 'skill.trigger':
        console.log(`  Skill: ${event.skillName} (${event.pluginName})`);
        break;
      case 'llm.call':
        console.log(`  Model: ${event.model}, Tokens: ${event.totalTokens}`);
        break;
      case 'cost.update':
        console.log(`  Cost: ${event.totalCost} ${event.currency}`);
        break;
      case 'rate_limit.warning':
        console.log(`  Service: ${event.service}, Usage: ${event.current}/${event.limit}`);
        break;
    }
  }

  /**
   * Get daemon status
   */
  getStatus(): {
    watcher: {
      conversationsPath: string;
      conversationCount: number;
    };
    server: {
      running: boolean;
      clients: number;
      host: string;
      port: number;
    };
  } {
    return {
      watcher: {
        conversationsPath: this.conversationsPath,
        conversationCount: this.watcher.getConversations().length,
      },
      server: this.server.getStatus(),
    };
  }
}

/**
 * CLI entry point
 */
async function main() {
  const daemon = new AnalyticsDaemon();

  // Handle graceful shutdown
  process.on('SIGINT', async () => {
    await daemon.stop();
    process.exit(0);
  });

  process.on('SIGTERM', async () => {
    await daemon.stop();
    process.exit(0);
  });

  // Start daemon
  await daemon.start();
}

// Run if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((error) => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}

export { AnalyticsDaemon };
