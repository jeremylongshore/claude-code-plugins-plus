# Debug-Endpoint Remediation Playbook

## Spring Boot Actuator

### Narrow the exposed endpoints (preferred)

Default Spring Boot 3.x already only exposes `health` + `info`. If
something widened the surface, narrow it back:

`application-prod.yml`:

```yaml
management:
  endpoints:
    web:
      exposure:
        include: health, info
        exclude: env, heapdump, jolokia, configprops, beans, mappings, threaddump, loggers
  endpoint:
    health:
      show-details: never  # or 'when-authorized'
```

### Require auth on Actuator endpoints

For internal-ops use of Actuator, gate behind authentication:

```yaml
management:
  endpoints:
    web:
      base-path: /internal/actuator  # not /actuator
```

`SecurityConfig.java`:

```java
@Configuration
public class ActuatorSecurityConfig {
    @Bean
    SecurityFilterChain actuatorChain(HttpSecurity http) throws Exception {
        http.securityMatcher(EndpointRequest.toAnyEndpoint())
            .authorizeHttpRequests(a -> a.anyRequest().hasRole("ACTUATOR_ADMIN"))
            .httpBasic(Customizer.withDefaults());
        return http.build();
    }
}
```

Or restrict by IP in a reverse proxy (nginx):

```nginx
location /actuator/ {
    allow 10.0.0.0/8;
    deny all;
    proxy_pass http://springapp:8080;
}
```

### Disable Jolokia entirely (most aggressive)

`pom.xml`:

```xml
<!-- Remove the dependency -->
<dependency>
    <groupId>org.jolokia</groupId>
    <artifactId>jolokia-core</artifactId>
    <!-- ... DELETE THIS BLOCK ... -->
</dependency>
```

Or via `application.yml`:

```yaml
management:
  endpoint:
    jolokia:
      access: NONE
```

## Apache mod_status

### Disable globally (preferred for production)

`httpd.conf`:

```apache
# Comment out or remove the mod_status load
# LoadModule status_module modules/mod_status.so

# Remove the Location block
# <Location "/server-status">
#     SetHandler server-status
#     Require local
# </Location>
```

### If needed, lock down by IP

```apache
<Location "/server-status">
    SetHandler server-status
    Require ip 10.0.0.0/8
    Require ip 192.168.0.0/16
    # Require local  # already includes 127.0.0.1 + IPv6 loopback
</Location>

<Location "/server-info">
    SetHandler server-info
    Require ip 10.0.0.0/8
</Location>

# Disable ExtendedStatus to stop URL disclosure in scoreboard
ExtendedStatus Off
```

## nginx stub_status

```nginx
location = /nginx_status {
    stub_status;
    allow 10.0.0.0/8;
    deny all;
}
```

Or remove the block entirely if not needed.

## Prometheus /metrics

### Add bearer-token auth

`application.yml` (Spring Boot example):

```yaml
management:
  endpoint:
    prometheus:
      enabled: true
  metrics:
    export:
      prometheus:
        enabled: true

# Apply security to the metrics path:
spring:
  security:
    user:
      name: prometheus
      password: ${PROMETHEUS_SCRAPE_PASSWORD}
```

### Or restrict by IP at the reverse proxy

```nginx
location /metrics {
    allow 10.0.10.5/32;  # the prometheus server IP
    deny all;
    proxy_pass http://app:8080;
}
```

### Audit metric labels for credential leaks

Run a sanity scan over the actual metric output:

```bash
curl -s http://localhost:8080/metrics | grep -iE 'token=|password=|key=|secret=' | head -20
```

If any labels contain credentials, fix the metric emission code to
sanitize / drop those labels before scraping.

## Elasticsearch _cat /_search

### Enable security (free in 7.x+ Basic license)

`elasticsearch.yml`:

```yaml
xpack.security.enabled: true
xpack.security.authc:
  api_key.enabled: true
xpack.security.transport.ssl.enabled: true
```

Then create users:

```bash
./bin/elasticsearch-setup-passwords interactive
# Set passwords for: elastic, apm_system, kibana_system, logstash_system, beats_system
```

Update Kibana + Logstash + Beats to authenticate with their new
credentials.

### Restrict to internal network

```yaml
# elasticsearch.yml
network.host: 10.0.10.42  # internal IP only, NOT 0.0.0.0
```

Or at the firewall: block 9200 from public internet entirely.

