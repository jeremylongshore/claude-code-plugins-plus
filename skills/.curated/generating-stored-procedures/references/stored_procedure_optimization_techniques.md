# Stored Procedure Optimization Techniques

## Set-Based vs Row-Based Operations

### Avoid Cursors When Possible

```sql
-- SLOW: Row-by-row cursor processing
CREATE FUNCTION update_prices_slow()
RETURNS VOID AS $$
DECLARE
    rec RECORD;
BEGIN
    FOR rec IN SELECT id, price FROM products LOOP
        UPDATE products SET price = rec.price * 1.1 WHERE id = rec.id;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- FAST: Set-based operation
CREATE FUNCTION update_prices_fast()
RETURNS INT AS $$
    UPDATE products SET price = price * 1.1;
    SELECT COUNT(*) FROM products;
$$ LANGUAGE sql;
```

**Performance difference**: Set-based is typically 10-100x faster.

## Reduce Network Round Trips

### Batch Operations

```sql
-- SLOW: Multiple calls
CALL insert_order_item(1, 101, 2);
CALL insert_order_item(1, 102, 1);
CALL insert_order_item(1, 103, 5);

-- FAST: Single call with table parameter (SQL Server)
CREATE PROCEDURE dbo.InsertOrderItems
    @OrderId INT,
    @Items dbo.OrderItemType READONLY
AS
BEGIN
    INSERT INTO OrderItems (OrderId, ProductId, Quantity)
    SELECT @OrderId, ProductId, Quantity FROM @Items;
END;

-- FAST: Single call with JSON (PostgreSQL/MySQL)
CREATE FUNCTION insert_order_items(p_order_id INT, p_items JSONB)
RETURNS VOID AS $$
BEGIN
    INSERT INTO order_items (order_id, product_id, quantity)
    SELECT p_order_id, (item->>'product_id')::INT, (item->>'quantity')::INT
    FROM jsonb_array_elements(p_items) AS item;
END;
$$ LANGUAGE plpgsql;
```

## Efficient Indexing

### Use Covering Indexes

```sql
-- Index covers all columns needed by query
CREATE INDEX idx_orders_covering ON orders (customer_id)
    INCLUDE (order_date, total_amount, status);

-- Procedure benefits from index-only scan
CREATE FUNCTION get_customer_orders(p_customer_id INT)
RETURNS TABLE(order_date DATE, total DECIMAL, status VARCHAR) AS $$
    SELECT order_date, total_amount, status
    FROM orders
    WHERE customer_id = p_customer_id;
$$ LANGUAGE sql STABLE;
```

### Index for Procedure Parameters

```sql
-- If procedure frequently filters by status + date
CREATE INDEX idx_orders_status_date ON orders (status, order_date DESC);

-- Procedure uses this index efficiently
CREATE FUNCTION get_pending_orders(p_days INT)
RETURNS SETOF orders AS $$
    SELECT * FROM orders
    WHERE status = 'pending'
      AND order_date > CURRENT_DATE - p_days;
$$ LANGUAGE sql STABLE;
```

## Query Plan Optimization

### PostgreSQL: Analyze Query Plans

```sql
CREATE FUNCTION analyze_query_example()
RETURNS TEXT AS $$
DECLARE
    v_plan TEXT;
BEGIN
    EXPLAIN (ANALYZE, FORMAT TEXT) INTO v_plan
    SELECT * FROM large_table WHERE indexed_col = 123;

    RETURN v_plan;
END;
$$ LANGUAGE plpgsql;
```

### SQL Server: Query Hints

```sql
CREATE PROCEDURE dbo.OptimizedSearch
    @SearchTerm NVARCHAR(100)
AS
BEGIN
    SELECT ProductId, ProductName
    FROM Products WITH (INDEX(IX_Products_Name))
    WHERE ProductName LIKE @SearchTerm + '%'
    OPTION (RECOMPILE);  -- Fresh plan each execution
END;
```

## Caching and Memoization

### PostgreSQL: Materialized Views

