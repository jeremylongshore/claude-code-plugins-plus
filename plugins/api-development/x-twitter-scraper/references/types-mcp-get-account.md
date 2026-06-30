# Xquik TypeScript Types: MCP: get-account

```typescript

interface McpAccount {
  plan: "active" | "inactive";
  monitorsAllowed: number;    // Deprecated; monitor slots are unlimited
  monitorsUsed: number;       // Number of active monitors
  monitorUsage: {
    activeDailyEstimate: string;
    activeHourlyBurn: string;
    creditsPerActiveMonitorDay: string;
    creditsPerActiveMonitorHour: string;
    eventsIncluded: boolean;
    instantCheckIntervalSeconds: number;
    unlimitedSlots: boolean;
  };
  creditInfo?: {
    balance: string;
    lifetimePurchased: string;
    lifetimeUsed: string;
  };
  xUsername?: string;
}

```
