# ARD: NFT Rarity Analyzer

> Part of [Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)

## Architecture Pattern

**Analytics Pipeline Pattern** - Python CLI that fetches NFT metadata, analyzes trait distribution, and calculates rarity scores.

## Workflow

```
Metadata Collection → Trait Parsing → Rarity Calculation → Ranking → Display
        ↓                   ↓                ↓                ↓          ↓
   OpenSea/ETH RPC     Normalize        Statistical       Sort by     Table/JSON
                       Attributes        Analysis         Score
```

## Data Flow

```
Input: Collection address/slug + optional token ID
          ↓
Fetch: Collection metadata from OpenSea or Alchemy
          ↓
Parse: Extract trait_type → value pairs for all tokens
          ↓
Analyze: Count trait frequencies across collection
          ↓
Calculate: Apply rarity algorithm to each token
          ↓
Rank: Sort tokens by composite rarity score
          ↓
Output: Rarity report with rankings and trait breakdown
```

## Directory Structure

```
skills/analyzing-nft-rarity/
├── PRD.md                    # Product requirements
├── ARD.md                    # Architecture document
├── SKILL.md                  # Agent instructions
├── scripts/
│   ├── rarity_analyzer.py    # Main CLI entry point
│   ├── metadata_fetcher.py   # OpenSea/Alchemy/RPC client
│   ├── trait_parser.py       # Trait normalization
│   ├── rarity_calculator.py  # Scoring algorithms
│   └── formatters.py         # Output formatting
├── references/
│   ├── errors.md             # Error handling guide
│   └── examples.md           # Usage examples
└── config/
    └── settings.yaml         # Default configuration
```

## API Integration

### OpenSea API v2

- **Endpoint**: `https://api.opensea.io/api/v2/`
- **Auth**: API key via `X-API-KEY` header
- **Endpoints**:
  - `GET /collection/{slug}` - Collection info
  - `GET /collection/{slug}/nfts` - NFT list with traits

### Alchemy NFT API

- **Endpoint**: `https://{network}.g.alchemy.com/nft/v2/{apiKey}/`
- **Endpoints**:
  - `getNFTsForCollection` - Batch fetch metadata
  - `getNFTMetadata` - Single token metadata

### IPFS Gateways

- `https://ipfs.io/ipfs/`
- `https://gateway.pinata.cloud/ipfs/`
- `https://cloudflare-ipfs.com/ipfs/`

## Component Design

### metadata_fetcher.py

```python
class MetadataFetcher:
    def fetch_collection(slug_or_address) -> CollectionData
    def fetch_token(collection, token_id) -> TokenData
    def batch_fetch(collection, start, limit) -> List[TokenData]
```

### trait_parser.py

```python
class TraitParser:
    def parse_attributes(metadata) -> List[Trait]
    def normalize_trait(trait_type, value) -> NormalizedTrait
    def build_trait_map(tokens) -> TraitFrequencyMap
```

### rarity_calculator.py

```python
class RarityCalculator:
    def calculate_statistical_rarity(trait, total) -> float
    def calculate_rarity_score(token, trait_map) -> float
    def calculate_information_content(token, trait_map) -> float
    def rank_collection(tokens, algorithm) -> List[RankedToken]
```

## Data Structures

### Token Metadata

```python
@dataclass
class TokenData:
    token_id: int
    name: str
    image_url: str
    attributes: List[Trait]
    rarity_score: float
    rarity_rank: int
```

### Trait

```python
@dataclass
class Trait:
    trait_type: str
    value: str
    frequency: float  # percentage
    rarity: float     # 1/frequency
```

## Rarity Scoring Formulas

### Rarity Score / Statistical Rarity

```
score = Σ (1 / trait_frequency) for all traits
```

Note: Both `statistical` and `rarity_score` algorithms use this same formula.
They are kept as separate enum values for backward compatibility.

### Average Rarity

```
score = Σ (trait_rarity) / trait_count
```

### Information Content (Entropy-based)

```
score = Σ (-log2(trait_frequency)) for all traits
```

## Score Normalization

Normalization is a post-processing step applied after calculating scores
using any primary algorithm. It scales scores to a 0-100 range:

```
normalized = (score - min_score) / (max_score - min_score) * 100
```

## Error Handling Strategy

| Error | Handling |
|-------|----------|
| Collection not found | Return error with search suggestions |
| Rate limited | Exponential backoff with cache fallback |
| IPFS timeout | Try alternate gateway |
| Missing attributes | Treat as "None" trait |
| Invalid token ID | Return error with valid range |

## Caching Strategy

- **Collection cache**: 1 hour TTL
- **Token cache**: 24 hour TTL (metadata rarely changes)
- **Trait map cache**: 1 hour (update with collection)
- **Storage**: Local JSON files in ~/.nft_cache/

## Performance Considerations

- Batch API requests (50 tokens per call)
- Cache collection data locally
- Lazy-load full trait analysis
- Parallelize IPFS fetches

## Security

- API keys stored in environment variables
- No wallet connections required
- Read-only operations only
- Rate limit respecting

## Supported Collections

Works with any ERC-721 or ERC-1155 collection that:

- Has metadata on OpenSea
- Has tokenURI pointing to valid JSON
- Uses standard attributes array format
