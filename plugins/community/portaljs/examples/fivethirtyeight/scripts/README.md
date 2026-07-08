# FiveThirtyEight Dataset Build Script

## Overview

This script rebuilds the FiveThirtyEight demo dataset catalog from the upstream ABC News repository while preserving curated metadata.

## What it does

1. Reads the canonical dataset list from `index.csv` (sourced from https://github.com/fivethirtyeight/data)
2. Updates existing datasets in `datasets.json` with fresh CSV file URLs and commit dates
3. Adds new datasets from upstream with metadata parsed from their READMEs
4. Preserves manually curated article titles and dates for existing datasets
5. Outputs an updated `datasets.json` file sorted by most recent first

## Prerequisites

- Node.js installed
- GitHub Personal Access Token with repo read access
- Environment variable `GITHUB_PAT` or `GITHUB_TOKEN` set to your token

## Usage

### 1. Update index.csv (if needed)

Download the latest catalog from upstream:

```bash
curl https://raw.githubusercontent.com/fivethirtyeight/data/master/index.csv -o index.csv
```

### 2. Set up GitHub token

Create a `.env` file in the `examples/fivethirtyeight` directory:

```
GITHUB_PAT=your_github_token_here
```

Or export it directly:

```bash
export GITHUB_PAT=your_github_token_here
```

### 3. Run the build script

```bash
npm run build:datasets
```

### 4. Review and commit

The script generates an updated `datasets.json` file. Review the changes and commit:

```bash
git add datasets.json
git commit -m "Update datasets from upstream"
```

## Output

The script outputs `datasets.json` containing:

- `url`: GitHub repository URL for the dataset
- `name`: Dataset folder name
- `displayName`: Formatted display name with styling
- `articles`: Array of related articles with titles, URLs, and dates
- `files`: Array of CSV file URLs from the dataset

## Notes

- Existing datasets preserve their curated article titles and dates
- New datasets attempt to parse article metadata from README files
- The script includes rate limiting delays to avoid GitHub API limits
- Average runtime: 2-3 minutes for 166 datasets
