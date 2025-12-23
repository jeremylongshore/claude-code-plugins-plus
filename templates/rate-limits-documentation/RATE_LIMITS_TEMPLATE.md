# Rate Limits & Resource Constraints Documentation Template

**Purpose:** Standardized template for documenting rate limits, registration requirements, and multi-agent coordination strategies per Tom's request on Discussion #148.

**When to use:** Add this section to any plugin that uses external APIs, self-hosted services, or has resource constraints that affect multi-agent usage.

---

## ⚠️ Rate Limits & [Service Type] Requirements

**[Plugin purpose] uses 100% free [data sources/services]** - no [paid alternative name] subscriptions required.

### Quick Comparison

| Service | Paid Alternative | FREE (This Plugin) |
|---------|-----------------|-------------------|
| **[Service Category]** | [Paid Service] ($XX/mo) | [Free Service]: **$0** |
| **[Second Category]** | [Paid Service 2] ($XX/mo) | [Free Service 2]: **$0** |
| **[Third Category]** | [Paid Service 3] ($XX/mo) | [Free Service 3]: **$0** |

**Annual Savings: $X,XXX-X,XXX** using free [service type] instead of paid alternatives.

---

## Free API Providers: Detailed Rate Limits

### 1. [Primary Service Name] (Primary - [Main Use Case])

**What:** [Brief description of what this service provides]

**Rate Limits:**
- **Requests/minute:** [X-Y] (or "Unlimited" with soft limit notes)
- **Daily requests:** [X,XXX] or "Unlimited"
- **Registration:** ❌ Not required / ✅ Required
- **API key:** ❌ Not required / ✅ Required
- **IP tracking:** ⚠️ [Description of tracking/bans]

**API Endpoints (All FREE):**
```bash
# [Endpoint description]
https://api.[service].com/[path]

# [Another endpoint description]
https://api.[service].com/[another-path]
```

**Setup:**
```json
{
  "dataSources": {
    "[service]": {
      "provider": "[service-name]",
      "endpoint": "https://api.[service].com",
      "rateLimit": {
        "maxPerSecond": X,
        "maxPerMinute": XX
      }
    }
  }
}
```

**Cost:** $0 ([signup requirement details])

