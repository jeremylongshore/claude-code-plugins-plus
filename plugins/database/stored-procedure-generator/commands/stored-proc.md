---
name: stored-proc
description: >
  Generate production-ready stored procedures and database functions
shortcut: stor
---
# Stored Procedure Generator

Generate production-ready stored procedures, functions, triggers, and custom database logic for complex business rules, performance optimization, and transaction safety across PostgreSQL, MySQL, and SQL Server.

## When to Use This Command

Use `/stored-proc` when you need to:
- Implement complex business logic close to the data
- Enforce data integrity constraints beyond foreign keys
- Optimize performance by reducing network round trips
- Implement atomic multi-step operations with transaction safety
- Create reusable database functions for reporting and analytics
- Build database triggers for audit logging and data synchronization

DON'T use this when:
- Business logic frequently changes (better in application layer)
- Logic requires external API calls or file I/O
- Team lacks database development expertise
- Migrating between database systems (vendor lock-in risk)
- Simple CRUD operations sufficient (ORMs handle this)

## Design Decisions

This command implements **comprehensive stored procedure generation** because:
- Encapsulates business logic at database level for data integrity
- Reduces network latency by executing multiple queries in single call
- Provides transaction safety for complex multi-step operations
- Enables code reuse across multiple applications
- Leverages database-specific optimizations (compiled execution plans)

**Alternative considered: Application-layer logic**
- More portable across database systems
- Easier to test and debug
- Better for frequently changing logic
- Recommended for API-heavy applications

**Alternative considered: Database views**
- Read-only, no data modification
- Cannot contain procedural logic
- Better query optimizer hints
- Recommended for read-heavy reporting

## Prerequisites

Before running this command:
1. Understanding of target database's procedural language (PL/pgSQL, MySQL, T-SQL)
2. Knowledge of business logic requirements and edge cases
3. Database permissions to create procedures/functions
4. Testing framework for stored procedure validation
5. Documentation of expected inputs/outputs and error handling

## Implementation Process

### Step 1: Analyze Business Logic Requirements
Define inputs, outputs, error conditions, and transaction boundaries.

### Step 2: Choose Procedure Type
Select function (returns value), procedure (performs action), or trigger (automated).

### Step 3: Implement Core Logic
Write procedural code with proper error handling and transaction management.

### Step 4: Add Validation and Security
Implement input validation, SQL injection prevention, and permission checks.

### Step 5: Test and Optimize
Test edge cases, measure performance, and optimize execution plans.

## Output Format

The command generates:
- `procedures/business_logic.sql` - Production-ready stored procedures
- `functions/calculations.sql` - Reusable database functions
- `triggers/audit_triggers.sql` - Automated data tracking triggers
- `tests/procedure_tests.sql` - Unit tests for validation
- `docs/procedure_api.md` - Documentation with usage examples

## Code Examples

### Example 1: PostgreSQL Complex Business Logic Function

