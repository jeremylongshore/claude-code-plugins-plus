# Cross-Chain Bridge Monitor Plugin

Monitor cross-chain bridge activity, track transfers, analyze security, and detect potential bridge exploits.

## Features

- **Real-time Bridge Monitoring** - Track activity on Wormhole, Multichain, Stargate, Synapse, Hop, Across
- **Transfer Tracking** - Monitor individual transactions with status updates
- **Security Analysis** - Assess TVL, validator sets, and audit status
- **Exploit Detection** - Identify unusual patterns and anomalies
- **Route Optimization** - Compare fees and speeds across bridges
- **Large Transfer Alerts** - "Whale watching" across chains

## Installation

```bash
/plugin install cross-chain-bridge-monitor@claude-code-plugins-plus
```

## Usage

The bridge monitor agent automatically activates when you discuss:
- Cross-chain bridges and transfers
- Bridge security and TVL
- Transaction status lookups
- Bridge fee comparisons
- Exploit detection and monitoring

### Example Queries

```
Monitor Wormhole bridge activity in the last 24 hours

What's the status of my bridge transaction 0x...?

Compare costs for bridging 1000 USDC from Ethereum to Arbitrum

Is Multichain safe to use right now?

Show me all large ETH transfers across bridges today

Which bridge has the lowest fees for Polygon to Ethereum?
```

## Supported Bridges

### Canonical Bridges
- Arbitrum Bridge (Official)
- Optimism Gateway (Official)
- Polygon PoS Bridge (Official)
- zkSync Bridge (Official)
- Base Bridge (Official)

### Third-Party Bridges
- Wormhole
- Multichain (Anyswap)
- Stargate (LayerZero)
- Synapse
- Hop Protocol
- Across
- Celer cBridge

### Specialized
- Portal (Wormhole)
- Connext
- Axelar

## Configuration

Create a `.bridge-monitor-config.json` file:

```json
{
  "bridges": ["wormhole", "stargate", "hop", "across"],
  "chains": ["ethereum", "arbitrum", "optimism", "polygon"],
  "monitoring": {
    "largeTransferThreshold": 100000,
    "tvlDropThreshold": 0.10,
    "checkInterval": 300
  },
  "alerts": {
    "largeTransfers": true,
    "tvlChanges": true,
    "bridgePaused": true,
    "unusualActivity": true
  }
}
```

## Security Models

### 1. Trusted Bridges
- Centralized validators/relayers
- Fast and low cost
- Trust in validators required
- Examples: Multichain, Wormhole

### 2. Optimistic Bridges
- Challenge period for disputes
- More decentralized
- Slower due to challenge window
- Examples: Hop, Across, Nomad

### 3. Light Client Bridges
- Cryptographic proofs
- Most secure, trustless
- Higher cost and complexity
- Examples: Rainbow Bridge, IBC

### 4. Liquidity Networks
- Liquidity pools on each chain
- Fast and scalable
- Risk of slippage and imbalances
- Examples: Stargate, Synapse

### 5. Canonical Bridges
- Official protocol bridges
- Highest trust
- May have longer withdrawal times
- Examples: Arbitrum Bridge, Optimism Gateway

## Risk Assessment

### TVL Risk Levels
- < $10M: Lower priority, less tested
- $10M - $100M: Moderate risk
- $100M - $1B: High value target
- > $1B: Critical infrastructure

### Validator Risk
- Single operator: Critical risk 
- < 5 validators: High centralization ️
- 5-15 validators: Moderate decentralization
- \> 15 validators: Good decentralization 

## Historical Bridge Exploits

Major incidents to learn from:
- **Ronin Bridge (2022)**: $625M - Validator compromise
- **Wormhole (2022)**: $325M - Signature bug
- **Nomad Bridge (2022)**: $190M - Initialization bug
- **Harmony Bridge (2022)**: $100M - Multisig compromise
- **Poly Network (2021)**: $611M - Contract vulnerability (funds returned)

## Best Practices

### For Users
1. Start with small test amounts
2. Verify destination addresses
3. Use reputable, audited bridges
4. Monitor TVL trends
5. Check bridge status before transferring
6. Save transaction hashes

### For Monitoring
1. Track volume, TVL, validators
2. Set appropriate alert thresholds
3. Cross-reference multiple data sources
4. Compare to historical patterns
5. Monitor audit reports and incidents

## Data Sources

- Bridge contract events
- LayerZero Scan
- Socket API
- Dune Analytics
- DefiLlama (TVL)
- Audit reports (CertiK, ChainSecurity)

## Risk Disclaimer

️ **Cross-chain bridges are high-risk infrastructure** with a history of major exploits.

Users should:
- Only bridge amounts they can afford to lose
- Understand the bridge's security model
- Verify bridge status before transferring
- Use official bridge interfaces
- Consider insurance where available

This plugin provides **monitoring and analysis only** - users accept all risk when using bridges.

## License

MIT License - See LICENSE file for details

## Support

- GitHub Issues: [Report bugs](https://github.com/jeremylongshore/claude-code-plugins/issues)
- Documentation: [Full docs](https://docs.claude-code-plugins.com)

---

*Built with ️ for cross-chain security by Intent Solutions IO*