## Kibana / Grafana / Eureka / Consul

All four follow the same pattern: gate behind reverse-proxy auth or
move to internal-network-only.

### nginx reverse proxy with basic auth

```nginx
server {
    listen 443 ssl;
    server_name internal-grafana.example.com;
    location / {
        auth_basic "Restricted";
        auth_basic_user_file /etc/nginx/.htpasswd;
        proxy_pass http://grafana:3000;
    }
}
```

### Consul ACL bootstrap

```bash
consul acl bootstrap
# Returns SecretID; store securely
# Create policy that denies anonymous access:
consul acl policy create -name "anonymous-deny" -rules='node_prefix "" { policy = "deny" } service_prefix "" { policy = "deny" }'
consul acl token update -id 00000000-0000-0000-0000-000000000002 -policy-name anonymous-deny
```

## phpMyAdmin

### Disable / remove entirely (preferred)

```bash
sudo apt-get remove phpmyadmin
sudo a2disconf phpmyadmin
sudo systemctl reload apache2
```

If you can't remove it because legacy ops use it:

### Restrict at the web server

```apache
<Directory /usr/share/phpmyadmin/>
    Require ip 10.0.0.0/8
    # Or use IP-based ACL specific to ops jump hosts
</Directory>
```

Or move it to a non-default path:

```apache
Alias /admin-tools-only-internal-do-not-share/phpmyadmin /usr/share/phpmyadmin
```

(Security by obscurity is not security, but combined with IP
restriction it's defense-in-depth.)

## GraphQL Playground / GraphiQL

### Apollo Server 4.x

```typescript
const server = new ApolloServer({
    typeDefs,
    resolvers,
    // Playground is OFF by default in production (NODE_ENV=production)
    introspection: process.env.NODE_ENV !== 'production',
});
```

### graphql-yoga

```typescript
import { createYoga } from 'graphql-yoga';
const yoga = createYoga({
    schema,
    graphiql: process.env.NODE_ENV !== 'production',
    landingPage: false,
});
```

### Express + express-graphql (legacy)

```javascript
app.use('/graphql', graphqlHTTP({
    schema,
    graphiql: false,  // disable in production
}));
```

## Swagger UI / OpenAPI

### Spring (springdoc-openapi)

```yaml
springdoc:
  swagger-ui:
    enabled: false  # disable in production
  api-docs:
    enabled: false
```

Or via profile:

```yaml
# application-prod.yml
springdoc:
  swagger-ui:
    enabled: false
```

### FastAPI

```python
app = FastAPI(
    docs_url=None if PRODUCTION else "/docs",
    redoc_url=None if PRODUCTION else "/redoc",
    openapi_url=None if PRODUCTION else "/openapi.json",
)
```

### Express + swagger-ui-express

Wrap with auth or skip mounting in production:

```javascript
if (process.env.NODE_ENV !== 'production') {
    app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(spec));
}
```

## Django

### Production settings

```python
# settings/production.py
DEBUG = False  # CRITICAL — never True in prod

# Remove debug toolbar from INSTALLED_APPS and MIDDLEWARE for prod
if DEBUG:
    INSTALLED_APPS.append('debug_toolbar')
    MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')
```

## Go expvar / pprof

Don't import `_ "net/http/pprof"` in production. Pull the import into
a build tag:

```go
// +build !production

package main

import _ "net/http/pprof"
```

Or expose pprof on a separate internal-only mux:

```go
go func() {
    // Internal-network-only listener
    log.Fatal(http.ListenAndServe("127.0.0.1:6060", nil))
}()
```

## CI integration

```yaml
- name: Debug-endpoint posture gate
  run: |
    python3 plugins/security/penetration-tester/skills/detecting-debug-endpoints/scripts/probe_debug.py \
        "${{ secrets.STAGING_URL }}" \
        --authorized \
        --min-severity high \
        --format json \
        --output debug-endpoint-report.json
- run: |
    if jq 'any(.severity == "critical" or .severity == "high")' debug-endpoint-report.json | grep -q true; then
      echo "::error::Debug endpoint posture regression"
      exit 1
    fi
```

## Verification after remediation

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/detecting-debug-endpoints/scripts/probe_debug.py \
    https://example.com --authorized --min-severity medium
```

Expected: exit 0, zero MEDIUM-or-higher findings. INFO findings on
deliberately-public Swagger / OpenAPI docs are operational choices.
