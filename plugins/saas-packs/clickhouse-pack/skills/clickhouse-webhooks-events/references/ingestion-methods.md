# ClickHouse Ingestion Methods

Deep reference for the server-side and code-free ingestion paths. The
application-side batched webhook receiver lives in the main SKILL.md; this file
covers the Kafka table engine, ClickHouse Cloud ClickPipes, and the HTTP
interface for bulk file/URL/S3 loads.

## Kafka Table Engine (Server-Side Ingestion)

The Kafka engine lets ClickHouse consume a topic directly — no application
consumer to run or scale. A materialized view moves rows from the Kafka engine
table into a durable MergeTree table.

```sql
-- Create a Kafka engine table (consumes messages automatically)
CREATE TABLE analytics.events_kafka (
    event_type  String,
    user_id     UInt64,
    properties  String,
    timestamp   DateTime
)
ENGINE = Kafka()
SETTINGS
    kafka_broker_list = 'kafka:9092',
    kafka_topic_list = 'events',
    kafka_group_name = 'clickhouse_consumer',
    kafka_format = 'JSONEachRow',
    kafka_num_consumers = 2,
    kafka_max_block_size = 65536;

-- Materialized view pipes Kafka → MergeTree automatically
CREATE MATERIALIZED VIEW analytics.events_kafka_mv
TO analytics.events
AS SELECT
    event_type,
    user_id,
    properties,
    timestamp AS created_at
FROM analytics.events_kafka;

-- ClickHouse now consumes from Kafka continuously!
-- Check lag:
SELECT * FROM system.kafka_consumers;
```

## ClickPipes (ClickHouse Cloud Managed Ingestion)

ClickHouse Cloud offers **ClickPipes** — a managed ingestion service that
connects to Kafka, Confluent, Amazon MSK, S3, and GCS without code.

```
ClickPipes Configuration (Cloud Console):
1. Source: Amazon MSK / Confluent Cloud / Apache Kafka
2. Topic: events
3. Format: JSONEachRow
4. Target: analytics.events
5. Scaling: 2 consumers (auto-scales)
```

## HTTP Interface Bulk Insert

The HTTP interface accepts bulk loads from local files, remote URLs, and S3 with
no client library — ideal for backfills and one-off imports.

```text
# Insert from CSV file via HTTP (no client needed)
curl 'http://localhost:8123/?query=INSERT+INTO+analytics.events+FORMAT+CSVWithNames' \
  --data-binary @events.csv

# Insert from NDJSON file
curl 'http://localhost:8123/?query=INSERT+INTO+analytics.events+FORMAT+JSONEachRow' \
  --data-binary @events.ndjson

# Insert from Parquet file
curl 'http://localhost:8123/?query=INSERT+INTO+analytics.events+FORMAT+Parquet' \
  --data-binary @events.parquet

# Insert from remote URL (ClickHouse fetches it)
INSERT INTO analytics.events
SELECT * FROM url('https://data.example.com/events.csv', CSVWithNames);

# Insert from S3
INSERT INTO analytics.events
SELECT * FROM s3(
    'https://my-bucket.s3.amazonaws.com/events/*.parquet',
    'ACCESS_KEY', 'SECRET_KEY',
    'Parquet'
);
```
