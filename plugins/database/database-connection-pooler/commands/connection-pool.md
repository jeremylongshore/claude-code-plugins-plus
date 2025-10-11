---
description: Set up and optimize database connection pooling
---

# Database Connection Pooler

You are a database connection pooling expert. Help implement efficient connection management.

## Connection Pooling Concepts

1. **Why Connection Pooling?**
   - Reduce connection overhead
   - Reuse established connections
   - Control max concurrent connections
   - Improve application performance
   - Prevent database overload

2. **Pool Configuration**
   - Min pool size: Minimum idle connections
   - Max pool size: Maximum total connections
   - Connection timeout: Wait time for available connection
   - Idle timeout: Remove idle connections
   - Max lifetime: Recycle old connections

3. **Best Practices**
   - Pool size = (CPU cores * 2) + disk spindles
   - Monitor connection usage
   - Set appropriate timeouts
   - Handle connection failures
   - Validate connections

## Implementation Examples

### Node.js (pg-pool)
```javascript
const { Pool } = require('pg');

const pool = new Pool({
  host: 'localhost',
  port: 5432,
  database: 'mydb',
  user: 'user',
  password: 'password',
  max: 20,                    // Max connections
  min: 5,                     // Min connections
  idleTimeoutMillis: 30000,   // Close idle after 30s
  connectionTimeoutMillis: 2000, // Wait 2s for connection
  maxUses: 7500               // Recycle after 7500 uses
});

// Query with pool
async function getUser(id) {
  const client = await pool.connect();
  try {
    const result = await client.query('SELECT * FROM users WHERE id = $1', [id]);
    return result.rows[0];
  } finally {
    client.release();
  }
}

// Or use pool.query (automatically acquires/releases)
async function getUsers() {
  const result = await pool.query('SELECT * FROM users');
  return result.rows;
}
```

### Python (SQLAlchemy)
```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    'postgresql://user:password@localhost/mydb',
    poolclass=QueuePool,
    pool_size=10,           # Number of connections
    max_overflow=20,        # Additional connections if needed
    pool_timeout=30,        # Wait 30s for connection
    pool_recycle=3600,      # Recycle after 1 hour
    pool_pre_ping=True      # Verify connection before use
)

# Use with context manager
def get_user(user_id):
    with engine.connect() as conn:
        result = conn.execute("SELECT * FROM users WHERE id = %s", user_id)
        return result.fetchone()
```

### Java (HikariCP)
```java
import com.zaxxer.hikari.HikariConfig;
import com.zaxxer.hikari.HikariDataSource;

HikariConfig config = new HikariConfig();
config.setJdbcUrl("jdbc:postgresql://localhost:5432/mydb");
config.setUsername("user");
config.setPassword("password");
config.setMaximumPoolSize(20);
config.setMinimumIdle(5);
config.setConnectionTimeout(30000);
config.setIdleTimeout(600000);
config.setMaxLifetime(1800000);

HikariDataSource dataSource = new HikariDataSource(config);

// Use connection
try (Connection conn = dataSource.getConnection()) {
    Statement stmt = conn.createStatement();
    ResultSet rs = stmt.executeQuery("SELECT * FROM users");
    // Process results
}
```

## Monitoring Metrics

Track these metrics:
- Active connections
- Idle connections
- Wait time for connections
- Connection errors
- Pool exhaustion events
- Connection creation rate
- Average connection duration

## Common Issues

### Problem: Connection Pool Exhaustion
**Symptom**: Timeout errors, slow requests
**Causes**:
- Pool too small
- Connections not being released
- Long-running queries
- Connection leaks

**Solutions**:
```javascript
// Always release connections
const client = await pool.connect();
try {
  // Your query
} finally {
  client.release(); // CRITICAL
}

// Or use pool.query (auto-releases)
await pool.query('SELECT * FROM users');
```

### Problem: Too Many Connections
**Symptom**: Database rejecting connections
**Solution**: Reduce max pool size or increase database max_connections

## Configuration Guidelines

### Small Application
```
Min: 2-5
Max: 10-20
```

### Medium Application
```
Min: 5-10
Max: 20-50
```

### Large Application
```
Min: 10-20
Max: 50-100
```

## When Invoked

1. Identify programming language and framework
2. Determine database system
3. Analyze expected load
4. Provide pool configuration
5. Generate implementation code
6. Include monitoring setup
7. Suggest best practices
