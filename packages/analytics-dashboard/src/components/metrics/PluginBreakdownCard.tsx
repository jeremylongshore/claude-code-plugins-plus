import { useMemo } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { useAnalyticsStore } from '../../store/analyticsStore';
import { selectTopPlugins } from '../../store/selectors';

// Color palette for pie chart segments
const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'];

/**
 * PluginBreakdownCard - Shows plugin usage distribution with pie chart
 * Displays top 5 most-used plugins with color-coded segments
 */
export function PluginBreakdownCard() {
  const topPlugins = useAnalyticsStore(selectTopPlugins(5));
  const pluginActivations = useAnalyticsStore((state) => state.pluginActivations);

  // Convert to chart data format with percentages
  const chartData = useMemo(() => {
    const total = Array.from(pluginActivations.values()).reduce((sum, count) => sum + count, 0);

    return topPlugins.map((plugin) => ({
      name: plugin.name,
      value: plugin.count,
      percentage: total > 0 ? ((plugin.count / total) * 100).toFixed(1) : '0',
    }));
  }, [topPlugins, pluginActivations]);

  const totalUsage = chartData.reduce((sum, item) => sum + item.value, 0);

  return (
    <div className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow duration-200">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-500">Plugin Usage</h3>
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
            d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
          />
        </svg>
      </div>

      {chartData.length > 0 ? (
        <>
          <p className="text-3xl font-bold text-gray-900 mb-4">{totalUsage}</p>

          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ percentage }) => `${percentage}%`}
                outerRadius={70}
                fill="#8884d8"
                dataKey="value"
              >
                {chartData.map((_entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value: number, name: string) => [`${value} uses`, name]}
              />
            </PieChart>
          </ResponsiveContainer>

          <div className="mt-4 space-y-2">
            {chartData.map((plugin, index) => (
              <div key={plugin.name} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: COLORS[index % COLORS.length] }}
                  />
                  <span className="text-sm text-gray-700 truncate max-w-[120px]">
                    {plugin.name}
                  </span>
                </div>
                <span className="text-sm font-medium text-gray-900">
                  {plugin.percentage}%
                </span>
              </div>
            ))}
          </div>
        </>
      ) : (
        <div className="flex items-center justify-center h-[200px]">
          <p className="text-sm text-gray-400 italic">No plugin usage data</p>
        </div>
      )}
    </div>
  );
}
