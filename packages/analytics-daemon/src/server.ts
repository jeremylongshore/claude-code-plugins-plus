import { WebSocketServer, WebSocket } from 'ws';
import type { ServerConfig, AnalyticsEvent } from './types.js';

/**
 * AnalyticsServer - WebSocket server for real-time analytics events
 */
export class AnalyticsServer {
  private wss: WebSocketServer | null = null;
  private config: Required<ServerConfig>;
  private clients: Set<WebSocket> = new Set();

  constructor(config: ServerConfig) {
    this.config = {
      port: config.port,
      host: config.host ?? 'localhost',
    };
  }

  /**
   * Start the WebSocket server
   */
  start(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.wss) {
        console.warn('Server already started');
        resolve();
        return;
      }

      this.wss = new WebSocketServer({
        port: this.config.port,
        host: this.config.host,
      });

      this.wss.on('connection', (ws) => this.handleConnection(ws));

      this.wss.on('error', (error) => {
        console.error('WebSocket server error:', error);
        reject(error);
      });

      this.wss.on('listening', () => {
        console.log(`Analytics server listening on ws://${this.config.host}:${this.config.port}`);
        resolve();
      });
    });
  }

  /**
   * Stop the WebSocket server
   */
  async stop(): Promise<void> {
    return new Promise((resolve) => {
      if (!this.wss) {
        resolve();
        return;
      }

      // Close all client connections
      for (const client of this.clients) {
        client.close();
      }
      this.clients.clear();

      this.wss.close(() => {
        this.wss = null;
        console.log('Analytics server stopped');
        resolve();
      });
    });
  }

  /**
   * Handle new WebSocket connection
   */
  private handleConnection(ws: WebSocket): void {
    console.log('New client connected');
    this.clients.add(ws);

    ws.on('close', () => {
      console.log('Client disconnected');
      this.clients.delete(ws);
    });

    ws.on('error', (error) => {
      console.error('Client connection error:', error);
      this.clients.delete(ws);
    });

    // Send welcome message
    this.sendToClient(ws, {
      type: 'server.connected',
      timestamp: Date.now(),
      message: 'Connected to Claude Code Analytics',
    });
  }

  /**
   * Broadcast event to all connected clients
   */
  broadcast(event: AnalyticsEvent): void {
    const message = JSON.stringify(event);
    let sentCount = 0;

    for (const client of this.clients) {
      if (client.readyState === WebSocket.OPEN) {
        try {
          client.send(message);
          sentCount++;
        } catch (error) {
          console.error('Error sending to client:', error);
          this.clients.delete(client);
        }
      }
    }

    if (sentCount > 0) {
      console.log(`Broadcast ${event.type} to ${sentCount} client(s)`);
    }
  }

  /**
   * Send message to specific client
   */
  private sendToClient(ws: WebSocket, data: unknown): void {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(data));
    }
  }

  /**
   * Get number of connected clients
   */
  getClientCount(): number {
    return this.clients.size;
  }

  /**
   * Get server status
   */
  getStatus(): {
    running: boolean;
    clients: number;
    host: string;
    port: number;
  } {
    return {
      running: this.wss !== null,
      clients: this.clients.size,
      host: this.config.host,
      port: this.config.port,
    };
  }
}
