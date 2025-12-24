/**
 * useWebSocket Hook - React hook for WebSocket connection
 */
import { useEffect, useRef } from 'react';
import { WebSocketService } from '../services/websocket';
import { useAnalyticsStore } from '../store/analyticsStore';
import type { ConnectionStatus } from '../types';

const WS_URL = 'ws://localhost:3456';

/**
 * Hook for WebSocket connection management
 */
export function useWebSocket() {
  const serviceRef = useRef<WebSocketService | null>(null);
  const { addEvent, setConnectionStatus } = useAnalyticsStore();

  useEffect(() => {
    // Create WebSocket service
    const service = new WebSocketService({
      url: WS_URL,
      reconnectDelay: 3000,
      maxReconnectAttempts: Infinity,
    });

    serviceRef.current = service;

    // Subscribe to events
    const unsubscribeEvent = service.onEvent((event) => {
      console.log('[useWebSocket] Event received:', event.type);
      addEvent(event);
    });

    // Subscribe to status changes
    const unsubscribeStatus = service.onStatusChange((status: ConnectionStatus) => {
      console.log('[useWebSocket] Status changed:', status);
      setConnectionStatus(status);
    });

    // Subscribe to errors
    const unsubscribeError = service.onError((error) => {
      console.error('[useWebSocket] Error:', error.message);
    });

    // Connect to WebSocket
    console.log('[useWebSocket] Connecting to', WS_URL);
    service.connect();

    // Cleanup on unmount
    return () => {
      console.log('[useWebSocket] Cleaning up');
      unsubscribeEvent();
      unsubscribeStatus();
      unsubscribeError();
      service.disconnect();
      serviceRef.current = null;
    };
  }, [addEvent, setConnectionStatus]);

  return {
    status: useAnalyticsStore((state) => state.connectionStatus),
    lastEventTimestamp: useAnalyticsStore((state) => state.lastEventTimestamp),
  };
}
