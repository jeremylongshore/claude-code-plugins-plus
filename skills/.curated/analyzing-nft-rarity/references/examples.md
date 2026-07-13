# Examples

## Quick Start

### Analyze a Collection

```bash
python rarity_analyzer.py collection pudgypenguins
```

Output:

```
COLLECTION: PUDGY PENGUINS
============================================================
Contract:     0xBd3531dA5CF5857e...
Total Supply: 8,888
Fetched:      200 tokens
Trait Types:  10
============================================================

TOKEN RANKINGS (by Rarity Score)
================================================================================
Rank     Token                Score        Percentile   Top Trait
--------------------------------------------------------------------------------
#1       Pudgy Penguin #1234  285.42       Top 0.5%     Background: Gold
#2       Pudgy Penguin #5678  278.31       Top 1.0%     Skin: Alien
#3       Pudgy Penguin #9012  265.19       Top 1.5%     Eyes: Laser
...
--------------------------------------------------------------------------------
Algorithm: rarity_score
Total Ranked: 200
================================================================================
```

### Analyze a Specific Token

```bash
python rarity_analyzer.py token boredapeyachtclub 1234
```

Output:

```
TOKEN: Bored Ape #1234
============================================================
Token ID:    1234
Rank:        #42
Percentile:  Top 0.42%
Score:       312.4500
Algorithm:   rarity_score

TRAIT BREAKDOWN
------------------------------------------------------------
Trait                Value                Rarity       Score +
------------------------------------------------------------
Fur                  Solid Gold           1 in 457     +457.00
Eyes                 Laser Eyes           1 in 69      +69.00
Background           Aquamarine           1 in 125     +125.00
Hat                  Sea Captain          1 in 283     +283.00
Mouth                Bored Cigarette      1 in 175     +175.00
Clothes              Tuxedo               1 in 137     +137.00
============================================================
```

## Collection Analysis Options

### Show More Tokens

```bash
python rarity_analyzer.py collection azuki --top 50
```

### Fetch Larger Sample

```bash
python rarity_analyzer.py collection doodles --limit 500
```

### Include Trait Distribution

```bash
python rarity_analyzer.py collection cryptopunks --traits
```

Output:

```
TRAIT DISTRIBUTION
======================================================================
Trait Type           Values     Coverage        Rarest Value
----------------------------------------------------------------------
Background           12         100.0%          Neon (0.1%)
Skin                 8          100.0%          Zombie (2.5%)
Eyes                 15         95.0%           Laser (0.3%)
Hat                  24         75.0%           Crown (0.2%)
...
======================================================================
```

### Show Rarest Traits

```bash
python rarity_analyzer.py collection boredapeyachtclub --rarest
```

## Different Algorithms

### Statistical Rarity

```bash
python rarity_analyzer.py collection azuki --algorithm statistical
```

### Information Content (Entropy)

```bash
python rarity_analyzer.py collection doodles --algorithm information
```

### Average Rarity

```bash
python rarity_analyzer.py collection coolcats --algorithm average
```

### Normalized Scores (0-100)

```bash
python rarity_analyzer.py collection pudgypenguins --normalize
```

## Compare Multiple Tokens

```bash
python rarity_analyzer.py compare boredapeyachtclub 1234,5678,9012
```

Output:

```
TOKEN COMPARISON
================================================================================
Trait                Bored Ape #1234  Bored Ape #5678  Bored Ape #9012
--------------------------------------------------------------------------------
Background           Aquamarine (2%)  Blue (15%)       New Punk Blue (3%)
Fur                  Solid Gold (0%)  Brown (12%)      Robot (2%)
Eyes                 Laser Eyes (1%)  Bored (25%)      Heart (5%)
Hat                  Sea Captain (0%) None (20%)       Crown (0%)
Mouth                Cigarette (6%)   Bored (23%)      Phoneme Vuh (1%)
Clothes              Tuxedo (1%)      None (18%)       Sailor Shirt (2%)
--------------------------------------------------------------------------------
RANK                 #42              #892             #156
SCORE                312.45           85.23            198.67
================================================================================
```

## View Trait Distribution Only

```bash
python rarity_analyzer.py traits clonex
```

## Export Data

### Export as JSON

```bash
python rarity_analyzer.py export azuki > azuki_rarity.json
```

### Export as CSV

```bash
python rarity_analyzer.py export azuki --format csv > azuki_rankings.csv
```

### Export with Full Collection

```bash
python rarity_analyzer.py export boredapeyachtclub --limit 10000 --format csv
```

## Cache Management

### View Cache Status

```bash
python rarity_analyzer.py cache
```

### List Cached Items

```bash
python rarity_analyzer.py cache --list
```

### Clear All Cache

```bash
python rarity_analyzer.py cache --clear
```

### Clear Specific Collection

```bash
python rarity_analyzer.py cache --clear --pattern pudgy
```

## JSON Output Mode

### Collection Analysis

```bash
python rarity_analyzer.py collection azuki --json | jq '.rankings[0]'
```

### Token Analysis

```bash
python rarity_analyzer.py token azuki 1234 --json | jq '.traits'
```

## Common Workflows

### Find Undervalued NFTs

```bash
# Get full rankings
python rarity_analyzer.py collection boredapeyachtclub --limit 1000 --top 100

# Compare specific tokens you're considering
python rarity_analyzer.py compare boredapeyachtclub 1234,5678,9012
```

### Analyze Your Collection

```bash
# Export your holdings
python rarity_analyzer.py export azuki --format csv > my_azuki.csv

# Check specific token
python rarity_analyzer.py token azuki 5432
```

### Research Before Mint

```bash
# Check trait distribution for revealed tokens
python rarity_analyzer.py traits newcollection --limit 500

# See what makes tokens rare
python rarity_analyzer.py collection newcollection --rarest
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