**Documentation:** [[service].com/docs]([https://service.com/docs])

---

### 2. [Secondary Service Name] (Fallback/Alternative)

[Repeat structure above for each major service]

**Rate Limits:**
- **Requests/minute:** XX
- **Daily requests:** X,XXX
- **Registration:** [Yes/No with details]
- **API key:** [Yes/No]
- **IP tracking:** [Description]

---

## Registration & Setup Requirements

| Provider | Email Signup | API Key | Payment Method | IP Tracking | Notes |
|----------|--------------|---------|----------------|-------------|-------|
| **[Service 1]** | ❌ No | ❌ No | ❌ No | ⚠️ Soft limits | [Additional notes] |
| **[Service 2]** | ✅ Yes | ✅ Yes | ❌ No (free tier) | ✅ Yes (X/sec) | [Setup link] |
| **[Service 3]** | ✅ Yes | ✅ Yes | ✅ Required | ✅ Yes | [Pricing notes] |

**Best No-Signup Combo:** [Service 1] + [Service 2] = 100% free, zero registration

---

## Multi-Agent Rate Limit Strategies

### Scenario: [X] Agents [Using Service] on Single IP

**Challenge:** Each agent needs [describe data needs]. Without coordination, agents could hit rate limits.

#### Strategy 1: Centralized Data Coordinator

```python
# Shared data coordinator for all agents
class [Service]DataCoordinator:
    def __init__(self):
        self.cache = {}  # Cache [data type]
        self.rate_limiter = RateLimiter()

        # Rate limiting
        self.last_request = 0
        self.requests_this_minute = 0

    def get_data(self, query):
        # Check cache first ([X]-minute TTL)
        if query in self.cache:
            cached_data, cached_time = self.cache[query]
            if time.time() - cached_time < [TTL_SECONDS]:
                return cached_data

        # Rate limit: max [X]/sec or [Y]/min
        time_since_last = time.time() - self.last_request
        if time_since_last < [MIN_INTERVAL]:
            time.sleep([MIN_INTERVAL] - time_since_last)

        # Fetch fresh data
        response = requests.get(f'[API_URL]', params={'query': query})
        data = response.json()

        # Update cache
        self.cache[query] = (data, time.time())
        self.last_request = time.time()

        return data

# All [X] agents share one coordinator
coordinator = [Service]DataCoordinator()

# Agent usage
def agent_process(agent_id, task):
    # Agents share cached data - no duplicate API calls
    data = coordinator.get_data(task)
    result = process(data)
    return result
```

**Result:** [X] agents only make 1 API call per unique data point (not [X] calls each)

---

#### Strategy 2: Request Batching

```python
# Batch multiple agent requests into one API call
class Batched[Service]Fetcher:
    def __init__(self):
        self.pending_requests = []
        self.batch_timer = None

    def request_data(self, query, callback):
        # Add to batch
        self.pending_requests.append((query, callback))

        # Start [X]ms timer to batch requests
        if self.batch_timer is None:
            self.batch_timer = threading.Timer([BATCH_DELAY], self.process_batch)
            self.batch_timer.start()

    def process_batch(self):
        # Deduplicate queries
        unique_queries = set(req[0] for req in self.pending_requests)

        # Single API call for all queries
        results = batch_api_call(unique_queries)

        # Call all callbacks
        for query, callback in self.pending_requests:
            callback(results.get(query))

        # Reset
        self.pending_requests = []
        self.batch_timer = None

# Usage by multiple agents
fetcher = Batched[Service]Fetcher()

# [X] agents request at same time
for agent_id in range([NUM_AGENTS]):
    fetcher.request_data(query, lambda data: agent_process(data))

# Only 1 API call is made for all [X] agents
```

**Result:** [X] agents → 1 API call ([X]x reduction)

---

#### Strategy 3: [Service-Specific Strategy Name]

```[language]
# [Description of this strategy]
class [Strategy]Class:
    # [Implementation details specific to this service]
```

**Result:** [Impact description]

---

#### Strategy 4: Time-Based Caching

```python
# Cache frequently accessed data with TTL
import time
from functools import lru_cache

class Cached[Service]Data:
    def __init__(self):
        self.cache = {}

    def get_cached(self, key, fetch_func, ttl_seconds=[DEFAULT_TTL]):
        """
        Generic caching with time-to-live

        Args:
            key: Cache key
            fetch_func: Function to call if cache miss
            ttl_seconds: How long to cache (default [X] minutes)
        """
        if key in self.cache:
            data, timestamp = self.cache[key]
            age = time.time() - timestamp

            if age < ttl_seconds:
                return data  # Cache hit

        # Cache miss - fetch fresh data
        fresh_data = fetch_func()
        self.cache[key] = (fresh_data, time.time())

        return fresh_data

# Usage
cache = Cached[Service]Data()

# First agent: fetches from API
data_1 = cache.get_cached(
    'query_key',
    lambda: requests.get('[API_URL]').json(),
    ttl_seconds=[TTL]
)

# [X] seconds later, second agent: returns cached data (no API call)
data_2 = cache.get_cached('query_key', lambda: ...)

# Result: 1 API call serves all agents for [X] minutes
```

**Caching Strategy:**
- **[Data Type 1]:** [X]-minute cache ([reasoning])
- **[Data Type 2]:** [Y]-minute cache ([reasoning])
- **[Data Type 3]:** [Z]-minute cache ([reasoning])

**Impact:** [X]% reduction in API calls

---

## Cost Comparison: Paid vs Free

### Paid Approach (Premium Subscriptions)

**Annual Costs:**
- **[Service 1]** ([use case]): $XX/mo → $XXX/year
- **[Service 2]** ([use case]): $XX/mo → $XXX/year
- **[Service 3]** ([use case]): $XX/mo → $XXX/year

**Total: $X,XXX/year**

### Free Approach (This Plugin)

**Annual Costs:**
- **[Free Service 1]:** $0
- **[Free Service 2]:** $0
- **[Free Service 3]:** $0

**Total: $0/year**

**Savings: $X,XXX/year** ([XX]% reduction)

---

## When Free APIs Are NOT Enough

**Consider paid services if:**

1. **[Use Case 1]** - Need [specific requirement]
2. **[Use Case 2]** - [Specific requirement]
3. **[Use Case 3]** - [Specific requirement]
4. **[Use Case 4]** - [Specific requirement]
5. **[Use Case 5]** - [Specific requirement]

**For [XX]% of [user type]:** Free APIs provide sufficient [quality/speed/reliability]

---

## Hybrid Approach (Best of Both Worlds)

**Use free APIs for development/testing, upgrade only when necessary:**

```[language]
const DATA_SOURCES = {
  development: {
    [service]: '[FREE_ENDPOINT]',  // FREE
  },
  production: {
    [service]: process.env.[PAID_ENDPOINT],  // Paid ($XX/mo)
  }
};

const config = DATA_SOURCES[process.env.NODE_ENV || 'development'];
```

**Cost Reduction:** $X,XXX/year → $XXX/year ([XX]% savings) by only paying for [critical component]

---

## Resources

- **[Service 1] API:** [[link](URL)] (FREE, [requirements])
- **[Service 2] API:** [[link](URL)] (FREE, [requirements])
- **[Service 3] Docs:** [[link](URL)] ([details])
- **[Comparison/List]:** [[link](URL)] ([description])

---

**Bottom Line:** [Summary of key benefits and cost savings]

---

## Template Usage Instructions

### How to Use This Template

1. **Copy this entire section** and paste it after the Installation section in your plugin README
2. **Replace all [PLACEHOLDERS]** with actual values:
   - `[Service Name]` → Actual service name (e.g., "CoinGecko", "DefiLlama")
   - `[X]` → Actual numbers (rate limits, agent counts, etc.)
   - `[language]` → Programming language (`python`, `javascript`, `bash`, etc.)
   - `[API_URL]` → Actual API endpoint URLs
   - `[TTL_SECONDS]` → Time-to-live in seconds
3. **Customize strategies** to match your specific service's constraints
4. **Remove strategies** that don't apply to your service
5. **Add service-specific strategies** if needed
6. **Update cost comparisons** with accurate pricing from service websites
7. **Include registration guides** with step-by-step screenshots if signup required

### Required Sections

- ✅ Quick Comparison table
- ✅ At least 2-3 free API providers with detailed rate limits
- ✅ Registration & Setup Requirements table
- ✅ At least 2 multi-agent coordination strategies with code examples
- ✅ Cost Comparison (Paid vs Free)
- ✅ When Free APIs Are NOT Enough
- ✅ Resources section

### Optional Sections (Add if Applicable)

- Hardware requirements (for self-hosted services)
- Execution throughput tables
- Storage requirements
- Docker/Kubernetes deployment examples
- Hybrid approach examples

### Validation Checklist

Before committing, verify:
- [ ] All placeholders replaced with real values
- [ ] Rate limits verified from official documentation
- [ ] Code examples tested and working
- [ ] Registration steps accurate (test by creating new account)
- [ ] Cost comparisons current (check pricing pages)
- [ ] Links working and pointing to official docs
- [ ] Multi-agent scenarios realistic and achievable
- [ ] Caching TTL values make sense for data freshness

### Tom's Requirements (Discussion #148)

Ensure you address these specific concerns:
- ✅ **Registration requirements** - Clearly state if email/payment needed
- ✅ **IP restrictions** - Document IP-based rate limiting or soft bans
- ✅ **Multi-agent coordination** - Show how agents can share one IP resourcefully
- ✅ **Real constraints** - Document actual limits, not marketing claims
- ✅ **Fallback chains** - Provide alternatives when primary service hits limits
- ✅ **Cost transparency** - Show real annual costs of paid vs free

---

## Examples of Plugins Using This Template

**Best implementations:**
- `plugins/ai-ml/ollama-local-ai/README.md` - Hardware-based constraints
- `plugins/finance/openbb-terminal/README.md` - Financial API rate limits
- `plugins/crypto/defi-yield-optimizer/README.md` - DeFi data sources
- `plugins/ai-agency/n8n-workflow-designer/README.md` - Self-hosted platform resources

**Study these examples** to see template variations for different service types.
