---
description: Generate optimized SQL queries from natural language descriptions
shortcut: sqb
category: database
difficulty: beginner
estimated_time: 2-3 minutes
---

# SQL Query Builder

Generates optimized SQL queries from natural language descriptions, supporting SELECT, INSERT, UPDATE, DELETE with JOINs, indexes, and best practices.

## What This Command Does

**Generated Queries:**
-  SELECT queries with JOINs
-  INSERT, UPDATE, DELETE operations
-  Aggregations and GROUP BY
-  Subqueries and CTEs
-  Indexes and optimization tips
-  PostgreSQL, MySQL, SQLite syntax

**Output:** Production-ready SQL queries

**Time:** 2-3 minutes

---

## Usage

```bash
# Generate query from description
/sql-query-builder "Get all users with their posts"

# Shortcut
/sqb "Find top 10 products by sales"

# Complex query
/sqb "Get users who have made purchases in last 30 days, grouped by country"

# Specific database
/sqb "List orders with customer info" --database postgresql
```

---

## Example Output

**Input:**
```
/sqb "Get all blog posts with author info and comment count, ordered by recent"
```

**Generated SQL:**

```sql
-- Query: Get all blog posts with author info and comment count
-- Database: PostgreSQL
-- Optimized for performance with proper indexes

-- Main query
SELECT
  p.id,
  p.title,
  p.slug,
  p.content,
  p.published,
  p.created_at,
  p.updated_at,
  -- Author information
  u.id AS author_id,
  u.name AS author_name,
  u.email AS author_email,
  -- Comment count (calculated)
  COUNT(c.id) AS comment_count
FROM posts p
INNER JOIN users u ON p.author_id = u.id
LEFT JOIN comments c ON p.id = c.post_id
WHERE p.published = true
GROUP BY
  p.id,
  p.title,
  p.slug,
  p.content,
  p.published,
  p.created_at,
  p.updated_at,
  u.id,
  u.name,
  u.email
ORDER BY p.created_at DESC
LIMIT 20 OFFSET 0;

-- Recommended indexes for optimal performance
CREATE INDEX IF NOT EXISTS idx_posts_published_created ON posts(published, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_posts_author_id ON posts(author_id);
CREATE INDEX IF NOT EXISTS idx_comments_post_id ON comments(post_id);

-- Explain plan (run to verify performance)
EXPLAIN ANALYZE
SELECT /* ... query above ... */;
```

---

## Query Examples

### **1. Simple SELECT**

**Request:** "Get all active users"

```sql
SELECT
  id,
  email,
  name,
  created_at
FROM users
WHERE active = true
ORDER BY created_at DESC;

-- Index recommendation
CREATE INDEX idx_users_active ON users(active, created_at DESC);
```

### **2. JOIN Queries**

**Request:** "Get orders with customer and product information"

```sql
SELECT
  o.id AS order_id,
  o.order_date,
  o.total,
  o.status,
  -- Customer info
  c.id AS customer_id,
  c.name AS customer_name,
  c.email AS customer_email,
  -- Order items
  oi.quantity,
  oi.price AS unit_price,
  -- Product info
  p.id AS product_id,
  p.name AS product_name
FROM orders o
INNER JOIN customers c ON o.customer_id = c.id
INNER JOIN order_items oi ON o.id = oi.order_id
INNER JOIN products p ON oi.product_id = p.id
WHERE o.created_at >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY o.created_at DESC;

-- Indexes
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_created_at ON orders(created_at DESC);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);
```

### **3. Aggregations**

**Request:** "Get total sales by product category"

