# WebSocket Server Examples

## WebSocket Server Setup (ws library)

```javascript
// ws/server.js
const { WebSocketServer } = require('ws');
const jwt = require('jsonwebtoken');

const wss = new WebSocketServer({ noServer: true });

// Authenticate during HTTP upgrade
server.on('upgrade', (request, socket, head) => {
  const url = new URL(request.url, `http://${request.headers.host}`);
  const token = url.searchParams.get('token');

  try {
    const user = jwt.verify(token, process.env.JWT_SECRET);
    wss.handleUpgrade(request, socket, head, (ws) => {
      ws.user = user;
      wss.emit('connection', ws, request);
    });
  } catch {
    socket.write('HTTP/1.1 401 Unauthorized\r\n\r\n');
    socket.destroy();
  }
});
```

## Connection Registry

```javascript
// ws/registry.js
class ConnectionRegistry {
  constructor() {
    this.connections = new Map(); // userId -> Set<ws>
    this.rooms = new Map();      // roomName -> Set<ws>
  }

  add(ws) {
    const userId = ws.user.id;
    if (!this.connections.has(userId)) this.connections.set(userId, new Set());
    this.connections.get(userId).add(ws);
  }

  remove(ws) {
    const userId = ws.user?.id;
    if (userId) {
      this.connections.get(userId)?.delete(ws);
      if (this.connections.get(userId)?.size === 0) this.connections.delete(userId);
    }
    for (const [room, members] of this.rooms) {
      members.delete(ws);
      if (members.size === 0) this.rooms.delete(room);
    }
  }

  joinRoom(ws, room) {
    if (!this.rooms.has(room)) this.rooms.set(room, new Set());
    this.rooms.get(room).add(ws);
  }

  leaveRoom(ws, room) {
    this.rooms.get(room)?.delete(ws);
  }

  broadcastToRoom(room, message, exclude) {
    const members = this.rooms.get(room);
    if (!members) return;
    const data = JSON.stringify(message);
    for (const ws of members) {
      if (ws !== exclude && ws.readyState === 1) ws.send(data);
    }
  }

  sendToUser(userId, message) {
    const sockets = this.connections.get(userId);
    if (!sockets) return;
    const data = JSON.stringify(message);
    for (const ws of sockets) {
      if (ws.readyState === 1) ws.send(data);
    }
  }
}

const registry = new ConnectionRegistry();
```

## Message Protocol and Handlers

```javascript
// ws/handlers.js
const messageHandlers = {
  'room.join': (ws, payload) => {
    registry.joinRoom(ws, payload.room);
    registry.broadcastToRoom(payload.room, {
      type: 'room.member_joined',
      payload: { userId: ws.user.id, room: payload.room },
    }, ws);
    ws.send(JSON.stringify({ type: 'room.joined', payload: { room: payload.room } }));
  },

  'room.leave': (ws, payload) => {
    registry.leaveRoom(ws, payload.room);
    registry.broadcastToRoom(payload.room, {
      type: 'room.member_left',
      payload: { userId: ws.user.id, room: payload.room },
    });
  },

  'message.send': (ws, payload) => {
    const message = {
      type: 'message.received',
      payload: {
        id: crypto.randomUUID(),
        from: ws.user.id,
        room: payload.room,
        text: payload.text,
        timestamp: new Date().toISOString(),
      },
    };
    registry.broadcastToRoom(payload.room, message);
  },

  'typing.start': (ws, payload) => {
    registry.broadcastToRoom(payload.room, {
      type: 'typing.indicator',
      payload: { userId: ws.user.id, room: payload.room, typing: true },
    }, ws);
  },
};

wss.on('connection', (ws) => {
  registry.add(ws);
  setupHeartbeat(ws);

  ws.on('message', (raw) => {
    try {
      const { type, payload, correlationId } = JSON.parse(raw);
      const handler = messageHandlers[type];
      if (handler) {
        handler(ws, payload, correlationId);
      } else {
        ws.send(JSON.stringify({ type: 'error', payload: { detail: `Unknown type: ${type}` } }));
      }
    } catch (err) {
      ws.send(JSON.stringify({ type: 'error', payload: { detail: 'Invalid message format' } }));
    }
  });

  ws.on('close', () => registry.remove(ws));
});
```

## Heartbeat Keepalive

```javascript
// ws/heartbeat.js
function setupHeartbeat(ws) {
  ws.isAlive = true;
  ws.on('pong', () => { ws.isAlive = true; });
}

