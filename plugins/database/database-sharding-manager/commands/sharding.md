---
name: sharding
description: >
  Implement horizontal database sharding for massive scale applications
shortcut: shar
---
# Database Sharding Manager

Design and implement horizontal database sharding strategies to distribute data across multiple database instances, enabling applications to scale beyond single-server limitations with consistent hashing, automatic rebalancing, and cross-shard query coordination.

## When to Use This Command

Use `/sharding` when you need to:
- Scale beyond single database server capacity (>10TB or >100k QPS)
- Distribute write load across multiple database servers
- Improve query performance through data locality
- Implement geographic data distribution for GDPR/data residency
- Reduce blast radius of database failures (isolate tenant data)
- Support multi-tenant SaaS with tenant-level isolation

DON'T use this when:
- Database is small (<1TB) and performing well
- Can solve with read replicas and caching instead
- Application can't handle distributed transactions complexity
- Team lacks expertise in distributed systems
- Cross-shard queries are majority of workload (use partitioning instead)

## Design Decisions

This command implements **consistent hashing with virtual nodes** because:
- Minimizes data movement when adding/removing shards (only K/n keys move)
- Distributes load evenly across shards with virtual nodes
- Supports gradual shard addition without downtime
- Enables geographic routing for data residency compliance
- Provides automatic failover with shard replica promotion

**Alternative considered: Range-based sharding**
- Simple to implement and understand
- Predictable data distribution
- Prone to hotspots if key distribution uneven
- Recommended for time-series data with sequential IDs

**Alternative considered: Directory-based sharding**
- Flexible shard assignment with lookup table
- Easy to move individual records
- Single point of failure (directory lookup)
- Recommended for small-scale or initial implementations

## Prerequisites

Before running this command:
1. Application supports sharding-aware database connections
2. Clear understanding of sharding key (immutable, high cardinality)
3. Strategy for handling cross-shard queries and joins
4. Monitoring infrastructure for shard health
5. Migration plan from single database to sharded architecture

## Implementation Process

### Step 1: Choose Sharding Strategy
Select sharding approach based on data access patterns and scale requirements.

### Step 2: Design Shard Key
Choose immutable, high-cardinality key that distributes data evenly (user_id, tenant_id).

### Step 3: Implement Shard Routing Layer
Build connection pooling and routing logic to direct queries to correct shard.

### Step 4: Migrate Data to Shards
Perform zero-downtime migration from monolithic to sharded architecture.

### Step 5: Monitor and Rebalance
Track shard load distribution and rebalance data as needed.

## Output Format

The command generates:
- `sharding/shard_router.py` - Consistent hashing router implementation
- `sharding/shard_manager.js` - Shard connection pool manager
- `migration/shard_migration.sql` - Data migration scripts per shard
- `monitoring/shard_health.sql` - Per-shard metrics and health checks
- `docs/sharding_architecture.md` - Architecture documentation and runbooks

## Code Examples

### Example 1: Consistent Hashing Shard Router with Virtual Nodes

