# Metrics Components

Core metric cards for the Analytics Dashboard. These components display real-time analytics data from the Zustand store.

## Components

### MetricsGrid
4-column responsive grid layout containing all metric cards.

```tsx
import { MetricsGrid } from './components/metrics';

function Dashboard() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Analytics Dashboard</h1>
      <MetricsGrid />
    </div>
  );
}
```

### ActiveSessionsCard
Displays total events and recent conversation activity.

- Shows count of all events in the store
- Lists last 3 conversation events (created/updated)
- Displays relative timestamps ("2 hours ago")

**Data Source:** `useAnalyticsStore.events`

### PluginBreakdownCard
Shows plugin usage distribution with a pie chart.

- Displays top 5 most-used plugins
- Color-coded pie chart with percentages
- Uses Recharts library for visualization
- Total plugin activations displayed

**Data Source:** `useAnalyticsStore.pluginActivations`

### CostTrackerCard
Tracks total AI API costs with model breakdown.

- Shows total accumulated cost (sum across all models)
- Breakdown by model (top 5 by cost)
- Currency formatting with 3 decimal places
- Progress bars showing cost distribution

**Data Source:** `useAnalyticsStore.totalCost` + cost events

### RateLimitCard
Displays rate limit status with visual warnings.

- Overall rate limit percentage
- Per-service rate limit gauges
- Red background when >80% limit reached
- Progress bars with warning colors

**Data Source:** Rate limit warning events

## Styling

All components use:
- Tailwind CSS for styling
- White background with subtle shadows
- Hover effects (shadow-lg on hover)
- Responsive design (stacks on mobile)
- Professional card layout

## Data Flow

```
Analytics Events (WebSocket)
  ↓
Zustand Store (analyticsStore.ts)
  ↓
Selectors (selectors.ts)
  ↓
Metric Components
  ↓
Visual Display
```

## Usage Example

```tsx
import { MetricsGrid } from './components/metrics';
import { useAnalyticsStore } from './store/analyticsStore';

function App() {
  const connectionStatus = useAnalyticsStore((state) => state.connectionStatus);

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold">Analytics Dashboard</h1>
          <p className="text-sm text-gray-500">Status: {connectionStatus}</p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        <MetricsGrid />
      </main>
    </div>
  );
}
```

## Testing

To populate the store with test data:

```tsx
import { useAnalyticsStore } from './store/analyticsStore';

// Add test events
const store = useAnalyticsStore.getState();

store.addEvent({
  type: 'plugin.activation',
  pluginName: 'test-plugin',
  timestamp: Date.now(),
  conversationId: 'test-123',
});

store.addEvent({
  type: 'cost.update',
  model: 'claude-sonnet-4-5',
  inputCost: 0.003,
  outputCost: 0.015,
  totalCost: 0.018,
  currency: 'USD',
  timestamp: Date.now(),
  conversationId: 'test-123',
});

store.addEvent({
  type: 'rate_limit.warning',
  service: 'Claude API',
  current: 4500,
  limit: 5000,
  timestamp: Date.now(),
  conversationId: 'test-123',
});
```

## Component Props

All metric cards are self-contained and require no props. They automatically subscribe to the Zustand store and update in real-time when events arrive.

## Performance

- All components use `useMemo` for expensive calculations
- Zustand selectors prevent unnecessary re-renders
- Charts are rendered with ResponsiveContainer for adaptive sizing
- No prop drilling - direct store access

## Dependencies

- `react` - UI framework
- `zustand` - State management
- `recharts` - Chart visualization
- `date-fns` - Date formatting
- `tailwindcss` - Styling
