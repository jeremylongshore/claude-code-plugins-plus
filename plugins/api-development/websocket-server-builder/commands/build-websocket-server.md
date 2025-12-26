---
name: build-websocket-server
description: >
  Build WebSocket servers for real-time bidirectional communication
shortcut: ws
---
# Build WebSocket Server

Automatically generate production-ready WebSocket servers with Socket.IO or native WebSocket implementations featuring room management, authentication, broadcasting, presence tracking, and resilient connection handling for real-time applications.

## When to Use This Command

Use `/build-websocket-server` when you need to:
- Build real-time chat applications or messaging systems
- Implement live collaboration features (Google Docs-style)
- Create real-time dashboards with live data updates
- Build multiplayer game servers
- Stream live data feeds (stock prices, sports scores)
- Implement real-time notifications and alerts

DON'T use this when:
- Simple request-response patterns suffice (use REST)
- Unidirectional server-to-client updates only (consider SSE)
- Very high throughput binary streaming (consider WebRTC)
- Message ordering is critical (consider message queues)

## Design Decisions

This command implements **Socket.IO** as the primary approach because:
- Automatic fallback to long-polling for compatibility
- Built-in room and namespace management
- Automatic reconnection with exponential backoff
- Binary data support with automatic serialization
- Event acknowledgments and timeouts
- Extensive middleware ecosystem

**Alternative considered: Native WebSocket (ws)**
- Lower overhead and better performance
- No automatic fallbacks
- Manual implementation of features
- Recommended for simple, high-performance needs

**Alternative considered: Server-Sent Events (SSE)**
- Simpler for unidirectional communication
- Works over HTTP/2
- No bidirectional support
- Recommended for news feeds, notifications

## Prerequisites

Before running this command:
1. Choose Socket.IO vs native WebSocket
2. Design event/message protocol
3. Plan authentication strategy
4. Define room/channel structure
5. Determine scaling approach (Redis adapter for multi-server)

## Implementation Process

### Step 1: Initialize WebSocket Server
Set up Socket.IO or ws server with proper configuration.

### Step 2: Implement Authentication
Add middleware for connection authentication and authorization.

### Step 3: Define Event Handlers
Create handlers for all client events and server broadcasts.

### Step 4: Add Room Management
Implement room joining, leaving, and broadcasting logic.

### Step 5: Configure Resilience
Set up reconnection, heartbeat, and error handling.

## Output Format

The command generates:
- `websocket/server.js` - Main WebSocket server setup
- `websocket/handlers/` - Event handler modules
- `websocket/middleware/` - Auth and validation middleware
- `websocket/rooms/` - Room management logic
- `websocket/presence/` - User presence tracking
- `websocket/client.js` - Client SDK/library
- `config/websocket.json` - Server configuration
- `tests/websocket/` - Integration tests

## Code Examples

### Example 1: Full-Featured Chat Server with Socket.IO

