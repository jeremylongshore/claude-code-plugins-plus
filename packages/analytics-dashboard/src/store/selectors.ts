/**
 * Zustand store selectors
 * Memoized selectors for efficient derived state
 */
import type { AnalyticsEvent } from '../types'

/**
 * Get total number of events
 */
export const selectEventCount = (state: { events: AnalyticsEvent[] }) => state.events.length

/**
 * Get events from last N minutes
 */
export const selectRecentEvents = (minutes: number) => (state: { events: AnalyticsEvent[] }) => {
  const cutoff = Date.now() - minutes * 60 * 1000
  return state.events.filter((event) => event.timestamp >= cutoff)
}

/**
 * Get plugin activation count
 */
export const selectPluginCount = (pluginName: string) => (state: { pluginActivations: Map<string, number> }) => {
  return state.pluginActivations.get(pluginName) || 0
}

/**
 * Get skill trigger count
 */
export const selectSkillCount = (skillName: string) => (state: { skillTriggers: Map<string, number> }) => {
  return state.skillTriggers.get(skillName) || 0
}

/**
 * Get top N most active plugins
 */
export const selectTopPlugins = (n: number = 5) => (state: { pluginActivations: Map<string, number> }) => {
  return Array.from(state.pluginActivations.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, n)
    .map(([name, count]) => ({ name, count }))
}

/**
 * Get top N most triggered skills
 */
export const selectTopSkills = (n: number = 5) => (state: { skillTriggers: Map<string, number> }) => {
  return Array.from(state.skillTriggers.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, n)
    .map(([name, count]) => ({ name, count }))
}

/**
 * Get total cost formatted
 */
export const selectFormattedCost = (state: { totalCost: number }) => {
  return `$${state.totalCost.toFixed(3)}`
}

/**
 * Get connection status with last event timestamp
 */
export const selectConnectionInfo = (state: {
  connectionStatus: string
  lastEventTimestamp: number | null
}) => ({
  status: state.connectionStatus,
  lastEvent: state.lastEventTimestamp,
  isConnected: state.connectionStatus === 'connected',
})

/**
 * Get LLM call events with token stats
 */
export const selectLLMStats = (state: { events: AnalyticsEvent[] }) => {
  const llmEvents = state.events.filter((e) => e.type === 'llm.call')

  const totalCalls = llmEvents.length
  const totalInputTokens = llmEvents.reduce((sum, e) => {
    return sum + (e.type === 'llm.call' ? e.inputTokens || 0 : 0)
  }, 0)
  const totalOutputTokens = llmEvents.reduce((sum, e) => {
    return sum + (e.type === 'llm.call' ? e.outputTokens || 0 : 0)
  }, 0)

  return {
    totalCalls,
    totalInputTokens,
    totalOutputTokens,
    totalTokens: totalInputTokens + totalOutputTokens,
  }
}

/**
 * Get events grouped by type
 */
export const selectEventsByType = (state: { events: AnalyticsEvent[] }) => {
  const grouped: Record<string, AnalyticsEvent[]> = {}

  state.events.forEach((event) => {
    if (!grouped[event.type]) {
      grouped[event.type] = []
    }
    grouped[event.type]!.push(event)
  })

  return grouped
}

/**
 * Get event rate (events per minute) over last N minutes
 */
export const selectEventRate = (minutes: number = 5) => (state: { events: AnalyticsEvent[] }) => {
  const cutoff = Date.now() - minutes * 60 * 1000
  const recentEvents = state.events.filter((event) => event.timestamp >= cutoff)

  return recentEvents.length / minutes
}
