# Database Security Guidelines for Stored Procedures

## Principle of Least Privilege

Grant only the minimum permissions required:

```sql
-- PostgreSQL
GRANT EXECUTE ON FUNCTION get_user(INT) TO app_readonly;
REVOKE ALL ON FUNCTION admin_reset_password FROM PUBLIC;

-- MySQL
GRANT EXECUTE ON PROCEDURE mydb.GetUserById TO 'appuser'@'localhost';

-- SQL Server
GRANT EXECUTE ON dbo.GetUserById TO AppUser;
```

## SQL Injection Prevention

### Never Concatenate User Input

```sql
-- VULNERABLE
CREATE PROCEDURE bad_search(p_name VARCHAR(100))
AS $$
BEGIN
    EXECUTE 'SELECT * FROM users WHERE name = ''' || p_name || '''';
END;
$$ LANGUAGE plpgsql;

-- Input: '; DROP TABLE users; --
-- Results in: SELECT * FROM users WHERE name = ''; DROP TABLE users; --'
```

### Use Parameterized Queries

```sql
-- PostgreSQL (Safe)
CREATE FUNCTION safe_search(p_name VARCHAR)
RETURNS SETOF users AS $$
BEGIN
    RETURN QUERY SELECT * FROM users WHERE name = p_name;
END;
$$ LANGUAGE plpgsql;

-- MySQL (Safe with prepared statements)
DELIMITER //
CREATE PROCEDURE SafeSearch(IN p_name VARCHAR(100))
BEGIN
    SET @sql = 'SELECT * FROM users WHERE name = ?';
    SET @name = p_name;
    PREPARE stmt FROM @sql;
    EXECUTE stmt USING @name;
    DEALLOCATE PREPARE stmt;
END //
DELIMITER ;

-- SQL Server (Safe with sp_executesql)
CREATE PROCEDURE dbo.SafeSearch
    @Name NVARCHAR(100)
AS
BEGIN
    DECLARE @SQL NVARCHAR(200) = N'SELECT * FROM Users WHERE Name = @SearchName';
    EXEC sp_executesql @SQL, N'@SearchName NVARCHAR(100)', @Name;
END;
```

## Input Validation

Validate all inputs before use:

```sql
-- PostgreSQL
CREATE FUNCTION validate_email(p_email VARCHAR)
RETURNS BOOLEAN AS $$
BEGIN
    IF p_email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$' THEN
        RAISE EXCEPTION 'Invalid email format: %', p_email
            USING ERRCODE = 'P0001';
    END IF;
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- SQL Server
CREATE PROCEDURE dbo.ValidateAndInsertUser
    @Email NVARCHAR(255),
    @Age INT
AS
BEGIN
    -- Validate email format
    IF @Email NOT LIKE '%_@__%.__%'
        THROW 50001, 'Invalid email format', 1;

    -- Validate age range
    IF @Age < 0 OR @Age > 150
        THROW 50002, 'Age must be between 0 and 150', 1;

    INSERT INTO Users (Email, Age) VALUES (@Email, @Age);
END;
```

## Sensitive Data Protection

### Avoid Logging Sensitive Data

```sql
-- BAD: Password in error message
RAISE NOTICE 'Login failed for password: %', p_password;

-- GOOD: Mask sensitive data
RAISE NOTICE 'Login failed for user: %', p_username;
```

### Use Encryption for Sensitive Columns

```sql
-- PostgreSQL with pgcrypto
CREATE FUNCTION store_secret(p_user_id INT, p_secret TEXT, p_key TEXT)
RETURNS VOID AS $$
BEGIN
    UPDATE users
    SET encrypted_secret = pgp_sym_encrypt(p_secret, p_key)
    WHERE id = p_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

## SECURITY DEFINER vs SECURITY INVOKER

### SECURITY DEFINER (PostgreSQL)

Executes with function owner's privileges:

```sql
-- Allows controlled access to sensitive table
CREATE FUNCTION admin_get_user_count()
RETURNS BIGINT
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
    SELECT COUNT(*) FROM admin.sensitive_users;
$$ LANGUAGE sql;

-- Regular users can call this but not access admin.sensitive_users directly
GRANT EXECUTE ON FUNCTION admin_get_user_count() TO app_user;
```

### SQL SECURITY DEFINER (MySQL)

```sql
CREATE DEFINER='admin'@'localhost' PROCEDURE GetSensitiveData()
SQL SECURITY DEFINER
BEGIN
    SELECT * FROM sensitive_table;
END;
```

### EXECUTE AS (SQL Server)

```sql
CREATE PROCEDURE dbo.GetSensitiveData
WITH EXECUTE AS 'AdminUser'
AS
BEGIN
    SELECT * FROM dbo.SensitiveTable;
END;
```

## Audit Logging

Track who does what:

```sql
-- PostgreSQL audit trigger
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100),
    operation VARCHAR(10),
    old_data JSONB,
    new_data JSONB,
    changed_by VARCHAR(100) DEFAULT current_user,
    changed_at TIMESTAMP DEFAULT NOW()
);

CREATE FUNCTION audit_trigger_func()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_log (table_name, operation, old_data, new_data)
    VALUES (
        TG_TABLE_NAME,
        TG_OP,
        CASE WHEN TG_OP = 'DELETE' THEN row_to_json(OLD) ELSE NULL END,
        CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN row_to_json(NEW) ELSE NULL END
    );
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

## Rate Limiting

Prevent abuse:

```sql
-- PostgreSQL rate limiting
CREATE FUNCTION check_rate_limit(p_user_id INT, p_action VARCHAR)
RETURNS BOOLEAN AS $$
DECLARE
    v_count INT;
BEGIN
    SELECT COUNT(*) INTO v_count
    FROM rate_limit_log
    WHERE user_id = p_user_id
      AND action = p_action
      AND created_at > NOW() - INTERVAL '1 minute';

    IF v_count >= 100 THEN
        RAISE EXCEPTION 'Rate limit exceeded for action: %', p_action
            USING ERRCODE = 'P0429';
    END IF;

    INSERT INTO rate_limit_log (user_id, action) VALUES (p_user_id, p_action);
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;
```

## Connection Security

### Use SSL/TLS

```sql
-- PostgreSQL: Check SSL status
SELECT ssl, version FROM pg_stat_ssl WHERE pid = pg_backend_pid();

-- MySQL: Require SSL for user
CREATE USER 'secure_user'@'%' REQUIRE SSL;
```

### Limit Connection Sources

```sql
-- PostgreSQL: pg_hba.conf restricts connections
-- MySQL: User@Host pattern
CREATE USER 'appuser'@'192.168.1.%' IDENTIFIED BY 'password';
```

## Security Checklist

| Category | Check | Status |
|----------|-------|--------|
| Authentication | Procedures don't bypass auth | Required |
| Authorization | Least privilege enforced | Required |
| Input Validation | All inputs sanitized | Required |
| SQL Injection | No string concatenation | Required |
| Error Handling | No sensitive data in errors | Required |
| Logging | Audit trail enabled | Recommended |
| Encryption | Sensitive data encrypted | Recommended |
| Rate Limiting | Abuse prevention in place | Recommended |