```javascript
// websocket/server.js - Socket.IO server with all features
const { Server } = require('socket.io');
const { createAdapter } = require('@socket.io/redis-adapter');
const { instrument } = require('@socket.io/admin-ui');
const jwt = require('jsonwebtoken');
const Redis = require('ioredis');
const crypto = require('crypto');

class WebSocketServer {
    constructor(httpServer, config = {}) {
        this.config = {
            cors: {
                origin: config.corsOrigin || ['http://localhost:3000'],
                credentials: true
            },
            pingTimeout: config.pingTimeout || 60000,
            pingInterval: config.pingInterval || 25000,
            transports: config.transports || ['websocket', 'polling'],
            maxHttpBufferSize: config.maxHttpBufferSize || 1e6, // 1MB
            ...config
        };

        this.io = new Server(httpServer, this.config);
        this.redis = new Redis(config.redisUrl);
        this.pubClient = this.redis;
        this.subClient = this.redis.duplicate();

        this.rooms = new Map();
        this.users = new Map();
        this.presence = new Map();

        this.setupRedisAdapter();
        this.setupMiddleware();
        this.setupEventHandlers();
        this.setupAdminUI();
        this.startPresenceTracking();
    }

    setupRedisAdapter() {
        // Enable horizontal scaling with Redis
        this.io.adapter(createAdapter(this.pubClient, this.subClient));
    }

    setupMiddleware() {
        // Authentication middleware
        this.io.use(async (socket, next) => {
            try {
                const token = socket.handshake.auth.token;
                if (!token) {
                    return next(new Error('Authentication required'));
                }

                const decoded = jwt.verify(token, process.env.JWT_SECRET);
                const user = await this.validateUser(decoded.userId);

                if (!user) {
                    return next(new Error('Invalid user'));
                }

                // Attach user data to socket
                socket.userId = user.id;
                socket.user = user;
                socket.sessionId = crypto.randomBytes(8).toString('hex');

                // Rate limiting per user
                const rateLimitKey = `ratelimit:${user.id}`;
                const requests = await this.redis.incr(rateLimitKey);

                if (requests === 1) {
                    await this.redis.expire(rateLimitKey, 60); // 1 minute window
                }

                if (requests > 100) { // 100 messages per minute
                    return next(new Error('Rate limit exceeded'));
                }

                next();
            } catch (error) {
                next(new Error('Authentication failed: ' + error.message));
            }
        });

        // Connection logging middleware
        this.io.use((socket, next) => {
            console.log(`New connection from ${socket.handshake.address}`);
            socket.on('error', (error) => {
                console.error(`Socket error for ${socket.userId}:`, error);
            });
            next();
        });
    }

    setupEventHandlers() {
        this.io.on('connection', (socket) => {
            this.handleConnection(socket);

            // Room management
            socket.on('join-room', (roomId, callback) =>
                this.handleJoinRoom(socket, roomId, callback)
            );

            socket.on('leave-room', (roomId, callback) =>
                this.handleLeaveRoom(socket, roomId, callback)
            );

            // Messaging
            socket.on('message', (data, callback) =>
                this.handleMessage(socket, data, callback)
            );

            socket.on('typing', (data) =>
                this.handleTyping(socket, data)
            );

            socket.on('stop-typing', (data) =>
                this.handleStopTyping(socket, data)
            );

            // Presence
            socket.on('update-status', (status) =>
                this.handleStatusUpdate(socket, status)
            );

            // Private messaging
            socket.on('private-message', (data, callback) =>
                this.handlePrivateMessage(socket, data, callback)
            );

            // File sharing
            socket.on('upload-start', (data, callback) =>
                this.handleUploadStart(socket, data, callback)
            );

            socket.on('upload-chunk', (data, callback) =>
                this.handleUploadChunk(socket, data, callback)
            );

            // Voice/Video calls
            socket.on('call-user', (data, callback) =>
                this.handleCallUser(socket, data, callback)
            );

            socket.on('call-answer', (data) =>
                this.handleCallAnswer(socket, data)
            );

            socket.on('ice-candidate', (data) =>
                this.handleIceCandidate(socket, data)
            );

            // Disconnection
            socket.on('disconnect', (reason) =>
                this.handleDisconnection(socket, reason)
            );
        });
    }

    async handleConnection(socket) {
        console.log(`User ${socket.userId} connected (${socket.sessionId})`);

        // Track user connection
        if (!this.users.has(socket.userId)) {
            this.users.set(socket.userId, new Set());
        }
        this.users.get(socket.userId).add(socket.id);

        // Update presence
        await this.updatePresence(socket.userId, 'online');

        // Send connection success with user data
        socket.emit('connected', {
            sessionId: socket.sessionId,
            userId: socket.userId,
            serverTime: Date.now()
        });

        // Rejoin previous rooms from session
        const previousRooms = await this.getUserRooms(socket.userId);
        for (const roomId of previousRooms) {
            socket.join(roomId);
            socket.to(roomId).emit('user-joined', {
                userId: socket.userId,
                user: socket.user,
                roomId
            });
        }

        // Send pending messages
        const pendingMessages = await this.getPendingMessages(socket.userId);
        if (pendingMessages.length > 0) {
            socket.emit('pending-messages', pendingMessages);
        }
    }

    async handleJoinRoom(socket, roomId, callback) {
        try {
            // Validate room access
            const hasAccess = await this.validateRoomAccess(socket.userId, roomId);
            if (!hasAccess) {
                return callback({ error: 'Access denied' });
            }

            // Join the room
            socket.join(roomId);

            // Track room membership
            if (!this.rooms.has(roomId)) {
                this.rooms.set(roomId, new Set());
            }
            this.rooms.get(roomId).add(socket.userId);

            // Get room info
            const roomInfo = await this.getRoomInfo(roomId);
            const members = await this.getRoomMembers(roomId);

            // Notify others in room
            socket.to(roomId).emit('user-joined', {
                userId: socket.userId,
                user: socket.user,
                roomId
            });

            // Send room state to joiner
            callback({
                success: true,
                room: roomInfo,
                members: members,
                recentMessages: await this.getRecentMessages(roomId)
            });

            // Update user's room list
            await this.addUserRoom(socket.userId, roomId);

        } catch (error) {
            console.error('Join room error:', error);
            callback({ error: error.message });
        }
    }

    async handleMessage(socket, data, callback) {
        try {
            // Validate message
            if (!data.roomId || !data.content) {
                return callback({ error: 'Invalid message format' });
            }

            // Check room membership
            if (!socket.rooms.has(data.roomId)) {
                return callback({ error: 'Not in room' });
            }

            // Create message object
            const message = {
                id: crypto.randomBytes(16).toString('hex'),
                roomId: data.roomId,
                userId: socket.userId,
                user: socket.user,
                content: data.content,
                type: data.type || 'text',
                timestamp: Date.now(),
                edited: false,
                deleted: false
            };

            // Store message
            await this.storeMessage(message);

            // Broadcast to room
            this.io.to(data.roomId).emit('new-message', message);

            // Send acknowledgment
            callback({
                success: true,
                messageId: message.id,
                timestamp: message.timestamp
            });

            // Update room activity
            await this.updateRoomActivity(data.roomId);

            // Send push notifications to offline users
            await this.sendPushNotifications(data.roomId, message, socket.userId);

        } catch (error) {
            console.error('Message error:', error);
            callback({ error: error.message });
        }
    }

    async handleTyping(socket, data) {
        if (data.roomId && socket.rooms.has(data.roomId)) {
            socket.to(data.roomId).emit('user-typing', {
                userId: socket.userId,
                user: socket.user,
                roomId: data.roomId
            });

            // Auto-stop typing after 3 seconds
            setTimeout(() => {
                socket.to(data.roomId).emit('user-stopped-typing', {
                    userId: socket.userId,
                    roomId: data.roomId
                });
            }, 3000);
        }
    }

    async handlePrivateMessage(socket, data, callback) {
        try {
            const targetUserId = data.targetUserId;
            const targetSockets = this.users.get(targetUserId);

            const message = {
                id: crypto.randomBytes(16).toString('hex'),
                fromUserId: socket.userId,
                fromUser: socket.user,
                toUserId: targetUserId,
                content: data.content,
                timestamp: Date.now(),
                read: false
            };

            // Store private message
            await this.storePrivateMessage(message);

            if (targetSockets && targetSockets.size > 0) {
                // User is online, deliver to all their connections
                for (const socketId of targetSockets) {
                    this.io.to(socketId).emit('private-message', message);
                }
                message.delivered = true;
            } else {
                // User is offline, queue for later
                await this.queueMessage(targetUserId, message);
                message.delivered = false;
            }

            callback({
                success: true,
                messageId: message.id,
                delivered: message.delivered
            });

        } catch (error) {
            console.error('Private message error:', error);
            callback({ error: error.message });
        }
    }

    async handleDisconnection(socket, reason) {
        console.log(`User ${socket.userId} disconnected: ${reason}`);

        // Remove socket from user's connections
        const userSockets = this.users.get(socket.userId);
        if (userSockets) {
            userSockets.delete(socket.id);

            // If no more connections, mark as offline
            if (userSockets.size === 0) {
                this.users.delete(socket.userId);
                await this.updatePresence(socket.userId, 'offline');

                // Notify rooms user was in
                for (const roomId of socket.rooms) {
                    if (roomId !== socket.id) { // Skip default room
                        socket.to(roomId).emit('user-left', {
                            userId: socket.userId,
                            roomId
                        });
                    }
                }
            }
        }

        // Clean up room memberships
        for (const [roomId, members] of this.rooms.entries()) {
            members.delete(socket.userId);
            if (members.size === 0) {
                this.rooms.delete(roomId);
            }
        }
    }

    // Presence tracking
    startPresenceTracking() {
        setInterval(async () => {
            for (const [userId, status] of this.presence.entries()) {
                // Check if user has active connections
                if (!this.users.has(userId)) {
                    this.presence.set(userId, 'offline');
                    await this.broadcastPresenceUpdate(userId, 'offline');
                }
            }
        }, 30000); // Check every 30 seconds
    }

    async updatePresence(userId, status) {
        this.presence.set(userId, status);
        await this.redis.setex(`presence:${userId}`, 120, status);
        await this.broadcastPresenceUpdate(userId, status);
    }

    async broadcastPresenceUpdate(userId, status) {
        // Get all rooms user is in
        const userRooms = await this.getUserRooms(userId);

        for (const roomId of userRooms) {
            this.io.to(roomId).emit('presence-update', {
                userId,
                status,
                timestamp: Date.now()
            });
        }
    }

    // Helper methods
    async validateUser(userId) {
        // Implement user validation
        return { id: userId, name: `User ${userId}` };
    }

    async validateRoomAccess(userId, roomId) {
        // Implement room access validation
        return true;
    }

    async getRoomInfo(roomId) {
        // Implement room info retrieval
        return { id: roomId, name: `Room ${roomId}` };
    }

    async getRoomMembers(roomId) {
        // Implement member list retrieval
        return Array.from(this.rooms.get(roomId) || []);
    }

    async getRecentMessages(roomId, limit = 50) {
        // Implement message history retrieval
        return [];
    }

    async storeMessage(message) {
        // Implement message storage
        await this.redis.lpush(
            `messages:${message.roomId}`,
            JSON.stringify(message)
        );
        await this.redis.ltrim(`messages:${message.roomId}`, 0, 999);
    }

    async getUserRooms(userId) {
        // Implement user room list retrieval
        return [];
    }

    async getPendingMessages(userId) {
        // Implement pending message retrieval
        return [];
    }

    setupAdminUI() {
        // Enable admin UI for monitoring
        instrument(this.io, {
            auth: {
                type: 'basic',
                username: process.env.SOCKETIO_ADMIN_USER || 'admin',
                password: process.env.SOCKETIO_ADMIN_PASSWORD || 'admin'
            },
            readonly: false
        });
    }

    // Public methods for external use
    async broadcast(event, data) {
        this.io.emit(event, data);
    }

    async broadcastToRoom(roomId, event, data) {
        this.io.to(roomId).emit(event, data);
    }

    async sendToUser(userId, event, data) {
        const userSockets = this.users.get(userId);
        if (userSockets) {
            for (const socketId of userSockets) {
                this.io.to(socketId).emit(event, data);
            }
        }
    }

    getOnlineUsers() {
        return Array.from(this.users.keys());
    }

    getRoomMembers(roomId) {
        return Array.from(this.rooms.get(roomId) || []);
    }
}

// Initialize server
const http = require('http');
const express = require('express');

const app = express();
const server = http.createServer(app);

const wsServer = new WebSocketServer(server, {
    corsOrigin: process.env.CORS_ORIGIN?.split(',') || ['http://localhost:3000'],
    redisUrl: process.env.REDIS_URL || 'redis://localhost:6379'
});

// REST endpoints for WebSocket management
app.get('/ws/stats', (req, res) => {
    res.json({
        onlineUsers: wsServer.getOnlineUsers().length,
        rooms: wsServer.rooms.size,
        connections: wsServer.io.engine.clientsCount
    });
});

app.post('/ws/broadcast', express.json(), async (req, res) => {
    const { event, data } = req.body;
    await wsServer.broadcast(event, data);
    res.json({ success: true });
});

server.listen(3000, () => {
    console.log('WebSocket server running on port 3000');
});

module.exports = { WebSocketServer };
```

