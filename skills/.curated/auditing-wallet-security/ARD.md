# ARD: Wallet Security Auditor

> Part of [Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)

## Architecture Pattern

**Security Analysis Pattern** - Python CLI that aggregates wallet data from multiple sources to assess security posture.

## Workflow

```
Data Collection → Risk Analysis → Score Calculation → Report
      ↓               ↓                ↓                ↓
  Approvals       Check Known      Weighted Score    Recommendations
  Transactions    Malicious        Risk Factors
```

## Data Flow

```
Input: Wallet address + chain
          ↓
Collect: Fetch approvals, transactions, interactions
          ↓
Analyze: Check against known risks, patterns
          ↓
Score: Calculate weighted security score
          ↓
Output: Risk report with recommendations
```

## Directory Structure

```
skills/auditing-wallet-security/
├── PRD.md                    # Product requirements
├── ARD.md                    # Architecture document
├── SKILL.md                  # Agent instructions
├── scripts/
│   ├── wallet_auditor.py     # Main CLI entry point
│   ├── approval_scanner.py   # Token approval scanner
│   ├── tx_analyzer.py        # Transaction pattern analysis
│   ├── risk_scorer.py        # Security score calculator
│   └── formatters.py         # Output formatting
├── references/
│   ├── errors.md             # Error handling guide
│   └── examples.md           # Usage examples
└── config/
    └── settings.yaml         # Default configuration
```

## API Integration

### ERC20 Approval Detection

- **Method**: eth_getLogs with Approval event topic
- **Topic**: `0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925`
- **Data**: Owner, spender, amount

### Block Explorer APIs

- **Etherscan**: `https://api.etherscan.io/api`
- **BSCScan**: `https://api.bscscan.com/api`
- **PolygonScan**: `https://api.polygonscan.com/api`

### Security Data APIs

- **GoPlus**: `https://api.gopluslabs.io/api/v1/`
- **Token Sniffer**: Token risk data
- **Revoke.cash**: Known scam contracts

## Component Design

### wallet_auditor.py

```python
# Main CLI with commands:
# - approvals: List token approvals
# - scan: Full security scan
# - score: Calculate risk score
# - history: Analyze transaction history
# - revoke-list: Generate revoke recommendations
# - report: Generate full security report
```

### approval_scanner.py

```python
class ApprovalScanner:
    def get_all_approvals(address: str) -> List[TokenApproval]
    def check_unlimited_approvals() -> List[TokenApproval]
    def check_risky_spenders() -> List[RiskyApproval]
    def get_approval_value_at_risk() -> Decimal
```

### tx_analyzer.py

```python
class TxAnalyzer:
    def get_recent_transactions(address: str, days: int) -> List[Transaction]
    def analyze_interaction_patterns() -> InteractionReport
    def detect_suspicious_activity() -> List[SuspiciousActivity]
    def get_contract_interactions() -> List[ContractInteraction]
```

### risk_scorer.py

```python
class RiskScorer:
    def calculate_approval_risk() -> int
    def calculate_interaction_risk() -> int
    def calculate_pattern_risk() -> int
    def get_total_score() -> SecurityScore
    def get_recommendations() -> List[Recommendation]
```

## Data Structures

### TokenApproval

```python
@dataclass
class TokenApproval:
    token_address: str
    token_symbol: str
    spender: str
    spender_name: Optional[str]
    allowance: Decimal
    is_unlimited: bool
    approval_tx: str
    approval_block: int
    is_risky: bool
    risk_reason: Optional[str]
```

### SecurityScore

```python
@dataclass
class SecurityScore:
    total_score: int  # 0-100 (higher = safer)
    approval_score: int
    interaction_score: int
    pattern_score: int
    risk_factors: List[RiskFactor]
    recommendations: List[Recommendation]
```

### RiskFactor

```python
@dataclass
class RiskFactor:
    category: str
    severity: str  # critical, high, medium, low
    description: str
    affected_items: List[str]
    mitigation: str
```

## Risk Scoring System

### Categories and Weights

| Category | Weight | Factors |
|----------|--------|---------|
| Approvals | 40% | Unlimited, risky spenders, stale |
| Interactions | 30% | Unknown contracts, flagged addresses |
| Patterns | 20% | Frequency, diversity, timing |
| Age | 10% | Wallet age, activity history |

### Risk Factors

| Factor | Severity | Score Impact |
|--------|----------|--------------|
| Unlimited approval to unknown | Critical | -30 |
| Approval to flagged contract | Critical | -25 |
| Interaction with known scam | High | -20 |
| Stale approval (>6 months) | Medium | -10 |
| Many unlimited approvals | Medium | -15 |
| First-time contract interaction | Low | -5 |

## Supported Chains

| Chain | Chain ID | Explorer API |
|-------|----------|--------------|
| Ethereum | 1 | Etherscan |
| BSC | 56 | BSCScan |
| Polygon | 137 | PolygonScan |
| Arbitrum | 42161 | Arbiscan |
| Optimism | 10 | Optimistic Etherscan |
| Base | 8453 | BaseScan |

## Error Handling Strategy

| Error | Handling |
|-------|----------|
| Invalid address | Validate checksum, show error |
| RPC unavailable | Fallback to explorer API |
| API rate limited | Exponential backoff |
| No approvals found | Show clean result |
| Chain not supported | List supported chains |

## Security Considerations

- Read-only operations only
- No private key handling
- No transaction signing
- Public API data only
- Rate limiting to avoid abuse
