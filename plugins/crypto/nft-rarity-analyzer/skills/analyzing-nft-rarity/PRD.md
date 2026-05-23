# PRD: NFT Rarity Analyzer

## Summary

**One-liner**: Analyze NFT collections to calculate trait rarity scores and rank tokens by uniqueness.

**Domain**: Cryptocurrency / NFT / Digital Collectibles

**Users**: NFT Collectors, Traders, Analysts, Developers

## Problem Statement

NFT collectors need to quickly assess rarity to make informed buying decisions. Manual trait analysis is time-consuming and error-prone. Existing tools are often expensive, require accounts, or lack transparency in their scoring methods.

## User Stories

1. **As an NFT collector**, I want to check rarity scores for tokens in a collection, so that I can identify undervalued pieces.

2. **As an NFT trader**, I want to compare multiple tokens by rarity rank, so that I can make data-driven purchase decisions.

3. **As a collection creator**, I want to analyze my collection's trait distribution, so that I can ensure balanced rarity across items.

4. **As an analyst**, I want to export rarity data for further analysis, so that I can create custom rarity models.

## Functional Requirements

- **REQ-1**: Fetch NFT collection metadata from OpenSea, Alchemy, or direct contract
- **REQ-2**: Parse and normalize trait attributes across collection
- **REQ-3**: Calculate trait rarity using statistical frequency analysis
- **REQ-4**: Compute composite rarity scores using multiple algorithms
- **REQ-5**: Rank tokens within collection by rarity
- **REQ-6**: Display trait breakdown with rarity percentages
- **REQ-7**: Support ERC-721 and ERC-1155 token standards
- **REQ-8**: Cache collection data for performance
- **REQ-9**: Export rarity data in JSON and CSV formats

## Rarity Algorithms

### Rarity Score / Statistical Rarity

`Score = sum(1 / trait_frequency) for each trait`

Both `statistical` and `rarity_score` use this formula - they are equivalent in the implementation.

### Average Rarity

`Score = sum(trait_rarities) / trait_count`

### Information Content

`Score = sum(-log2(trait_frequency))` (higher = rarer)

### Score Normalization (Post-processing)

After calculating scores, they can be normalized to 0-100 scale:
`normalized = (score - min_score) / (max_score - min_score) * 100`

## API Integrations

- **OpenSea API**: Collection metadata, token traits
- **Alchemy NFT API**: Fast metadata fetching
- **Ethereum RPC**: Direct tokenURI reads
- **IPFS Gateway**: Metadata from decentralized storage

## Success Metrics

- Activation triggers on NFT rarity queries
- Accurate rarity rankings match established tools
- Fast analysis (<5s for cached collections)
- Support for collections up to 20,000 items

## Non-Goals

- Price predictions based on rarity
- Automated trading or sniping
- Collection indexing from scratch
- Real-time floor price tracking
