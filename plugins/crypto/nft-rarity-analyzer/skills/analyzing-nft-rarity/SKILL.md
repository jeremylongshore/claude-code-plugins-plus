---
name: analyzing-nft-rarity
description: |
  Calculate NFT rarity scores and rank tokens by trait uniqueness.
  Use when analyzing NFT collections, checking token rarity, or comparing NFTs.
  Trigger with phrases like "check NFT rarity", "analyze collection", "rank tokens", "compare NFTs".
allowed-tools: Read, Bash(python3:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---

# Analyzing NFT Rarity

## Overview

NFT rarity analysis skill that:
- Fetches collection metadata from OpenSea API
- Parses and normalizes trait attributes
- Calculates rarity using multiple algorithms
- Ranks tokens by composite rarity score
- Exports data in JSON and CSV formats

## Prerequisites

- Python 3.8+ with requests library
- Optional: `OPENSEA_API_KEY` for higher rate limits
- Optional: `ALCHEMY_API_KEY` for direct metadata fetching

## Instructions

### 1. Analyze a Collection

```bash
cd {baseDir}/scripts && python3 rarity_analyzer.py collection boredapeyachtclub
```

Options:
- `--limit 500`: Fetch more tokens for analysis
- `--top 50`: Show top 50 tokens
- `--traits`: Include trait distribution
- `--rarest`: Show rarest traits
- `--algorithm [statistical|rarity_score|average|information]`

### 2. Check Specific Token

```bash
cd {baseDir}/scripts && python3 rarity_analyzer.py token pudgypenguins 1234
```

### 3. Compare Multiple Tokens

```bash
cd {baseDir}/scripts && python3 rarity_analyzer.py compare azuki 1234,5678,9012
```

### 4. View Trait Distribution

```bash
cd {baseDir}/scripts && python3 rarity_analyzer.py traits doodles
```

### 5. Export Rankings

JSON:
```bash
cd {baseDir}/scripts && python3 rarity_analyzer.py export coolcats > rankings.json
```

CSV:
```bash
cd {baseDir}/scripts && python3 rarity_analyzer.py export coolcats --format csv > rankings.csv
```

### 6. Manage Cache

```bash
cd {baseDir}/scripts && python3 rarity_analyzer.py cache --list
cd {baseDir}/scripts && python3 rarity_analyzer.py cache --clear
```

## Rarity Algorithms

| Algorithm | Description | Best For |
|-----------|-------------|----------|
| `rarity_score` | Sum of 1/frequency (default) | General use, matches rarity.tools |
| `statistical` | Same as rarity_score | Backward compatibility |
| `average` | Mean of trait rarities | Balanced scoring |
| `information` | Entropy-based (-log2) | Information theory approach |

## Output

- **Collection Summary**: Name, supply, trait types
- **Rankings**: Tokens sorted by rarity score with percentile
- **Token Detail**: Full trait breakdown with contribution
- **Comparison**: Side-by-side trait comparison

## Supported Collections

Works with any ERC-721/ERC-1155 collection that has:
- OpenSea listing
- Standard attributes array format
- Accessible metadata

## Error Handling

See `{baseDir}/references/errors.md` for:
- API rate limiting
- IPFS gateway issues
- Collection not found
- Token ID not found

## Examples

See `{baseDir}/references/examples.md` for:
- Collection analysis workflows
- Token comparison
- Export and caching
- Algorithm comparison

## Resources

- [OpenSea API](https://docs.opensea.io/reference/api-overview) - Metadata source
- [Rarity Tools](https://rarity.tools/) - Reference rankings
- [IPFS](https://ipfs.io/) - Decentralized metadata
