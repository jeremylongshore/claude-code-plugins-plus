/**
 * WebSocket Integration Example
 * 
 * This file demonstrates how to use the WebSocket integration
 * in your React components.
 */
import React from 'react';
import { useWebSocket } from '../hooks';
import { useAnalyticsStore } from '../store/analyticsStore';

// Example 1: Basic Usage
export const BasicExample: React.FC = () => {
  const { status } = useWebSocket();
  const events = useAnalyticsStore((state) => state.events);
  
  return (
    <div>
      <p>Status: {status}</p>
      <p>Events: {events.length}</p>
    </div>
  );
};

// Example 2: Plugin Usage
export const PluginUsage: React.FC = () => {
  const pluginActivations = useAnalyticsStore((state) => state.pluginActivations);
  
  return (
    <div>
      {Array.from(pluginActivations.entries()).map(([name, count]) => (
        <p key={name}>{name}: {count}</p>
      ))}
    </div>
  );
};

// Example 3: Cost Tracker
export const CostExample: React.FC = () => {
  const totalCost = useAnalyticsStore((state) => state.totalCost);
  return <p>Total: ${totalCost.toFixed(4)}</p>;
};
