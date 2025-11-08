# SQL Injection Detector Plugin

Comprehensive SQL injection vulnerability detection with pattern matching, context analysis, and exploit verification.

## Features

- **Multi-Database Support** - MySQL, PostgreSQL, SQL Server, Oracle, SQLite
- **Context-Aware Analysis** - Understand query context and structure
- **ORM Detection** - Identify unsafe ORM usage
- **Blind SQLi Detection** - Time-based and boolean-based
- **Exploitation Verification** - Safe proof-of-concept testing
- **Remediation Guidance** - Parameterized query examples

## Installation

```bash
/plugin install sql-injection-detector@claude-code-plugins-plus
```

## Usage

```bash
/detect-sqli
# Or shortcut
/sqli
```

## Detection Methods

### 1. Code Pattern Analysis
Scans for dangerous patterns:
- String concatenation in queries
- Unsafe variable interpolation
- Dynamic query construction
- Missing parameterization

### 2. Input Vector Analysis
Checks all input sources:
- GET/POST parameters
- HTTP headers
- Cookies
- JSON/XML payloads
- GraphQL variables

### 3. Context Analysis
Understands query context:
- WHERE clause injection
- ORDER BY injection
- LIMIT injection
- UPDATE/DELETE injection
- INSERT injection
- UNION-based injection

## Common Vulnerabilities

### Classic SQL Injection
```javascript
// VULNERABLE
const query = `SELECT * FROM users WHERE username='${username}'`;
db.query(query);

// Exploit
username = "admin' OR '1'='1' --"
// Results in: SELECT * FROM users WHERE username='admin' OR '1'='1' --'

// SECURE
const query = 'SELECT * FROM users WHERE username = ?';
db.query(query, [username]);
```

### Second-Order SQL Injection
```javascript
// VULNERABLE
app.post('/register', (req, res) => {
    const username = req.body.username;
    db.query(`INSERT INTO users (username) VALUES ('${username}')`);
});

app.get('/profile', (req, res) => {
    const username = req.session.username;
    // Unsafe use of previously stored data
    db.query(`SELECT * FROM profiles WHERE username='${username}'`);
});

// Attack
username = "admin' OR '1'='1' --"
// Stored in database during registration
// Exploited when profile is loaded

// SECURE
Use parameterized queries for all database interactions
```

### ORM Misuse
```javascript
// VULNERABLE (Sequelize)
User.findAll({
    where: {
        username: req.query.username,
        $or: req.query.filter // User-controlled raw query
    }
});

// SECURE
User.findAll({
    where: {
        username: req.query.username
    }
});
```

### Blind SQL Injection
```javascript
// VULNERABLE
const query = `SELECT * FROM products WHERE id=${id}`;
const result = db.query(query);
// No error message, but behavior changes

// Time-based blind SQLi exploit
id = "1 AND SLEEP(5)--"

// SECURE
const query = 'SELECT * FROM products WHERE id = ?';
db.query(query, [id]);
```

## Example Report

