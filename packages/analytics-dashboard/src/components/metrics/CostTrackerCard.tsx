import { useMemo } from 'react';
import { useAnalyticsStore } from '../../store/analyticsStore';
import { formatCurrency } from '../../utils/formatters';

/**
 * CostTrackerCard - Shows total cost and breakdown by model
 * Displays total cost with model-level breakdown from cost events
 */
export function CostTrackerCard() {
  const totalCost = useAnalyticsStore((state) => state.totalCost);
  const events = useAnalyticsStore((state) => state.events);

  // Calculate breakdown by model from cost events
  const costBreakdown = useMemo(() => {
    const costsByModel = new Map<string, number>();

    events.forEach((event) => {
      if (event.type === 'cost.update') {
        const current = costsByModel.get(event.model) || 0;
        costsByModel.set(event.model, current + event.totalCost);
      }
    });

    // Sort by cost (descending) and take top 5 models
    const breakdown = Array.from(costsByModel.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([model, cost]) => ({
        model,
        cost,
        percentage: totalCost > 0 ? ((cost / totalCost) * 100).toFixed(1) : '0',
      }));

    return breakdown;
  }, [events, totalCost]);

  return (
    <div className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow duration-200">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-500">Total Cost</h3>
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
            d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
      </div>

      <p className="text-3xl font-bold text-gray-900 mb-4">
        {formatCurrency(totalCost)}
      </p>

      {costBreakdown.length > 0 ? (
        <div className="space-y-3">
          <p className="text-xs font-medium text-gray-400 uppercase tracking-wide">
            Breakdown by Model
          </p>
          {costBreakdown.map((item) => (
            <div key={item.model} className="space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-700 truncate max-w-[150px]">
                  {item.model}
                </span>
                <span className="text-sm font-medium text-gray-900">
                  {formatCurrency(item.cost)}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-1.5">
                <div
                  className="bg-blue-600 h-1.5 rounded-full transition-all duration-300"
                  style={{ width: `${item.percentage}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-gray-400 italic">No cost data available</p>
      )}
    </div>
  );
}
