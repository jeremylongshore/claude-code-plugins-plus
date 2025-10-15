# Database & Backend Plugins Pack

A comprehensive collection of 25 database and backend plugins for Claude Code, covering migration management, performance optimization, security, monitoring, and advanced database operations.

## Plugin Categories

### Schema & Design (4 plugins)
- **database-migration-manager** - Database migration management with version control
- **database-schema-designer** - Design and visualize database schemas with ERD generation
- **orm-code-generator** - Generate ORM models from schemas (TypeORM, Prisma, SQLAlchemy, etc.)
- **nosql-data-modeler** - Design NoSQL data models for MongoDB, DynamoDB, Cassandra

### Performance & Optimization (5 plugins)
- **sql-query-optimizer** - Analyze and optimize SQL queries
- **query-performance-analyzer** - EXPLAIN plan interpretation and bottleneck identification
- **database-index-advisor** - Recommend optimal indexes based on query patterns
- **database-connection-pooler** - Implement efficient connection pooling
- **database-cache-layer** - Implement caching strategies with Redis/Memcached

### Data Management (4 plugins)
- **data-seeder-generator** - Generate realistic test data and seed scripts
- **data-validation-engine** - Implement comprehensive data validation rules
- **database-diff-tool** - Compare schemas and generate migration scripts
- **database-documentation-gen** - Generate database documentation and ERDs

### Operations & Monitoring (5 plugins)
- **database-backup-automator** - Automated backup with scheduling and retention
- **database-health-monitor** - Monitor database health and performance metrics
- **database-transaction-monitor** - Track transaction performance and issues
- **database-deadlock-detector** - Detect and resolve database deadlocks
- **database-audit-logger** - Track database changes for compliance

### High Availability & Scaling (4 plugins)
- **database-replication-manager** - Manage replication and failover
- **database-sharding-manager** - Implement database sharding strategies
- **database-partition-manager** - Manage table partitioning for large datasets
- **database-recovery-manager** - Disaster recovery and PITR (Point-in-Time Recovery)

### Security & Maintenance (3 plugins)
- **database-security-scanner** - Scan for security vulnerabilities
- **stored-procedure-generator** - Generate stored procedures and functions
- **database-archival-system** - Archive old data with retention policies

## Installation

Install individual plugins:
```bash
/plugin install database-migration-manager@claude-code-plugins-plus
/plugin install sql-query-optimizer@claude-code-plugins-plus
/plugin install orm-code-generator@claude-code-plugins-plus
```

## Quick Reference

| Plugin | Command/Agent | Primary Use Case |
|--------|---------------|------------------|
| database-migration-manager | `/migration` | Create and run migrations |
| sql-query-optimizer | `/optimize-query` | Optimize slow queries |
| database-backup-automator | `/backup` | Set up automated backups |
| orm-code-generator | agent | Generate ORM models |
| database-schema-designer | `/design-schema` | Design database schemas |
| query-performance-analyzer | agent | Analyze EXPLAIN plans |
| database-connection-pooler | `/connection-pool` | Configure connection pooling |
| data-seeder-generator | `/seed-data` | Generate test data |
| database-replication-manager | `/replication` | Set up replication |
| database-index-advisor | `/index-advisor` | Get index recommendations |
| database-audit-logger | `/audit-log` | Implement audit logging |
| nosql-data-modeler | agent | Design NoSQL schemas |
| database-health-monitor | `/health-check` | Monitor database health |
| stored-procedure-generator | `/stored-proc` | Generate stored procedures |
| database-diff-tool | `/db-diff` | Compare schemas |
| database-documentation-gen | `/db-docs` | Generate documentation |
| data-validation-engine | agent | Implement validation |
| database-security-scanner | `/security-scan` | Security audit |
| database-cache-layer | `/caching` | Implement caching |
| database-sharding-manager | `/sharding` | Design sharding |
| database-transaction-monitor | `/transactions` | Monitor transactions |
| database-deadlock-detector | `/deadlock` | Detect deadlocks |
| database-partition-manager | `/partitioning` | Partition large tables |
| database-archival-system | `/archival` | Archive old data |
| database-recovery-manager | `/recovery` | Disaster recovery |

## Supported Databases

### SQL Databases
- **PostgreSQL** - Full support for all plugins
- **MySQL/MariaDB** - Full support with minor syntax variations
- **SQLite** - Supported for development use cases
- **SQL Server** - Supported for enterprise scenarios
- **Oracle** - Supported for enterprise scenarios

### NoSQL Databases
- **MongoDB** - Document database modeling and operations
- **DynamoDB** - AWS key-value store
- **Cassandra** - Wide-column store
- **Redis** - Caching and data structures
- **Elasticsearch** - Search and analytics