```sql
SELECT
  c.name AS category,
  COUNT(DISTINCT o.id) AS order_count,
  SUM(oi.quantity) AS units_sold,
  SUM(oi.quantity * oi.price) AS total_revenue,
  AVG(oi.price) AS avg_price
FROM categories c
INNER JOIN products p ON c.id = p.category_id
INNER JOIN order_items oi ON p.id = oi.product_id
INNER JOIN orders o ON oi.order_id = o.id
WHERE o.status = 'completed'
  AND o.created_at >= CURRENT_DATE - INTERVAL '1 year'
GROUP BY c.id, c.name
HAVING SUM(oi.quantity * oi.price) > 1000
ORDER BY total_revenue DESC;
```

### **4. Subqueries**

**Request:** "Get users who have never made a purchase"

```sql
SELECT
  u.id,
  u.email,
  u.name,
  u.created_at
FROM users u
WHERE NOT EXISTS (
  SELECT 1
  FROM orders o
  WHERE o.customer_id = u.id
)
ORDER BY u.created_at DESC;

-- Alternative using LEFT JOIN (often faster)
SELECT
  u.id,
  u.email,
  u.name,
  u.created_at
FROM users u
LEFT JOIN orders o ON u.id = o.customer_id
WHERE o.id IS NULL
ORDER BY u.created_at DESC;
```

### **5. Common Table Expressions (CTEs)**

**Request:** "Get top customers by purchase amount with their order history"

```sql
WITH customer_totals AS (
  SELECT
    c.id,
    c.name,
    c.email,
    COUNT(o.id) AS order_count,
    SUM(o.total) AS total_spent
  FROM customers c
  INNER JOIN orders o ON c.id = o.customer_id
  WHERE o.status = 'completed'
  GROUP BY c.id, c.name, c.email
  HAVING SUM(o.total) > 500
)
SELECT
  ct.*,
  o.id AS order_id,
  o.order_date,
  o.total AS order_total
FROM customer_totals ct
INNER JOIN orders o ON ct.id = o.customer_id
ORDER BY ct.total_spent DESC, o.order_date DESC;
```

### **6. Window Functions**

**Request:** "Rank products by sales within each category"

```sql
SELECT
  p.id,
  p.name AS product_name,
  c.name AS category_name,
  SUM(oi.quantity * oi.price) AS total_sales,
  RANK() OVER (
    PARTITION BY p.category_id
    ORDER BY SUM(oi.quantity * oi.price) DESC
  ) AS rank_in_category
FROM products p
INNER JOIN categories c ON p.category_id = c.id
INNER JOIN order_items oi ON p.id = oi.product_id
INNER JOIN orders o ON oi.order_id = o.id
WHERE o.status = 'completed'
GROUP BY p.id, p.name, p.category_id, c.name
ORDER BY c.name, rank_in_category;
```

### **7. INSERT Queries**

**Request:** "Insert new user with validation"

```sql
-- Insert single user
INSERT INTO users (id, email, name, password, created_at, updated_at)
VALUES (
  gen_random_uuid(),
  '[email protected]',
  'John Doe',
  'hashed_password_here',
  CURRENT_TIMESTAMP,
  CURRENT_TIMESTAMP
)
ON CONFLICT (email) DO NOTHING
RETURNING id, email, name, created_at;

-- Bulk insert
INSERT INTO users (id, email, name, password, created_at, updated_at)
VALUES
  (gen_random_uuid(), '[email protected]', 'User 1', 'hash1', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (gen_random_uuid(), '[email protected]', 'User 2', 'hash2', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (gen_random_uuid(), '[email protected]', 'User 3', 'hash3', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT (email) DO NOTHING;
```

### **8. UPDATE Queries**

**Request:** "Update product stock after order"

```sql
-- Single update
UPDATE products
SET
  stock = stock - 5,
  updated_at = CURRENT_TIMESTAMP
WHERE id = 'product-uuid-here'
  AND stock >= 5 -- Safety check
RETURNING id, name, stock;

-- Batch update with JOIN
UPDATE products p
SET
  stock = p.stock - oi.quantity,
  updated_at = CURRENT_TIMESTAMP
FROM order_items oi
WHERE p.id = oi.product_id
  AND oi.order_id = 'order-uuid-here'
  AND p.stock >= oi.quantity;
```

