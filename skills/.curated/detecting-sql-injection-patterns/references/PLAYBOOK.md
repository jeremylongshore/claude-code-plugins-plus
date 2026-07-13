# SQL-Injection Remediation Playbook

Each section is a copy-paste-ready before/after pair for the matched
pattern. The principle is universal: parameterized query with
placeholder, values passed as a separate argument.

## Python — sqlite3 / psycopg / SQLAlchemy

### Before

```python
def get_user(user_id):
    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
    return cursor.fetchone()
```

### After (psycopg)

```python
def get_user(user_id):
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    return cursor.fetchone()
```

### After (SQLAlchemy ORM)

```python
def get_user(user_id):
    return session.query(User).filter(User.id == user_id).first()
```

### Identifier interpolation (dynamic table / column) — allow-list

```python
SORTABLE = {"id", "name", "email", "created_at"}

def list_users(sort_by):
    if sort_by not in SORTABLE:
        raise ValueError(f"Invalid sort column: {sort_by}")
    # Now safe: sort_by is one of a finite known-safe set
    cursor.execute(f"SELECT * FROM users ORDER BY {sort_by}")
    return cursor.fetchall()
```

For runtime-dynamic identifiers (rare), use psycopg's typed
identifier helper:

```python
from psycopg.sql import SQL, Identifier

def query_table(table_name):
    if table_name not in ALLOWED_TABLES:
        raise ValueError()
    stmt = SQL("SELECT * FROM {}").format(Identifier(table_name))
    cursor.execute(stmt)
```

## Node.js — mysql2 / pg / sequelize / knex

### Before (mysql2)

```javascript
const result = await db.query(`SELECT * FROM users WHERE id = ${userId}`);
```

### After (mysql2)

```javascript
const [rows] = await db.query("SELECT * FROM users WHERE id = ?", [userId]);
```

### After (pg)

```javascript
const result = await db.query("SELECT * FROM users WHERE id = $1", [userId]);
```

### Sequelize before

```javascript
const users = await sequelize.query(
    `SELECT * FROM users WHERE name = '${name}'`,
    { type: QueryTypes.SELECT }
);
```

### Sequelize after

```javascript
const users = await sequelize.query(
    "SELECT * FROM users WHERE name = :name",
    {
        replacements: { name },
        type: QueryTypes.SELECT
    }
);
```

### Knex before

```javascript
const rows = await knex.raw(`SELECT * FROM users WHERE id = ${id}`);
```

### Knex after (use the query builder, not raw)

```javascript
const rows = await knex("users").where("id", id);
// Or with raw + binding:
const rows = await knex.raw("SELECT * FROM users WHERE id = ?", [id]);
```

## Ruby on Rails

### Before

```ruby
User.where("name = '#{params[:name]}'")
```

### After (hash form)

```ruby
User.where(name: params[:name])
```

### After (array form with `?`)

```ruby
User.where("name = ?", params[:name])
```

### For raw SQL

```ruby
User.find_by_sql([
    "SELECT * FROM users WHERE name = ? AND active = ?",
    params[:name], true
])
```

## Go (database/sql)

### Before

```go
rows, err := db.Query(fmt.Sprintf("SELECT * FROM users WHERE id = %d", id))
```

### After (MySQL / SQLite — `?` placeholders)

```go
rows, err := db.Query("SELECT * FROM users WHERE id = ?", id)
```

### After (PostgreSQL — `$1` placeholders)

```go
rows, err := db.Query("SELECT * FROM users WHERE id = $1", id)
```

### sqlx (named binds)

```go
type User struct {
    ID   int    `db:"id"`
    Name string `db:"name"`
}
var u User
err := db.Get(&u, "SELECT * FROM users WHERE id = $1", id)
```

## Java (JDBC)

### Before

```java
Statement stmt = conn.createStatement();
ResultSet rs = stmt.executeQuery("SELECT * FROM users WHERE id = " + id);
```

### After

```java
PreparedStatement stmt = conn.prepareStatement("SELECT * FROM users WHERE id = ?");
stmt.setInt(1, id);
ResultSet rs = stmt.executeQuery();
```

### Hibernate / JPA

```java
List<User> users = entityManager
    .createQuery("SELECT u FROM User u WHERE u.id = :id", User.class)
    .setParameter("id", id)
    .getResultList();
```

## PHP

### Before (legacy mysql_query)

```php
$result = mysql_query("SELECT * FROM users WHERE id = " . $id);
```

### After (PDO with named placeholders)

```php
$stmt = $pdo->prepare("SELECT * FROM users WHERE id = :id");
$stmt->execute(["id" => $id]);
$user = $stmt->fetch();
```

### After (mysqli with positional)

```php
$stmt = $mysqli->prepare("SELECT * FROM users WHERE id = ?");
$stmt->bind_param("i", $id);
$stmt->execute();
$result = $stmt->get_result();
```

## C# / .NET

### Before

```csharp
var cmd = new SqlCommand("SELECT * FROM users WHERE id = " + userId, conn);
```

### After

```csharp
var cmd = new SqlCommand("SELECT * FROM users WHERE id = @userId", conn);
cmd.Parameters.AddWithValue("@userId", userId);
```

### Entity Framework / EF Core

```csharp
var user = context.Users.FirstOrDefault(u => u.Id == userId);
// or with raw SQL + interpolated query (EF Core auto-parameterizes interpolation in FromSqlInterpolated):
var users = context.Users.FromSqlInterpolated(
    $"SELECT * FROM users WHERE id = {userId}"
).ToList();
```

Note: `FromSqlInterpolated` is one of the rare safe interpolation
APIs — EF Core treats interpolated values as parameters under the
hood.

## Pre-commit hook

`.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: scan-sqli
        name: Scan for SQL-injection patterns
        entry: python3 plugins/security/penetration-tester/skills/detecting-sql-injection-patterns/scripts/scan_sqli.py
        language: system
        args: ['--min-severity', 'high']
        pass_filenames: false
```

## CI integration

```yaml
- name: SQL-injection pattern scan
  run: |
    python3 plugins/security/penetration-tester/skills/detecting-sql-injection-patterns/scripts/scan_sqli.py \
        . --min-severity high --format json --output sqli-scan.json
- run: |
    if jq 'length > 0' sqli-scan.json | grep -q true; then
      echo "::error::SQL injection patterns detected"
      cat sqli-scan.json
      exit 1
    fi
```

## After remediation: dynamic-SQL hardening

If your application legitimately builds dynamic SQL (multi-tenant
routing, user-defined queries in a reporting tool), the
parameterization-only approach isn't sufficient. Add:

1. **Allow-list identifiers.** Maintain a fixed set of permitted
   table / column names. Validate against the set before
   interpolation.

2. **Use the database's identifier-quoting API.** Each driver
   exposes one (psycopg's `Identifier`, Sequelize's
   `sequelize.escape`, etc.).

3. **Lowest-privilege database role.** The application's DB user
   should only have the permissions the app needs. A SELECT-only
   query running under a role that can't INSERT/UPDATE/DELETE
   bounds the blast radius of any injection that does slip through.

4. **Database firewall (optional, high-value targets).** Tools
   like ProxySQL or PostgreSQL's `pg_audit` can log every query
   and alert on anomalies (queries containing `; DROP`, queries
   accessing unexpected tables).

## Verification after remediation

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/detecting-sql-injection-patterns/scripts/scan_sqli.py \
    /path/to/repo --min-severity medium
```

Expected: exit 0, zero medium-or-higher findings. Remaining LOW
findings (Django `.extra()` calls with verified allow-listed
identifiers) are acceptable trade-offs documented per-call.