### Example 2: High-Performance Native WebSocket Implementation

```javascript
// websocket/native-server.js - Pure WebSocket with advanced features
const WebSocket = require('ws');
const http = require('http');
const crypto = require('crypto');
const EventEmitter = require('events');

class NativeWebSocketServer extends EventEmitter {
    constructor(server, options = {}) {
        super();

        this.wss = new WebSocket.Server({
            server,
            perMessageDeflate: options.compression !== false,
            maxPayload: options.maxPayload || 10 * 1024 * 1024, // 10MB
            clientTracking: true,
            ...options
        });

        this.clients = new Map();
        this.rooms = new Map();
        this.messageHandlers = new Map();
        this.heartbeatInterval = options.heartbeatInterval || 30000;

        this.setupEventHandlers();
        this.startHeartbeat();
    }

    setupEventHandlers() {
        this.wss.on('connection', (ws, req) => {
            this.handleConnection(ws, req);
        });

        this.wss.on('error', (error) => {
            console.error('WebSocket server error:', error);
            this.emit('error', error);
        });
    }

    handleConnection(ws, req) {
        // Generate client ID
        const clientId = crypto.randomBytes(16).toString('hex');

        // Parse authentication from URL or headers
        const token = this.extractToken(req);
        const user = this.authenticateToken(token);

        if (!user) {
            ws.close(1008, 'Unauthorized');
            return;
        }

        // Setup client
        const client = {
            id: clientId,
            ws: ws,
            user: user,
            rooms: new Set(),
            isAlive: true,
            joinedAt: Date.now(),
            lastActivity: Date.now(),
            messageCount: 0
        };

        this.clients.set(clientId, client);

        // Send connection acknowledgment
        this.send(client, {
            type: 'connected',
            clientId: clientId,
            timestamp: Date.now()
        });

        // Setup client event handlers
        ws.on('message', (data) => this.handleMessage(client, data));
        ws.on('pong', () => this.handlePong(client));
        ws.on('close', (code, reason) => this.handleClose(client, code, reason));
        ws.on('error', (error) => this.handleError(client, error));

        this.emit('connection', client);
    }

    handleMessage(client, data) {
        try {
            // Update activity
            client.lastActivity = Date.now();
            client.messageCount++;

            // Parse message
            let message;
            if (typeof data === 'string') {
                message = JSON.parse(data);
            } else {
                // Handle binary data
                message = this.parseBinaryMessage(data);
            }

            // Rate limiting
            if (client.messageCount > 100) {
                const timeDiff = Date.now() - client.joinedAt;
                if (timeDiff < 60000) { // Less than 1 minute
                    this.send(client, {
                        type: 'error',
                        error: 'Rate limit exceeded'
                    });
                    client.ws.close(1008, 'Rate limit exceeded');
                    return;
                }
                client.messageCount = 0;
                client.joinedAt = Date.now();
            }

            // Route message to handler
            const handler = this.messageHandlers.get(message.type);
            if (handler) {
                handler(client, message);
            } else {
                this.handleDefaultMessage(client, message);
            }

            this.emit('message', client, message);

        } catch (error) {
            console.error('Message handling error:', error);
            this.send(client, {
                type: 'error',
                error: 'Invalid message format'
            });
        }
    }

    handleDefaultMessage(client, message) {
        switch (message.type) {
            case 'join':
                this.joinRoom(client, message.room);
                break;
            case 'leave':
                this.leaveRoom(client, message.room);
                break;
            case 'broadcast':
                this.broadcastToRoom(message.room, message.data, client);
                break;
            case 'ping':
                this.send(client, { type: 'pong', timestamp: Date.now() });
                break;
            default:
                this.emit('custom-message', client, message);
        }
    }

    joinRoom(client, roomId) {
        if (!roomId) return;

        // Add client to room
        if (!this.rooms.has(roomId)) {
            this.rooms.set(roomId, new Set());
        }
        this.rooms.get(roomId).add(client.id);
        client.rooms.add(roomId);

        // Notify room members
        this.broadcastToRoom(roomId, {
            type: 'user-joined',
            userId: client.user.id,
            roomId: roomId,
            timestamp: Date.now()
        }, client);

        // Send confirmation
        this.send(client, {
            type: 'joined',
            roomId: roomId,
            members: this.getRoomMembers(roomId)
        });

        this.emit('room-joined', client, roomId);
    }

    leaveRoom(client, roomId) {
        if (!roomId || !client.rooms.has(roomId)) return;

        // Remove client from room
        const room = this.rooms.get(roomId);
        if (room) {
            room.delete(client.id);
            if (room.size === 0) {
                this.rooms.delete(roomId);
            }
        }
        client.rooms.delete(roomId);

        // Notify room members
        this.broadcastToRoom(roomId, {
            type: 'user-left',
            userId: client.user.id,
            roomId: roomId,
            timestamp: Date.now()
        });

        // Send confirmation
        this.send(client, {
            type: 'left',
            roomId: roomId
        });

        this.emit('room-left', client, roomId);
    }

    broadcastToRoom(roomId, data, excludeClient = null) {
        const room = this.rooms.get(roomId);
        if (!room) return;

        const message = typeof data === 'object' ? JSON.stringify(data) : data;

        for (const clientId of room) {
            if (excludeClient && clientId === excludeClient.id) continue;

            const client = this.clients.get(clientId);
            if (client && client.ws.readyState === WebSocket.OPEN) {
                client.ws.send(message);
            }
        }
    }

    broadcast(data, excludeClient = null) {
        const message = typeof data === 'object' ? JSON.stringify(data) : data;

        this.clients.forEach((client) => {
            if (excludeClient && client.id === excludeClient.id) return;

            if (client.ws.readyState === WebSocket.OPEN) {
                client.ws.send(message);
            }
        });
    }

    send(client, data) {
        if (client.ws.readyState === WebSocket.OPEN) {
            const message = typeof data === 'object' ? JSON.stringify(data) : data;
            client.ws.send(message);
        }
    }

    handlePong(client) {
        client.isAlive = true;
    }

    handleClose(client, code, reason) {
        console.log(`Client ${client.id} disconnected: ${code} - ${reason}`);

        // Leave all rooms
        for (const roomId of client.rooms) {
            this.leaveRoom(client, roomId);
        }

        // Remove client
        this.clients.delete(client.id);

        this.emit('disconnection', client, code, reason);
    }

    handleError(client, error) {
        console.error(`Client ${client.id} error:`, error);
        this.emit('client-error', client, error);
    }

    startHeartbeat() {
        setInterval(() => {
            this.clients.forEach((client) => {
                if (!client.isAlive) {
                    console.log(`Terminating inactive client ${client.id}`);
                    client.ws.terminate();
                    this.clients.delete(client.id);
                    return;
                }

                client.isAlive = false;
                client.ws.ping();
            });
        }, this.heartbeatInterval);
    }

    // Utility methods
    extractToken(req) {
        // Extract from query string or authorization header
        const url = new URL(req.url, `http://${req.headers.host}`);
        return url.searchParams.get('token') ||
               req.headers.authorization?.replace('Bearer ', '');
    }

    authenticateToken(token) {
        // Implement token validation
        if (!token) return null;
        return { id: 'user123', name: 'Test User' };
    }

    getRoomMembers(roomId) {
        const room = this.rooms.get(roomId);
        if (!room) return [];

        return Array.from(room).map(clientId => {
            const client = this.clients.get(clientId);
            return client ? client.user : null;
        }).filter(Boolean);
    }

    // Public API
    registerHandler(type, handler) {
        this.messageHandlers.set(type, handler);
    }

    getClient(clientId) {
        return this.clients.get(clientId);
    }

    getClients() {
        return Array.from(this.clients.values());
    }

    getRooms() {
        return Array.from(this.rooms.keys());
    }

    close() {
        clearInterval(this.heartbeatTimer);
        this.wss.close();
    }
}