```python
# sharding/consistent_hash_router.py
import hashlib
import bisect
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ShardConfig:
    """Configuration for a database shard."""
    shard_id: int
    host: str
    port: int
    database: str
    weight: int = 1  # Relative weight for load distribution
    status: str = 'active'  # active, readonly, maintenance

class ConsistentHashRouter:
    """
    Consistent hashing implementation with virtual nodes.

    Virtual nodes ensure even distribution even with heterogeneous shard sizes.
    Adding/removing shards only affects K/n keys where n = number of shards.
    """

    def __init__(self, virtual_nodes: int = 150):
        """
        Initialize consistent hash ring.

        Args:
            virtual_nodes: Number of virtual nodes per physical shard.
                          More nodes = better distribution, higher memory usage.
        """
        self.virtual_nodes = virtual_nodes
        self.ring: List[int] = []  # Sorted hash values
        self.ring_map: Dict[int, ShardConfig] = {}  # Hash -> Shard mapping
        self.shards: Dict[int, ShardConfig] = {}  # Shard ID -> Config

    def add_shard(self, shard: ShardConfig) -> None:
        """Add shard to consistent hash ring with virtual nodes."""
        self.shards[shard.shard_id] = shard

        # Create virtual nodes weighted by shard capacity
        num_vnodes = self.virtual_nodes * shard.weight

        for i in range(num_vnodes):
            # Create unique hash for each virtual node
            vnode_key = f"{shard.shard_id}:{shard.host}:{i}"
            hash_value = self._hash(vnode_key)

            # Insert into sorted ring
            bisect.insort(self.ring, hash_value)
            self.ring_map[hash_value] = shard

        logger.info(
            f"Added shard {shard.shard_id} ({shard.host}) with {num_vnodes} virtual nodes"
        )

    def remove_shard(self, shard_id: int) -> None:
        """Remove shard from hash ring."""
        if shard_id not in self.shards:
            raise ValueError(f"Shard {shard_id} not found")

        shard = self.shards[shard_id]

        # Remove all virtual nodes for this shard
        num_vnodes = self.virtual_nodes * shard.weight
        removed_count = 0

        for i in range(num_vnodes):
            vnode_key = f"{shard.shard_id}:{shard.host}:{i}"
            hash_value = self._hash(vnode_key)

            if hash_value in self.ring_map:
                self.ring.remove(hash_value)
                del self.ring_map[hash_value]
                removed_count += 1

        del self.shards[shard_id]

        logger.info(
            f"Removed shard {shard_id} ({removed_count} virtual nodes)"
        )

    def get_shard(self, key: str) -> Optional[ShardConfig]:
        """
        Find shard for given key using consistent hashing.

        Args:
            key: Sharding key (user_id, tenant_id, etc.)

        Returns:
            ShardConfig for the shard responsible for this key
        """
        if not self.ring:
            raise ValueError("No shards available in hash ring")

        key_hash = self._hash(key)

        # Find first hash value >= key_hash (clockwise search)
        idx = bisect.bisect_right(self.ring, key_hash)

        # Wrap around to beginning if at end of ring
        if idx == len(self.ring):
            idx = 0

        shard = self.ring_map[self.ring[idx]]

        # Skip if shard is in maintenance
        if shard.status == 'maintenance':
            logger.warning(f"Shard {shard.shard_id} in maintenance, finding alternate")
            return self._find_next_active_shard(idx)

        return shard

    def _find_next_active_shard(self, start_idx: int) -> Optional[ShardConfig]:
        """Find next active shard in ring, skipping maintenance shards."""
        for i in range(len(self.ring)):
            idx = (start_idx + i) % len(self.ring)
            shard = self.ring_map[self.ring[idx]]

            if shard.status == 'active':
                return shard

        raise ValueError("No active shards available")

    def _hash(self, key: str) -> int:
        """
        Generate consistent hash value for key.

        Uses MD5 for speed. SHA256 is more secure but slower.
        """
        return int(hashlib.md5(key.encode()).hexdigest(), 16)

    def get_shard_distribution(self) -> Dict[int, int]:
        """Analyze key distribution across shards (for testing)."""
        distribution = {shard_id: 0 for shard_id in self.shards}

        # Sample 10000 keys to estimate distribution
        for i in range(10000):
            shard = self.get_shard(str(i))
            distribution[shard.shard_id] += 1

        return distribution

    def rebalance_check(self) -> Dict[str, Any]:
        """
        Check if shards are balanced and recommend rebalancing.

        Returns:
            Dict with balance metrics and recommendations
        """
        distribution = self.get_shard_distribution()

        total = sum(distribution.values())
        expected_per_shard = total / len(self.shards)

        imbalance = {}
        for shard_id, count in distribution.items():
            deviation = abs(count - expected_per_shard) / expected_per_shard * 100
            imbalance[shard_id] = {
                'count': count,
                'expected': expected_per_shard,
                'deviation_percent': round(deviation, 2)
            }

        max_deviation = max(s['deviation_percent'] for s in imbalance.values())

        return {
            'balanced': max_deviation < 10,  # <10% deviation is acceptable
            'max_deviation_percent': max_deviation,
            'shard_distribution': imbalance,
            'recommendation': (
                'Rebalancing recommended' if max_deviation > 20
                else 'Distribution acceptable'
            )
        }

# Usage example
if __name__ == "__main__":
    # Initialize router
    router = ConsistentHashRouter(virtual_nodes=150)

    # Add shards
    router.add_shard(ShardConfig(
        shard_id=1,
        host='shard1.db.example.com',
        port=5432,
        database='myapp_shard1',
        weight=1
    ))

    router.add_shard(ShardConfig(
        shard_id=2,
        host='shard2.db.example.com',
        port=5432,
        database='myapp_shard2',
        weight=2  # Double capacity
    ))

    router.add_shard(ShardConfig(
        shard_id=3,
        host='shard3.db.example.com',
        port=5432,
        database='myapp_shard3',
        weight=1
    ))

    # Route queries
    user_id = "user_12345"
    shard = router.get_shard(user_id)
    print(f"User {user_id} → Shard {shard.shard_id} ({shard.host})")

    # Check balance
    balance_report = router.rebalance_check()
    print(f"\nBalance report:")
    print(f"  Balanced: {balance_report['balanced']}")
    print(f"  Max deviation: {balance_report['max_deviation_percent']}%")
```