```
SQL INJECTION SCAN REPORT
=========================
Files Scanned: 247
Vulnerabilities Found: 12
Critical: 8
High: 3
Medium: 1

CRITICAL VULNERABILITIES
------------------------

1. SQL Injection in User Authentication
   File: src/auth/login.js:45
   Severity: CRITICAL (CVSS 9.8)
   Database: MySQL

   Vulnerable Code:
   const query = `SELECT * FROM users WHERE username='${username}' AND password='${password}'`;
   const user = await db.query(query);

   Attack Vector:
   username: admin' --
   password: anything

   Resulting Query:
   SELECT * FROM users WHERE username='admin' --' AND password='anything'

   Impact:
   - Authentication bypass
   - Access to all user accounts
   - Complete database access

   Proof of Concept:
   curl -X POST http://localhost:3000/api/login \
     -H "Content-Type: application/json" \
     -d '{"username":"admin'\'' --","password":"anything"}'

   Remediation:
   const query = 'SELECT * FROM users WHERE username = ? AND password = ?';
   const user = await db.query(query, [username, hashedPassword]);

   Additional Security:
   - Use bcrypt for password hashing
   - Implement rate limiting
   - Add account lockout
   - Log failed attempts

2. SQL Injection in Product Search
   File: src/api/products.js:78
   Severity: CRITICAL (CVSS 9.1)
   Database: PostgreSQL

   Vulnerable Code:
   app.get('/api/products/search', (req, res) => {
       const searchQuery = `
           SELECT * FROM products
           WHERE name LIKE '%${req.query.q}%'
           ORDER BY ${req.query.sort}
       `;
       const results = db.query(searchQuery);
       res.json(results);
   });

   Attack Vectors:
   1. UNION-based extraction:
      q=test%' UNION SELECT username,password,email FROM users--

   2. ORDER BY injection:
      sort=price; DROP TABLE products--

   Impact:
   - Complete database extraction
   - Data modification/deletion
   - Privilege escalation

   Remediation:
   app.get('/api/products/search', async (req, res) => {
       const allowedSorts = ['price', 'name', 'date'];
       const sort = allowedSorts.includes(req.query.sort) ? req.query.sort : 'name';

       const query = `
           SELECT * FROM products
           WHERE name LIKE $1
           ORDER BY ${sort}
       `;
       const results = await db.query(query, [`%${req.query.q}%`]);
       res.json(results);
   });

3. NoSQL Injection in MongoDB
   File: src/api/users.js:34
   Severity: CRITICAL (CVSS 8.9)
   Database: MongoDB

   Vulnerable Code:
   app.post('/api/login', (req, res) => {
       const user = await User.findOne({
           username: req.body.username,
           password: req.body.password
       });
   });

   Attack Vector:
   {
       "username": {"$ne": null},
       "password": {"$ne": null}
   }

   This bypasses authentication by using MongoDB operators

   Impact:
   - Authentication bypass
   - Access to any account

   Remediation:
   app.post('/api/login', async (req, res) => {
       // Validate input types
       if (typeof req.body.username !== 'string' ||
           typeof req.body.password !== 'string') {
           return res.status(400).json({error: 'Invalid input'});
       }

       const user = await User.findOne({
           username: req.body.username
       });

       if (user && await bcrypt.compare(req.body.password, user.hashedPassword)) {
           // Success
       }
   });
```

## Database-Specific Exploits

### MySQL
- UNION SELECT attacks
- INTO OUTFILE file writes
- LOAD_FILE() reads
- Blind injection with SLEEP()

### PostgreSQL
- COPY TO PROGRAM command execution
- pg_read_file() arbitrary file reads
- Large object manipulation

### SQL Server
- xp_cmdshell command execution
- OPENROWSET file access
- Linked server attacks

### Oracle
- UTL_FILE file operations
- UTL_HTTP SSRF attacks
- Java stored procedures

## Prevention Best Practices

1. **Use Parameterized Queries**
   ```javascript
   // Node.js (mysql2)
   db.execute('SELECT * FROM users WHERE id = ?', [userId]);

   // Python (psycopg2)
   cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))

   // PHP (PDO)
   $stmt = $pdo->prepare('SELECT * FROM users WHERE id = :id');
   $stmt->execute(['id' => $userId]);
   ```

2. **Input Validation**
   - Whitelist allowed characters
   - Validate data types
   - Limit input length
   - Sanitize special characters

3. **Least Privilege**
   - Use dedicated database users per application
   - Minimal required permissions
   - No admin/root access from application

4. **Web Application Firewall**
   - ModSecurity with OWASP Core Rule Set
   - Cloud WAF (Cloudflare, AWS WAF)

5. **Monitoring & Logging**
   - Log all database queries
   - Alert on suspicious patterns
   - Regular log review

## License

MIT License - See LICENSE file for details
