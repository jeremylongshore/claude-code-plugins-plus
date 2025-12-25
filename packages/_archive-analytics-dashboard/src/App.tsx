/**
 * App Component - Main application wrapper
 */
import React from 'react';
import { useWebSocket } from './hooks';
import { ConnectionStatus, ErrorBoundary } from './components/shared';
import { useAnalyticsStore } from './store/analyticsStore';

export const App: React.FC = () => {
  const { status } = useWebSocket();
  const events = useAnalyticsStore((state) => state.events);
  const totalCost = useAnalyticsStore((state) => state.totalCost);

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <ConnectionStatus />
        
        <div className="container mx-auto px-4 py-8">
          <header className="mb-8">
            <h1 className="text-4xl font-bold text-gray-900 dark:text-gray-100 mb-2">
              Claude Code Analytics Dashboard
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Real-time monitoring of plugin usage, skills, and API costs
            </p>
          </header>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-6">
              <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-2">
                Connection Status
              </h3>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100 capitalize">
                {status}
              </p>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-6">
              <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-2">
                Total Events
              </h3>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {events.length}
              </p>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-6">
              <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-2">
                Total Cost
              </h3>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                ${totalCost.toFixed(4)}
              </p>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-6">
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">
              Recent Events
            </h2>
            
            {events.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-gray-500 dark:text-gray-400">
                  Waiting for events from analytics daemon...
                </p>
                <p className="text-sm text-gray-400 dark:text-gray-500 mt-2">
                  Make sure the daemon is running on ws://localhost:3456
                </p>
              </div>
            ) : (
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {events.slice(-20).reverse().map((event, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                          {event.type}
                        </span>
                        {'pluginName' in event && (
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            {event.pluginName}
                          </span>
                        )}
                        {'skillName' in event && (
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            {event.skillName}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        {new Date(event.timestamp).toLocaleTimeString()}
                      </p>
                    </div>
                    
                    {'totalCost' in event && (
                      <span className="text-sm font-mono text-green-600 dark:text-green-400">
                        ${event.totalCost.toFixed(4)}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </ErrorBoundary>
  );
};
