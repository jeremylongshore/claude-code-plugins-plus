# Xquik TypeScript Types: MCP: compose-tweet

```typescript

interface McpComposeTweet {
  algorithmInsights: {
    name: string;             // Ranking signal name
    polarity: "positive" | "negative"; // Whether this signal helps or hurts ranking
    description: string;      // What this signal measures
  }[];
  contentRules: {
    rule: string;             // Actionable content rule
    description: string;      // Why this rule matters based on algorithm architecture
  }[];
  engagementMultipliers: {
    action: string;           // Engagement action (e.g. reply chain, quote tweet)
    multiplier: string;       // Relative value compared to a like (e.g. "27x a like")
    source: string;           // Data source for this multiplier
  }[];
  engagementVelocity: string; // How early engagement velocity affects distribution
  followUpQuestions: string[]; // Questions for the AI to ask the user before composing
  scorerWeights: {
    signal: string;           // Signal name in the scoring model
    weight: number;           // Weight applied to predicted probability
    context: string;          // Practical meaning of this weight
  }[];
  topPenalties: string[];     // Most severe negative signals to avoid
  source: string;             // Attribution to algorithm source code
}

```
