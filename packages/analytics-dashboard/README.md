# Analytics Dashboard - WebSocket Integration

Real-time analytics dashboard for Claude Code plugin usage, skill triggers, and API costs.

## Quick Start

### 1. Start Backend
```bash
cd packages/analytics-daemon
pnpm build && pnpm start
```

### 2. Start Frontend
```bash
cd packages/analytics-dashboard
pnpm dev
```

### 3. Open Browser
Navigate to `http://localhost:5173/`

You should see:
- Green connection indicator (top-right)
- "Connected" status
- Dashboard with metrics cards

## Features

### Core Functionality
- ✅ WebSocket connection to `ws://localhost:3456`
- ✅ Real-time event streaming
- ✅ Auto-reconnect (3-second delay)
- ✅ Connection status indicator
- ✅ Error boundary for graceful error handling
- ✅ Event storage (last 1,000 events)

### Event Types
- `plugin.activation` - Plugin activated
- `skill.trigger` - Agent skill triggered
- `llm.call` - LLM API called
- `cost.update` - Cost calculation
- `rate_limit.warning` - Rate limit warning
- `conversation.created` - New conversation
- `conversation.updated` - Conversation modified

### Metrics Tracked
- Total events received
- Plugin activation counts
- Skill trigger counts
- Total API costs
- Connection health

## Architecture

```
Frontend (React + TypeScript)
├── useWebSocket Hook
│   └── WebSocketService
│       └── ws://localhost:3456
│
├── Zustand Store (State)
│   ├── Events storage
│   ├── Metrics calculation
│   └── Connection status
│
└── UI Components
    ├── ConnectionStatus
    ├── ErrorBoundary
    └── Metrics Cards
```

## Usage Example

```typescript
import { useWebSocket } from './hooks';
import { useAnalyticsStore } from './store/analyticsStore';

const MyComponent = () => {
  // Get connection status
  const { status } = useWebSocket();
  
  // Get events and metrics
  const events = useAnalyticsStore((state) => state.events);
  const totalCost = useAnalyticsStore((state) => state.totalCost);
  const pluginActivations = useAnalyticsStore(
    (state) => state.pluginActivations
  );
  
  return (
    <div>
      <p>Status: {status}</p>
      <p>Events: {events.length}</p>
      <p>Cost: ${totalCost.toFixed(4)}</p>
    </div>
  );
};
```

## File Structure

```
src/
├── types/
│   └── analytics.ts          # Event types
├── services/
│   └── websocket.ts          # WebSocket service
├── store/
│   └── analyticsStore.ts     # Zustand state
├── hooks/
│   └── useWebSocket.ts       # React hook
├── components/
│   └── shared/
│       ├── ConnectionStatus.tsx
│       └── ErrorBoundary.tsx
└── App.tsx                   # Main app
```

## Documentation

- `WEBSOCKET-INTEGRATION.md` - Complete technical documentation
- `IMPLEMENTATION-SUMMARY.md` - Implementation details
- `QUICK-START.md` - Quick start guide
- `COMPLETION-REPORT.md` - Task completion report

## Testing

### Test Connection
1. Start backend server
2. Start frontend dashboard
3. Check for green connection indicator
4. Open browser console
5. Verify logs: "WebSocket connected"

### Test Auto-Reconnect
1. Stop backend server (Ctrl+C)
2. Watch indicator turn red
3. Restart backend server
4. Watch indicator turn green (within 3 seconds)

### Test Event Reception
- Events appear in "Recent Events" list
- Metrics update in real-time
- Console logs show event details

## Configuration

### Change WebSocket URL
Edit `src/hooks/useWebSocket.ts`:
```typescript
const WS_URL = 'ws://localhost:3456';
```

### Change Reconnect Delay
Edit `src/hooks/useWebSocket.ts`:
```typescript
reconnectDelay: 3000,  // milliseconds
```

### Change Event Limit
Edit `src/store/analyticsStore.ts`:
```typescript
maxEvents: 1000,  // events to keep in memory
```

## Dependencies

- `react` ^18.3.1 - UI framework
- `react-dom` ^18.3.1 - React DOM
- `zustand` ^5.0.2 - State management
- `typescript` ^5.5.0 - Type safety
- `vite` ^6.0.11 - Dev server
- `tailwindcss` ^4.1.18 - Styling

## Browser Support

- Chrome/Edge: ✅
- Firefox: ✅
- Safari: ✅

## Status

✅ **Complete and Ready for Testing**

All components implemented:
- WebSocket service layer ✅
- Zustand store ✅
- React hooks ✅
- UI components ✅
- Error handling ✅
- Documentation ✅

## Next Steps

1. Test with analytics-daemon backend
2. Integrate with metrics components
3. Add event filtering
4. Add charts (recharts)
5. Add data export

## Support

See documentation files for detailed information:
- Technical docs: `WEBSOCKET-INTEGRATION.md`
- Quick start: `QUICK-START.md`
- Examples: `src/examples/WebSocketExample.tsx`
