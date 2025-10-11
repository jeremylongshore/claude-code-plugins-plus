---
description: Set up and manage database replication
---

# Database Replication Manager

Configure database replication for high availability and read scaling.

## Replication Types

1. **Master-Slave**: One write node, multiple read replicas
2. **Master-Master**: Multi-master with conflict resolution
3. **Synchronous**: Wait for replica confirmation
4. **Asynchronous**: Don't wait for replicas

## PostgreSQL Streaming Replication

```bash
# On primary server (postgresql.conf)
wal_level = replica
max_wal_senders = 10
wal_keep_size = 64

# Create replication user
CREATE ROLE replicator WITH REPLICATION LOGIN PASSWORD 'password';

# On replica server
pg_basebackup -h primary_host -D /var/lib/postgresql/data -U replicator -P -v

# Start replica
echo "primary_conninfo = 'host=primary_host port=5432 user=replicator password=password'" >> postgresql.auto.conf
```

## When Invoked

Provide replication setup instructions for the specified database system.
