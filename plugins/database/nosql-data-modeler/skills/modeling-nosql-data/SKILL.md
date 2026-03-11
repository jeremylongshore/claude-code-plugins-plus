---
name: modeling-nosql-data
description: |
  Build use when you need to work with NoSQL data modeling.
  This skill provides NoSQL database design with comprehensive guidance and automation.
  Trigger with phrases like "model NoSQL data", "design document structure",
  or "optimize NoSQL schema".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(psql:*), Bash(mysql:*), Bash(mongosh:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# NoSQL Data Modeler

## Overview

Design data models for NoSQL databases including MongoDB (document), DynamoDB (key-value/wide-column), Redis (key-value), and Cassandra (wide-column). Unlike relational modeling where normalization drives design, NoSQL modeling starts from access patterns and query requirements, then shapes the data to serve those patterns efficiently. This skill covers embedding vs. referencing decisions, partition key design, denormalization strategies, and schema evolution.

## Prerequisites

- `mongosh`, `aws dynamodb` CLI, `redis-cli`, or `cqlsh` installed depending on target database
- Documented list of application access patterns (read/write queries the application performs)
- Expected data volumes (document count, average document size, growth rate)
- Read/write ratio and latency requirements for each access pattern
- Understanding of consistency requirements (strong vs. eventual consistency)

## Instructions

1. Catalog all application access patterns as a table with columns: pattern name, query description, frequency (queries/sec), latency requirement, and data fields accessed. This drives every modeling decision.

2. For MongoDB document modeling, apply the embedding vs. referencing decision framework:
   - **Embed** when: data is always accessed together, child data has no independent lifecycle, cardinality is bounded (1:few), and updates are infrequent.
   - **Reference** when: data has independent access patterns, cardinality is unbounded (1:many/many:many), child documents are large, or data is shared across parents.

3. Design document schemas that match query patterns. If the application needs "all orders for a customer with line items," embed line items inside the order document. If the application needs "all products across all orders," use references to a products collection.

4. For DynamoDB, design the partition key and sort key to support the primary access pattern with a single-table design. Use composite sort keys (e.g., `ORDER#2024-01-15#12345`) for hierarchical data. Plan GSIs (Global Secondary Indexes) for secondary access patterns, keeping total GSI count under 5.

5. Evaluate denormalization trade-offs: duplicating data across documents reduces read latency but increases write complexity and storage. Denormalize data that changes rarely (user names, product categories) but reference data that changes frequently (prices, inventory counts).

6. Handle one-to-many relationships by choosing between embedding (small arrays), child referencing (parent stores child IDs), or parent referencing (child stores parent ID). For unbounded one-to-many, always use parent referencing to avoid document size limits (16MB in MongoDB).

7. Model many-to-many relationships using an array of references in each document or a dedicated junction collection. For DynamoDB, use adjacency list patterns with inverted GSIs.

8. Plan for schema evolution by using schema versioning fields (`schemaVersion: 2`), writing migration scripts that update documents in batches, and ensuring application code handles both old and new document shapes during rollout.

9. Validate the model against access patterns by running sample queries with `explain()` in MongoDB or examining consumed capacity units in DynamoDB. Verify that primary access patterns require only single-partition reads.

10. Document the final data model with sample documents, index definitions, and the access pattern mapping that justifies each modeling decision.

## Output

- **Data model diagrams** showing document/collection structure, embedded vs. referenced relationships
- **Sample documents** in JSON format for each collection/table with realistic data
- **Index definitions** including compound indexes, partial indexes, and TTL indexes
- **Access pattern mapping** table linking each query to its supporting collection and index
- **Migration scripts** for evolving schemas from existing relational models to NoSQL

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| Document exceeds 16MB size limit (MongoDB) | Unbounded array growth from embedding too many child documents | Switch from embedding to referencing; use the bucket pattern to chunk large arrays into fixed-size sub-documents |
| Hot partition in DynamoDB | Partition key with low cardinality causes uneven distribution | Add a random suffix or use a composite key; distribute writes across partitions with write sharding |
| High read latency on referenced documents | Too many round trips to resolve references (N+1 query problem) | Denormalize frequently accessed reference data; use `$lookup` aggregation for server-side joins; batch reference resolution |
| Inconsistent denormalized data | Write to source succeeds but denormalized copies not updated | Implement change streams (MongoDB) or DynamoDB Streams to propagate updates; use transactional writes where supported |
| Query requires full collection scan | Missing index on query filter fields | Create compound indexes matching query predicates and sort order; use `explain()` to verify index usage |

## Examples

**E-commerce product catalog in MongoDB**: Products embed variant arrays (size, color, price) since variants are always accessed with the product. Reviews reference the product by ID since reviews are accessed independently and grow unboundedly. A compound index on `{category: 1, price: 1}` supports filtered browsing.

**Social media feed in DynamoDB single-table design**: Partition key is `USER#userId`, sort key is `POST#timestamp` for user timeline queries. A GSI with partition key `HASHTAG#tag` and sort key `timestamp` supports hashtag feeds. User profile data uses sort key `PROFILE` on the same partition.

**IoT sensor data in Cassandra**: Partition key is `sensor_id`, clustering column is `timestamp DESC`. Each partition holds one sensor's readings, ordered by time. TTL of 90 days automatically expires old readings. Materialized views support queries by location and sensor type.

## Resources

- MongoDB data modeling patterns: https://www.mongodb.com/docs/manual/data-modeling/
- DynamoDB single-table design: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-modeling-nosql.html
- Cassandra data modeling guide: https://cassandra.apache.org/doc/latest/cassandra/data_modeling/
- Redis data structures: https://redis.io/docs/data-types/
- NoSQL design patterns catalog: https://www.mongodb.com/docs/manual/applications/data-models/
