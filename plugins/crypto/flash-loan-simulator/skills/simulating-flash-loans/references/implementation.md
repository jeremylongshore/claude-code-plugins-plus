# Implementation Guide

### Step 1: Configure Data Sources
Set up connections to crypto data providers:
1. Use Read tool to load API credentials from ${CLAUDE_SKILL_DIR}/config/crypto-apis.env
2. Configure blockchain RPC endpoints for target networks
3. Set up exchange API connections if required
4. Verify rate limits and subscription tiers
5. Test connectivity and authentication

### Step 2: Query Crypto Data
Retrieve relevant blockchain and market data:
1. Use Bash(crypto:flashloan-*) to execute crypto data queries
2. Fetch real-time prices, volumes, and market cap data
3. Query blockchain for on-chain metrics and transactions
4. Retrieve exchange order book and trade history
5. Aggregate data from multiple sources for accuracy

### Step 3: Analyze and Process
Process crypto data to generate insights:
- Calculate key metrics (returns, volatility, correlation)
- Identify patterns and anomalies in data
- Apply technical indicators or on-chain signals
- Compare across timeframes and assets
- Generate actionable insights and alerts

### Step 4: Generate Reports
Document findings in ${CLAUDE_SKILL_DIR}/crypto-reports/:
- Market summary with key price movements
- Detailed analysis with charts and metrics
- Trading signals or opportunity recommendations
- Risk assessment and position sizing guidance
- Historical context and trend analysis