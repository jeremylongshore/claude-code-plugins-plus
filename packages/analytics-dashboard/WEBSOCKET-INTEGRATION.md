# WebSocket Integration Layer

This document describes the WebSocket integration for the Analytics Dashboard.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Analytics Dashboard (Frontend)           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐     ┌──────────────┐     ┌─────────────┐ │
│  │ useWebSocket │────▶│ WebSocket    │────▶│   Zustand   │ │
│  │   Hook       │     │   Service    │     │    Store    │ │
│  └──────────────┘     └──────────────┘     └─────────────┘ │
│         │                     │                     │       │
│         │                     │                     │       │
│         ▼                     ▼                     ▼       │
│  ┌──────────────┐     ┌──────────────┐     ┌─────────────┐ │
│  │ Connection   │     │ Event        │     │  React      │ │
│  │   Status     │     │ Handlers     │     │ Components  │ │
│  └──────────────┘     └──────────────┘     └─────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ WebSocket (ws://localhost:3456)
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Analytics Daemon (Backend)                      │
│              packages/analytics-daemon                       │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. Types (`src/types/analytics.ts`)

Defines all event types and connection states:

- **AnalyticsEvent**: Union type of all possible events
  - `plugin.activation`: Plugin activated
  - `skill.trigger`: Agent skill triggered
  - `llm.call`: LLM API called
  - `cost.update`: Cost calculation updated
  - `rate_limit.warning`: Rate limit warning
  - `conversation.created`: New conversation
  - `conversation.updated`: Conversation modified
  - `server.connected`: Welcome message from server

- **ConnectionStatus**: `'connecting' | 'connected' | 'disconnected'`

### 2. WebSocket Service (`src/services/websocket.ts`)

Low-level WebSocket connection management:

**Features:**
- Automatic reconnection with configurable delay (default: 3 seconds)
- Infinite retry attempts (configurable)
- Event-based architecture with handlers
- Connection lifecycle management

**Key Methods:**
```typescript
connect(): void              // Connect to WebSocket server
disconnect(): void           // Disconnect and stop reconnection
onEvent(handler): () => void // Subscribe to events (returns unsubscribe)
onStatusChange(handler): () => void  // Subscribe to status changes
onError(handler): () => void // Subscribe to errors
getStatus(): ConnectionStatus // Get current connection status
```

**Configuration:**
```typescript
const service = new WebSocketService({
  url: 'ws://localhost:3456',
  reconnectDelay: 3000,          // 3 seconds
  maxReconnectAttempts: Infinity // Unlimited retries
});
```

### 3. Zustand Store (`src/store/analyticsStore.ts`)

Global state management for analytics data:

**State:**
```typescript
interface AnalyticsState {
  // Connection
  connectionStatus: ConnectionStatus;
  lastEventTimestamp: number | null;

  // Events
  events: AnalyticsEvent[];
  maxEvents: number; // Default: 1000

  // Metrics
  pluginActivations: Map<string, number>;
  skillTriggers: Map<string, number>;
  totalCost: number;

  // Actions
  setConnectionStatus(status): void;
  addEvent(event): void;
  clearEvents(): void;
  getEventsByType(type): AnalyticsEvent[];
}
```

**Usage:**
```typescript
import { useAnalyticsStore } from './store/analyticsStore';

const MyComponent = () => {
  const connectionStatus = useAnalyticsStore((state) => state.connectionStatus);
  const events = useAnalyticsStore((state) => state.events);
  const { addEvent } = useAnalyticsStore();
  
  // Component logic...
};
```

### 4. useWebSocket Hook (`src/hooks/useWebSocket.ts`)

React hook for WebSocket integration:

**Features:**
- Automatic connection on mount
- Cleanup on unmount
- Integration with Zustand store
- Error handling

**Usage:**
```typescript
import { useWebSocket } from './hooks';

const MyComponent = () => {
  const { status, lastEventTimestamp } = useWebSocket();
  
  return (
    <div>
      <p>Status: {status}</p>
      <p>Last event: {lastEventTimestamp}</p>
    </div>
  );
};
```

**Lifecycle:**
1. On mount: Creates WebSocketService instance
2. Connects to `ws://localhost:3456`
3. Subscribes to events → calls `addEvent()` in store
4. Subscribes to status changes → calls `setConnectionStatus()` in store
5. On unmount: Unsubscribes all handlers and disconnects

### 5. ConnectionStatus Component (`src/components/shared/ConnectionStatus.tsx`)

Visual connection indicator:

**Features:**
- Fixed position (top-right corner)
- Color-coded status:
  - Green: Connected (with pulse animation)
  - Yellow: Connecting (with pulse animation)
  - Red: Disconnected (no animation)
- Shows last event timestamp
- Responsive design
- Dark mode support

**Display Logic:**
```typescript
if (diff < 1s)     → "Just now"
if (diff < 60s)    → "Xs ago"
if (diff < 3600s)  → "Xm ago"
else               → HH:MM:SS
```

### 6. ErrorBoundary Component (`src/components/shared/ErrorBoundary.tsx`)

React error boundary for graceful error handling:

**Features:**
- Catches React errors during render
- Displays user-friendly error messages
- Shows error details and component stack
- Provides "Try Again" and "Reload Page" buttons
- Troubleshooting tips for common issues
- Dark mode support

**Usage:**
```typescript
<ErrorBoundary>
  <App />
</ErrorBoundary>
```

## Event Flow

```
1. Backend broadcasts event
   ↓
2. WebSocket.onmessage fires
   ↓
3. JSON.parse(event.data)
   ↓
4. WebSocketService.handleEvent()
   ↓
5. Calls all registered event handlers
   ↓
6. useWebSocket hook's event handler
   ↓
7. analyticsStore.addEvent()
   ↓
8. State updated, React components re-render
```

## Auto-Reconnect Logic

```
1. Connection lost (network error, server restart)
   ↓
2. ws.onclose fires
   ↓
3. Check if manual close (isManualClose)
   ↓
4. If NOT manual: scheduleReconnect()
   ↓
5. Wait reconnectDelay (3 seconds)
   ↓
6. Attempt reconnect
   ↓
7. On success: Reset reconnectAttempts to 0
   ↓
8. On failure: Increment reconnectAttempts, repeat from step 5
```

## Connection States

### Connecting
```typescript
status = 'connecting'
- Yellow indicator with pulse
- "Connecting..." text
- Attempting to establish connection
```

### Connected
```typescript
status = 'connected'
- Green indicator with pulse
- "Connected" text
- Ready to receive events
```

### Disconnected
```typescript
status = 'disconnected'
- Red indicator (no pulse)
- "Disconnected" text
- Will auto-reconnect unless manually closed
```

## Testing

### 1. Start Backend Server

```bash
cd packages/analytics-daemon
pnpm build
pnpm start
```

Expected output:
```
Analytics server listening on ws://localhost:3456
```

### 2. Start Frontend

```bash
cd packages/analytics-dashboard
pnpm dev
```

Expected output:
```
VITE v6.0.11  ready in X ms
Local: http://localhost:5173/
```

### 3. Test Connection

Open browser to `http://localhost:5173/`

**Console logs (should see):**
```
[useWebSocket] Connecting to ws://localhost:3456
WebSocket connected to ws://localhost:3456
[useWebSocket] Status changed: connected
```

**UI should show:**
- Green connection indicator (top-right)
- "Connected" status
- "Waiting for events..." message

### 4. Test Event Reception

Trigger a test event from backend:

```bash
# In analytics-daemon directory
pnpm test:event
```

**Console logs (should see):**
```
Received event: plugin.activation { ... }
[useWebSocket] Event received: plugin.activation
```

**UI should update:**
- Last event timestamp updates
- Event appears in "Recent Events" list
- Metrics update accordingly

### 5. Test Auto-Reconnect

1. Stop backend server (Ctrl+C)
2. Observe UI:
   - Status changes to "disconnected" (red)
   - Console shows reconnection attempts
3. Restart backend server
4. Observe UI:
   - Status changes to "connected" (green)
   - Console shows successful reconnection

## Error Handling

### Network Errors
- Caught in `ws.onerror`
- Triggers auto-reconnect
- Logged to console

### JSON Parse Errors
- Caught in `ws.onmessage`
- Invalid JSON logged to console
- Connection remains active

### React Errors
- Caught by ErrorBoundary
- Displays user-friendly error UI
- Provides recovery options

## Configuration

### WebSocket URL

Default: `ws://localhost:3456`

To change:
```typescript
// src/hooks/useWebSocket.ts
const WS_URL = 'ws://your-server:port';
```

### Reconnect Settings

```typescript
// src/hooks/useWebSocket.ts
const service = new WebSocketService({
  url: WS_URL,
  reconnectDelay: 3000,          // Milliseconds between retries
  maxReconnectAttempts: Infinity // Max retry attempts
});
```

### Event Storage

```typescript
// src/store/analyticsStore.ts
maxEvents: 1000  // Keep last 1000 events in memory
```

## Completion Criteria

All criteria have been met:

- [x] WebSocket connects to ws://localhost:3456
- [x] Connection status displays in UI (ConnectionStatus component)
- [x] Events logged to console when received
- [x] Auto-reconnect works after disconnect (3-second delay)
- [x] Error states handled gracefully (ErrorBoundary)

## Files Created

```
packages/analytics-dashboard/
├── src/
│   ├── types/
│   │   ├── analytics.ts          # Event types and interfaces
│   │   └── index.ts              # Type exports
│   ├── services/
│   │   ├── websocket.ts          # WebSocket service layer
│   │   └── index.ts              # Service exports
│   ├── store/
│   │   └── analyticsStore.ts     # Zustand state management
│   ├── hooks/
│   │   ├── useWebSocket.ts       # WebSocket React hook
│   │   └── index.ts              # Hook exports
│   ├── components/
│   │   └── shared/
│   │       ├── ConnectionStatus.tsx  # Connection indicator
│   │       ├── ErrorBoundary.tsx     # Error boundary
│   │       └── index.ts              # Component exports
│   ├── App.tsx                   # Main app component (with test UI)
│   ├── main.tsx                  # Entry point
│   └── index.css                 # Global styles
├── index.html                    # HTML template
└── WEBSOCKET-INTEGRATION.md      # This document
```

## Next Steps

1. **Integration with Metrics Components**: The WebSocket layer is now ready to be consumed by the metrics dashboard components (ActiveSessionsCard, CostTrackerCard, etc.)

2. **Backend Event Generation**: Implement conversation file watching and event emission in analytics-daemon

3. **Advanced Features**:
   - Event filtering and search
   - Historical data persistence
   - Export analytics data
   - Custom event subscriptions
   - Real-time charts and graphs
