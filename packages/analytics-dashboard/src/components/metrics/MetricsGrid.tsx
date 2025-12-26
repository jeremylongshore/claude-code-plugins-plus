import { ActiveSessionsCard } from './ActiveSessionsCard';
import { PluginBreakdownCard } from './PluginBreakdownCard';
import { CostTrackerCard } from './CostTrackerCard';
import { RateLimitCard } from './RateLimitCard';

/**
 * MetricsGrid - 4-column responsive grid layout for metric cards
 * Stacks on mobile, 2-column on tablet, 4-column on desktop
 */
export function MetricsGrid() {
  return (
    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
      <ActiveSessionsCard />
      <PluginBreakdownCard />
      <CostTrackerCard />
      <RateLimitCard />
    </div>
  );
}