// Check every 30 seconds
const heartbeatInterval = setInterval(() => {
  for (const ws of wss.clients) {
    if (!ws.isAlive) {
      registry.remove(ws);
      return ws.terminate();
    }
    ws.isAlive = false;
    ws.ping();
  }
}, 30000);

wss.on('close', () => clearInterval(heartbeatInterval));
```

## Redis Pub/Sub Adapter (Multi-Instance)

```javascript
// ws/adapters/redis.js
const Redis = require('ioredis');
const pub = new Redis(process.env.REDIS_URL);
const sub = new Redis(process.env.REDIS_URL);

sub.subscribe('ws:broadcast');
sub.on('message', (channel, message) => {
  const { room, data, excludeServer } = JSON.parse(message);
  if (excludeServer === process.env.SERVER_ID) return;

  if (room) {
    registry.broadcastToRoom(room, data);
  } else {
    for (const ws of wss.clients) {
      if (ws.readyState === 1) ws.send(JSON.stringify(data));
    }
  }
});

function clusterBroadcast(room, data) {
  // Broadcast locally
  registry.broadcastToRoom(room, data);
  // Publish to other instances
  pub.publish('ws:broadcast', JSON.stringify({
    room, data, excludeServer: process.env.SERVER_ID,
  }));
}
```

## Message Protocol Format

```json
// Client -> Server
{ "type": "room.join", "payload": { "room": "general" }, "correlationId": "abc123" }
{ "type": "message.send", "payload": { "room": "general", "text": "Hello!" } }
{ "type": "typing.start", "payload": { "room": "general" } }

// Server -> Client
{ "type": "room.joined", "payload": { "room": "general" } }
{ "type": "message.received", "payload": { "id": "msg_1", "from": "usr_1", "text": "Hello!", "timestamp": "2026-03-10T14:30:00Z" } }
{ "type": "room.member_joined", "payload": { "userId": "usr_2", "room": "general" } }
```

## Browser Client

```javascript
const ws = new WebSocket(`wss://api.example.com/ws?token=${token}`);

ws.onopen = () => {
  ws.send(JSON.stringify({ type: 'room.join', payload: { room: 'general' } }));
};

ws.onmessage = (event) => {
  const { type, payload } = JSON.parse(event.data);
  switch (type) {
    case 'message.received':
      console.log(`${payload.from}: ${payload.text}`);
      break;
    case 'typing.indicator':
      console.log(`${payload.userId} is typing...`);
      break;
  }
};

ws.onclose = (event) => {
  console.log(`Connection closed: ${event.code} ${event.reason}`);
  setTimeout(() => reconnect(), 3000); // Auto-reconnect
};

function sendMessage(room, text) {
  ws.send(JSON.stringify({ type: 'message.send', payload: { room, text } }));
}
```

## WebSocket Tests

```javascript
const WebSocket = require('ws');

describe('WebSocket Server', () => {
  it('authenticates and joins room', (done) => {
    const ws = new WebSocket(`ws://localhost:3000/ws?token=${validToken}`);
    ws.on('open', () => {
      ws.send(JSON.stringify({ type: 'room.join', payload: { room: 'test' } }));
    });
    ws.on('message', (data) => {
      const msg = JSON.parse(data);
      if (msg.type === 'room.joined') {
        expect(msg.payload.room).toBe('test');
        ws.close();
        done();
      }
    });
  });

  it('rejects invalid token', (done) => {
    const ws = new WebSocket('ws://localhost:3000/ws?token=invalid');
    ws.on('error', () => done()); // 401 closes connection
  });

  it('broadcasts messages to room members', (done) => {
    const ws1 = new WebSocket(`ws://localhost:3000/ws?token=${token1}`);
    const ws2 = new WebSocket(`ws://localhost:3000/ws?token=${token2}`);

    ws2.on('message', (data) => {
      const msg = JSON.parse(data);
      if (msg.type === 'message.received') {
        expect(msg.payload.text).toBe('Hello!');
        ws1.close(); ws2.close();
        done();
      }
    });

    // Both join same room, then ws1 sends message
    ws1.on('open', () => ws1.send(JSON.stringify({ type: 'room.join', payload: { room: 'chat' } })));
    ws2.on('open', () => {
      ws2.send(JSON.stringify({ type: 'room.join', payload: { room: 'chat' } }));
      setTimeout(() => {
        ws1.send(JSON.stringify({ type: 'message.send', payload: { room: 'chat', text: 'Hello!' } }));
      }, 100);
    });
  });
});
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
