# MySQL Stored Procedure Best Practices

## Basic Structure

```sql
DELIMITER //
CREATE PROCEDURE procedure_name(
    IN param1 INT,
    OUT param2 VARCHAR(255),
    INOUT param3 DECIMAL(10,2)
)
BEGIN
    -- Procedure body
END //
DELIMITER ;
```

## Parameter Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| IN | Input only (default) | Pass values to procedure |
| OUT | Output only | Return values from procedure |
| INOUT | Both input and output | Modify and return value |

```sql
DELIMITER //
CREATE PROCEDURE calculate_order_total(
    IN p_order_id INT,
    OUT p_subtotal DECIMAL(10,2),
    OUT p_tax DECIMAL(10,2),
    OUT p_total DECIMAL(10,2)
)
BEGIN
    SELECT SUM(quantity * unit_price)
    INTO p_subtotal
    FROM order_items
    WHERE order_id = p_order_id;

    SET p_tax = p_subtotal * 0.08;
    SET p_total = p_subtotal + p_tax;
END //
DELIMITER ;

-- Call procedure
CALL calculate_order_total(123, @subtotal, @tax, @total);
SELECT @subtotal, @tax, @total;
```

## Variables and Data Types

```sql
DELIMITER //
CREATE PROCEDURE variable_examples()
BEGIN
    -- Variable declaration
    DECLARE v_count INT DEFAULT 0;
    DECLARE v_name VARCHAR(100);
    DECLARE v_created_at DATETIME DEFAULT NOW();
    DECLARE v_is_active BOOLEAN DEFAULT TRUE;

    -- Assignment
    SET v_count = v_count + 1;
    SELECT name INTO v_name FROM users WHERE id = 1;

    -- Multiple assignment
    SELECT COUNT(*), MAX(name)
    INTO v_count, v_name
    FROM users;
END //
DELIMITER ;
```

## Control Flow

### IF-THEN-ELSE

```sql
DELIMITER //
CREATE PROCEDURE get_discount(
    IN p_customer_type VARCHAR(20),
    OUT p_discount DECIMAL(5,2)
)
BEGIN
    IF p_customer_type = 'premium' THEN
        SET p_discount = 0.20;
    ELSEIF p_customer_type = 'regular' THEN
        SET p_discount = 0.10;
    ELSE
        SET p_discount = 0.00;
    END IF;
END //
DELIMITER ;
```

### CASE Statement

```sql
DELIMITER //
CREATE PROCEDURE get_status_label(
    IN p_status_code INT,
    OUT p_label VARCHAR(50)
)
BEGIN
    SET p_label = CASE p_status_code
        WHEN 1 THEN 'Pending'
        WHEN 2 THEN 'Processing'
        WHEN 3 THEN 'Shipped'
        WHEN 4 THEN 'Delivered'
        ELSE 'Unknown'
    END;
END //
DELIMITER ;
```

### Loops

```sql
DELIMITER //
CREATE PROCEDURE process_batch()
BEGIN
    DECLARE v_done BOOLEAN DEFAULT FALSE;
    DECLARE v_id INT;
    DECLARE cur CURSOR FOR SELECT id FROM pending_items;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_done = TRUE;

    OPEN cur;

    read_loop: LOOP
        FETCH cur INTO v_id;
        IF v_done THEN
            LEAVE read_loop;
        END IF;

        -- Process each item
        UPDATE pending_items SET status = 'processed' WHERE id = v_id;
    END LOOP;

    CLOSE cur;
END //
DELIMITER ;
```

## Error Handling

```sql
DELIMITER //
CREATE PROCEDURE safe_transfer(
    IN p_from_account INT,
    IN p_to_account INT,
    IN p_amount DECIMAL(15,2)
)
BEGIN
    -- Declare handler for any SQL exception
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SELECT 'Transaction failed' AS message;
    END;

    -- Declare handler for specific error
    DECLARE EXIT HANDLER FOR 1062
    BEGIN
        SELECT 'Duplicate entry error' AS message;
    END;

    START TRANSACTION;

    -- Check sufficient funds
    IF (SELECT balance FROM accounts WHERE id = p_from_account) < p_amount THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Insufficient funds';
    END IF;

    UPDATE accounts SET balance = balance - p_amount WHERE id = p_from_account;
    UPDATE accounts SET balance = balance + p_amount WHERE id = p_to_account;

    COMMIT;
    SELECT 'Transfer successful' AS message;
END //
DELIMITER ;
```

