# PostgreSQL Stored Procedure Best Practices

## Function vs Procedure

PostgreSQL 11+ supports both:

- **FUNCTION**: Returns values, can be used in SELECT
- **PROCEDURE**: No return value, supports COMMIT/ROLLBACK inside

```sql
-- Function (returns value)
CREATE FUNCTION get_user(p_id INT) RETURNS users AS $$
    SELECT * FROM users WHERE id = p_id;
$$ LANGUAGE sql;

-- Procedure (no return, can commit)
CREATE PROCEDURE archive_old_orders() AS $$
BEGIN
    INSERT INTO orders_archive SELECT * FROM orders WHERE created_at < NOW() - INTERVAL '1 year';
    DELETE FROM orders WHERE created_at < NOW() - INTERVAL '1 year';
    COMMIT;
END;
$$ LANGUAGE plpgsql;
```

## Parameter Naming

Use `p_` prefix for parameters to avoid column name conflicts:

```sql
-- GOOD: Clear parameter naming
CREATE FUNCTION update_user(p_user_id INT, p_email VARCHAR)
RETURNS VOID AS $$
BEGIN
    UPDATE users SET email = p_email WHERE id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- BAD: Ambiguous naming causes bugs
CREATE FUNCTION update_user(user_id INT, email VARCHAR)
RETURNS VOID AS $$
BEGIN
    -- BUG: 'email = email' always true due to column name conflict
    UPDATE users SET email = email WHERE id = user_id;
END;
$$ LANGUAGE plpgsql;
```

## Return Types

### Single Row

```sql
CREATE FUNCTION get_user(p_id INT)
RETURNS users AS $$
    SELECT * FROM users WHERE id = p_id;
$$ LANGUAGE sql;
```

### Multiple Rows

```sql
CREATE FUNCTION get_active_users()
RETURNS SETOF users AS $$
    SELECT * FROM users WHERE active = true;
$$ LANGUAGE sql;
```

### Custom Columns

```sql
CREATE FUNCTION get_user_summary(p_id INT)
RETURNS TABLE(name VARCHAR, order_count BIGINT, total_spent NUMERIC) AS $$
BEGIN
    RETURN QUERY
    SELECT u.name, COUNT(o.id), SUM(o.total)
    FROM users u
    LEFT JOIN orders o ON o.user_id = u.id
    WHERE u.id = p_id
    GROUP BY u.id;
END;
$$ LANGUAGE plpgsql;
```

## Error Handling

```sql
CREATE FUNCTION safe_divide(a NUMERIC, b NUMERIC)
RETURNS NUMERIC AS $$
BEGIN
    IF b = 0 THEN
        RAISE EXCEPTION 'Division by zero'
            USING ERRCODE = '22012',
                  HINT = 'Ensure divisor is not zero';
    END IF;
    RETURN a / b;
EXCEPTION
    WHEN division_by_zero THEN
        RAISE NOTICE 'Caught division by zero';
        RETURN NULL;
    WHEN OTHERS THEN
        RAISE NOTICE 'Unexpected error: %', SQLERRM;
        RAISE;
END;
$$ LANGUAGE plpgsql;
```

## Security: SECURITY DEFINER

Execute with function owner's privileges:

```sql
-- Runs as function owner, not caller
CREATE FUNCTION admin_reset_password(p_user_id INT, p_new_hash VARCHAR)
RETURNS VOID
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    UPDATE users SET password_hash = p_new_hash WHERE id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- Grant execute to specific role
REVOKE ALL ON FUNCTION admin_reset_password FROM PUBLIC;
GRANT EXECUTE ON FUNCTION admin_reset_password TO app_admin;
```

## Performance Tips

### Use IMMUTABLE/STABLE/VOLATILE Correctly

```sql
-- IMMUTABLE: Same input = same output, no DB access
CREATE FUNCTION double(x INT) RETURNS INT AS $$
    SELECT x * 2;
$$ LANGUAGE sql IMMUTABLE;

-- STABLE: Same output within single query, reads DB
CREATE FUNCTION get_setting(key TEXT) RETURNS TEXT AS $$
    SELECT value FROM settings WHERE name = key;
$$ LANGUAGE sql STABLE;

-- VOLATILE (default): May return different values, modifies DB
CREATE FUNCTION log_access() RETURNS VOID AS $$
    INSERT INTO access_log (accessed_at) VALUES (NOW());
$$ LANGUAGE sql VOLATILE;
```

### Avoid Row-by-Row Processing

```sql
-- BAD: Slow cursor loop
CREATE FUNCTION update_all_prices_bad() RETURNS VOID AS $$
DECLARE
    rec RECORD;
BEGIN
    FOR rec IN SELECT id, price FROM products LOOP
        UPDATE products SET price = rec.price * 1.1 WHERE id = rec.id;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- GOOD: Single UPDATE statement
CREATE FUNCTION update_all_prices_good() RETURNS INT AS $$
    UPDATE products SET price = price * 1.1;
    SELECT COUNT(*) FROM products;
$$ LANGUAGE sql;
```

## Debugging

```sql
CREATE FUNCTION debug_example(p_value INT) RETURNS INT AS $$
BEGIN
    RAISE DEBUG 'Input value: %', p_value;
    RAISE NOTICE 'Processing value: %', p_value;
    RAISE WARNING 'Value might be too high: %', p_value;

    -- Log to table for persistent debugging
    INSERT INTO debug_log (message, created_at)
    VALUES (format('debug_example called with %s', p_value), NOW());

    RETURN p_value * 2;
END;
$$ LANGUAGE plpgsql;
```

## Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Functions | snake_case, verb prefix | `get_user`, `calculate_total` |
| Parameters | p_ prefix | `p_user_id`, `p_amount` |
| Local variables | v_ prefix | `v_count`, `v_result` |
| Cursors | cur_ prefix | `cur_orders` |

## Testing

```sql
-- Create test wrapper
CREATE FUNCTION test_get_user() RETURNS BOOLEAN AS $$
DECLARE
    v_result users;
BEGIN
    -- Setup
    INSERT INTO users (id, name) VALUES (999, 'Test User');

    -- Test
    SELECT * INTO v_result FROM get_user(999);

    -- Assert
    IF v_result.name != 'Test User' THEN
        RAISE EXCEPTION 'Test failed: expected Test User, got %', v_result.name;
    END IF;

    -- Cleanup
    DELETE FROM users WHERE id = 999;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;
```
