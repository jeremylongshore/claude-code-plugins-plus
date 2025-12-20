/**
 * Client-Side Analytics Utility
 *
 * Privacy-respecting, localStorage-based analytics for plugin tracking.
 * No personal data collected, no external services.
 *
 * Bead ID: claude-code-plugins-5q4
 */

interface PluginView {
    slug: string;
    timestamp: number;
    count: number;
}

interface PluginInstall {
    slug: string;
    timestamp: number;
}

interface AnalyticsData {
    views: Record<string, PluginView>;
    installs: PluginInstall[];
    sessionStart: number;
}

const STORAGE_KEY = 'ccpi_analytics';
const WEEK_MS = 7 * 24 * 60 * 60 * 1000;

/**
 * Get analytics data from localStorage
 */
function getAnalytics(): AnalyticsData {
    try {
        const data = localStorage.getItem(STORAGE_KEY);
        if (!data) {
            return {
                views: {},
                installs: [],
                sessionStart: Date.now()
            };
        }
        return JSON.parse(data);
    } catch {
        return {
            views: {},
            installs: [],
            sessionStart: Date.now()
        };
    }
}

/**
 * Save analytics data to localStorage
 */
function saveAnalytics(data: AnalyticsData): void {
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    } catch (error) {
        console.warn('Failed to save analytics:', error);
    }
}

/**
 * Track a plugin view
 */
export function trackView(slug: string): void {
    const data = getAnalytics();

    if (!data.views[slug]) {
        data.views[slug] = {
            slug,
            timestamp: Date.now(),
            count: 1
        };
    } else {
        data.views[slug].count++;
        data.views[slug].timestamp = Date.now();
    }

    saveAnalytics(data);
}

/**
 * Track a plugin install (when user copies install command)
 */
export function trackInstall(slug: string): void {
    const data = getAnalytics();

    data.installs.push({
        slug,
        timestamp: Date.now()
    });

    saveAnalytics(data);
}

/**
 * Get popular plugins this week
 */
export function getPopularThisWeek(limit: number = 10): Array<{ slug: string; installs: number }> {
    const data = getAnalytics();
    const weekAgo = Date.now() - WEEK_MS;

    // Filter installs from last week
    const recentInstalls = data.installs.filter(install => install.timestamp > weekAgo);

    // Count installs per plugin
    const counts: Record<string, number> = {};
    recentInstalls.forEach(install => {
        counts[install.slug] = (counts[install.slug] || 0) + 1;
    });

    // Convert to array and sort
    return Object.entries(counts)
        .map(([slug, installs]) => ({ slug, installs }))
        .sort((a, b) => b.installs - a.installs)
        .slice(0, limit);
}

/**
 * Get install count for a specific plugin (last 7 days)
 */
export function getInstallCount(slug: string): number {
    const data = getAnalytics();
    const weekAgo = Date.now() - WEEK_MS;

    return data.installs.filter(
        install => install.slug === slug && install.timestamp > weekAgo
    ).length;
}

/**
 * Get view count for a specific plugin
 */
export function getViewCount(slug: string): number {
    const data = getAnalytics();
    return data.views[slug]?.count || 0;
}

/**
 * Get total stats
 */
export function getStats() {
    const data = getAnalytics();
    const weekAgo = Date.now() - WEEK_MS;

    return {
        totalViews: Object.values(data.views).reduce((sum, v) => sum + v.count, 0),
        totalInstalls: data.installs.length,
        installsThisWeek: data.installs.filter(i => i.timestamp > weekAgo).length,
        uniquePluginsViewed: Object.keys(data.views).length,
        uniquePluginsInstalled: new Set(data.installs.map(i => i.slug)).size,
        sessionDuration: Date.now() - data.sessionStart
    };
}

/**
 * Clean old data (older than 30 days)
 */
export function cleanOldData(): void {
    const data = getAnalytics();
    const thirtyDaysAgo = Date.now() - (30 * 24 * 60 * 60 * 1000);

    // Clean old installs
    data.installs = data.installs.filter(install => install.timestamp > thirtyDaysAgo);

    // Clean old views
    Object.keys(data.views).forEach(slug => {
        if (data.views[slug].timestamp < thirtyDaysAgo) {
            delete data.views[slug];
        }
    });

    saveAnalytics(data);
}

/**
 * Export analytics data (for debugging or sharing)
 */
export function exportData(): string {
    const data = getAnalytics();
    return JSON.stringify(data, null, 2);
}

/**
 * Clear all analytics data
 */
export function clearData(): void {
    try {
        localStorage.removeItem(STORAGE_KEY);
    } catch (error) {
        console.warn('Failed to clear analytics:', error);
    }
}

// Auto-clean old data on module load (runs once per session)
if (typeof window !== 'undefined') {
    cleanOldData();
}
