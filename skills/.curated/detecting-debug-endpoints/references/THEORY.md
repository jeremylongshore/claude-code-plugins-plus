# Debug-Endpoint Theory

## The recurring pattern

Modern application frameworks ship rich introspection by default
because developers need it to debug locally. The framework defaults
assume "this is running on my laptop in development mode." The
production deploy inherits the same defaults unless someone
explicitly disables them. The result is a class of finding that's
almost universal: any non-trivial Spring Boot / Apache / Prometheus /
ELK / Consul deployment exposes at least one of these endpoints
unless an operator went out of their way to disable them.

Each framework deserves its own short explanation.

## Spring Boot Actuator

Actuator is Spring Boot's introspection module. By default (in
Spring Boot 2.x with `management.endpoints.web.exposure.include=*`),
it exposes a JSON-shaped tree at `/actuator/` with endpoints like:

- `/actuator/env` — every Spring configuration property and every
  environment variable, including database URLs, API keys read from
  env, and JVM args.
- `/actuator/heapdump` — a live JVM heap dump (HPROF binary).
  Contains all in-memory state: connection pool internals, recent
  request data, cached credentials, JWT signing keys if they're
  string-allocated.
- `/actuator/jolokia` — JMX-over-HTTP. With write permissions, this
  is pre-auth RCE: an attacker can invoke arbitrary JMX MBeans
  including `javax.management.Diagnostic.threadDump` and (with the
  right MBean) execute arbitrary code.
- `/actuator/loggers` — POST changes log level for any package at
  runtime. An attacker can silence logs of their own activity by
  setting `org.springframework.security` to OFF.
- `/actuator/threaddump` — current thread state. Reveals which
  business operations are in flight + stack traces with method
  names (informs targeted attacks).
- `/actuator/health` — dependency state ("UP" / "DOWN" per
  database / cache / external service). Maps the internal topology.
- `/actuator/mappings` — full route table including paths the public
  app doesn't expose anywhere else.

Spring Boot 2.x default was exposure-everything; Spring Boot 3.x
default narrowed to `/health` + `/info` only. Many deployments still
have legacy 2.x-era `management.endpoints.web.exposure.include=*`
overrides in `application-prod.yml` that wasn't audited at the 3.x
upgrade.

The combined finding chain: `/actuator/env` exposes the database
connection string + creds. Connect to the database directly. End.

## Apache mod_status

`mod_status` exposes server runtime stats at `/server-status`:

- Apache version + OS
- Active worker count + idle workers
- **The URL of every active request** (the "Scoreboard" extended
  view, enabled by `ExtendedStatus On`)
- The client IP of every active connection

The URL-disclosure axis is the operational risk: any session token,
OAuth code, or password-in-query-string that flows through Apache is
visible to anyone polling `/server-status`. A scraper hitting it
once a second can collect tokens at scale.

The default in older Apache versions was to allow `/server-status`
from localhost; many configs were edited to allow internal IP ranges,
then forgotten about as networks evolved.

## nginx stub_status

`/nginx_status` exposes connection counts and request counts. Less
sensitive than Apache's mod_status (doesn't show URLs) but still
operational telemetry the attacker shouldn't have. Common on
deployments that copy-pasted `stub_status on;` from a tutorial.

## Prometheus /metrics

Prometheus's `/metrics` endpoint is the data source for monitoring.
The exposed surface is the application's own metric series.

The non-obvious risk: metric LABELS often contain credentials by
accident. A "request count by endpoint" series might label requests
by full URL including query string. A "database connection state"
metric might label connections by full connection string. The
labels are designed for Grafana queries; they're not designed to be
adversarially scrutinized.

Common label-leak categories:

- `http_requests_total{path="/api/users?token=...", ...}`
- `database_connections_active{dsn="postgresql://user:pass@..."}`
- `external_api_calls_total{key="sk-..."}`

The fix is twofold: bring the endpoint behind auth (a static bearer
token is the conventional Prometheus pattern), AND audit the label
cardinality for accidental credential disclosure.

## Elasticsearch _cat /_search

Elasticsearch endpoints under `/_cat/` and `/_cluster/` expose
cluster state, indices, document counts, and node metadata. The
`/_search` endpoint serves arbitrary queries against any visible
index without authentication if the cluster is unconfigured.

The historical pattern: Elasticsearch shipped with no auth defaults
until version 7.x (the Basic license added security in late 2020).
A cluster set up before that date and never upgraded with security
enabled is fully open to anyone who can reach port 9200.

