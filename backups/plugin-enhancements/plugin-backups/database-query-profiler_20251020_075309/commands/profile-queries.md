---
description: Profile and optimize database queries
---

# Database Query Profiler

Analyze database queries for performance issues and optimization opportunities.

## Analysis Areas

1. **N+1 Queries**: Detect and fix N+1 query patterns
2. **Missing Indexes**: Identify columns needing indexes
3. **Full Table Scans**: Queries scanning entire tables
4. **Inefficient Joins**: Complex or unnecessary joins
5. **Large Result Sets**: Queries returning excessive data
6. **Query Complexity**: Overly complex SQL queries
7. **Connection Pooling**: Database connection management

## Process

1. Locate all database queries in codebase
2. Analyze query patterns and ORM usage
3. Identify N+1 query problems
4. Check for proper indexing
5. Evaluate query complexity
6. Generate optimization recommendations

## Output

Provide detailed report with:
- Query inventory with execution patterns
- N+1 query identification with locations
- Index recommendations with CREATE INDEX statements
- Query optimization examples (before/after)
- Connection pooling configuration
- Estimated performance improvements