```sql
-- Order processing with inventory management and audit logging
CREATE OR REPLACE FUNCTION process_order(
    p_customer_id INTEGER,
    p_order_items JSONB,
    p_shipping_address JSONB
) RETURNS TABLE (
    order_id INTEGER,
    total_amount DECIMAL(10,2),
    status VARCHAR(50),
    estimated_delivery DATE
) AS $$
DECLARE
    v_order_id INTEGER;
    v_total DECIMAL(10,2) := 0;
    v_item JSONB;
    v_product_id INTEGER;
    v_quantity INTEGER;
    v_price DECIMAL(10,2);
    v_available_stock INTEGER;
BEGIN
    -- Validate customer exists and is active
    IF NOT EXISTS (
        SELECT 1 FROM customers
        WHERE customer_id = p_customer_id AND status = 'active'
    ) THEN
        RAISE EXCEPTION 'Customer % not found or inactive', p_customer_id
            USING HINT = 'Check customer_id and status';
    END IF;

    -- Create order record
    INSERT INTO orders (customer_id, order_date, status, shipping_address)
    VALUES (
        p_customer_id,
        CURRENT_TIMESTAMP,
        'pending',
        p_shipping_address
    )
    RETURNING order_id INTO v_order_id;

    -- Process each order item
    FOR v_item IN SELECT * FROM jsonb_array_elements(p_order_items)
    LOOP
        v_product_id := (v_item->>'product_id')::INTEGER;
        v_quantity := (v_item->>'quantity')::INTEGER;

        -- Validate product exists
        SELECT price INTO v_price
        FROM products
        WHERE product_id = v_product_id AND active = true;

        IF v_price IS NULL THEN
            RAISE EXCEPTION 'Product % not found or inactive', v_product_id;
        END IF;

        -- Check inventory availability
        SELECT stock_quantity INTO v_available_stock
        FROM inventory
        WHERE product_id = v_product_id
        FOR UPDATE;  -- Lock row for update

        IF v_available_stock < v_quantity THEN
            RAISE EXCEPTION 'Insufficient stock for product %. Available: %, Requested: %',
                v_product_id, v_available_stock, v_quantity
                USING HINT = 'Reduce quantity or remove from order';
        END IF;

        -- Create order item
        INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal)
        VALUES (
            v_order_id,
            v_product_id,
            v_quantity,
            v_price,
            v_quantity * v_price
        );

        -- Update inventory
        UPDATE inventory
        SET stock_quantity = stock_quantity - v_quantity,
            last_updated = CURRENT_TIMESTAMP
        WHERE product_id = v_product_id;

        -- Add to total
        v_total := v_total + (v_quantity * v_price);
    END LOOP;

    -- Update order total
    UPDATE orders
    SET total_amount = v_total,
        status = 'confirmed'
    WHERE order_id = v_order_id;

    -- Calculate estimated delivery (3-5 business days)
    DECLARE
        v_delivery_date DATE;
    BEGIN
        v_delivery_date := CURRENT_DATE + INTERVAL '3 days';

        -- Skip weekends
        WHILE EXTRACT(DOW FROM v_delivery_date) IN (0, 6) LOOP
            v_delivery_date := v_delivery_date + INTERVAL '1 day';
        END LOOP;
    END;

    -- Log audit trail
    INSERT INTO order_audit_log (order_id, action, user_id, timestamp, details)
    VALUES (
        v_order_id,
        'order_created',
        CURRENT_USER,
        CURRENT_TIMESTAMP,
        jsonb_build_object(
            'customer_id', p_customer_id,
            'total_amount', v_total,
            'item_count', jsonb_array_length(p_order_items)
        )
    );

    -- Return order details
    RETURN QUERY
    SELECT
        v_order_id,
        v_total,
        'confirmed'::VARCHAR(50),
        v_delivery_date;

EXCEPTION
    WHEN OTHERS THEN
        -- Log error
        INSERT INTO error_log (function_name, error_message, error_detail, timestamp)
        VALUES (
            'process_order',
            SQLERRM,
            SQLSTATE,
            CURRENT_TIMESTAMP
        );

        -- Re-raise exception
        RAISE;
END;
$$ LANGUAGE plpgsql;

-- Usage example
SELECT * FROM process_order(
    123,  -- customer_id
    '[
        {"product_id": 456, "quantity": 2},
        {"product_id": 789, "quantity": 1}
    ]'::JSONB,
    '{"street": "123 Main St", "city": "Portland", "state": "OR", "zip": "97201"}'::JSONB
);
```

### Example 2: MySQL Stored Procedure with Cursors and Error Handling

```sql
-- User activity report generator with aggregations
DELIMITER $$

CREATE PROCEDURE generate_user_activity_report(
    IN p_start_date DATE,
    IN p_end_date DATE,
    IN p_user_type VARCHAR(50)
)
BEGIN
    DECLARE v_user_id INT;
    DECLARE v_username VARCHAR(255);
    DECLARE v_total_logins INT;
    DECLARE v_total_transactions DECIMAL(10,2);
    DECLARE v_done INT DEFAULT FALSE;

    -- Cursor to iterate over users
    DECLARE user_cursor CURSOR FOR
        SELECT user_id, username
        FROM users
        WHERE user_type = p_user_type
          AND created_at <= p_end_date
        ORDER BY username;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_done = TRUE;

    -- Create temporary results table
    DROP TEMPORARY TABLE IF EXISTS temp_user_report;
    CREATE TEMPORARY TABLE temp_user_report (
        user_id INT,
        username VARCHAR(255),
        total_logins INT,
        total_transactions DECIMAL(10,2),
        avg_transaction_value DECIMAL(10,2),
        last_activity_date DATETIME,
        activity_status VARCHAR(20)
    );

    -- Start transaction
    START TRANSACTION;

    -- Open cursor
    OPEN user_cursor;

    user_loop: LOOP
        FETCH user_cursor INTO v_user_id, v_username;

        IF v_done THEN
            LEAVE user_loop;
        END IF;

        -- Count login attempts
        SELECT COUNT(*) INTO v_total_logins
        FROM login_history
        WHERE user_id = v_user_id
          AND login_date BETWEEN p_start_date AND p_end_date
          AND status = 'success';

        -- Sum transaction amounts
        SELECT COALESCE(SUM(amount), 0) INTO v_total_transactions
        FROM transactions
        WHERE user_id = v_user_id
          AND transaction_date BETWEEN p_start_date AND p_end_date
          AND status = 'completed';

        -- Insert aggregated data
        INSERT INTO temp_user_report (
            user_id,
            username,
            total_logins,
            total_transactions,
            avg_transaction_value,
            last_activity_date,
            activity_status
        )
        SELECT
            v_user_id,
            v_username,
            v_total_logins,
            v_total_transactions,
            CASE
                WHEN v_total_logins > 0 THEN v_total_transactions / v_total_logins
                ELSE 0
            END,
            (SELECT MAX(activity_date)
             FROM (
                 SELECT MAX(login_date) AS activity_date FROM login_history WHERE user_id = v_user_id
                 UNION ALL
                 SELECT MAX(transaction_date) FROM transactions WHERE user_id = v_user_id
             ) activities),
            CASE
                WHEN v_total_logins >= 20 THEN 'highly_active'
                WHEN v_total_logins >= 5 THEN 'active'
                WHEN v_total_logins > 0 THEN 'low_activity'
                ELSE 'inactive'
            END;

    END LOOP;

    CLOSE user_cursor;

    -- Commit transaction
    COMMIT;

    -- Return final report
    SELECT
        user_id,
        username,
        total_logins,
        FORMAT(total_transactions, 2) AS total_transactions,
        FORMAT(avg_transaction_value, 2) AS avg_transaction_value,
        DATE_FORMAT(last_activity_date, '%Y-%m-%d %H:%i:%s') AS last_activity,
        activity_status
    FROM temp_user_report
    ORDER BY total_transactions DESC;

END$$

DELIMITER ;

-- Usage
CALL generate_user_activity_report('2024-01-01', '2024-12-31', 'premium');
```

