# SQL-Injection Pattern Theory

## Why this class persists

SQL injection has been the canonical web vulnerability since the
late 1990s. Every framework's documentation warns about it. Every
ORM defaults to parameterized queries. Yet it remains a top-10
finding category year over year.

Three patterns generate ongoing introductions:

1. **The "just need a dynamic table name" trap.** ORMs handle
   parameterized VALUES well but typically can't parameterize
   IDENTIFIERS (table names, column names). An engineer
   string-builds the identifier portion, leaves the values
   parameterized, and convinces themselves it's safe. Then a
   feature request adds user-controlled column sorting and the
   "safe" pattern becomes the vulnerability.

2. **Legacy code that predates the ORM.** Pre-ORM Java / PHP /
   classic ASP codebases used raw JDBC / mysql_query() / Recordset
   APIs. Migrating to parameterized queries is mechanical but
   tedious. Many migrations stalled at 70-80% and the remaining
   raw queries are still in production.

3. **Misuse of "raw" escape hatches.** Every ORM has a raw()
   method (knex.raw, sequelize.query, ActiveRecord.execute,
   Django .extra()) for cases where the ORM's query builder
   doesn't cover something. The escape hatch is fine; concat
   into the escape hatch is the failure mode.

## How parameterization actually works

The vulnerable pattern looks like this (Python):

```python
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
```

The string is built by Python before being passed to the database
driver. The driver sees one giant string `SELECT * FROM users
WHERE id = 1 OR 1=1`. The injection is in the string before the
SQL parser even sees it. The parser parses the whole thing as a
single statement.

Parameterized version:

```python
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
```

The driver sends the query (with `%s` as a placeholder) AND the
parameters AS SEPARATE PROTOCOL FIELDS. The database parses the
query first, identifies the placeholder, then BINDS the parameter
into the parameter slot. The bound parameter is not parsed as
SQL — it's treated as a literal value, regardless of what
characters it contains.

Even an attacker sending `1 OR 1=1` as the `user_id` value gets
treated as the literal string `1 OR 1=1` looking for a row where
the ID column equals that exact string.

This is why parameterization works: the parser separates structure
from data. Concatenation eliminates the separation.

## Per-language patterns

### Python

**Unsafe:**

```python
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
cursor.execute("SELECT * FROM users WHERE id = " + str(user_id))
cursor.execute("SELECT * FROM users WHERE id = %s" % user_id)
cursor.execute("SELECT * FROM users WHERE id = {}".format(user_id))
```

**Safe:**

```python
# sqlite3
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))

# psycopg / psycopg2
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))

# SQLAlchemy Core
result = conn.execute(text("SELECT * FROM users WHERE id = :uid"), {"uid": user_id})

# SQLAlchemy ORM
session.query(User).filter(User.id == user_id).all()
```

### Node.js

**Unsafe:**

```javascript
db.query(`SELECT * FROM users WHERE id = ${userId}`)
db.query("SELECT * FROM users WHERE id = " + userId)
sequelize.query(`SELECT * FROM users WHERE name = '${name}'`)
```

**Safe:**

```javascript
// mysql2
db.query("SELECT * FROM users WHERE id = ?", [userId])

// pg
db.query("SELECT * FROM users WHERE id = $1", [userId])

// sequelize with replacements
sequelize.query(
    "SELECT * FROM users WHERE name = :name",
    { replacements: { name }, type: QueryTypes.SELECT }
)

// knex (parameterized by default)
knex("users").where("id", userId)
```

### Ruby (Rails)

**Unsafe:**

```ruby
User.where("name = '#{name}'")
ActiveRecord::Base.connection.execute("SELECT * FROM users WHERE id = #{id}")
```

**Safe:**

```ruby
# Hash conditions
User.where(name: name)

# Array conditions with ?
User.where("name = ?", name)

# Or for raw SQL:
User.find_by_sql(["SELECT * FROM users WHERE name = ?", name])
```

### Go

**Unsafe:**

```go
db.Query(fmt.Sprintf("SELECT * FROM users WHERE id = %d", id))
db.Query("SELECT * FROM users WHERE id = " + strconv.Itoa(id))
```

**Safe:**

```go
db.Query("SELECT * FROM users WHERE id = ?", id)
// PostgreSQL driver uses $1, $2, ...:
db.Query("SELECT * FROM users WHERE id = $1", id)
```

### Java

**Unsafe:**

```java
Statement stmt = conn.createStatement();
stmt.executeQuery("SELECT * FROM users WHERE id = " + id);
```

**Safe:**

```java
PreparedStatement stmt = conn.prepareStatement("SELECT * FROM users WHERE id = ?");
stmt.setInt(1, id);
ResultSet rs = stmt.executeQuery();
```

### PHP

**Unsafe:**

```php
mysqli_query($conn, "SELECT * FROM users WHERE id = $id");
mysql_query("SELECT * FROM users WHERE id = " . $id);
```

**Safe (PDO):**

```php
$stmt = $pdo->prepare("SELECT * FROM users WHERE id = :id");
$stmt->execute(["id" => $id]);
```

**Safe (mysqli):**

```php
$stmt = $mysqli->prepare("SELECT * FROM users WHERE id = ?");
$stmt->bind_param("i", $id);
$stmt->execute();
```

## The identifier-interpolation problem

ORMs parameterize VALUES, not IDENTIFIERS. If you need to
dynamically choose a table or column at runtime (e.g., for
multi-tenant routing or user-controlled sort columns), you can't
use parameter binding for it.

The right pattern is allow-list validation:

```python
# Allow-list known columns
SORTABLE_COLUMNS = {"id", "name", "created_at", "updated_at"}
sort_col = request.args.get("sort_by")
if sort_col not in SORTABLE_COLUMNS:
    raise ValueError("Invalid sort column")
cursor.execute(f"SELECT * FROM users ORDER BY {sort_col}", ())
```

The interpolated `sort_col` is now constrained to a finite set of
known-safe values. The f-string is fine because the only possible
values are pre-validated.

For dynamic table names (rare; usually indicates a schema-design
issue), apply the same allow-list pattern PLUS quote the identifier:

```python
# Python with psycopg
from psycopg.sql import SQL, Identifier
cursor.execute(SQL("SELECT * FROM {}").format(Identifier(table_name)))
```

`Identifier()` applies the database's identifier quoting rules,
preventing the table-name from being parsed as SQL.

## Why the scanner can't be perfect

Static-pattern matching has irreducible false positives:

- A literal-only f-string `f"SELECT * FROM users WHERE id = 1"`
  matches the pattern but has no injection vector (the interpolated
  value is `1`, a literal).
- A pre-validated value `f"SELECT ... ORDER BY {col}"` where `col`
  is from a known allow-list looks identical to the vulnerable
  pattern but is safe.

A full taint-tracking AST analyzer (Semgrep, CodeQL, Bandit with
`-r`) would catch these. This skill is a regex pass — high
recall, moderate precision. Treat findings as "verify each by
reading the code," not "auto-merge a fix."

## Primary sources

- [CWE-89 SQL Injection](https://cwe.mitre.org/data/definitions/89.html)
- [OWASP A03:2021 Injection](https://owasp.org/Top10/A03_2021-Injection/)
- [OWASP SQL Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)
- [Bobby Tables — A guide to preventing SQL injection](https://bobby-tables.com/)
- Psycopg parameterized-query docs
- ActiveRecord query interface documentation
