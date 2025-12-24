#!/usr/bin/env node

/**
 * Example WebSocket client for Claude Code Analytics Daemon
 *
 * Run this to connect to the analytics daemon and see live events:
 *   node example-client.js
 */

import { WebSocket } from 'ws';

const ANALYTICS_URL = 'ws://localhost:3456';

console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('📊 Claude Code Analytics Client');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log();
console.log(`Connecting to: ${ANALYTICS_URL}`);
console.log('Press Ctrl+C to disconnect');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log();

const ws = new WebSocket(ANALYTICS_URL);

ws.on('open', () => {
  console.log('✓ Connected to analytics daemon');
  console.log('  Listening for events...\n');
});

ws.on('message', (data) => {
  try {
    const event = JSON.parse(data.toString());
    const timestamp = new Date(event.timestamp).toLocaleTimeString();

    console.log(`[${timestamp}] ${event.type}`);

    switch (event.type) {
      case 'server.connected':
        console.log(`  ${event.message}\n`);
        break;

      case 'plugin.activation':
        console.log(`  Plugin: ${event.pluginName}`);
        if (event.pluginVersion) {
          console.log(`  Version: ${event.pluginVersion}`);
        }
        if (event.marketplace) {
          console.log(`  Marketplace: ${event.marketplace}`);
        }
        console.log();
        break;

      case 'skill.trigger':
        console.log(`  Skill: ${event.skillName}`);
        console.log(`  Plugin: ${event.pluginName}`);
        if (event.triggerPhrase) {
          console.log(`  Trigger: "${event.triggerPhrase}"`);
        }
        console.log();
        break;

      case 'llm.call':
        console.log(`  Model: ${event.model}`);
        if (event.totalTokens) {
          console.log(`  Tokens: ${event.totalTokens.toLocaleString()}`);
          if (event.inputTokens && event.outputTokens) {
            console.log(`    Input: ${event.inputTokens.toLocaleString()}`);
            console.log(`    Output: ${event.outputTokens.toLocaleString()}`);
          }
        }
        console.log();
        break;

      case 'cost.update':
        console.log(`  Model: ${event.model}`);
        console.log(`  Cost: $${event.totalCost.toFixed(4)} ${event.currency}`);
        console.log(`    Input: $${event.inputCost.toFixed(4)}`);
        console.log(`    Output: $${event.outputCost.toFixed(4)}`);
        console.log();
        break;

      case 'rate_limit.warning':
        const percentage = ((event.current / event.limit) * 100).toFixed(1);
        console.log(`  Service: ${event.service}`);
        console.log(`  Usage: ${event.current}/${event.limit} (${percentage}%)`);
        if (event.resetAt) {
          const resetTime = new Date(event.resetAt).toLocaleString();
          console.log(`  Resets: ${resetTime}`);
        }
        console.log();
        break;

      case 'conversation.created':
        console.log(`  Conversation ID: ${event.conversationId}`);
        if (event.title) {
          console.log(`  Title: ${event.title}`);
        }
        console.log();
        break;

      case 'conversation.updated':
        console.log(`  Conversation ID: ${event.conversationId}`);
        console.log(`  Messages: ${event.messageCount}`);
        console.log();
        break;

      default:
        console.log(`  Data: ${JSON.stringify(event, null, 2)}\n`);
    }
  } catch (error) {
    console.error('Error parsing event:', error);
  }
});

ws.on('error', (error) => {
  console.error('\n❌ Connection error:', error.message);
  console.error('\nMake sure the analytics daemon is running:');
  console.error('  cd packages/analytics-daemon');
  console.error('  pnpm start\n');
});

ws.on('close', () => {
  console.log('\n✓ Disconnected from analytics daemon');
  process.exit(0);
});

// Handle graceful shutdown
process.on('SIGINT', () => {
  console.log('\nDisconnecting...');
  ws.close();
});
