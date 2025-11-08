# Blockchain Explorer CLI

Command-line blockchain explorer for analyzing transactions, addresses, smart contracts, blocks, and tokens across multiple networks.

## Installation

```bash
/plugin install blockchain-explorer-cli@claude-code-plugins-plus
```

## Usage

### Explore Command

```bash
/explore
```

Or use the shortcut:
```bash
/explore
```

### Example Queries

```bash
# Analyze address
/explore Look up address 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb

# Check transaction
/explore Analyze transaction 0xabc123def456...

# Smart contract analysis
/explore What does this contract do: 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48

# ENS lookup
/explore Show me vitalik.eth portfolio

# Block information
/explore What's in the latest Ethereum block?

# Token analysis
/explore Analyze USDC token contract

# Multi-query
/explore Compare addresses: 0xabc... and 0xdef...
```

## Features

- **Address Analysis** - Balance, tokens, NFTs, transaction history, activity patterns
- **Transaction Lookup** - Status, gas fees, decoded input, token transfers, events
- **Smart Contract Explorer** - Verification status, functions, security analysis, source code
- **Block Information** - Producer, transactions, gas usage, statistics
- **Token Analytics** - Supply, holders, distribution, recent transfers
- **Multi-Network Support** - Ethereum, Polygon, Arbitrum, Optimism, Base, and more
- **ENS Resolution** - Lookup .eth domains
- **Data Decoding** - Function calls, event logs, input data

## What It Analyzes

### Addresses
1. **Balances** - Native tokens and ERC-20s
2. **NFT Portfolio** - All NFT holdings
3. **Transaction History** - Sent and received
4. **Contract Interactions** - DeFi protocols used
5. **Activity Patterns** - Trader/investor/bot classification

### Transactions
1. **Status & Confirmations** - Success/failure state
2. **Transfer Details** - From, to, value
3. **Gas & Fees** - Cost breakdown
4. **Method Calls** - Decoded function parameters
5. **Token Transfers** - ERC-20/721 movements
6. **Event Logs** - Contract events emitted

### Smart Contracts
1. **Verification Status** - Source code availability
2. **Contract Functions** - Public methods and signatures
3. **Security Analysis** - Proxy patterns, upgradeability, admin keys
4. **Token Standards** - ERC-20/721/1155 implementation
5. **Usage Metrics** - Transaction count, unique users

### Blocks
1. **Block Details** - Number, hash, timestamp
2. **Producer Info** - Miner/validator, rewards
3. **Transaction List** - All txs in block
4. **Gas Statistics** - Usage and base fee

### Tokens
1. **Supply Metrics** - Total, circulating, max supply
2. **Holder Distribution** - Top holders, concentration
3. **Market Data** - Price, market cap, volume
4. **Transfer Activity** - Recent movements

## Supported Networks

- **Ethereum Mainnet** - Primary network
- **Layer 2s** - Arbitrum, Optimism, Base
- **Sidechains** - Polygon, BNB Chain, Avalanche
- **Others** - Fantom, Gnosis Chain

## Output Formats

### Comprehensive Tables
- Balance breakdowns
- Token holdings
- Transaction history
- Top holders

### Decoded Data
- Function parameters
- Event logs
- Input data

### Visual Indicators
-  Success /  Failed
-  Verified / ️ Unverified
-  Charts and percentages

### Security Warnings
- Unverified contracts
- High-risk patterns
- Suspicious activity

## Data Interpretation

### Transaction Status
- **Success**: Executed correctly
- **Failed**: Reverted (check reason)
- **Pending**: Awaiting confirmation

### Address Types
- **EOA**: User wallet (can initiate transactions)
- **Contract**: Smart contract (code at address)
- **Token**: ERC standard implementation
- **Proxy**: Upgradeable contract

### Gas Efficiency
- **Low (<50%)**: Efficient operation
- **Medium (50-90%)**: Normal complexity
- **High (>90%)**: Very complex or near limit

## Common Use Cases

### Portfolio Tracking
Check wallet balances and token holdings.

### Transaction Verification
Confirm transaction success and details.

### Contract Research
Understand what a smart contract does.

### Security Analysis
Check for contract verification and known issues.

### Token Discovery
Research new tokens before trading.

### On-Chain Forensics
Trace transaction flows and connections.

## Important Notes

- Data refreshes continuously as blocks are mined
- Provides blockchain data, not financial advice
- Unverified contracts may be risky
- Gas prices are estimates, actual may vary
- Some contract functions require special permissions
- ENS names are resolved on-chain
- Token prices may not be real-time

## Data Sources

Analysis uses blockchain explorers APIs:
- Etherscan (Ethereum)
- Polygonscan (Polygon)
- Arbiscan (Arbitrum)
- Optimistic Etherscan (Optimism)
- And network-specific explorers

## Privacy Note

Blockchain data is public and transparent. All addresses, transactions, and contract interactions are visible to everyone.

## Requirements

- Address, transaction hash, or block number
- (Optional) Network specification
- (Optional) What specific aspect to analyze

## Files

- `commands/explore.md` - Main blockchain exploration command

## License

MIT License - See LICENSE file for details
