import { useAnalyticsStore } from '../../store/analyticsStore';
import { selectRecentEvents } from '../../store/selectors';
import { formatTimestamp } from '../../utils/formatters';

/**
 * ActiveSessionsCard - Displays count of active events and recent conversation activity
 * Shows total events with list of last 3 conversation events
 */
export function ActiveSessionsCard() {
  const recentEvents = useAnalyticsStore(selectRecentEvents(60)); // Last 60 minutes
  const events = useAnalyticsStore((state) => state.events);

  // Get last 3 conversation events
  const recentConversations = recentEvents
    .filter(
      (e) => e.type === 'conversation.created' || e.type === 'conversation.updated'
    )
    .slice(-3)
    .reverse();

  return (
    <div className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow duration-200">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-500">Active Events</h3>
        <svg
          className="w-5 h-5 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
          />
        </svg>
      </div>

      <p className="text-3xl font-bold text-gray-900 mb-4">{events.length}</p>

      {recentConversations.length > 0 ? (
        <div className="space-y-2">
          <p className="text-xs font-medium text-gray-400 uppercase tracking-wide">
            Recent Activity
          </p>
          {recentConversations.map((event) => (
            <div key={event.timestamp} className="border-l-2 border-blue-500 pl-3 py-1">
              <p className="text-sm text-gray-700 font-medium truncate">
                {event.type === 'conversation.created'
                  ? event.title || 'New Conversation'
                  : `${(event as any).messageCount || 0} messages`}
              </p>
              <p className="text-xs text-gray-500">
                {formatTimestamp(event.timestamp)}
              </p>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-gray-400 italic">No recent activity</p>
      )}
    </div>
  );
}
