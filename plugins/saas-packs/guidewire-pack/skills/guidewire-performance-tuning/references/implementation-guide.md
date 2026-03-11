# Guidewire Performance Tuning - Implementation Guide

## Performance Metrics Baseline

| Metric | Target | Critical |
|--------|--------|----------|
| Page load time | < 2s | > 5s |
| API response time (95th) | < 1s | > 3s |
| Batch job completion | Within window | Exceeds window |
| Database query time | < 100ms | > 1s |
| Memory utilization | < 80% | > 95% |

## Instructions

### Step 1: Query Optimization

```gosu
// Query optimization patterns
package gw.performance

uses gw.api.database.Query
uses gw.api.database.Relop
uses gw.api.util.Logger

class QueryOptimization {
  private static final var LOG = Logger.forCategory("QueryOptimization")

  // BAD: Loads all data into memory
  static function getAllActivePoliciesBad() : List<Policy> {
    return Query.make(Policy).select().toList()
      .where(\p -> p.Status == PolicyStatus.TC_INFORCE)
  }

  // GOOD: Filter at database level
  static function getAllActivePoliciesGood() : List<Policy> {
    return Query.make(Policy)
      .compare(Policy#Status, Equals, PolicyStatus.TC_INFORCE)
      .select()
      .toList()
  }

  // BAD: N+1 query problem
  static function getAccountsWithPoliciesBad() : Map<Account, List<Policy>> {
    var accounts = Query.make(Account).select().toList()
    return accounts.mapToValue(\account -> account.Policies.toList())  // N additional queries!
  }

  // GOOD: Eager loading with join
  static function getAccountsWithPoliciesGood() : Map<Account, List<Policy>> {
    var policies = Query.make(Policy)
      .compare(Policy#Account, IsNotNull, null)
      .select()
      .toList()

    return policies.partition(\p -> p.Account)
  }

  // Pagination for large result sets
  static function getPoliciesPaginated(pageSize : int, pageNumber : int) : List<Policy> {
    var offset = pageNumber * pageSize
    return Query.make(Policy)
      .compare(Policy#Status, Equals, PolicyStatus.TC_INFORCE)
      .select()
      .orderBy(\p -> p.IssueDate)
      .skip(offset)
      .take(pageSize)
      .toList()
  }

  // Use indexes effectively
  static function findPolicyByNumber(policyNumber : String) : Policy {
    // PolicyNumber is indexed - this will be fast
    return Query.make(Policy)
      .compare(Policy#PolicyNumber, Equals, policyNumber)
      .select()
      .AtMostOneRow
  }

  // Avoid wildcard searches when possible
  // BAD: Leading wildcard prevents index use
  static function searchPoliciesBad(searchTerm : String) : List<Policy> {
    return Query.make(Policy)
      .contains(Policy#PolicyNumber, searchTerm, true)  // Contains = %term%
      .select()
      .toList()
  }

  // GOOD: Use startsWith for index-friendly search
  static function searchPoliciesGood(searchTerm : String) : List<Policy> {
    return Query.make(Policy)
      .startsWith(Policy#PolicyNumber, searchTerm, true)  // StartsWith = term%
      .select()
      .toList()
  }
}
```

### Step 2: Batch Processing Optimization

```gosu
// Efficient batch processing
package gw.performance.batch

uses gw.api.util.Logger
uses gw.api.database.Query
uses gw.transaction.Transaction

class BatchProcessor {
  private static final var LOG = Logger.forCategory("BatchProcessor")
  private static final var BATCH_SIZE = 100

  // Process large datasets in batches
  static function processAllPolicies(processor(policy : Policy)) {
    var processed = 0
    var query = Query.make(Policy)
      .compare(Policy#Status, Equals, PolicyStatus.TC_INFORCE)

    var iterator = query.select().iterator()
    var batch = new ArrayList<Policy>()

    while (iterator.hasNext()) {
      batch.add(iterator.next())

      if (batch.size() >= BATCH_SIZE) {
        processBatch(batch, processor)
        processed += batch.size()
        batch.clear()
        LOG.info("Processed ${processed} policies")
      }
    }

    // Process remaining items
    if (!batch.Empty) {
      processBatch(batch, processor)
      processed += batch.size()
    }

    LOG.info("Batch processing complete: ${processed} total policies")
  }

  private static function processBatch(batch : List<Policy>, processor(policy : Policy)) {
    Transaction.runWithNewBundle(\bundle -> {
      batch.each(\policy -> {
        var p = bundle.add(policy)
        processor(p)
      })
    })
  }

  // Parallel processing for independent operations
  static function processParallel<T>(
    items : List<T>,
    processor(item : T),
    threadCount : int = 4
  ) {
    var executor = java.util.concurrent.Executors.newFixedThreadPool(threadCount)

    try {
      var futures = items.map(\item -> {
        executor.submit(\-> {
          try {
            processor(item)
          } catch (e : Exception) {
            LOG.error("Processing failed for item", e)
          }
        })
      })

      // Wait for all to complete
      futures.each(\f -> f.get())
    } finally {
      executor.shutdown()
    }
  }
}
```

