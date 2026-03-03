# ARD: Blockchain Explorer CLI

## Architectural Overview

### Pattern
Script Automation with Multi-Provider Fallback

### Architecture Diagram
```
┌─────────────────────────────────────────────────────────────────┐
│                     User Request                                 │
│         "explore tx 0xabc..." / "check balance 0x123"           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   blockchain_explorer.py                         │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────────┐ │
│  │ tx_query   │ │ addr_query │ │ block_query│ │contract_query│ │
│  └────────────┘ └────────────┘ └────────────┘ └──────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     chain_client.py                              │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ ChainClient: Multi-chain RPC + Explorer API abstraction     ││
│  │   - Ethereum (Etherscan + RPC provider)                     ││
│  │   - Polygon (Polygonscan + RPC)                             ││
│  │   - BSC (BSCScan + RPC)                                     ││
│  │   - Arbitrum, Optimism, Base, Avalanche                     ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
       ┌───────────┐   ┌───────────┐   ┌───────────┐
       │ Etherscan │   │  Provider │   │ CoinGecko │
       │    API    │   │    RPC    │   │    API    │
       └───────────┘   └───────────┘   └───────────┘
```

### Workflow
1. Parse user query (tx hash, address, block number, contract call)
2. Detect chain from address/hash prefix or explicit parameter
3. Route to appropriate chain client
4. Fetch data from RPC + Explorer API
5. Enrich with prices, token metadata, decoded data
6. Format and display results

## Progressive Disclosure Strategy

| Level | Content | Location |
|-------|---------|----------|
| L1: Quick Start | CLI examples, common queries | SKILL.md |
| L2: Runtime Config | API keys, built-in chain endpoints | scripts/chain_client.py |
| L3: Implementation | Multi-chain routing, caching | references/implementation.md |
| L4: Advanced | Custom RPC, ABI decoding | references/examples.md |

Note: `config/settings.yaml` is provided as a reference template and is not auto-loaded by the current CLI scripts.

## Directory Structure

```
skills/exploring-blockchain-data/
├── SKILL.md                    # Core instructions
├── PRD.md                      # Product requirements
├── ARD.md                      # Architecture (this file)
├── scripts/
│   ├── blockchain_explorer.py  # Main CLI
│   ├── chain_client.py         # Multi-chain abstraction
│   ├── tx_decoder.py           # Transaction decoding
│   ├── token_resolver.py       # Token metadata + prices
│   └── formatters.py           # Output formatting
├── references/
│   ├── errors.md               # Error handling
│   ├── examples.md             # Usage examples
│   └── implementation.md       # Implementation details
└── config/
    └── settings.yaml           # Reference template (not auto-loaded)
```

## API Integration Architecture

### Primary: Explorer APIs (Etherscan family)
```python
# Transaction details with internal txs
GET /api?module=account&action=txlist&address={addr}

# Contract ABI for decoding
GET /api?module=contract&action=getabi&address={contract}

# Token transfers
GET /api?module=account&action=tokentx&address={addr}
```

### Secondary: RPC (provider-agnostic JSON-RPC calls)
```python
# Real-time balance
eth_getBalance(address, 'latest')

# Transaction receipt
eth_getTransactionReceipt(txHash)

# Contract state
eth_call({to: contract, data: encoded_call}, 'latest')
```

## Data Flow Architecture

```
Input: "explore tx 0xabc123..."
         │
         ▼
┌─────────────────────────┐
│   Parse & Validate      │
│   - Detect query type   │
│   - Validate hash/addr  │
│   - Detect chain        │
└─────────────────────────┘
         │
         ▼
┌─────────────────────────┐
│   Fetch Core Data       │
│   - RPC: tx receipt     │
│   - Explorer: details   │
│   - Decode input data   │
└─────────────────────────┘
         │
         ▼
┌─────────────────────────┐
│   Enrich Data           │
│   - Token metadata      │
│   - USD values          │
│   - Contract names      │
└─────────────────────────┘
         │
         ▼
┌─────────────────────────┐
│   Format Output         │
│   - Table / JSON / CSV  │
│   - Color coding        │
│   - Links to explorers  │
└─────────────────────────┘
```

## Error Handling Strategy

| Error | Cause | Recovery |
|-------|-------|----------|
| Invalid hash | Wrong format | Validate format, suggest correction |
| TX not found | Not mined or wrong chain | Try other chains, check mempool |
| Rate limited | Too many requests | Exponential backoff, rotate keys |
| RPC timeout | Node congestion | Retry with backup RPC |
| Unknown token | Not in registry | Fetch from chain, cache result |

## Caching Strategy

- **Transaction data**: Immutable, cache permanently
- **Block data**: Immutable, cache permanently
- **Address balance**: TTL 30 seconds
- **Token metadata**: TTL 24 hours
- **Prices**: TTL 60 seconds

## Security Considerations

- API keys stored in environment variables only
- No private key handling
- Rate limit compliance
- Input sanitization for all user queries