```sql
-- Create materialized view for expensive aggregations
CREATE MATERIALIZED VIEW mv_daily_sales AS
SELECT
    DATE(order_date) AS sale_date,
    SUM(total_amount) AS daily_total,
    COUNT(*) AS order_count
FROM orders
GROUP BY DATE(order_date);

-- Procedure uses cached data
CREATE FUNCTION get_daily_sales(p_date DATE)
RETURNS TABLE(daily_total DECIMAL, order_count BIGINT) AS $$
    SELECT daily_total, order_count
    FROM mv_daily_sales
    WHERE sale_date = p_date;
$$ LANGUAGE sql STABLE;

-- Refresh periodically
CREATE FUNCTION refresh_sales_cache()
RETURNS VOID AS $$
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_sales;
$$ LANGUAGE sql;
```

## Volatility Declarations (PostgreSQL)

```sql
-- IMMUTABLE: Same input = same output, always
-- Can be used in indexes, parallelized
CREATE FUNCTION calculate_tax(amount DECIMAL)
RETURNS DECIMAL AS $$
    SELECT amount * 0.08;
$$ LANGUAGE sql IMMUTABLE;

-- STABLE: Same output within single transaction
-- Safe for index scans
CREATE FUNCTION get_current_user_id()
RETURNS INT AS $$
    SELECT current_setting('app.user_id')::INT;
$$ LANGUAGE sql STABLE;

-- VOLATILE: May return different values (default)
-- Prevents certain optimizations
CREATE FUNCTION log_and_return(val INT)
RETURNS INT AS $$
BEGIN
    INSERT INTO log_table (value, logged_at) VALUES (val, NOW());
    RETURN val;
END;
$$ LANGUAGE plpgsql VOLATILE;
```

## Reduce Lock Contention

### Use Appropriate Isolation Levels

```sql
-- PostgreSQL: Read-only procedure with reduced locking
CREATE FUNCTION read_only_report()
RETURNS SETOF report_type AS $$
BEGIN
    SET TRANSACTION ISOLATION LEVEL READ COMMITTED READ ONLY;
    RETURN QUERY SELECT * FROM generate_report();
END;
$$ LANGUAGE plpgsql;
```

### Batch Large Updates

```sql
-- Instead of updating 1M rows at once
-- Process in batches to reduce lock time
CREATE PROCEDURE dbo.BatchUpdate
AS
BEGIN
    DECLARE @BatchSize INT = 10000;
    DECLARE @Affected INT = 1;

    WHILE @Affected > 0
    BEGIN
        UPDATE TOP (@BatchSize) Products
        SET LastUpdated = GETDATE()
        WHERE LastUpdated < DATEADD(YEAR, -1, GETDATE());

        SET @Affected = @@ROWCOUNT;

        -- Allow other transactions to proceed
        WAITFOR DELAY '00:00:00.100';
    END
END;
```

## Statistics and Plan Cache

### Keep Statistics Updated

```sql
-- PostgreSQL
ANALYZE table_name;

-- SQL Server
UPDATE STATISTICS table_name;

-- MySQL
ANALYZE TABLE table_name;
```

### Clear Plan Cache When Needed

```sql
-- SQL Server: Clear specific procedure plan
EXEC sp_recompile 'dbo.ProcedureName';

-- PostgreSQL: No procedure-specific cache, but:
DISCARD PLANS;  -- Clears all plans in session
```

## Optimization Checklist

| Technique | Impact | When to Use |
|-----------|--------|-------------|
| Set-based operations | High | Always prefer over cursors |
| Covering indexes | High | Frequent queries with predictable columns |
| Batch processing | Medium | Large data modifications |
| Volatility hints | Medium | PostgreSQL pure functions |
| Query hints | Low | Last resort after other optimizations |
| Plan recompile | Low | Variable parameter distribution |

## Monitoring and Profiling

```sql
-- PostgreSQL: Enable timing
SET track_functions = 'all';
SELECT * FROM pg_stat_user_functions;

-- SQL Server: Execution statistics
SELECT
    OBJECT_NAME(object_id) AS ProcedureName,
    execution_count,
    total_worker_time / 1000 AS TotalCPU_ms,
    total_elapsed_time / 1000 AS TotalElapsed_ms,
    total_logical_reads
FROM sys.dm_exec_procedure_stats
ORDER BY total_worker_time DESC;

-- MySQL: Performance schema
SELECT * FROM performance_schema.events_statements_summary_by_digest
ORDER BY SUM_TIMER_WAIT DESC LIMIT 10;
```