### Step 3: Caching Strategies

```gosu
// Caching implementation
package gw.performance.cache

uses gw.api.util.Logger
uses java.util.concurrent.ConcurrentHashMap
uses java.util.concurrent.TimeUnit

class CacheManager {
  private static final var LOG = Logger.forCategory("CacheManager")
  private static var _caches = new ConcurrentHashMap<String, Cache<Object, Object>>()

  static function getCache<K, V>(name : String, ttlSeconds : int = 300) : Cache<K, V> {
    return _caches.computeIfAbsent(name, \n -> new Cache<K, V>(ttlSeconds)) as Cache<K, V>
  }

  static function clearAll() {
    _caches.values().each(\c -> c.clear())
  }
}

class Cache<K, V> {
  private var _data = new ConcurrentHashMap<K, CacheEntry<V>>()
  private var _ttlMs : long

  construct(ttlSeconds : int) {
    _ttlMs = TimeUnit.SECONDS.toMillis(ttlSeconds)
  }

  function get(key : K, loader() : V) : V {
    var entry = _data.get(key)

    if (entry != null && !entry.isExpired()) {
      return entry.Value
    }

    var value = loader()
    _data.put(key, new CacheEntry<V>(value, _ttlMs))
    return value
  }

  function invalidate(key : K) {
    _data.remove(key)
  }

  function clear() {
    _data.clear()
  }

  property get Size() : int {
    return _data.size()
  }
}

class CacheEntry<V> {
  private var _value : V
  private var _expiresAt : long

  construct(value : V, ttlMs : long) {
    _value = value
    _expiresAt = System.currentTimeMillis() + ttlMs
  }

  property get Value() : V {
    return _value
  }

  function isExpired() : boolean {
    return System.currentTimeMillis() > _expiresAt
  }
}

// Usage example: Caching product lookup
class ProductService {
  private static var _productCache = CacheManager.getCache<String, Product>("products", 3600)

  static function getProduct(code : String) : Product {
    return _productCache.get(code, \-> loadProductFromDatabase(code))
  }

  private static function loadProductFromDatabase(code : String) : Product {
    return gw.api.productmodel.ProductLookup.getByCode(code)
  }
}
```

### Step 4: Database Connection Pool Tuning

```properties
# database.properties - Connection pool optimization

# Pool size - based on concurrent users
# Formula: connections = (core_count * 2) + effective_spindle_count
database.connection.pool.minSize=10
database.connection.pool.maxSize=50
database.connection.pool.initialSize=10

# Connection validation
database.connection.validationQuery=SELECT 1
database.connection.testOnBorrow=true
database.connection.testWhileIdle=true
database.connection.timeBetweenEvictionRunsMillis=30000

# Statement caching
database.preparedStatement.cacheSize=250

# Timeout settings
database.connection.timeoutMs=30000
database.query.timeoutSeconds=60
```

### Step 5: JVM Tuning

```bash
# JVM options for Guidewire Cloud applications
# Production-optimized settings

JAVA_OPTS="
  # Memory settings
  -Xms4g
  -Xmx8g
  -XX:MetaspaceSize=512m
  -XX:MaxMetaspaceSize=1g

  # G1 Garbage Collector (recommended for heap > 4GB)
  -XX:+UseG1GC
  -XX:MaxGCPauseMillis=200
  -XX:G1HeapRegionSize=16m
  -XX:+ParallelRefProcEnabled

  # GC logging
  -Xlog:gc*:file=/var/log/gc.log:time,uptime:filecount=5,filesize=100m

  # Performance flags
  -XX:+UseStringDeduplication
  -XX:+OptimizeStringConcat
  -XX:+UseCompressedOops

  # Debugging (remove in production)
  # -XX:+HeapDumpOnOutOfMemoryError
  # -XX:HeapDumpPath=/var/dumps/
"
```

### Step 6: API Response Optimization

