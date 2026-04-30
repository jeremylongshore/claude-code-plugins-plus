---
name: oraclecloud-schema-migration
description: "Migrate to OCI Autonomous Database \u2014 wallet setup, mTLS, Data Pump,\
  \ and python-oracledb.\nUse when provisioning Autonomous DB, downloading wallets,\
  \ or migrating data with Data Pump.\nTrigger with \"autonomous database\", \"oci\
  \ adb\", \"wallet download\", \"data pump oci\", \"mtls oracle\".\n"
allowed-tools: Read, Write, Edit, Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- oraclecloud
- oci
compatibility: Designed for Claude Code
---
# OCI Autonomous Database — Migration & Connection

## Overview

Migrate to and connect with OCI Autonomous Database (ADB) using the Python SDK and python-oracledb. Autonomous Database is OCI's crown jewel but migrating to it from standard Oracle DB or other databases is full of gotchas — wallet downloads require SDK calls (not just console clicks), mTLS is mandatory by default, connection strings use a different format than standard Oracle, and Data Pump exports need specific parameter adjustments for ADB compatibility.

**Purpose:** Provision an Autonomous Database, download the wallet, establish a connection, and migrate data using Data Pump.

## Prerequisites

- **OCI Python SDK** — `pip install oci`
- **Oracle DB driver** — `pip install oracledb`
- **Config file** at `~/.oci/config` with fields: `user`, `fingerprint`, `tenancy`, `region`, `key_file`
- **IAM policy** — `Allow group Developers to manage autonomous-databases in compartment <name>`
- **Python 3.8+**
- For Data Pump: access to the source Oracle database with DBA privileges

## Instructions

### Step 1: Provision an Autonomous Database

```python
import oci
import base64
import zipfile
import os

config = oci.config.from_file("~/.oci/config")
db_client = oci.database.DatabaseClient(config)

# Create Autonomous Database (Transaction Processing workload)
adb = db_client.create_autonomous_database(
    oci.database.models.CreateAutonomousDatabaseDetails(
        compartment_id=config["tenancy"],
        display_name="app-adb",
        db_name="appadb",
        cpu_core_count=1,           # 1 OCPU (Always Free eligible)
        data_storage_size_in_tbs=1,  # 1 TB (Always Free: 20GB)
        admin_password="SecureP@ss123!",  # Must meet complexity requirements
        db_workload="OLTP",         # OLTP, DW, AJD, or APEX
        is_free_tier=True,          # Always Free if eligible
        is_mtls_connection_required=True,  # Default — use mTLS
    )
).data

print(f"ADB provisioning: {adb.id}")
print(f"State: {adb.lifecycle_state}")
```

### Step 2: Wait for Provisioning and Download Wallet

The wallet contains certificates and connection descriptors needed for mTLS. You must download it via the SDK — the wallet password is set at download time, not during provisioning.

```python
# Wait for ADB to become AVAILABLE
waiter = oci.wait_until(
    db_client,
    db_client.get_autonomous_database(adb.id),
    "lifecycle_state",
    "AVAILABLE",
    max_wait_seconds=600,
)
print(f"ADB ready: {waiter.data.lifecycle_state}")

# Download wallet
wallet_response = db_client.generate_autonomous_database_wallet(
    autonomous_database_id=adb.id,
    generate_autonomous_database_wallet_details=oci.database.models.GenerateAutonomousDatabaseWalletDetails(
        password="WalletP@ss456!",  # Wallet password (different from admin)
        generate_type="SINGLE",     # SINGLE for one DB, ALL for region
    ),
)

# Save and extract wallet
wallet_dir = os.path.expanduser("~/wallets/appadb")
os.makedirs(wallet_dir, exist_ok=True)
wallet_path = os.path.join(wallet_dir, "wallet.zip")

with open(wallet_path, "wb") as f:
    f.write(wallet_response.data.content)

with zipfile.ZipFile(wallet_path, "r") as z:
    z.extractall(wallet_dir)

print(f"Wallet extracted to: {wallet_dir}")
print(f"Files: {os.listdir(wallet_dir)}")
```

### Step 3: Connect Using python-oracledb (Thin Mode)

python-oracledb thin mode does not require Oracle Client libraries. It connects directly using the wallet files.

```python
import oracledb

# Thin mode connection (no Oracle Client needed)
connection = oracledb.connect(
    user="ADMIN",
    password="SecureP@ss123!",
    dsn="appadb_tp",  # From tnsnames.ora in wallet (_tp = Transaction Processing)
    config_dir=os.path.expanduser("~/wallets/appadb"),
    wallet_location=os.path.expanduser("~/wallets/appadb"),
    wallet_password="WalletP@ss456!",
)

# Verify connection
cursor = connection.cursor()
cursor.execute("SELECT banner FROM v$version")
print(f"Connected: {cursor.fetchone()[0]}")

# Check ADB-specific info
cursor.execute("SELECT * FROM v$pdbs")
print(f"PDB: {cursor.fetchone()}")

cursor.close()
connection.close()
```

### Step 4: Data Pump Export from Source Database

Data Pump is the standard Oracle tool for bulk data migration. These parameters ensure ADB compatibility.

```bash
# On the SOURCE database server
# Create a directory object pointing to a dump location
sqlplus sys/password@source_db as sysdba <<EOF
CREATE OR REPLACE DIRECTORY export_dir AS '/tmp/datapump';
GRANT READ, WRITE ON DIRECTORY export_dir TO schema_owner;
EOF

# Export with ADB-compatible parameters
expdp schema_owner/password@source_db \
  directory=export_dir \
  dumpfile=migration_%U.dmp \
  logfile=export.log \
  schemas=APP_SCHEMA \
  exclude=INDEX,CLUSTER,INDEXTYPE,MATERIALIZED_VIEW,MATERIALIZED_VIEW_LOG,MATERIALIZED_ZONEMAP,DB_LINK \
  version=19 \
  parallel=4
```

