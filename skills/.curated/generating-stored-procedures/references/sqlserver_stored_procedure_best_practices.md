# SQL Server Stored Procedure Best Practices

## Basic Structure

```sql
CREATE PROCEDURE dbo.ProcedureName
    @Param1 INT,
    @Param2 VARCHAR(100) = NULL,  -- Optional with default
    @Result INT OUTPUT            -- Output parameter
AS
BEGIN
    SET NOCOUNT ON;

    -- Procedure body

    SET @Result = @@ROWCOUNT;
END;
GO
```

## Parameter Conventions

| Prefix | Use Case |
|--------|----------|
| @ | Required for all parameters |
| OUTPUT | Return values to caller |
| = value | Default value (makes param optional) |

```sql
CREATE PROCEDURE dbo.GetUserOrders
    @UserId INT,
    @StartDate DATE = NULL,
    @EndDate DATE = NULL,
    @TotalCount INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    -- Default date range if not provided
    SET @StartDate = ISNULL(@StartDate, DATEADD(MONTH, -1, GETDATE()));
    SET @EndDate = ISNULL(@EndDate, GETDATE());

    SELECT
        OrderId,
        OrderDate,
        TotalAmount
    FROM dbo.Orders
    WHERE UserId = @UserId
        AND OrderDate BETWEEN @StartDate AND @EndDate
    ORDER BY OrderDate DESC;

    SET @TotalCount = @@ROWCOUNT;
END;
GO

-- Calling with output parameter
DECLARE @Count INT;
EXEC dbo.GetUserOrders @UserId = 123, @TotalCount = @Count OUTPUT;
SELECT @Count AS OrderCount;
```

## Error Handling with TRY-CATCH

```sql
CREATE PROCEDURE dbo.TransferFunds
    @FromAccountId INT,
    @ToAccountId INT,
    @Amount DECIMAL(18,2)
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;  -- Auto-rollback on error

    BEGIN TRY
        BEGIN TRANSACTION;

        -- Validate sufficient funds
        IF NOT EXISTS (
            SELECT 1 FROM dbo.Accounts
            WHERE AccountId = @FromAccountId AND Balance >= @Amount
        )
        BEGIN
            RAISERROR('Insufficient funds', 16, 1);
        END

        -- Perform transfer
        UPDATE dbo.Accounts
        SET Balance = Balance - @Amount
        WHERE AccountId = @FromAccountId;

        UPDATE dbo.Accounts
        SET Balance = Balance + @Amount
        WHERE AccountId = @ToAccountId;

        -- Log transaction
        INSERT INTO dbo.TransactionLog (FromAccount, ToAccount, Amount, TransactionDate)
        VALUES (@FromAccountId, @ToAccountId, @Amount, GETDATE());

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        -- Re-throw error with details
        DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
        DECLARE @ErrorSeverity INT = ERROR_SEVERITY();
        DECLARE @ErrorState INT = ERROR_STATE();

        RAISERROR(@ErrorMessage, @ErrorSeverity, @ErrorState);
    END CATCH
END;
GO
```

## Custom Error Handling

```sql
CREATE PROCEDURE dbo.ValidateOrder
    @OrderId INT
AS
BEGIN
    SET NOCOUNT ON;

    -- Check order exists
    IF NOT EXISTS (SELECT 1 FROM dbo.Orders WHERE OrderId = @OrderId)
    BEGIN
        RAISERROR('Order %d not found', 16, 1, @OrderId);
        RETURN -1;
    END

    -- Check order status
    DECLARE @Status VARCHAR(20);
    SELECT @Status = Status FROM dbo.Orders WHERE OrderId = @OrderId;

    IF @Status = 'Cancelled'
    BEGIN
        RAISERROR('Order %d has been cancelled', 16, 1, @OrderId);
        RETURN -2;
    END

    -- Throw custom error (SQL 2012+)
    IF @Status = 'Shipped'
    BEGIN
        THROW 51000, 'Cannot modify shipped order', 1;
    END

    RETURN 0;  -- Success
END;
GO
```

## Table-Valued Parameters

```sql
-- Create table type
CREATE TYPE dbo.OrderItemType AS TABLE
(
    ProductId INT NOT NULL,
    Quantity INT NOT NULL,
    UnitPrice DECIMAL(10,2) NOT NULL
);
GO

-- Use in procedure
CREATE PROCEDURE dbo.CreateOrderWithItems
    @CustomerId INT,
    @Items dbo.OrderItemType READONLY
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @OrderId INT;

    BEGIN TRANSACTION;

    INSERT INTO dbo.Orders (CustomerId, OrderDate, Status)
    VALUES (@CustomerId, GETDATE(), 'Pending');

    SET @OrderId = SCOPE_IDENTITY();

    INSERT INTO dbo.OrderItems (OrderId, ProductId, Quantity, UnitPrice)
    SELECT @OrderId, ProductId, Quantity, UnitPrice
    FROM @Items;

    COMMIT TRANSACTION;

    SELECT @OrderId AS NewOrderId;
END;
GO

-- Calling with table parameter
DECLARE @OrderItems dbo.OrderItemType;
INSERT INTO @OrderItems VALUES (101, 2, 29.99), (102, 1, 49.99);
EXEC dbo.CreateOrderWithItems @CustomerId = 1, @Items = @OrderItems;
```

