import { useMemo } from 'react';
import { useAnalyticsStore } from '../../store/analyticsStore';
import { formatPercentage } from '../../utils/formatters';

interface RateLimitInfo {
  service: string;
  current: number;
  limit: number;
  resetAt?: number;
}

/**
 * RateLimitCard - Shows rate limit gauges with warning colors
 * Displays current/limit ratios with progress bars
 * Warning color (red) when >80% used
 */
export function RateLimitCard() {
  const events = useAnalyticsStore((state) => state.events);

  // Extract rate limits from events
  const rateLimits = useMemo(() => {
    const limitsByService = new Map<string, RateLimitInfo>();

    events.forEach((event) => {
      if (event.type === 'rate_limit.warning') {
        limitsByService.set(event.service, {
          service: event.service,
          current: event.current,
          limit: event.limit,
          resetAt: event.resetAt,
        });
      }
    });

    return Array.from(limitsByService.values());
  }, [events]);

  // Calculate overall rate limit status
  const overallStatus = useMemo(() => {
    if (rateLimits.length === 0) return { percentage: 0, isWarning: false };

    const totalPercentage =
      rateLimits.reduce((sum: number, rl: RateLimitInfo) => {
        const percentage = rl.limit > 0 ? (rl.current / rl.limit) * 100 : 0;
        return sum + percentage;
      }, 0) / rateLimits.length;

    return {
      percentage: totalPercentage,
      isWarning: totalPercentage > 80,
    };
  }, [rateLimits]);

  return (
    <div
      className={`rounded-lg shadow p-6 hover:shadow-lg transition-shadow duration-200 ${
        overallStatus.isWarning ? 'bg-red-50' : 'bg-white'
      }`}
    >
      <div className="flex items-center justify-between mb-4">
        <h3
          className={`text-sm font-medium ${
            overallStatus.isWarning ? 'text-red-600' : 'text-gray-500'
          }`}
        >
          Rate Limits
        </h3>
        <svg
          className={`w-5 h-5 ${overallStatus.isWarning ? 'text-red-500' : 'text-gray-400'}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
      </div>

      <p
        className={`text-3xl font-bold mb-4 ${
          overallStatus.isWarning ? 'text-red-700' : 'text-gray-900'
        }`}
      >
        {formatPercentage(overallStatus.percentage)}
      </p>

      {rateLimits.length > 0 ? (
        <div className="space-y-3">
          <p className="text-xs font-medium text-gray-400 uppercase tracking-wide">
            Service Limits
          </p>
          {rateLimits.map((rateLimit: RateLimitInfo) => {
            const percentage =
              rateLimit.limit > 0 ? (rateLimit.current / rateLimit.limit) * 100 : 0;
            const isWarning = percentage > 80;

            return (
              <div key={rateLimit.service} className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-700 truncate max-w-[120px]">
                    {rateLimit.service}
                  </span>
                  <span
                    className={`text-sm font-medium ${
                      isWarning ? 'text-red-600' : 'text-gray-900'
                    }`}
                  >
                    {rateLimit.current}/{rateLimit.limit}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all duration-300 ${
                      isWarning ? 'bg-red-600' : 'bg-green-600'
                    }`}
                    style={{ width: `${Math.min(percentage, 100)}%` }}
                  />
                </div>
                {isWarning && (
                  <p className="text-xs text-red-600 font-medium">
                    Warning: {formatPercentage(percentage)} of limit reached
                  </p>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        <p className="text-sm text-gray-400 italic">No rate limit data</p>
      )}
    </div>
  );
}
