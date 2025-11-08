# NFT Rarity Analyzer

Analyze NFT rarity scores, trait distributions, and valuations to make informed decisions about NFT purchases and sales.

## Installation

```bash
/plugin install nft-rarity-analyzer@claude-code-plugins-plus
```

## Usage

### Analyze NFT Command

```bash
/analyze-nft
```

Or use the shortcut:
```bash
/nft
```

### Example Queries

```bash
# Analyze specific NFT
/nft Analyze Bored Ape Yacht Club #1234

# Compare NFTs
/nft Compare rarity: Azuki #100 vs Azuki #200

# Valuation check
/nft Is CryptoPunk #5678 undervalued based on its rarity?

# Collection analysis
/nft What are the rarest traits in Doodles collection?

# Investment perspective
/nft Should I buy Pudgy Penguin #999 at 3 ETH? Rank #450
```

## Features

- **Trait Analysis** - Break down all traits with rarity percentages
- **Multiple Scoring Methods** - Statistical, normalized, and OpenRarity scores
- **Valuation Estimates** - Price predictions based on rarity and comparable sales
- **Market Context** - Trading volume, floor price, and trend analysis
- **Comparative Analysis** - Compare NFTs within same collection
- **Investment Insights** - Buy/hold/sell recommendations with reasoning

## What It Analyzes

1. **Individual Traits** - Rarity of each attribute
2. **Overall Rarity** - Composite scores and rankings
3. **Collection Metrics** - Floor price, volume, supply
4. **Comparable Sales** - Recent transactions of similar rarity NFTs
5. **Market Trends** - Trading activity and price momentum
6. **Valuation Range** - Conservative to optimistic price estimates

## Output Includes

- Detailed trait breakdown with rarity scores
- Multiple rarity ranking methodologies
- Estimated value range based on comparables
- Market insights and trading patterns
- Investment recommendation with rationale
- Key strengths and risk factors

## Rarity Methodologies

### Statistical Rarity
Based on trait frequency in the collection.

### Trait Normalization
Adjusts for number of traits to prevent bias.

### OpenRarity Standard
Industry-standard calculation using information content.

## Data Sources

Analysis references:
- OpenSea (primary marketplace data)
- Rarity.tools (rarity rankings)
- LooksRare (alternative pricing)
- Blur (pro trader activity)
- NFTGo (analytics platform)

## Important Notes

- Rarity is one of many factors in NFT value
- Aesthetic appeal and community sentiment also matter
- Market conditions can override rarity metrics
- Different platforms may show different rarity scores
- This provides educational analysis, not financial advice
- Always consider liquidity and your holding period

## Requirements

- Collection name
- Token ID or specific NFT identifier
- (Optional) User's investment timeline and goals

## Files

- `commands/analyze-nft.md` - Main NFT analysis command

## License

MIT License - See LICENSE file for details
