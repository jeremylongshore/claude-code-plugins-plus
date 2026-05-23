## Implementation Guide

1. Identify input surfaces and data flows into database queries.
2. Review query construction and parameterization patterns.
3. Flag injection vectors and document impact.
4. Recommend fixes (parameterized queries, ORM patterns, validation) and tests.

### 1. Code Discovery Phase

Locate database interaction code:

- SQL query construction
- ORM usage (ActiveRecord, Hibernate, SQLAlchemy, etc.)
- Stored procedure calls
- Dynamic query builders
- User input handling for database operations

**Common patterns to search**:

- Direct SQL: `SELECT`, `INSERT`, `UPDATE`, `DELETE` statements
- String concatenation with user input
- ORM raw query methods
- Template-based query construction

### 2. Vulnerability Pattern Detection

**Critical SQL Injection Patterns**:

**String Concatenation (Highly Vulnerable)**:

```python
# INSECURE: Direct concatenation

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
