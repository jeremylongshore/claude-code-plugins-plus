# Error Handling Reference

Comprehensive guide to errors, causes, and solutions for the scanning-market-movers skill.

## Error Categories

### 1. Dependency Errors

#### DependencyNotFoundError

**Message:** `tracking-crypto-prices dependency not found`

**Cause:** The market-price-tracker plugin with tracking-crypto-prices skill is not installed or not found at the expected path.

**Solution:**

1. Ensure market-price-tracker plugin is installed
2. Verify the plugin is in the same plugins/crypto/ directory
3. Check the path structure matches expected layout

**Expected Path:**

```
plugins/crypto/
├── market-movers-scanner/
│   └── skills/scanning-market-movers/   ← This skill
└── market-price-tracker/
    └── skills/tracking-crypto-prices/   ← Dependency
```

---

#### ImportError

**Message:** `Failed to import from tracking-crypto-prices: [details]`

**Cause:** The dependency exists but required modules are missing or have errors.

**Solution:**

1. Check that tracking-crypto-prices has all required files
2. Ensure Python dependencies are installed: `pip install requests pandas`
3. Run dependency's tests to verify it works independently

---

### 2. API Errors

#### RateLimitError

**Message:** `Rate limit exceeded` or `429 Too Many Requests`

**Cause:** CoinGecko API rate limit reached.

**Solution:**

1. Wait for rate limit reset (typically 60 seconds)
2. Partial results may still be returned
3. Use cached data when available

**Prevention:**

- Use tracking-crypto-prices caching
- Limit scan scope with filters
- Consider CoinGecko API key for higher limits

---

#### NetworkError

**Message:** `Connection failed` or `Request timed out`

**Cause:** No internet connection or API unreachable.

**Solution:**

1. Check internet connectivity
2. Verify CoinGecko API is accessible
3. Cached data will be used as fallback

---

### 3. Filter Errors

#### NoResultsError

**Message:** `No movers found matching your criteria`

**Cause:** Filter thresholds are too strict for current market conditions.

**Solution:**

1. Relax thresholds:

   ```bash
   python scanner.py --min-change 3 --volume-spike 1.5
   ```

2. Expand market cap range:

   ```bash
   python scanner.py --min-cap 1000000  # Lower to $1M
   ```

3. Remove category filter to scan all assets

**Suggested Adjustments:**
The scanner suggests relaxed parameters when zero results are found.

---

#### InvalidThresholdError

**Message:** `Invalid threshold value`

**Cause:** Threshold value is out of acceptable range.

**Solution:**

- min-change: Must be >= 0
- volume-spike: Must be >= 1.0
- min-cap: Must be >= 0

---

### 4. Configuration Errors

#### PresetNotFoundError

**Message:** `Warning: Preset 'xyz' not found, using defaults`

**Cause:** Named preset file doesn't exist in config/presets/.

**Solution:**

1. Check available presets:

   ```bash
   ls config/presets/
   ```

2. Create the preset:

   ```yaml
   # config/presets/xyz.yaml
   min_change: 10
   volume_spike: 3
   ```

---

#### InvalidConfigError

**Message:** `YAML parsing error`

**Cause:** Malformed settings.yaml file.

**Solution:**

1. Validate YAML syntax
2. Use spaces, not tabs
3. Delete settings.yaml to use defaults

---

### 5. Output Errors

#### FileWriteError

**Message:** `Error writing to output file`

**Cause:** Cannot write to specified path.

**Solution:**

1. Check directory exists
2. Check file permissions
3. Ensure disk space available

---

## Error Handling Strategy

### Fallback Hierarchy

```
1. Primary: CoinGecko markets API
     ↓ (fails)
2. Fallback: Cached market data
     ↓ (no cache)
3. Last Resort: Partial results with warning
     ↓ (total failure)
4. Error: Clear message with remediation
```

### Graceful Degradation

| Scenario | Behavior |
|----------|----------|
| Rate limited | Return partial results, warn user |
| Network error | Use cached data with stale warning |
| No results | Suggest relaxed thresholds |
| Dependency missing | Clear error with installation steps |

---

## Debugging

### Enable Verbose Mode

```bash
python scanner.py --verbose
```

Shows:

- Dependency loading status
- API calls and responses
- Filter statistics
- Timing information

### Check Dependency

```bash
# Verify dependency exists
ls ../market-price-tracker/skills/tracking-crypto-prices/scripts/

# Test dependency directly
python ../market-price-tracker/skills/tracking-crypto-prices/scripts/price_tracker.py --help
```

---

## Error Codes

| Code | Category | Meaning |
|------|----------|---------|
| 1 | General | Argument error or unknown error |
| 2 | Dependency | Required skill not found |
| 3 | API | Network or rate limit error |
| 4 | Filter | No results match criteria |
| 5 | Config | Configuration error |
| 6 | Output | File write error |

---

## Reporting Issues

When reporting issues, include:

1. **Command executed:**

   ```bash
   python scanner.py --verbose [your options]
   ```

2. **Full error output** (with `--verbose`)

3. **Environment:**

   ```bash
   python --version
   pip list | grep -E "requests|pandas"
   ```

4. **Dependency check:**

   ```bash
   ls ../market-price-tracker/skills/tracking-crypto-prices/
   ```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
