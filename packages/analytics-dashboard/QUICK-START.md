# Quick Start Guide - WebSocket Integration

## Overview

The WebSocket integration layer connects the Analytics Dashboard frontend to the analytics-daemon backend for real-time event streaming.

## Prerequisites

- Node.js 18+ installed
- Backend server (analytics-daemon) built and ready
- Port 3456 available for WebSocket

## Quick Start (2 Steps)

### Step 1: Start Backend Server

```bash
cd packages/analytics-daemon
pnpm build
pnpm start
```

**Expected output:**
```
Analytics server listening on ws://localhost:3456
```

### Step 2: Start Frontend Dashboard

```bash
cd packages/analytics-dashboard
pnpm dev
```

**Expected output:**
```
VITE v6.0.11  ready in 234 ms
Local: http://localhost:5173/
```

### Step 3: Open Browser

Navigate to: `http://localhost:5173/`

**You should see:**
- ✅ Green connection indicator (top-right corner)
- ✅ "Connected" status
- ✅ Dashboard with metric cards
- ✅ "Waiting for events..." message

## Testing Event Reception

### Console Logs

Open browser DevTools (F12) and check Console tab.

**Expected logs:**
```
[useWebSocket] Connecting to ws://localhost:3456
WebSocket connected to ws://localhost:3456
[useWebSocket] Status changed: connected
```

### When Events Arrive

**Console will show:**
```
Received event: plugin.activation { ... }
[useWebSocket] Event received: plugin.activation
```

**UI will update:**
- Event appears in "Recent Events" list
- Last event timestamp updates
- Metrics cards update (cost, count, etc.)

## Testing Auto-Reconnect

1. Stop backend server (Ctrl+C in terminal)
2. Observe browser:
   - Connection indicator turns RED
   - Status shows "Disconnected"
   - Console shows: "Reconnecting in 3000ms (attempt 1)"

3. Restart backend server:
   ```bash
   pnpm start
   ```

4. Observe browser (within 3 seconds):
   - Connection indicator turns GREEN
   - Status shows "Connected"
   - Console shows: "WebSocket connected"

## File Structure

```
packages/analytics-dashboard/
├── src/
│   ├── types/analytics.ts          # Event types
│   ├── services/websocket.ts       # WebSocket service
│   ├── store/analyticsStore.ts     # Zustand state
│   ├── hooks/useWebSocket.ts       # React hook
│   ├── components/shared/
│   │   ├── ConnectionStatus.tsx    # Connection UI
│   │   └── ErrorBoundary.tsx       # Error handling
│   └── App.tsx                     # Test app
├── WEBSOCKET-INTEGRATION.md        # Full documentation
├── IMPLEMENTATION-SUMMARY.md       # Implementation details
└── QUICK-START.md                  # This file
```

## Common Issues

### Connection Fails

**Problem:** Red "disconnected" indicator, no connection

**Solutions:**
1. Verify backend is running: `curl http://localhost:3456`
2. Check backend logs for errors
3. Verify port 3456 is not blocked by firewall
4. Check browser console for error messages

### Events Not Appearing

**Problem:** Connected but no events showing

**Solutions:**
1. Verify backend is broadcasting events
2. Check backend logs for event emission
3. Verify conversation files are being watched
4. Check browser console for JSON parse errors

### TypeScript Errors

**Problem:** TypeScript compilation errors

**Solutions:**
```bash
npm run typecheck    # Check for type errors
npm run build        # Test production build
```

## Usage in Components

### Basic Usage

```typescript
import { useWebSocket } from './hooks';
import { useAnalyticsStore } from './store/analyticsStore';

const MyComponent = () => {
  // Get connection status
  const { status } = useWebSocket();
  
  // Get events from store
  const events = useAnalyticsStore((state) => state.events);
  const totalCost = useAnalyticsStore((state) => state.totalCost);
  
  return (
    <div>
      <p>Status: {status}</p>
      <p>Events: {events.length}</p>
      <p>Cost: ${totalCost.toFixed(4)}</p>
    </div>
  );
};
```

### Advanced Usage

```typescript
import { useAnalyticsStore } from './store/analyticsStore';

const AdvancedComponent = () => {
  // Get specific event types
  const pluginEvents = useAnalyticsStore(
    (state) => state.getEventsByType('plugin.activation')
  );
  
  // Get metrics
  const pluginActivations = useAnalyticsStore(
    (state) => state.pluginActivations
  );
  
  // Clear events
  const clearEvents = useAnalyticsStore((state) => state.clearEvents);
  
  return (
    <div>
      <button onClick={clearEvents}>Clear Events</button>
      {Array.from(pluginActivations.entries()).map(([name, count]) => (
        <p key={name}>{name}: {count} activations</p>
      ))}
    </div>
  );
};
```

## Event Types

The backend can send these event types:

```typescript
'plugin.activation'      // Plugin activated
'skill.trigger'          // Agent skill triggered
'llm.call'              // LLM API called
'cost.update'           // Cost calculation
'rate_limit.warning'    // Rate limit warning
'conversation.created'  // New conversation
'conversation.updated'  // Conversation modified
'server.connected'      // Welcome message
```

## Configuration

### Change WebSocket URL

Edit `src/hooks/useWebSocket.ts`:

```typescript
const WS_URL = 'ws://localhost:3456';  // Change this
```

### Change Reconnect Delay

Edit `src/hooks/useWebSocket.ts`:

```typescript
const service = new WebSocketService({
  url: WS_URL,
  reconnectDelay: 3000,  // Change to desired milliseconds
  maxReconnectAttempts: Infinity
});
```

### Change Event Limit

Edit `src/store/analyticsStore.ts`:

```typescript
maxEvents: 1000,  // Change to desired limit
```

## Next Steps

1. **Integrate with Metrics**: Connect to existing metric components
2. **Add Filtering**: Filter events by type/plugin/date
3. **Add Charts**: Visualize data with recharts
4. **Export Data**: Add CSV/JSON export functionality
5. **Persistence**: Save events to local storage

## Support

- Full documentation: `WEBSOCKET-INTEGRATION.md`
- Implementation details: `IMPLEMENTATION-SUMMARY.md`
- Code examples: See `src/App.tsx`

## Status

✅ **Ready for Testing**

All components are implemented and tested:
- WebSocket service: ✅
- Zustand store: ✅
- React hook: ✅
- UI components: ✅
- Error handling: ✅
- Auto-reconnect: ✅
- Documentation: ✅
