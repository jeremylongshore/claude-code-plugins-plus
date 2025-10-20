---
name: fairdb-onboard-customer
description: Complete customer onboarding workflow for FairDB PostgreSQL service
model: sonnet
---

# FairDB Customer Onboarding Workflow

You are onboarding a new customer for FairDB PostgreSQL as a Service. This comprehensive workflow creates their database, users, configures access, sets up backups, and provides connection details.

## Step 1: Gather Customer Information

Collect these details:
1. **Customer Name**: Company/organization name
2. **Database Name**: Preferred database name (lowercase, no spaces)
3. **Primary Contact**: Name and email
4. **Plan Type**: Starter/Professional/Enterprise
5. **IP Allowlist**: Customer IP addresses for access
6. **Special Requirements**: Extensions, configurations, etc.

## Step 2: Validate Resources

```bash
# Check available resources
df -h /var/lib/postgresql
free -h
sudo -u postgres psql -c "SELECT count(*) as database_count FROM pg_database WHERE datistemplate = false;"

# Check current connections
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity;"
```

## Step 3: Create Customer Database

```bash
# Set customer variables
CUSTOMER_NAME="customer_name"  # Replace with actual
DB_NAME="${CUSTOMER_NAME}_db"
DB_OWNER="${CUSTOMER_NAME}_owner"
DB_USER="${CUSTOMER_NAME}_user"
DB_READONLY="${CUSTOMER_NAME}_readonly"

# Generate secure passwords
DB_OWNER_PASS=$(openssl rand -base64 32)
DB_USER_PASS=$(openssl rand -base64 32)
DB_READONLY_PASS=$(openssl rand -base64 32)

# Create database and users
sudo -u postgres psql << EOF
-- Create database owner role
CREATE ROLE ${DB_OWNER} WITH LOGIN PASSWORD '${DB_OWNER_PASS}'
  CREATEDB CREATEROLE CONNECTION LIMIT 5;

-- Create application user
CREATE ROLE ${DB_USER} WITH LOGIN PASSWORD '${DB_USER_PASS}'
  CONNECTION LIMIT 50;

-- Create read-only user
CREATE ROLE ${DB_READONLY} WITH LOGIN PASSWORD '${DB_READONLY_PASS}'
  CONNECTION LIMIT 10;

-- Create customer database
CREATE DATABASE ${DB_NAME}
  WITH OWNER = ${DB_OWNER}
  ENCODING = 'UTF8'
  LC_COLLATE = 'en_US.UTF-8'
  LC_CTYPE = 'en_US.UTF-8'
  TEMPLATE = template0
  CONNECTION LIMIT = 100;

-- Configure database
\c ${DB_NAME}

-- Create schema
CREATE SCHEMA IF NOT EXISTS ${CUSTOMER_NAME} AUTHORIZATION ${DB_OWNER};

-- Grant permissions
GRANT CONNECT ON DATABASE ${DB_NAME} TO ${DB_USER}, ${DB_READONLY};
GRANT USAGE ON SCHEMA ${CUSTOMER_NAME} TO ${DB_USER}, ${DB_READONLY};
GRANT CREATE ON SCHEMA ${CUSTOMER_NAME} TO ${DB_USER};

-- Default privileges for tables
ALTER DEFAULT PRIVILEGES FOR ROLE ${DB_OWNER} IN SCHEMA ${CUSTOMER_NAME}
  GRANT ALL ON TABLES TO ${DB_USER};

ALTER DEFAULT PRIVILEGES FOR ROLE ${DB_OWNER} IN SCHEMA ${CUSTOMER_NAME}
  GRANT SELECT ON TABLES TO ${DB_READONLY};

-- Default privileges for sequences
ALTER DEFAULT PRIVILEGES FOR ROLE ${DB_OWNER} IN SCHEMA ${CUSTOMER_NAME}
  GRANT ALL ON SEQUENCES TO ${DB_USER};

ALTER DEFAULT PRIVILEGES FOR ROLE ${DB_OWNER} IN SCHEMA ${CUSTOMER_NAME}
  GRANT SELECT ON SEQUENCES TO ${DB_READONLY};

-- Enable useful extensions
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS citext;
EOF

echo "Database ${DB_NAME} created successfully"
```

## Step 4: Configure Network Access

