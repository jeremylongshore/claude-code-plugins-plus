/**
 * Analytics Store - Zustand state management
 */
import { create } from 'zustand';
import type { AnalyticsEvent, ConnectionStatus } from '../types';

interface AnalyticsState {
  // Connection state
  connectionStatus: ConnectionStatus;
  lastEventTimestamp: number | null;

  // Event storage
  events: AnalyticsEvent[];
  maxEvents: number;

  // Metrics (derived from events)
  pluginActivations: Map<string, number>;
  skillTriggers: Map<string, number>;
  totalCost: number;

  // Actions
  setConnectionStatus: (status: ConnectionStatus) => void;
  addEvent: (event: AnalyticsEvent) => void;
  clearEvents: () => void;
  getEventsByType: (type: string) => AnalyticsEvent[];
}

/**
 * Create analytics store with Zustand
 */
export const useAnalyticsStore = create<AnalyticsState>((set, get) => ({
  // Initial state
  connectionStatus: 'disconnected',
  lastEventTimestamp: null,
  events: [],
  maxEvents: 1000, // Keep last 1000 events
  pluginActivations: new Map(),
  skillTriggers: new Map(),
  totalCost: 0,

  // Update connection status
  setConnectionStatus: (status: ConnectionStatus) => {
    set({ connectionStatus: status });
  },

  // Add new event
  addEvent: (event: AnalyticsEvent) => {
    set((state) => {
      // Update last event timestamp
      const lastEventTimestamp = event.timestamp;

      // Add event to array, keep only last maxEvents
      const events = [...state.events, event];
      if (events.length > state.maxEvents) {
        events.shift(); // Remove oldest event
      }

      // Update metrics based on event type
      let pluginActivations = new Map(state.pluginActivations);
      let skillTriggers = new Map(state.skillTriggers);
      let totalCost = state.totalCost;

      switch (event.type) {
        case 'plugin.activation': {
          const count = pluginActivations.get(event.pluginName) || 0;
          pluginActivations.set(event.pluginName, count + 1);
          break;
        }
        case 'skill.trigger': {
          const count = skillTriggers.get(event.skillName) || 0;
          skillTriggers.set(event.skillName, count + 1);
          break;
        }
        case 'cost.update': {
          totalCost += event.totalCost;
          break;
        }
      }

      return {
        events,
        lastEventTimestamp,
        pluginActivations,
        skillTriggers,
        totalCost,
      };
    });
  },

  // Clear all events
  clearEvents: () => {
    set({
      events: [],
      pluginActivations: new Map(),
      skillTriggers: new Map(),
      totalCost: 0,
      lastEventTimestamp: null,
    });
  },

  // Get events by type
  getEventsByType: (type: string) => {
    return get().events.filter((event) => event.type === type);
  },
}));