// Usage
const server = http.createServer();
const wsServer = new NativeWebSocketServer(server, {
    compression: true,
    heartbeatInterval: 30000
});

// Register custom message handlers
wsServer.registerHandler('chat', (client, message) => {
    wsServer.broadcastToRoom(message.room, {
        type: 'chat',
        from: client.user.name,
        content: message.content,
        timestamp: Date.now()
    });
});

wsServer.registerHandler('file-upload', (client, message) => {
    // Handle file upload
    console.log(`File upload from ${client.user.name}:`, message.filename);
});

// Event listeners
wsServer.on('connection', (client) => {
    console.log(`New connection: ${client.user.name}`);
});

wsServer.on('room-joined', (client, roomId) => {
    console.log(`${client.user.name} joined room ${roomId}`);
});

server.listen(3000, () => {
    console.log('Native WebSocket server running on port 3000');
});
```

### Example 3: Client SDK and Testing

```javascript
// websocket/client.js - Browser/Node.js client
class WebSocketClient {
    constructor(url, options = {}) {
        this.url = url;
        this.options = options;
        this.ws = null;
        this.messageHandlers = new Map();
        this.messageQueue = [];
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = options.maxReconnectAttempts || 5;
        this.reconnectDelay = options.reconnectDelay || 1000;
        this.isConnected = false;
    }