## Custom Errors with SIGNAL

```sql
DELIMITER //
CREATE PROCEDURE validate_age(IN p_age INT)
BEGIN
    IF p_age < 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Age cannot be negative',
                MYSQL_ERRNO = 1001;
    ELSEIF p_age > 150 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Age seems unrealistic',
                MYSQL_ERRNO = 1002;
    END IF;

    SELECT 'Age is valid' AS result;
END //
DELIMITER ;
```

## Transaction Management

```sql
DELIMITER //
CREATE PROCEDURE create_order_with_items(
    IN p_customer_id INT,
    IN p_items JSON
)
BEGIN
    DECLARE v_order_id INT;
    DECLARE v_item JSON;
    DECLARE v_i INT DEFAULT 0;
    DECLARE v_count INT;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    -- Create order
    INSERT INTO orders (customer_id, created_at)
    VALUES (p_customer_id, NOW());
    SET v_order_id = LAST_INSERT_ID();

    -- Add items
    SET v_count = JSON_LENGTH(p_items);
    WHILE v_i < v_count DO
        SET v_item = JSON_EXTRACT(p_items, CONCAT('$[', v_i, ']'));

        INSERT INTO order_items (order_id, product_id, quantity, unit_price)
        VALUES (
            v_order_id,
            JSON_EXTRACT(v_item, '$.product_id'),
            JSON_EXTRACT(v_item, '$.quantity'),
            JSON_EXTRACT(v_item, '$.price')
        );

        SET v_i = v_i + 1;
    END WHILE;

    COMMIT;
    SELECT v_order_id AS order_id;
END //
DELIMITER ;
```

## Security Best Practices

### Use SQL SECURITY

```sql
-- DEFINER: Runs with creator's privileges (default)
CREATE DEFINER='admin'@'localhost' PROCEDURE admin_only_proc()
SQL SECURITY DEFINER
BEGIN
    -- Can access tables admin has access to
END;

-- INVOKER: Runs with caller's privileges
CREATE PROCEDURE user_proc()
SQL SECURITY INVOKER
BEGIN
    -- Limited to caller's permissions
END;
```

### Prevent SQL Injection

```sql
-- BAD: Dynamic SQL vulnerable to injection
CREATE PROCEDURE bad_search(IN p_name VARCHAR(100))
BEGIN
    SET @sql = CONCAT('SELECT * FROM users WHERE name = ''', p_name, '''');
    PREPARE stmt FROM @sql;
    EXECUTE stmt;
END;

-- GOOD: Use parameterized prepared statements
CREATE PROCEDURE good_search(IN p_name VARCHAR(100))
BEGIN
    SET @sql = 'SELECT * FROM users WHERE name = ?';
    SET @name = p_name;
    PREPARE stmt FROM @sql;
    EXECUTE stmt USING @name;
    DEALLOCATE PREPARE stmt;
END;
```

## Performance Tips

1. **Avoid SELECT * in procedures** - Specify columns
2. **Use appropriate indexes** - Ensure WHERE clauses are indexed
3. **Limit result sets** - Use LIMIT when possible
4. **Avoid cursors for bulk operations** - Use set-based operations
5. **Use EXPLAIN** - Analyze query plans within procedures

```sql
-- Set-based (fast)
UPDATE products SET price = price * 1.1 WHERE category = 'electronics';

-- Cursor-based (slow)
-- Avoid unless absolutely necessary
```

## Debugging

```sql
DELIMITER //
CREATE PROCEDURE debug_proc()
BEGIN
    -- Create debug table if needed
    CREATE TEMPORARY TABLE IF NOT EXISTS debug_log (
        id INT AUTO_INCREMENT PRIMARY KEY,
        message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    INSERT INTO debug_log (message) VALUES ('Procedure started');

    -- Your logic here

    INSERT INTO debug_log (message) VALUES ('Procedure completed');

    SELECT * FROM debug_log;
END //
DELIMITER ;
```