## Common Use Cases

### 1. New Project Setup
```bash
/design-schema          # Design your schema
/migration              # Create initial migration
/seed-data              # Generate test data
/backup                 # Set up backups
```

### 2. Performance Optimization
```bash
/optimize-query         # Optimize slow queries
/index-advisor          # Get index recommendations
/caching                # Implement caching
/connection-pool        # Configure pooling
```

### 3. Production Operations
```bash
/health-check           # Monitor health
/replication            # Set up HA
/backup                 # Automate backups
/security-scan          # Security audit
```

### 4. Migration & Scaling
```bash
/db-diff                # Compare environments
/partitioning           # Partition large tables
/sharding               # Implement sharding
/archival               # Archive old data
```

## Best Practices

### Migration Management
- One logical change per migration
- Always include rollback (down migration)
- Test migrations in development first
- Use version control for migration files

### Performance Optimization
- Index WHERE and JOIN columns
- Avoid SELECT * in production
- Use connection pooling
- Implement caching for read-heavy workloads

### Security
- Principle of least privilege
- Use SSL/TLS for connections
- Implement audit logging
- Regular security scans

### High Availability
- Set up replication for critical databases
- Regular backup testing
- Document recovery procedures
- Monitor replication lag

### Data Management
- Implement data validation at database level
- Use constraints and foreign keys
- Regular data archival for old records
- Maintain database documentation

## Integration Examples

### Full Stack Development Workflow

```bash
# 1. Design Phase
/design-schema
# Result: ERD diagram and SQL schema

# 2. Code Generation
# Agent automatically generates ORM models
# Result: TypeORM/Prisma/SQLAlchemy models

# 3. Migration Creation
/migration
# Result: Migration files for version control

# 4. Performance Setup
/connection-pool
/caching
# Result: Pooling and caching configuration

# 5. Testing Setup
/seed-data
# Result: Test data generators

# 6. Production Prep
/backup
/replication
/health-check
# Result: Production-ready database setup
```

### Performance Troubleshooting Workflow

```bash
# 1. Identify Slow Query
/health-check
# Result: List of slow queries

# 2. Analyze Performance
# Paste EXPLAIN output to performance analyzer agent
# Result: Bottleneck identification

# 3. Optimize Query
/optimize-query
# Result: Rewritten query

# 4. Index Recommendations
/index-advisor
# Result: CREATE INDEX statements

# 5. Verify Improvement
# Run EXPLAIN again with performance analyzer
# Result: Performance comparison
```

## Architecture Patterns

### Microservices Database Pattern
Each plugin supports microservices architecture:
- Independent database per service
- Connection pooling per service
- Service-specific caching layers
- Distributed transaction monitoring

### Monolith to Microservices Migration
- Use db-diff to identify schema dependencies
- Implement data partitioning by domain
- Set up replication for gradual migration
- Monitor transactions during transition

### Multi-Tenant Architecture
- Sharding strategies for tenant isolation
- Row-level security with audit logging
- Tenant-specific backup schedules
- Performance monitoring per tenant

## Technology Stack Coverage

### Backend Frameworks
- **Node.js**: Express, NestJS, Fastify
- **Python**: Django, Flask, FastAPI
- **Java**: Spring Boot, Hibernate
- **Ruby**: Rails, Sinatra
- **PHP**: Laravel, Symfony
- **Go**: GORM, sqlx
- **C#**: Entity Framework, Dapper

### ORM Support
- TypeORM (TypeScript)
- Prisma (TypeScript)
- Sequelize (JavaScript)
- SQLAlchemy (Python)
- Django ORM (Python)
- Hibernate (Java)
- Entity Framework (C#)
- ActiveRecord (Ruby)
- Eloquent (PHP)

### Cloud Platforms
- **AWS**: RDS, Aurora, DynamoDB
- **Google Cloud**: Cloud SQL, Firestore, BigQuery
- **Azure**: SQL Database, Cosmos DB
- **Heroku**: Postgres
- **DigitalOcean**: Managed Databases

## Contributing

These plugins follow database best practices and industry standards. Contributions welcome for:
- Additional database system support
- New optimization patterns
- Cloud-specific implementations
- Enterprise features

## Support & Documentation

Each plugin includes:
- Comprehensive README with examples
- Command/agent documentation
- Best practices guide
- Common troubleshooting tips

## License

All plugins are released under MIT License.

---

**Database Plugin Pack** - Comprehensive database and backend development tools for Claude Code
**Total Plugins**: 25
**Categories**: Schema Design, Performance, Operations, HA/Scaling, Security
**Last Updated**: October 2025
