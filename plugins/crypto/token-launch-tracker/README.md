# Token Launch Tracker Plugin

Track new token launches, detect rugpulls, and analyze smart contract security for early-stage cryptocurrency projects.

## Features

- **Real-time Launch Detection** - Monitor new tokens across Ethereum, BSC, Polygon, Arbitrum
- **Rugpull Detection** - Identify honeypots, hidden mints, and dangerous functions
- **Contract Security Analysis** - Static analysis and vulnerability detection
- **Liquidity Monitoring** - Verify LP locks and track liquidity changes
- **Social Verification** - Assess team legitimacy and community presence
- **Risk Scoring** - Composite risk score (0-100) for quick assessment

## Installation

```bash
/plugin install token-launch-tracker@claude-code-plugins-plus
```

## Usage

The launch tracker agent automatically activates when you discuss:
- New token launches and analysis
- Rugpull detection and scam identification
- Contract security verification
- Liquidity lock checking
- Team and social media verification

### Example Queries

```
Analyze this newly launched token: 0x1234...

Monitor Uniswap for new token launches in the last hour

Is this contract address a rugpull?

Check if liquidity is locked for this token

Scan for honeypot functions in this contract

What are the safest new token launches today?
```

## Risk Assessment

### Critical Red Flags (Avoid)
- Unverified contract source code
- No liquidity lock
- Owner has not renounced
- Hidden mint/blacklist functions
- Extremely high taxes (> 20%)
- No social media presence

### Warning Signs (High Risk)
- Very new social accounts
- Anonymous team, no KYC
- Short liquidity lock (< 30 days)
- High token concentration
- Paid promotion only

### Safety Indicators
- Contract verified 
- Liquidity locked > 1 year 
- Ownership renounced 
- Audit completed 
- Active community 

## Configuration

Create a `.token-launch-config.json` file:

```json
{
  "networks": ["ethereum", "bsc", "polygon"],
  "monitoring": {
    "minLiquidity": 50000,
    "maxRiskScore": 60,
    "requiredLockDays": 365
  },
  "alerts": {
    "newLaunch": true,
    "rugpullDetected": true,
    "liquidityRemoved": true
  },
  "security": {
    "requireVerified": true,
    "requireRenounced": false,
    "requireAudit": false
  }
}
```

## Risk Scoring System

**Contract Security (40 points)**
- Verified source code
- Ownership renounced
- No dangerous functions
- Audit completed

**Liquidity (30 points)**
- LP locked > 1 year
- LP burned
- Initial liquidity > $50k

**Team & Community (20 points)**
- KYC verified
- Active socials
- Organic community

**Trading Metrics (10 points)**
- Healthy distribution
- Normal volume

**Risk Levels:**
- 80-100: Low Risk 
- 60-79: Medium Risk ️
- 40-59: High Risk 
- 0-39: Critical Risk 

## Data Sources

- Etherscan/BSCScan APIs
- DexScreener
- Token Sniffer
- Honeypot.is
- Team Finance, Unicrypt, PinkLock
- CertiK, PeckShield audits

## Security Tools

- OpenZeppelin patterns
- Slither static analysis
- MythX security platform
- Manual contract review

## Legal Disclaimer

️ **This plugin provides informational analysis only** and is NOT financial advice.

Users must:
- Conduct their own research (DYOR)
- Understand investment risks
- Only invest what they can afford to lose
- Verify all information independently
- Accept full responsibility for decisions

Token launches are **highly speculative and risky** - many fail or are scams. Extreme caution advised.

## License

MIT License - See LICENSE file for details

## Support

- GitHub Issues: [Report bugs](https://github.com/jeremylongshore/claude-code-plugins/issues)
- Documentation: [Full docs](https://docs.claude-code-plugins.com)

---

*Built with ️ for crypto safety by Intent Solutions IO*