    connect() {
        return new Promise((resolve, reject) => {
            try {
                this.ws = new WebSocket(this.url);

                this.ws.onopen = () => {
                    console.log('WebSocket connected');
                    this.isConnected = true;
                    this.reconnectAttempts = 0;

                    // Send queued messages
                    while (this.messageQueue.length > 0) {
                        const message = this.messageQueue.shift();
                        this.send(message);
                    }

                    resolve();
                };

                this.ws.onmessage = (event) => {
                    this.handleMessage(event.data);
                };

                this.ws.onerror = (error) => {
                    console.error('WebSocket error:', error);
                    reject(error);
                };

                this.ws.onclose = (event) => {
                    console.log('WebSocket closed:', event.code, event.reason);
                    this.isConnected = false;
                    this.handleReconnect();
                };

            } catch (error) {
                reject(error);
            }
        });
    }

    handleMessage(data) {
        try {
            const message = JSON.parse(data);
            const handler = this.messageHandlers.get(message.type);

            if (handler) {
                handler(message);
            } else {
                console.log('Unhandled message:', message);
            }
        } catch (error) {
            console.error('Message parsing error:', error);
        }
    }

    on(type, handler) {
        this.messageHandlers.set(type, handler);
    }

    send(data) {
        const message = typeof data === 'object' ? JSON.stringify(data) : data;

        if (this.isConnected && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(message);
        } else {
            // Queue message for later
            this.messageQueue.push(data);
        }
    }

    handleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            return;
        }

        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

        console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

        setTimeout(() => {
            this.connect().catch(console.error);
        }, delay);
    }

    close() {
        if (this.ws) {
            this.ws.close();
        }
    }
}

// tests/websocket.test.js
const { WebSocketServer } = require('../websocket/server');
const WebSocketClient = require('../websocket/client');

describe('WebSocket Server Tests', () => {
    let server;
    let client;

    beforeEach(async () => {
        server = new WebSocketServer(3001);
        await server.start();

        client = new WebSocketClient('ws://localhost:3001', {
            token: 'test-token'
        });
    });

    afterEach(async () => {
        client.close();
        await server.close();
    });

    test('should connect successfully', async () => {
        await client.connect();
        expect(client.isConnected).toBe(true);
    });

    test('should join room', async () => {
        await client.connect();

        const joined = new Promise((resolve) => {
            client.on('joined', resolve);
        });

        client.send({ type: 'join', room: 'test-room' });

        const result = await joined;
        expect(result.roomId).toBe('test-room');
    });

    test('should broadcast messages', async () => {
        const client2 = new WebSocketClient('ws://localhost:3001');
        await client.connect();
        await client2.connect();

        // Both join same room
        client.send({ type: 'join', room: 'test-room' });
        client2.send({ type: 'join', room: 'test-room' });

        // Set up message listener
        const messageReceived = new Promise((resolve) => {
            client2.on('chat', resolve);
        });

        // Send message
        client.send({
            type: 'chat',
            room: 'test-room',
            content: 'Hello World'
        });

        const message = await messageReceived;
        expect(message.content).toBe('Hello World');
    });

    test('should handle reconnection', async () => {
        await client.connect();

        // Force disconnect
        server.disconnectClient(client.id);

        // Wait for reconnection
        await new Promise(resolve => setTimeout(resolve, 2000));

        expect(client.isConnected).toBe(true);
        expect(client.reconnectAttempts).toBeGreaterThan(0);
    });
});
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| "WebSocket connection failed" | Network issues or wrong URL | Check network and WebSocket URL |
| "Authentication required" | Missing or invalid token | Include valid auth token |
| "Rate limit exceeded" | Too many messages | Implement client-side throttling |
| "Maximum payload size exceeded" | Message too large | Split large messages or use chunking |
| "Connection timeout" | No heartbeat response | Check network stability |