### Example 2: Shard-Aware Database Connection Pool

```javascript
// sharding/shard_connection_pool.js
const { Pool } = require('pg');
const crypto = require('crypto');

class ShardConnectionPool {
    constructor(shardConfigs) {
        this.shards = new Map();
        this.virtualNodes = 150;
        this.ring = [];
        this.ringMap = new Map();

        // Initialize connection pools for each shard
        shardConfigs.forEach(config => {
            const pool = new Pool({
                host: config.host,
                port: config.port,
                database: config.database,
                user: config.user,
                password: config.password,
                max: 20,  // Max connections per shard
                idleTimeoutMillis: 30000,
                connectionTimeoutMillis: 2000
            });

            this.shards.set(config.shardId, {
                config,
                pool,
                stats: {
                    queries: 0,
                    errors: 0,
                    avgLatency: 0
                }
            });

            this.addToRing(config);
        });

        console.log(`Initialized ${this.shards.size} shards with ${this.ring.length} virtual nodes`);
    }

    addToRing(config) {
        const numVNodes = this.virtualNodes * (config.weight || 1);

        for (let i = 0; i < numVNodes; i++) {
            const vnodeKey = `${config.shardId}:${config.host}:${i}`;
            const hash = this.hash(vnodeKey);

            this.ring.push(hash);
            this.ringMap.set(hash, config.shardId);
        }

        // Sort ring for binary search
        this.ring.sort((a, b) => a - b);
    }

    hash(key) {
        return parseInt(
            crypto.createHash('md5').update(key).digest('hex').substring(0, 8),
            16
        );
    }

    getShardId(key) {
        if (this.ring.length === 0) {
            throw new Error('No shards available');
        }

        const keyHash = this.hash(key);

        // Binary search for next hash >= keyHash
        let idx = this.ring.findIndex(h => h >= keyHash);

        if (idx === -1) {
            idx = 0;  // Wrap around
        }

        return this.ringMap.get(this.ring[idx]);
    }

    async query(shardKey, sql, params = []) {
        const shardId = this.getShardId(shardKey);
        const shard = this.shards.get(shardId);

        if (!shard) {
            throw new Error(`Shard ${shardId} not found`);
        }

        const startTime = Date.now();

        try {
            const result = await shard.pool.query(sql, params);

            // Update stats
            shard.stats.queries++;
            const latency = Date.now() - startTime;
            shard.stats.avgLatency =
                (shard.stats.avgLatency * (shard.stats.queries - 1) + latency) /
                shard.stats.queries;

            return result;

        } catch (error) {
            shard.stats.errors++;
            console.error(`Query error on shard ${shardId}:`, error);
            throw error;
        }
    }

    async queryMultipleShards(sql, params = []) {
        /**
         * Execute query across all shards and merge results.
         * Use sparingly - cross-shard queries are expensive.
         */
        const promises = Array.from(this.shards.values()).map(async shard => {
            try {
                const result = await shard.pool.query(sql, params);
                return {
                    shardId: shard.config.shardId,
                    rows: result.rows,
                    success: true
                };
            } catch (error) {
                return {
                    shardId: shard.config.shardId,
                    error: error.message,
                    success: false
                };
            }
        });

        const results = await Promise.all(promises);

        // Merge rows from all shards
        const allRows = results
            .filter(r => r.success)
            .flatMap(r => r.rows);

        return {
            rows: allRows,
            shardResults: results
        };
    }

    async transaction(shardKey, callback) {
        /**
         * Execute transaction on specific shard.
         * Cross-shard transactions require 2PC (not implemented).
         */
        const shardId = this.getShardId(shardKey);
        const shard = this.shards.get(shardId);

        const client = await shard.pool.connect();

        try {
            await client.query('BEGIN');
            const result = await callback(client);
            await client.query('COMMIT');
            return result;
        } catch (error) {
            await client.query('ROLLBACK');
            throw error;
        } finally {
            client.release();
        }
    }

    getStats() {
        const stats = {};

        for (const [shardId, shard] of this.shards) {
            stats[shardId] = {
                ...shard.stats,
                poolSize: shard.pool.totalCount,
                idleConnections: shard.pool.idleCount,
                waitingClients: shard.pool.waitingCount
            };
        }

        return stats;
    }

    async close() {
        for (const shard of this.shards.values()) {
            await shard.pool.end();
        }
    }
}

// Usage example
const shardPool = new ShardConnectionPool([
    {
        shardId: 1,
        host: 'shard1.db.example.com',
        port: 5432,
        database: 'myapp_shard1',
        user: 'app_user',
        password: 'password',
        weight: 1
    },
    {
        shardId: 2,
        host: 'shard2.db.example.com',
        port: 5432,
        database: 'myapp_shard2',
        user: 'app_user',
        password: 'password',
        weight: 2
    }
]);

// Single-shard query
const userId = 'user_12345';
const user = await shardPool.query(
    userId,
    'SELECT * FROM users WHERE user_id = $1',
    [userId]
);

// Cross-shard query (expensive - avoid if possible)
const allActiveUsers = await shardPool.queryMultipleShards(
    'SELECT * FROM users WHERE status = $1',
    ['active']
);

console.log(`Found ${allActiveUsers.rows.length} active users across all shards`);

// Transaction on specific shard
await shardPool.transaction(userId, async (client) => {
    await client.query(
        'UPDATE users SET balance = balance - $1 WHERE user_id = $2',
        [100, userId]
    );

    await client.query(
        'INSERT INTO transactions (user_id, amount, type) VALUES ($1, $2, $3)',
        [userId, -100, 'withdrawal']
    );
});

// Monitor shard health
setInterval(() => {
    const stats = shardPool.getStats();
    console.log('Shard statistics:', JSON.stringify(stats, null, 2));
}, 60000);
```