```bash
# Add customer IP to pg_hba.conf
CUSTOMER_IP="203.0.113.0/32"  # Replace with actual customer IP

# Backup pg_hba.conf
sudo cp /etc/postgresql/16/main/pg_hba.conf /etc/postgresql/16/main/pg_hba.conf.$(date +%Y%m%d)

# Add customer access rules
cat << EOF | sudo tee -a /etc/postgresql/16/main/pg_hba.conf

# Customer: ${CUSTOMER_NAME}
hostssl ${DB_NAME}     ${DB_OWNER}      ${CUSTOMER_IP}    scram-sha-256
hostssl ${DB_NAME}     ${DB_USER}       ${CUSTOMER_IP}    scram-sha-256
hostssl ${DB_NAME}     ${DB_READONLY}   ${CUSTOMER_IP}    scram-sha-256
EOF

# Update firewall
sudo ufw allow from ${CUSTOMER_IP} to any port 5432 comment "FairDB: ${CUSTOMER_NAME}"

# Reload PostgreSQL configuration
sudo systemctl reload postgresql
```

## Step 5: Set Resource Limits

```bash
# Configure per-database resource limits based on plan
case "${PLAN_TYPE}" in
  "starter")
    MAX_CONN=50
    WORK_MEM="4MB"
    SHARED_BUFFERS="256MB"
    ;;
  "professional")
    MAX_CONN=100
    WORK_MEM="8MB"
    SHARED_BUFFERS="1GB"
    ;;
  "enterprise")
    MAX_CONN=200
    WORK_MEM="16MB"
    SHARED_BUFFERS="4GB"
    ;;
esac

# Apply database-specific settings
sudo -u postgres psql -d ${DB_NAME} << EOF
-- Set connection limit
ALTER DATABASE ${DB_NAME} CONNECTION LIMIT ${MAX_CONN};

-- Set database parameters
ALTER DATABASE ${DB_NAME} SET work_mem = '${WORK_MEM}';
ALTER DATABASE ${DB_NAME} SET maintenance_work_mem = '${WORK_MEM}';
ALTER DATABASE ${DB_NAME} SET effective_cache_size = '${SHARED_BUFFERS}';
ALTER DATABASE ${DB_NAME} SET random_page_cost = 1.1;
ALTER DATABASE ${DB_NAME} SET log_statement = 'all';
ALTER DATABASE ${DB_NAME} SET log_duration = on;
EOF
```

## Step 6: Configure Backup Policy

```bash
# Create customer-specific backup configuration
cat << EOF | sudo tee -a /opt/fairdb/configs/backup-${CUSTOMER_NAME}.conf
# Backup configuration for ${CUSTOMER_NAME}
DATABASE=${DB_NAME}
BACKUP_RETENTION_DAYS=30
BACKUP_SCHEDULE="0 3 * * *"  # Daily at 3 AM
BACKUP_TYPE="full"
S3_PREFIX="${CUSTOMER_NAME}/"
EOF

# Add to pgBackRest configuration
sudo tee -a /etc/pgbackrest/pgbackrest.conf << EOF

[${CUSTOMER_NAME}]
pg1-path=/var/lib/postgresql/16/main
pg1-database=${DB_NAME}
pg1-port=5432
backup-user=backup_user
process-max=2
repo1-retention-full=4
repo1-retention-diff=7
EOF

# Create backup stanza for customer
sudo -u postgres pgbackrest --stanza=${CUSTOMER_NAME} stanza-create

# Schedule customer backup
echo "0 3 * * * postgres pgbackrest --stanza=${CUSTOMER_NAME} --type=full backup" | \
  sudo tee -a /etc/cron.d/fairdb-customer-${CUSTOMER_NAME}
```

## Step 7: Setup Monitoring