### Example 3: Database Triggers for Audit Logging

```sql
-- PostgreSQL audit trigger for tracking all table changes
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log (
            table_name,
            operation,
            row_id,
            new_data,
            changed_by,
            changed_at
        ) VALUES (
            TG_TABLE_NAME,
            'INSERT',
            NEW.id,
            row_to_json(NEW),
            CURRENT_USER,
            CURRENT_TIMESTAMP
        );
        RETURN NEW;

    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_log (
            table_name,
            operation,
            row_id,
            old_data,
            new_data,
            changed_by,
            changed_at
        ) VALUES (
            TG_TABLE_NAME,
            'UPDATE',
            NEW.id,
            row_to_json(OLD),
            row_to_json(NEW),
            CURRENT_USER,
            CURRENT_TIMESTAMP
        );
        RETURN NEW;

    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log (
            table_name,
            operation,
            row_id,
            old_data,
            changed_by,
            changed_at
        ) VALUES (
            TG_TABLE_NAME,
            'DELETE',
            OLD.id,
            row_to_json(OLD),
            CURRENT_USER,
            CURRENT_TIMESTAMP
        );
        RETURN OLD;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Apply audit trigger to sensitive tables
CREATE TRIGGER users_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER orders_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON orders
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER transactions_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON transactions
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| "Function does not exist" | Missing or misspelled function name | Check function signature and schema |
| "Deadlock detected" | Concurrent transactions locking same rows | Use `FOR UPDATE SKIP LOCKED` or retry logic |
| "Stack depth limit exceeded" | Infinite recursion in function | Add recursion depth limit checks |
| "Out of shared memory" | Too many cursors or temp tables | Close cursors explicitly, limit temp table size |
| "Division by zero" | Unhandled edge case | Add NULL/zero checks before calculations |

## Configuration Options

**Function Types**
- **RETURNS TABLE**: Multi-row result sets
- **RETURNS SETOF**: Dynamic result sets
- **RETURNS VOID**: No return value (procedures)
- **RETURNS TRIGGER**: Trigger functions

**Volatility Categories**
- `IMMUTABLE`: Pure function, same inputs = same outputs
- `STABLE`: Results consistent within transaction
- `VOLATILE`: May change even with same inputs (default)

**Security Options**
- `SECURITY DEFINER`: Runs with creator's permissions
- `SECURITY INVOKER`: Runs with caller's permissions (default)

## Best Practices

DO:
- Use explicit parameter names (p_customer_id, not just id)
- Handle all possible error conditions with meaningful messages
- Use transactions for multi-step operations
- Close cursors explicitly to free resources
- Add input validation at function start
- Document parameters and return values

DON'T:
- Use `SELECT *` in production functions (specify columns)
- Perform network I/O or file operations in functions
- Create overly complex logic (split into multiple functions)
- Ignore SQL injection risks in dynamic SQL
- Forget to handle NULL values
- Use SECURITY DEFINER without careful permission checks

## Performance Considerations

- Functions add ~1-5ms overhead per call (acceptable for complex logic)
- Cached execution plans provide 10-50% speedup on repeated calls
- Triggers add overhead to every INSERT/UPDATE/DELETE (use sparingly)
- Use `FOR UPDATE SKIP LOCKED` to avoid blocking in high-concurrency scenarios
- Avoid cursors when set-based operations possible (cursors 10-100x slower)
- Index columns used in function WHERE clauses

## Related Commands

- `/database-migration-manager` - Deploy stored procedures across environments
- `/sql-query-optimizer` - Optimize queries within procedures
- `/database-transaction-monitor` - Monitor procedure execution and locks
- `/database-security-scanner` - Audit procedure permissions and SQL injection risks

## Version History

- v1.0.0 (2024-10): Initial implementation with PostgreSQL, MySQL, SQL Server support
- Planned v1.1.0: Add automated procedure testing framework and performance profiling