### Example 3: Geographic Sharding with Data Residency

```python
# sharding/geo_shard_router.py
from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum

class Region(Enum):
    """Geographic regions for data residency compliance."""
    US_EAST = 'us-east'
    US_WEST = 'us-west'
    EU_WEST = 'eu-west'
    ASIA_PACIFIC = 'asia-pacific'

@dataclass
class GeoShardConfig:
    region: Region
    shard_id: int
    host: str
    port: int
    database: str
    data_residency_compliant: bool = True

class GeographicShardRouter:
    """
    Route queries to region-specific shards for GDPR/data residency compliance.

    Each user/tenant is assigned to a geographic region and all their data
    resides in shards within that region.
    """

    def __init__(self):
        self.region_shards: Dict[Region, list[GeoShardConfig]] = {}
        self.user_region_map: Dict[str, Region] = {}  # user_id -> region

    def add_region_shard(self, shard: GeoShardConfig) -> None:
        """Add shard for specific geographic region."""
        if shard.region not in self.region_shards:
            self.region_shards[shard.region] = []

        self.region_shards[shard.region].append(shard)
        print(f"Added shard {shard.shard_id} for region {shard.region.value}")

    def assign_user_region(self, user_id: str, region: Region) -> None:
        """Assign user to geographic region (permanent assignment)."""
        if user_id in self.user_region_map:
            raise ValueError(
                f"User {user_id} already assigned to {self.user_region_map[user_id]}"
            )

        self.user_region_map[user_id] = region
        print(f"Assigned user {user_id} to region {region.value}")

    def get_shard_for_user(self, user_id: str) -> Optional[GeoShardConfig]:
        """Get shard for user based on regional assignment."""
        region = self.user_region_map.get(user_id)

        if not region:
            raise ValueError(f"User {user_id} not assigned to any region")

        shards = self.region_shards.get(region)

        if not shards:
            raise ValueError(f"No shards available for region {region.value}")

        # Simple round-robin across shards in region
        # Could use consistent hashing within region for better distribution
        shard_idx = hash(user_id) % len(shards)
        return shards[shard_idx]

    def validate_data_residency(self, user_id: str, shard: GeoShardConfig) -> bool:
        """Ensure data residency compliance before query execution."""
        user_region = self.user_region_map.get(user_id)

        if user_region != shard.region:
            raise ValueError(
                f"Data residency violation: User {user_id} in {user_region.value} "
                f"attempting access to shard in {shard.region.value}"
            )

        return True

# Usage
geo_router = GeographicShardRouter()

# Add region-specific shards
geo_router.add_region_shard(GeoShardConfig(
    region=Region.US_EAST,
    shard_id=1,
    host='us-east-shard1.db.example.com',
    port=5432,
    database='myapp_us_east'
))

geo_router.add_region_shard(GeoShardConfig(
    region=Region.EU_WEST,
    shard_id=2,
    host='eu-west-shard1.db.example.com',
    port=5432,
    database='myapp_eu_west',
    data_residency_compliant=True
))

# Assign users to regions (based on signup location)
geo_router.assign_user_region('user_us_12345', Region.US_EAST)
geo_router.assign_user_region('user_eu_67890', Region.EU_WEST)

# Route queries to correct regional shard
us_user_shard = geo_router.get_shard_for_user('user_us_12345')
print(f"US user → {us_user_shard.host}")

eu_user_shard = geo_router.get_shard_for_user('user_eu_67890')
print(f"EU user → {eu_user_shard.host}")
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| "No shards available" | All shards offline or empty ring | Add at least one shard, check shard health |
| "Cross-shard foreign key violation" | Reference to data on different shard | Denormalize data or use application-level joins |
| "Shard rebalancing in progress" | Data migration active | Retry query or route to new shard |
| "Distributed transaction failure" | 2PC coordinator unreachable | Implement saga pattern or idempotent operations |
| "Hotspot detected on shard" | Uneven key distribution | Rebalance with more virtual nodes or reshard |

## Configuration Options

**Sharding Strategies**
- `consistent_hash`: Best for even distribution, minimal rebalancing
- `range`: Simple, good for time-series, prone to hotspots
- `directory`: Flexible, requires lookup table maintenance
- `geographic`: Data residency compliance, region isolation

**Virtual Nodes**
- 50-100: Faster routing, less even distribution
- 150-200: Balanced (recommended for production)
- 300+: Most even distribution, higher memory usage

**Connection Pooling**
- `max_connections_per_shard`: 10-50 depending on load
- `idle_timeout`: 30-60 seconds
- `connection_timeout`: 2-5 seconds

## Best Practices

DO:
- Use immutable, high-cardinality shard keys (user_id, tenant_id)
- Implement connection pooling per shard
- Monitor shard load distribution continuously
- Design for cross-shard query minimization
- Use read replicas within shards for scale
- Plan shard capacity for 2-3 years growth

DON'T:
- Use mutable shard keys (email, username can change)
- Perform JOINs across shards (denormalize instead)
- Ignore shard imbalance (leads to hotspots)
- Add shards without capacity planning
- Skip monitoring per-shard metrics
- Use distributed transactions without strong justification

## Performance Considerations

- Shard routing adds ~1-5ms latency per query
- Cross-shard queries 10-100x slower than single-shard
- Adding shard affects K/n keys where K=total keys, n=shard count
- Virtual nodes increase routing time O(log(v*n)) but improve distribution
- Connection pool per shard adds memory overhead (~10MB per pool)
- Rebalancing requires dual-write period (5-10% overhead)

## Related Commands

- `/database-partition-manager` - Partition tables within shards
- `/database-replication-manager` - Set up replicas per shard
- `/database-migration-manager` - Migrate data between shards
- `/database-health-monitor` - Monitor per-shard health metrics

## Version History

- v1.0.0 (2024-10): Initial implementation with consistent hashing and geographic routing
- Planned v1.1.0: Add automatic shard rebalancing and distributed transaction support