```typescript
// Optimize API responses
import { LRUCache } from 'lru-cache';

interface CacheConfig {
  maxSize: number;
  ttlMs: number;
}

class OptimizedApiClient {
  private cache: LRUCache<string, any>;

  constructor(cacheConfig: CacheConfig = { maxSize: 500, ttlMs: 60000 }) {
    this.cache = new LRUCache({
      max: cacheConfig.maxSize,
      ttl: cacheConfig.ttlMs
    });
  }

  // Use field selection to reduce payload size
  async getPolicy(policyId: string, fields?: string[]): Promise<Policy> {
    const cacheKey = `policy:${policyId}:${fields?.join(',') || 'all'}`;

    const cached = this.cache.get(cacheKey);
    if (cached) return cached;

    // Only request needed fields
    const fieldParam = fields?.length
      ? `?fields=${fields.join(',')}`
      : '?fields=policyNumber,effectiveDate,totalPremium,status';

    const response = await this.client.get(`/policy/v1/policies/${policyId}${fieldParam}`);

    this.cache.set(cacheKey, response.data);
    return response.data;
  }

  // Use includes to reduce round trips
  async getAccountWithRelated(accountId: string): Promise<Account> {
    return this.client.get(
      `/account/v1/accounts/${accountId}?include=policies,contacts,locations`
    );
  }

  // Parallel requests for independent data
  async getDashboardData(accountId: string): Promise<DashboardData> {
    const [account, policies, claims, invoices] = await Promise.all([
      this.getAccount(accountId),
      this.getPolicies(accountId),
      this.getClaims(accountId),
      this.getInvoices(accountId)
    ]);

    return { account, policies, claims, invoices };
  }
}
```

### Step 7: Performance Monitoring

```gosu
// Performance monitoring utilities
package gw.performance.monitor

uses gw.api.util.Logger
uses java.util.concurrent.ConcurrentHashMap
uses java.util.concurrent.atomic.AtomicLong

class PerformanceMonitor {
  private static final var LOG = Logger.forCategory("PerformanceMonitor")
  private static var _metrics = new ConcurrentHashMap<String, OperationMetrics>()

  static function time<T>(operationName : String, operation() : T) : T {
    var startTime = System.nanoTime()
    var success = true

    try {
      return operation()
    } catch (e : Exception) {
      success = false
      throw e
    } finally {
      var duration = (System.nanoTime() - startTime) / 1_000_000.0  // ms
      recordMetric(operationName, duration, success)

      if (duration > 1000) {  // Log slow operations
        LOG.warn("Slow operation: ${operationName} took ${duration}ms")
      }
    }
  }

  private static function recordMetric(name : String, durationMs : double, success : boolean) {
    var metrics = _metrics.computeIfAbsent(name, \n -> new OperationMetrics(n))
    metrics.record(durationMs, success)
  }

  static function getMetrics() : Map<String, OperationMetrics> {
    return new HashMap<String, OperationMetrics>(_metrics)
  }

  static function reset() {
    _metrics.clear()
  }
}

class OperationMetrics {
  private var _name : String
  private var _count = new AtomicLong(0)
  private var _totalMs = new AtomicLong(0)
  private var _maxMs = new AtomicLong(0)
  private var _failures = new AtomicLong(0)

  construct(name : String) {
    _name = name
  }

  function record(durationMs : double, success : boolean) {
    _count.incrementAndGet()
    _totalMs.addAndGet(durationMs as long)

    // Update max (thread-safe)
    var currentMax = _maxMs.get()
    while (durationMs > currentMax) {
      if (_maxMs.compareAndSet(currentMax, durationMs as long)) {
        break
      }
      currentMax = _maxMs.get()
    }

    if (!success) {
      _failures.incrementAndGet()
    }
  }

  property get Name() : String { return _name }
  property get Count() : long { return _count.get() }
  property get AverageMs() : double { return _totalMs.get() / Math.max(_count.get(), 1) as double }
  property get MaxMs() : long { return _maxMs.get() }
  property get FailureRate() : double { return _failures.get() / Math.max(_count.get(), 1) as double }
}
```

## Performance Checklist

| Area | Check | Status |
|------|-------|--------|
| Queries | All queries use indexes | [ ] |
| Queries | No N+1 query patterns | [ ] |
| Queries | Large results paginated | [ ] |
| Batch | Appropriate batch sizes | [ ] |
| Batch | Within maintenance windows | [ ] |
| Caching | Frequently accessed data cached | [ ] |
| Caching | Cache invalidation implemented | [ ] |
| JVM | Memory settings optimized | [ ] |
| JVM | GC logs analyzed | [ ] |