```bash
# Create monitoring user and grants
sudo -u postgres psql -d ${DB_NAME} << EOF
-- Grant monitoring permissions
GRANT pg_monitor TO ${DB_READONLY};
GRANT EXECUTE ON FUNCTION pg_stat_statements_reset() TO ${DB_OWNER};
EOF

# Create customer monitoring script
cat << 'EOF' | sudo tee /opt/fairdb/scripts/monitor-${CUSTOMER_NAME}.sh
#!/bin/bash
# Monitoring script for ${CUSTOMER_NAME}

DB_NAME="${DB_NAME}"
ALERT_THRESHOLD_CONNECTIONS=80
ALERT_THRESHOLD_SIZE_GB=100

# Check connection usage
CONN_USAGE=$(sudo -u postgres psql -t -c "
  SELECT (count(*) * 100.0 / setting::int)::int as pct
  FROM pg_stat_activity, pg_settings
  WHERE name = 'max_connections'
  AND datname = '${DB_NAME}'
  GROUP BY setting;")

if [ ${CONN_USAGE:-0} -gt $ALERT_THRESHOLD_CONNECTIONS ]; then
  echo "ALERT: Connection usage at ${CONN_USAGE}% for ${CUSTOMER_NAME}"
fi

# Check database size
DB_SIZE_GB=$(sudo -u postgres psql -t -c "
  SELECT pg_database_size('${DB_NAME}') / 1024 / 1024 / 1024;")

if [ ${DB_SIZE_GB:-0} -gt $ALERT_THRESHOLD_SIZE_GB ]; then
  echo "ALERT: Database size is ${DB_SIZE_GB}GB for ${CUSTOMER_NAME}"
fi

# Check for long-running queries
sudo -u postgres psql -d ${DB_NAME} -c "
  SELECT pid, now() - pg_stat_activity.query_start AS duration, query
  FROM pg_stat_activity
  WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes'
  AND state = 'active';"
EOF

sudo chmod +x /opt/fairdb/scripts/monitor-${CUSTOMER_NAME}.sh

# Add to monitoring cron
echo "*/10 * * * * root /opt/fairdb/scripts/monitor-${CUSTOMER_NAME}.sh" | \
  sudo tee -a /etc/cron.d/fairdb-monitor-${CUSTOMER_NAME}
```

## Step 8: Generate SSL Certificates

```bash
# Create customer SSL certificate
sudo mkdir -p /etc/postgresql/16/main/ssl/${CUSTOMER_NAME}
cd /etc/postgresql/16/main/ssl/${CUSTOMER_NAME}

# Generate customer-specific SSL cert
sudo openssl req -new -x509 -days 365 -nodes \
  -out server.crt -keyout server.key \
  -subj "/C=US/ST=State/L=City/O=FairDB/OU=${CUSTOMER_NAME}/CN=${CUSTOMER_NAME}.fairdb.io"

# Set permissions
sudo chmod 600 server.key
sudo chown postgres:postgres server.*

# Create client certificate
sudo openssl req -new -nodes \
  -out client.csr -keyout client.key \
  -subj "/C=US/ST=State/L=City/O=FairDB/OU=${CUSTOMER_NAME}/CN=${DB_USER}"

sudo openssl x509 -req -CAcreateserial \
  -in client.csr -CA server.crt -CAkey server.key \
  -out client.crt -days 365

# Package client certificates
tar czf /tmp/${CUSTOMER_NAME}-ssl-bundle.tar.gz client.crt client.key server.crt
```

## Step 9: Create Connection Documentation

