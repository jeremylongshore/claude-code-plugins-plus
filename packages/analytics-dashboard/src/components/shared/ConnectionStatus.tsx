/**
 * ConnectionStatus Component - WebSocket connection indicator
 */
import React from 'react';
import { useAnalyticsStore } from '../../store/analyticsStore';

export const ConnectionStatus: React.FC = () => {
  const connectionStatus = useAnalyticsStore((state) => state.connectionStatus);
  const lastEventTimestamp = useAnalyticsStore((state) => state.lastEventTimestamp);

  // Status colors and text
  const statusConfig = {
    connected: {
      color: 'bg-green-500',
      text: 'Connected',
      pulse: true,
    },
    connecting: {
      color: 'bg-yellow-500',
      text: 'Connecting...',
      pulse: true,
    },
    disconnected: {
      color: 'bg-red-500',
      text: 'Disconnected',
      pulse: false,
    },
  };

  const config = statusConfig[connectionStatus];

  // Format last event time
  const formatLastEvent = () => {
    if (!lastEventTimestamp) return 'No events yet';
    
    const now = Date.now();
    const diff = now - lastEventTimestamp;
    
    if (diff < 1000) return 'Just now';
    if (diff < 60000) return Math.floor(diff / 1000) + 's ago';
    if (diff < 3600000) return Math.floor(diff / 60000) + 'm ago';
    return new Date(lastEventTimestamp).toLocaleTimeString();
  };

  return (
    <div className="fixed top-4 right-4 z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 px-4 py-3">
        <div className="flex items-center gap-3">
          {/* Status indicator */}
          <div className="relative">
            <div className={'w-3 h-3 rounded-full ' + config.color} />
            {config.pulse && (
              <div className={'absolute inset-0 w-3 h-3 rounded-full ' + config.color + ' animate-ping opacity-75'} />
            )}
          </div>

          {/* Status text */}
          <div className="flex flex-col">
            <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
              {config.text}
            </span>
            {lastEventTimestamp && (
              <span className="text-xs text-gray-500 dark:text-gray-400">
                Last event: {formatLastEvent()}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