### **9. DELETE Queries**

**Request:** "Delete old inactive users"

```sql
-- Soft delete (recommended)
UPDATE users
SET
  deleted_at = CURRENT_TIMESTAMP,
  updated_at = CURRENT_TIMESTAMP
WHERE active = false
  AND last_login_at < CURRENT_DATE - INTERVAL '1 year'
RETURNING id, email;

-- Hard delete (with safety checks)
DELETE FROM users
WHERE active = false
  AND last_login_at < CURRENT_DATE - INTERVAL '2 years'
  AND id NOT IN (
    SELECT DISTINCT customer_id FROM orders
  );
```

### **10. Full-Text Search**

**Request:** "Search blog posts by keyword"

**PostgreSQL:**
```sql
-- Create text search index
CREATE INDEX idx_posts_search ON posts
USING GIN (to_tsvector('english', title || ' ' || content));

-- Search query
SELECT
  id,
  title,
  content,
  ts_rank(
    to_tsvector('english', title || ' ' || content),
    plainto_tsquery('english', 'search keywords')
  ) AS relevance
FROM posts
WHERE to_tsvector('english', title || ' ' || content) @@
      plainto_tsquery('english', 'search keywords')
  AND published = true
ORDER BY relevance DESC, created_at DESC
LIMIT 20;
```

**MySQL:**
```sql
-- Create fulltext index
CREATE FULLTEXT INDEX idx_posts_search ON posts(title, content);

-- Search query
SELECT
  id,
  title,
  content,
  MATCH(title, content) AGAINST('search keywords' IN NATURAL LANGUAGE MODE) AS relevance
FROM posts
WHERE MATCH(title, content) AGAINST('search keywords' IN NATURAL LANGUAGE MODE)
  AND published = true
ORDER BY relevance DESC, created_at DESC
LIMIT 20;
```

---

## Optimization Tips

**1. Use Indexes Wisely:**
```sql
--  GOOD: Index foreign keys
CREATE INDEX idx_posts_author_id ON posts(author_id);

--  GOOD: Index columns in WHERE clauses
CREATE INDEX idx_posts_published ON posts(published, created_at DESC);

--  GOOD: Partial index for specific queries
CREATE INDEX idx_active_users ON users(email) WHERE active = true;
```

**2. Avoid SELECT *:**
```sql
--  BAD
SELECT * FROM users;

--  GOOD
SELECT id, email, name FROM users;
```

**3. Use LIMIT:**
```sql
--  BAD (fetches all rows)
SELECT * FROM posts ORDER BY created_at DESC;

--  GOOD (pagination)
SELECT * FROM posts ORDER BY created_at DESC LIMIT 20 OFFSET 0;
```

**4. Optimize JOINs:**
```sql
-- Use INNER JOIN when possible (faster than LEFT JOIN)
-- Use EXISTS instead of IN for large datasets

--  BAD
SELECT * FROM users WHERE id IN (SELECT user_id FROM orders);

--  GOOD
SELECT u.* FROM users u WHERE EXISTS (
  SELECT 1 FROM orders o WHERE o.user_id = u.id
);
```

---

## Database-Specific Syntax

**PostgreSQL:**
- `gen_random_uuid()` for UUIDs
- `INTERVAL` for date math
- `RETURNING` clause
- Full-text search with `tsvector`

**MySQL:**
- `UUID()` for UUIDs
- `DATE_SUB()` for date math
- FULLTEXT indexes for search

**SQLite:**
- `hex(randomblob(16))` for UUIDs
- `datetime()` for dates
- Limited JOIN types

---

## Related Commands

- `/prisma-schema-gen` - Generate Prisma schemas
- Database Designer (agent) - Schema design review

---

**Query smarter. Optimize faster. Scale confidently.** 
