---
title: "Distributed Systems Architecture Patterns Cheat Sheet"
description: "Distributed Systems Architecture Patterns Cheat Sheet"
date: "2025-01-13"
tags: ["start-ai-tools"]
featured: false
---
<p>A quick reference guide for distributed systems architecture patterns, covering when to use each pattern and the classic problems they solve.</p>
<h2 id="distributed-systems-architecture-patterns-cheat-sheet">
 Distributed Systems Architecture Patterns Cheat Sheet
<p><a class="anchor" href="#distributed-systems-architecture-patterns-cheat-sheet">#</a></p>
</h2>
<table>
<thead>
<tr>
<th>Pattern</th>
<th>Core Idea</th>
<th>When to Use</th>
<th>Classic Problems</th>
</tr>
</thead>
<tbody>
<tr>
<td>Caching (cache-aside / write-through / write-back)</td>
<td>Keep hot data close to the app</td>
<td>Read-heavy workloads, expensive queries, slow upstreams</td>
<td>Speed up product pages, session stores, ranking feeds</td>
</tr>
<tr>
<td>CDN</td>
<td>Push static/streamable assets to edge</td>
<td>Global users, large media, static bundles</td>
<td>Image/CSS delivery, video streaming, downloads</td>
</tr>
<tr>
<td>Load Balancing (L4/L7)</td>
<td>Spread traffic across instances</td>
<td>Scale stateless services, HA</td>
<td>Web/API tier scaling, zero-downtime deploys</td>
</tr>
<tr>
<td>Rate Limiting &amp; Throttling</td>
<td>Control request volume per key/client</td>
<td>Protect downstream services, fair usage</td>
<td>Public APIs, login abuse protection</td>
</tr>
<tr>
<td>Circuit Breaker</td>
<td>Fail fast when a dependency is unhealthy</td>
<td>Prevent cascades, degrade gracefully</td>
<td>Payment gateway outage, flaky search backend</td>
</tr>
<tr>
<td>Backpressure</td>
<td>Signal producers to slow down</td>
<td>Spiky traffic, limited consumers</td>
<td>Upload pipelines, stream processing stability</td>
</tr>
<tr>
<td>Retry + Idempotency</td>
<td>Safe replays of failed ops</td>
<td>Unreliable networks, async workflows</td>
<td>Order creation, webhook delivery</td>
</tr>
<tr>
<td>Read Replicas</td>
<td>Offload reads from primary DB</td>
<td>Read-heavy, reporting, geo-reads</td>
<td>Analytics pages, timelines, leaderboards</td>
</tr>
<tr>
<td>Sharding (Hash/Range/Geo)</td>
<td>Split data across nodes</td>
<td>Data &gt; single node, parallelism</td>
<td>Multi-TB user tables, geo data stores</td>
</tr>
<tr>
<td>Replication (Sync/Async)</td>
<td>Keep copies for HA &amp; reads</td>
<td>Availability, DR, low-latency reads</td>
<td>Active-passive failover, follower reads</td>
</tr>
<tr>
<td>CQRS</td>
<td>Separate read/write models</td>
<td>Complex reads + high write throughput</td>
<td>Event feeds, denormalized dashboards</td>
</tr>
<tr>
<td>Event Sourcing</td>
<td>State = log of events</td>
<td>Full audit, rebuild state, temporal queries</td>
<td>Ledger systems, order state timelines</td>
</tr>
<tr>
<td>Message Queue / Stream (SQS/Kafka)</td>
<td>Async decoupling via durable logs</td>
<td>Spikes, fan-out, ordered pipelines</td>
<td>Email/SMS, ETL, clickstream processing</td>
</tr>
<tr>
<td>Saga (Orchestration/Choreography)</td>
<td>Distributed transaction via steps + compensation</td>
<td>Cross-service workflows without 2PC</td>
<td>Book-pay-reserve flows, refunds</td>
</tr>
<tr>
<td>Search Index (ES/OpenSearch)</td>
<td>Inverted index for fast text/filters</td>
<td>Full-text, aggregations, relevance</td>
<td>Product search, logs explorer</td>
</tr>
<tr>
<td>Time-Series DB</td>
<td>Append-heavy metrics optimized by time</td>
<td>Monitoring, IoT, financial ticks</td>
<td>Prometheus/TSDB, sensor data</td>
</tr>
<tr>
<td>Write-Optimized Stores (LSM)</td>
<td>Fast writes, compaction later</td>
<td>High ingest, occasional reads</td>
<td>Audit/event logs, analytics ingest</td>
</tr>
<tr>
<td>Geo-Replication / Geo-Sharding</td>
<td>Place data near users</td>
<td>Low latency, data residency</td>
<td>Multi-region apps, GDPR residency</td>
</tr>
<tr>
<td>Consistency Models (Strong/Eventual)</td>
<td>Pick latency vs guarantees</td>
<td>Cross-region apps, offline tolerance</td>
<td>Cart totals vs likes counters</td>
</tr>
<tr>
<td>API Gateway</td>
<td>Central entry: auth, routing, limits</td>
<td>Many services, uniform policies</td>
<td>Public API front door, mTLS termination</td>
</tr>
<tr>
<td>Webhooks &amp; Outboxes</td>
<td>Reliable external notifications</td>
<td>Integrations, third-party callbacks</td>
<td>Payment status updates, CRM sync</td>
</tr>
<tr>
<td>Blob/Object Storage</td>
<td>Cheap infinite files</td>
<td>Media, backups, exports</td>
<td>User uploads, data lakes</td>
</tr>
<tr>
<td>Workflow Orchestrator (Airflow/Temporal)</td>
<td>Durable, reliable step with state</td>
<td>Long-running jobs, SLAs</td>
<td>Report generation, video pipelines</td>
</tr>
<tr>
<td>Blue-Green / Canary Deploys</td>
<td>Shift traffic gradually</td>
<td>Safer releases, quick rollback</td>
<td>API rollout, config changes</td>
</tr>
<tr>
<td>Feature Flags</td>
<td>Runtime on/off % rollouts</td>
<td>Experimentation, kill-switches</td>
<td>A/B tests, dark launches</td>
</tr>
<tr>
<td>Schema Migration Strategy</td>
<td>Backward-/forward-compatible changes</td>
<td>Zero-downtime DB upgrades</td>
<td>Expand-migrate-contract patterns</td>
</tr>
<tr>
<td>Distributed Locks / Leader Election</td>
<td>Coordinate one active worker</td>
<td>Cron uniqueness, shared ownership</td>
<td>Single consumer, partition leader</td>
</tr>
<tr>
<td>Observability (Logs/Metrics/Traces)</td>
<td>See what the system is doing</td>
<td>SLOs, debugging, capacity planning</td>
<td>P99 latency, error budgets, trace trees</td>
</tr>
<tr>
<td>Security: AuthN/AuthZ</td>
<td>Verify identity and permissions</td>
<td>Multi-tenant products, external APIs</td>
<td>OAuth2/OIDC, RBAC/ABAC</td>
</tr>
<tr>
<td>Multi-Tenancy (Pool/Bridge/Isolated)</td>
<td>Resource &amp; data isolation levels</td>
<td>SaaS with many customers</td>
<td>Per-tenant DBs vs shared schema</td>
</tr>
<tr>
<td>Edge Compute / Functions</td>
<td>Run logic near the user</td>
<td>Latency-sensitive, light workloads</td>
<td>Personalization at edge, AB tests</td>
</tr>
<tr>
<td>Rate-Aware DB Patterns</td>
<td>Batch, queue, throttle at DB edge</td>
<td>Hot partitions, lock contention</td>
<td>Bulk imports, ID sequence hot-spot</td>
</tr>
<tr>
<td>Pagination Strategies</td>
<td>Keyset + Offset for big data</td>
<td>Infinite scroll, large tables</td>
<td>Feed pagination, admin lists</td>
</tr>
</tbody>
</table>
<h2 id="how-to-use-this-cheat-sheet">
 How to Use This Cheat Sheet
<p><a class="anchor" href="#how-to-use-this-cheat-sheet">#</a></p></h2>
