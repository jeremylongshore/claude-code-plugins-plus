import express, { type Express, type Request, type Response } from 'express';
import cors from 'cors';
import { createServer, type Server } from 'http';
import type { ConversationWatcher } from './watcher.js';
import type { AnalyticsServer } from './server.js';

/**
 * HTTP API for analytics data access
 */
export class AnalyticsAPI {
  private app: Express;
  private server: Server | null = null;
  private port: number;
  private host: string;

  constructor(
    private watcher: ConversationWatcher,
    private wsServer: AnalyticsServer,
    config: { port?: number; host?: string } = {}
  ) {
    this.port = config.port ?? 3333;
    this.host = config.host ?? 'localhost';
    this.app = express();

    this.setupMiddleware();
    this.setupRoutes();
  }

  /**
   * Configure Express middleware
   */
  private setupMiddleware(): void {
    // CORS for local access only
    this.app.use(
      cors({
        origin: ['http://localhost:*', 'http://127.0.0.1:*'],
        credentials: true,
      })
    );

    // JSON body parsing
    this.app.use(express.json());

    // Request logging
    this.app.use((req, res, next) => {
      console.log(`[API] ${req.method} ${req.path}`);
      next();
    });
  }

  /**
   * Setup API routes
   */
  private setupRoutes(): void {
    // Health check
    this.app.get('/health', (req, res) => {
      res.json({
        status: 'healthy',
        timestamp: Date.now(),
        uptime: process.uptime(),
      });
    });

    // List all sessions
    this.app.get('/api/sessions', (req, res) => {
      this.handleGetSessions(req, res);
    });

    // Get session details
    this.app.get('/api/session/:id', (req, res) => {
      this.handleGetSession(req, res);
    });

    // Server status
    this.app.get('/api/status', (req, res) => {
      this.handleGetStatus(req, res);
    });

    // WebSocket info endpoint
    this.app.get('/api/realtime', (req, res) => {
      const wsStatus = this.wsServer.getStatus();
      res.json({
        websocket: {
          url: `ws://${wsStatus.host}:${wsStatus.port}`,
          running: wsStatus.running,
          clients: wsStatus.clients,
        },
        instructions: {
          connect: `const ws = new WebSocket('ws://${wsStatus.host}:${wsStatus.port}');`,
          events: [
            'plugin.activation',
            'skill.trigger',
            'llm.call',
            'cost.update',
            'rate_limit.warning',
            'conversation.created',
            'conversation.updated',
          ],
        },
      });
    });

    // 404 handler
    this.app.use((req, res) => {
      res.status(404).json({
        error: 'Not Found',
        message: `Route ${req.method} ${req.path} does not exist`,
      });
    });

    // Error handler
    this.app.use((err: Error, req: Request, res: Response, next: Function) => {
      console.error('API error:', err);
      res.status(500).json({
        error: 'Internal Server Error',
        message: err.message,
      });
    });
  }

  /**
   * Handle GET /api/sessions
   */
  private handleGetSessions(req: Request, res: Response): void {
    try {
      const conversations = this.watcher.getConversations();

      const sessions = conversations.map((conv) => ({
        id: conv.id,
        title: conv.title ?? 'Untitled',
        messageCount: conv.messages.length,
        plugins: conv.metadata?.plugins ?? [],
        skills: conv.metadata?.skills ?? [],
        model: conv.metadata?.model,
        lastMessage: conv.messages[conv.messages.length - 1]?.timestamp,
      }));

      res.json({
        sessions,
        total: sessions.length,
        timestamp: Date.now(),
      });
    } catch (error) {
      console.error('Error fetching sessions:', error);
      res.status(500).json({
        error: 'Failed to fetch sessions',
        message: error instanceof Error ? error.message : 'Unknown error',
      });
    }
  }

  /**
   * Handle GET /api/session/:id
   */
  private handleGetSession(req: Request, res: Response): void {
    try {
      const { id } = req.params;
      const conversation = this.watcher.getConversation(id);

      if (!conversation) {
        res.status(404).json({
          error: 'Not Found',
          message: `Session ${id} not found`,
        });
        return;
      }

      // Return full conversation details
      res.json({
        id: conversation.id,
        title: conversation.title ?? 'Untitled',
        messageCount: conversation.messages.length,
        metadata: conversation.metadata,
        messages: conversation.messages.map((msg) => ({
          role: msg.role,
          timestamp: msg.timestamp,
          plugin: msg.metadata?.plugin,
          skill: msg.metadata?.skill,
          tokens: msg.metadata?.tokens,
          // Don't include full content for privacy
          hasContent: !!msg.content,
          contentLength: msg.content?.length ?? 0,
        })),
        timestamp: Date.now(),
      });
    } catch (error) {
      console.error('Error fetching session:', error);
      res.status(500).json({
        error: 'Failed to fetch session',
        message: error instanceof Error ? error.message : 'Unknown error',
      });
    }
  }

  /**
   * Handle GET /api/status
   */
  private handleGetStatus(req: Request, res: Response): void {
    const wsStatus = this.wsServer.getStatus();
    const conversations = this.watcher.getConversations();

    res.json({
      api: {
        running: this.server !== null,
        host: this.host,
        port: this.port,
      },
      websocket: wsStatus,
      watcher: {
        conversationCount: conversations.length,
        totalMessages: conversations.reduce((sum, c) => sum + c.messages.length, 0),
      },
      system: {
        uptime: process.uptime(),
        nodeVersion: process.version,
        platform: process.platform,
      },
      timestamp: Date.now(),
    });
  }

  /**
   * Start the HTTP API server
   */
  start(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.server) {
        console.warn('API server already started');
        resolve();
        return;
      }

      this.server = createServer(this.app);

      this.server.on('error', (error) => {
        console.error('HTTP API error:', error);
        reject(error);
      });

      this.server.listen(this.port, this.host, () => {
        console.log(`Analytics API listening on http://${this.host}:${this.port}`);
        console.log(`  Health check: http://${this.host}:${this.port}/health`);
        console.log(`  Sessions: http://${this.host}:${this.port}/api/sessions`);
        console.log(`  Status: http://${this.host}:${this.port}/api/status`);
        resolve();
      });
    });
  }

  /**
   * Stop the HTTP API server
   */
  async stop(): Promise<void> {
    return new Promise((resolve) => {
      if (!this.server) {
        resolve();
        return;
      }

      this.server.close(() => {
        this.server = null;
        console.log('Analytics API stopped');
        resolve();
      });
    });
  }

  /**
   * Get Express app instance (for testing)
   */
  getApp(): Express {
    return this.app;
  }
}