The Shodan-style internet scan of exposed Elasticsearch clusters is
a recurring "another data breach" story; the underlying issue is
always this misconfiguration.

## Kibana / Grafana / Eureka / Consul

Service-discovery and observability panels. Each can expose:

- Kibana: full search of Elasticsearch indices through the UI
- Grafana: dashboards that may include connection strings in
  variable definitions
- Eureka: service registry with internal IPs + ports of every
  microservice
- Consul: service catalog + agent checks with full topology

For Eureka and Consul specifically, the API is designed to be
read-mostly from inside the service mesh. Exposing it externally
hands an attacker the network map.

## phpMyAdmin

GUI for MySQL/MariaDB administration. Many shared-hosting
installations include it at `/phpmyadmin/` by default; legacy LAMP
stacks deploy it next to the app. If reachable AND unauthenticated
(or with default credentials), it's full DB access via web GUI.

Fingerprint: HTML body containing "phpMyAdmin" + a login form with
`name="pma_username"`.

## GraphQL Playground / GraphiQL

Interactive GraphQL UI for developers. Enabled by default in many
GraphQL server setups (Apollo Server, graphql-yoga). The risk has
two layers:

1. **Schema introspection** — the playground reveals the full
   schema, which informs every subsequent query/mutation attack.
2. **Query execution** — if the GraphQL endpoint is publicly
   reachable AND the playground is too, the attacker has both a
   schema map AND an interactive interface to craft attacks against
   it.

Best practice: disable introspection in production, disable the
playground in production. Apollo Server 4.x has both off by default
in `NODE_ENV=production`; older versions need explicit config.

## Swagger UI / OpenAPI

Same pattern as GraphQL: the schema (OpenAPI spec) tells an attacker
what endpoints exist, what parameters they accept, what response
shapes look like. Exposing `/swagger-ui` or `/openapi.json` on
production isn't a critical vulnerability but it's free recon.

Some defensive postures keep Swagger publicly reachable as a feature
(public API docs). That's a deliberate choice; the finding is
informational unless the API itself has auth issues.

## Django debug toolbar

If `DEBUG=True` shipped to production, the Django debug toolbar
exposes SQL queries, request env, settings, template context.
Effectively equivalent to `/actuator/env` for Django stacks.

## Go expvar / pprof

Built-in Go stdlib endpoints:

- `/debug/vars` — JSON dump of expvar package: cmdline, memstats,
  custom-registered metrics
- `/debug/pprof/` — pprof profiles for CPU, heap, goroutines

The pprof endpoints can be triggered to start CPU profiling that
slows the server, AND can be used to download heap profiles that
contain live memory state (similar risk to Spring Boot heapdump).

If Go's `net/http/pprof` package is imported anywhere in the app
(it auto-registers handlers on the default mux), and the default
mux is exposed externally, pprof is reachable.

## Why fingerprint-checking matters

Same logic as `detecting-exposed-secrets-files` (#6). SPAs return
their `index.html` for any unknown route. Without fingerprinting,
every `/actuator/*` probe returns 200 against an SPA, all false
positives.

Each framework has a distinctive body fingerprint:

- Actuator: JSON `{"_links":...}` or `"propertySources"`
- mod_status: HTML containing "Apache Server Status"
- Prometheus: text starting with `# HELP` or `# TYPE`
- Elasticsearch: tabular text with status indicators
- phpMyAdmin: HTML containing "phpMyAdmin" + `pma_username`
- Jolokia: JSON `{"agent":"jolokia"}`

The fingerprint check is what separates a real finding from SPA
noise.

## Primary sources

- [OWASP WSTG-CONF-05 — Enumerate Infrastructure and Application Admin Interfaces](https://owasp.org/www-project-web-security-testing-guide/v42/4-Web_Application_Security_Testing/02-Configuration_and_Deployment_Management_Testing/05-Enumerate_Infrastructure_and_Application_Admin_Interfaces)
- [Spring Boot Actuator docs — Production-ready features](https://docs.spring.io/spring-boot/docs/current/reference/html/actuator.html)
- [Apache mod_status docs](https://httpd.apache.org/docs/2.4/mod/mod_status.html)
- [CWE-749 — Exposed Dangerous Method or Function](https://cwe.mitre.org/data/definitions/749.html)
- [CWE-285 — Improper Authorization](https://cwe.mitre.org/data/definitions/285.html)
- [Jolokia security advisory background](https://jolokia.org/reference/html/security.html)