```bash
# Generate connection details document
cat << EOF > /tmp/${CUSTOMER_NAME}-connection-details.md
# FairDB PostgreSQL Connection Details
## Customer: ${CUSTOMER_NAME}

### Database Information
- **Database Name**: ${DB_NAME}
- **Host**: fairdb-prod.example.com
- **Port**: 5432
- **SSL Required**: Yes

### User Credentials
#### Database Owner (DDL Operations)
- **Username**: ${DB_OWNER}
- **Password**: ${DB_OWNER_PASS}
- **Connection Limit**: 5
- **Permissions**: Full database owner

#### Application User (DML Operations)
- **Username**: ${DB_USER}
- **Password**: ${DB_USER_PASS}
- **Connection Limit**: 50
- **Permissions**: CRUD operations on all tables

#### Read-Only User (Reporting)
- **Username**: ${DB_READONLY}
- **Password**: ${DB_READONLY_PASS}
- **Connection Limit**: 10
- **Permissions**: SELECT only

### Connection Strings
\`\`\`
# Standard connection
postgresql://${DB_USER}:${DB_USER_PASS}@fairdb-prod.example.com:5432/${DB_NAME}?sslmode=require

# With SSL certificate
postgresql://${DB_USER}:${DB_USER_PASS}@fairdb-prod.example.com:5432/${DB_NAME}?sslmode=require&sslcert=client.crt&sslkey=client.key&sslrootcert=server.crt

# JDBC URL
jdbc:postgresql://fairdb-prod.example.com:5432/${DB_NAME}?ssl=true&sslmode=require

# psql command
psql "host=fairdb-prod.example.com port=5432 dbname=${DB_NAME} user=${DB_USER} sslmode=require"
\`\`\`

### Resource Limits
- **Plan**: ${PLAN_TYPE}
- **Max Connections**: ${MAX_CONN}
- **Storage Quota**: Unlimited (pay per GB)
- **Backup Retention**: 30 days
- **Backup Schedule**: Daily at 3:00 AM UTC

### Support Information
- **Email**: support@fairdb.io
- **Emergency**: +1-xxx-xxx-xxxx
- **Documentation**: https://docs.fairdb.io
- **Status Page**: https://status.fairdb.io

### Important Notes
1. Always use SSL connections
2. Rotate passwords every 90 days
3. Monitor connection pool usage
4. Test restore procedures quarterly
5. Keep IP allowlist updated

### Next Steps
1. Download SSL certificates: ${CUSTOMER_NAME}-ssl-bundle.tar.gz
2. Test connection with provided credentials
3. Configure application connection pool
4. Set up monitoring dashboards
5. Review security best practices

Generated: $(date)
EOF

echo "Connection details saved to /tmp/${CUSTOMER_NAME}-connection-details.md"
```

## Step 10: Final Verification

```bash
# Test all user connections
echo "Testing database connections..."

# Test owner connection
PGPASSWORD=${DB_OWNER_PASS} psql -h localhost -U ${DB_OWNER} -d ${DB_NAME} -c "SELECT current_user, current_database();"

# Test app user connection
PGPASSWORD=${DB_USER_PASS} psql -h localhost -U ${DB_USER} -d ${DB_NAME} -c "SELECT current_user, current_database();"

# Test readonly connection
PGPASSWORD=${DB_READONLY_PASS} psql -h localhost -U ${DB_READONLY} -d ${DB_NAME} -c "SELECT current_user, current_database();"

# Verify backup configuration
sudo -u postgres pgbackrest --stanza=${CUSTOMER_NAME} check

# Check monitoring
/opt/fairdb/scripts/monitor-${CUSTOMER_NAME}.sh

# Generate onboarding summary
echo "
===========================================
FairDB Customer Onboarding Complete
===========================================
Customer: ${CUSTOMER_NAME}
Database: ${DB_NAME}
Created: $(date)
Plan: ${PLAN_TYPE}

Files Generated:
- /tmp/${CUSTOMER_NAME}-connection-details.md
- /tmp/${CUSTOMER_NAME}-ssl-bundle.tar.gz

Next Actions:
1. Send connection details to customer
2. Schedule onboarding call
3. Monitor initial usage
4. Follow up in 24 hours
===========================================
"
```

## Onboarding Checklist

Verify completion:
- [ ] Database created
- [ ] Users created with secure passwords
- [ ] Network access configured
- [ ] Resource limits applied
- [ ] Backup policy configured
- [ ] Monitoring enabled
- [ ] SSL certificates generated
- [ ] Documentation created
- [ ] Connection tests passed
- [ ] Customer notified

## Rollback Procedure

If onboarding fails:
```bash
# Remove database and users
sudo -u postgres psql << EOF
DROP DATABASE IF EXISTS ${DB_NAME};
DROP ROLE IF EXISTS ${DB_OWNER};
DROP ROLE IF EXISTS ${DB_USER};
DROP ROLE IF EXISTS ${DB_READONLY};
EOF

# Remove configurations
sudo rm -f /etc/cron.d/fairdb-customer-${CUSTOMER_NAME}
sudo rm -f /etc/cron.d/fairdb-monitor-${CUSTOMER_NAME}
sudo rm -f /opt/fairdb/scripts/monitor-${CUSTOMER_NAME}.sh
sudo rm -rf /etc/postgresql/16/main/ssl/${CUSTOMER_NAME}

# Remove firewall rule
sudo ufw delete allow from ${CUSTOMER_IP} to any port 5432

echo "Customer ${CUSTOMER_NAME} rollback complete"
```