## Dynamic SQL (Safe)

```sql
CREATE PROCEDURE dbo.SearchProducts
    @SearchTerm NVARCHAR(100) = NULL,
    @CategoryId INT = NULL,
    @MinPrice DECIMAL(10,2) = NULL,
    @MaxPrice DECIMAL(10,2) = NULL,
    @SortColumn NVARCHAR(50) = 'ProductName',
    @SortDirection NVARCHAR(4) = 'ASC'
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @SQL NVARCHAR(MAX);
    DECLARE @ParamDef NVARCHAR(500);

    -- Validate sort column (prevent injection)
    IF @SortColumn NOT IN ('ProductName', 'Price', 'CategoryId', 'CreatedDate')
        SET @SortColumn = 'ProductName';

    IF @SortDirection NOT IN ('ASC', 'DESC')
        SET @SortDirection = 'ASC';

    SET @SQL = N'
        SELECT ProductId, ProductName, Price, CategoryId
        FROM dbo.Products
        WHERE 1=1';

    IF @SearchTerm IS NOT NULL
        SET @SQL += N' AND ProductName LIKE @SearchTerm + ''%''';

    IF @CategoryId IS NOT NULL
        SET @SQL += N' AND CategoryId = @CategoryId';

    IF @MinPrice IS NOT NULL
        SET @SQL += N' AND Price >= @MinPrice';

    IF @MaxPrice IS NOT NULL
        SET @SQL += N' AND Price <= @MaxPrice';

    SET @SQL += N' ORDER BY ' + QUOTENAME(@SortColumn) + N' ' + @SortDirection;

    SET @ParamDef = N'
        @SearchTerm NVARCHAR(100),
        @CategoryId INT,
        @MinPrice DECIMAL(10,2),
        @MaxPrice DECIMAL(10,2)';

    EXEC sp_executesql @SQL, @ParamDef,
        @SearchTerm, @CategoryId, @MinPrice, @MaxPrice;
END;
GO
```

## Performance Best Practices

### Use SET NOCOUNT ON

```sql
CREATE PROCEDURE dbo.FastProcedure
AS
BEGIN
    SET NOCOUNT ON;  -- Prevents "n rows affected" messages
    -- Your logic
END;
```

### Avoid SELECT *

```sql
-- BAD
SELECT * FROM dbo.Users WHERE UserId = @UserId;

-- GOOD
SELECT UserId, UserName, Email, CreatedDate
FROM dbo.Users
WHERE UserId = @UserId;
```

### Use Appropriate Indexes

```sql
-- Add index hint if needed (use sparingly)
SELECT *
FROM dbo.Orders WITH (INDEX(IX_Orders_CustomerId))
WHERE CustomerId = @CustomerId;
```

### Schema-Qualify Objects

```sql
-- BAD (requires schema resolution)
SELECT * FROM Users;

-- GOOD (direct access)
SELECT * FROM dbo.Users;
```

## Security

### Principle of Least Privilege

```sql
-- Grant EXECUTE only, not direct table access
GRANT EXECUTE ON dbo.GetUserOrders TO AppUser;
-- User can only access data through the procedure
```

### Ownership Chaining

```sql
-- Procedure and tables in same schema = automatic access
CREATE PROCEDURE dbo.SecureDataAccess
WITH EXECUTE AS OWNER  -- Run as procedure owner
AS
BEGIN
    SELECT * FROM dbo.SensitiveData;  -- Works even if caller can't access table
END;
```

## Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Procedure | PascalCase with verb | `GetUserById`, `CreateOrder` |
| Parameters | @PascalCase | `@UserId`, `@OrderDate` |
| Variables | @camelCase or @PascalCase | `@totalAmount`, `@RowCount` |
| Schema | Always specify | `dbo.ProcedureName` |

## Documentation

```sql
CREATE PROCEDURE dbo.ProcessDailyReport
    @ReportDate DATE,
    @IncludeDetails BIT = 0
AS
/*
Purpose: Generates daily summary report
Author: Jeremy Longshore
Created: 2025-01-15
Modified: 2025-01-18 - Added @IncludeDetails parameter

Parameters:
    @ReportDate - Date for the report (required)
    @IncludeDetails - Include line-item details (optional, default 0)

Returns:
    Result set with daily summary
    If @IncludeDetails = 1, second result set with details

Example:
    EXEC dbo.ProcessDailyReport @ReportDate = '2025-01-15', @IncludeDetails = 1;
*/
BEGIN
    SET NOCOUNT ON;
    -- Implementation
END;
GO
```