## Configuration Options

**Server Options**
- `perMessageDeflate`: Enable compression
- `maxPayload`: Maximum message size
- `pingInterval`: Heartbeat frequency
- `pingTimeout`: Heartbeat timeout
- `transports`: Allowed transports (Socket.IO)

**Client Options**
- `reconnection`: Enable auto-reconnection
- `reconnectionAttempts`: Max reconnect tries
- `reconnectionDelay`: Initial reconnect delay
- `timeout`: Connection timeout
- `auth`: Authentication data

## Best Practices

DO:
- Implement heartbeat/ping-pong for connection health
- Use rooms/namespaces for logical grouping
- Add authentication before accepting connections
- Implement message acknowledgments for critical data
- Use compression for text data
- Monitor connection count and memory usage

DON'T:
- Send large payloads without chunking
- Store state only in memory without persistence
- Skip authentication for production
- Ignore connection limits
- Use synchronous operations in handlers
- Broadcast sensitive data to all clients

## Performance Considerations

- Use binary frames for large data transfers
- Implement message batching for high-frequency updates
- Use Redis adapter for horizontal scaling
- Enable compression for text-heavy payloads
- Limit connection count per IP/user
- Implement connection pooling for database queries

## Security Considerations

- Always use WSS (WebSocket Secure) in production
- Validate all incoming messages
- Implement rate limiting per connection
- Use JWT or session-based authentication
- Sanitize user input before broadcasting
- Implement CORS properly
- Monitor for abnormal connection patterns

## Related Commands

- `/webhook-handler-creator` - Handle webhooks
- `/real-time-sync` - Implement data synchronization
- `/message-queue-setup` - Configure message queues
- `/pubsub-system` - Build pub/sub architecture
- `/notification-service` - Push notifications

## Version History

- v1.0.0 (2024-10): Initial implementation with Socket.IO and native WebSocket
- Planned v1.1.0: Add WebRTC signaling server and video streaming support