**Critical ADB exclusions:** ADB manages its own indexes, clusters, and materialized views. Including them causes import failures.

### Step 5: Import into Autonomous Database

```python
# Upload dump files to Object Storage first
storage = oci.object_storage.ObjectStorageClient(config)
namespace = storage.get_namespace().data

# Upload dump file
with open("/tmp/datapump/migration_01.dmp", "rb") as f:
    storage.put_object(
        namespace_name=namespace,
        bucket_name="migration-dumps",
        object_name="migration_01.dmp",
        put_object_body=f,
    )
print("Dump file uploaded to Object Storage")
```

Then run the import from SQL Developer Web or via credential + DBMS_CLOUD:

```sql
-- In ADB SQL worksheet (SQL Developer Web or sqlcl)
-- Step 1: Create credential for Object Storage access
BEGIN
  DBMS_CLOUD.CREATE_CREDENTIAL(
    credential_name => 'OCI_CRED',
    username        => 'oraclecloud_user@example.com',
    password        => 'auth_token_from_console'
  );
END;
/

-- Step 2: Import via Data Pump from Object Storage
DECLARE
  h NUMBER;
BEGIN
  h := DBMS_DATAPUMP.OPEN('IMPORT', 'SCHEMA', NULL, 'MIGRATION_IMPORT');
  DBMS_DATAPUMP.ADD_FILE(h, 'migration_01.dmp', 'DATA_PUMP_DIR');
  DBMS_DATAPUMP.SET_PARAMETER(h, 'TABLE_EXISTS_ACTION', 'REPLACE');
  DBMS_DATAPUMP.START_JOB(h);
END;
/
```

### Step 6: Verify Migration

```python
connection = oracledb.connect(
    user="ADMIN",
    password="SecureP@ss123!",
    dsn="appadb_tp",
    config_dir=os.path.expanduser("~/wallets/appadb"),
    wallet_location=os.path.expanduser("~/wallets/appadb"),
    wallet_password="WalletP@ss456!",
)

cursor = connection.cursor()

# Count tables
cursor.execute("""
    SELECT table_name, num_rows
    FROM all_tables
    WHERE owner = 'APP_SCHEMA'
    ORDER BY num_rows DESC
""")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} rows")

# Check for invalid objects
cursor.execute("""
    SELECT object_name, object_type, status
    FROM all_objects
    WHERE owner = 'APP_SCHEMA' AND status = 'INVALID'
""")
invalid = cursor.fetchall()
if invalid:
    print(f"\nWARNING: {len(invalid)} invalid objects found:")
    for obj in invalid:
        print(f"  {obj[1]} {obj[0]}: {obj[2]}")
else:
    print("\nAll objects valid — migration successful")

cursor.close()
connection.close()
```

## Output

Successful completion produces:
- A provisioned Autonomous Database with mTLS wallet downloaded and extracted
- A working python-oracledb connection in thin mode (no Oracle Client required)
- Data Pump export with ADB-compatible exclusions
- Object Storage upload and DBMS_CLOUD import workflow
- Migration verification with table counts and invalid object checks

## Error Handling

| Error | Code | Cause | Solution |
|-------|------|-------|----------|
| Wallet download fails | 404 NotAuthorizedOrNotFound | ADB not in AVAILABLE state | Wait for provisioning to complete (Step 2) |
| DPY-6005: cannot connect | N/A | Wrong wallet path or password | Verify `config_dir` and `wallet_location` paths, check wallet password |
| ORA-01017: invalid password | N/A | Wrong admin password | Reset via `db_client.update_autonomous_database()` with new `admin_password` |
| Data Pump ORA-39083 | N/A | Unsupported object type in ADB | Add object type to `exclude=` list in expdp command |
| Not authenticated | 401 NotAuthenticated | Bad API key or config | Verify `~/.oci/config` key_file and fingerprint |
| Rate limited | 429 TooManyRequests | Too many API calls | Add backoff; OCI does not return Retry-After header |
| mTLS handshake failure | N/A CERTIFICATE_VERIFY_FAILED | Expired or wrong wallet certificates | Re-download wallet; check wallet expiry (180 days default) |

## Examples

**Quick ADB list via CLI:**

```bash
oci db autonomous-database list \
  --compartment-id <OCID> \
  --query "data[*].{Name:\"display-name\",State:\"lifecycle-state\",OCPUs:\"cpu-core-count\"}" \
  --output table
```

**Test connection with one-liner:**

```python
import oracledb
conn = oracledb.connect(user="ADMIN", password="P@ss!", dsn="appadb_tp",
                         config_dir="~/wallets/appadb", wallet_location="~/wallets/appadb",
                         wallet_password="WalletP@ss!")
print(conn.version)
conn.close()
```

## Resources

- [Autonomous Database Overview](https://docs.oracle.com/en-us/iaas/Content/) — provisioning and management
- [Python SDK Reference](https://docs.oracle.com/en-us/iaas/tools/python/latest/) — DatabaseClient API
- [CLI Reference](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/cliconcepts.htm) — `oci db` commands
- [Always Free Tier](https://www.oracle.com/cloud/free/) — includes Autonomous Database
- [SDK Troubleshooting](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdk_troubleshooting.htm) — connection and auth errors
- [Pricing](https://www.oracle.com/cloud/pricing/) — ADB pricing by OCPU-hour

## Next Steps

After migration, see `oraclecloud-query-transform` to set up monitoring alarms on ADB metrics (CPU, storage, session count), or `oraclecloud-data-handling` to manage Object Storage buckets used for Data Pump dumps.
