# Integration and Infrastructure Testing

## Contents

[Purpose](#purpose) · [Integration Test Patterns](#integration-test-patterns) · [Testcontainers — Per Language](#testcontainers--per-language) · [Database Integration](#database-integration) · [Fake / Stub Services](#fake--stub-services) · [Message-Queue Integration](#message-queue-integration) · [Migration Tests](#migration-tests) · [Infrastructure-as-Code Tests](#infrastructure-as-code-tests) · [Kubernetes Test Layer](#kubernetes-test-layer) · [Enforcement Checklist](#enforcement-checklist) · [Sources](#sources)

## Purpose

Unit tests verify components in isolation. Integration tests verify they
work together *against real dependencies*. Infrastructure tests verify
that the code's environment itself is correct. This reference catalogs
what belongs in these layers and how to audit their presence.

The sweep flags a repo as **P0-incomplete** if it has unit tests but zero
integration tests and the code obviously has external dependencies
(database, message queue, HTTP clients, filesystem).

## Integration Test Patterns

### The test-pyramid sweet spot

Mike Cohn's classic pyramid: many unit → some integration → few E2E.

```
                    /\
                   /  \   E2E (slow, brittle, real browser/device)
                  /____\
                 /      \
                /        \  Integration (real deps, fast if scoped)
               /__________\
              /            \
             /              \  Unit (many, fast, isolated)
            /________________\
```

Integration tests are the most undersupplied layer in most repos. The
sweep looks for their presence explicitly.

### Arrange-Act-Assert with real dependencies

```python
def test_user_can_register(postgres_container, smtp_fake):
    # Arrange: real database, stubbed email
    client = TestClient(app, db_url=postgres_container.url)
    # Act
    res = client.post("/register", json={"email": "a@b.c", "pw": "s3cr3t"})
    # Assert
    assert res.status_code == 201
    assert smtp_fake.last_message.to == ["a@b.c"]
    assert postgres_container.query("SELECT count(*) FROM users") == [(1,)]
```

### Scope discipline

Integration tests must **not** cross system boundaries they don't own
(don't hit production APIs in tests). Use stubs for external HTTP
dependencies; use real containers for self-owned infra.

## Testcontainers — Per Language

The gold standard for integration tests against real infra. Each language
has an idiomatic port.

### Node.js / TypeScript

```bash
pnpm add -D testcontainers
```

```ts
import { PostgreSqlContainer } from "@testcontainers/postgresql";

test("queries users", async () => {
  const pg = await new PostgreSqlContainer().start();
  const client = new Client({ connectionString: pg.getConnectionUri() });
  await client.connect();
  // ...
  await pg.stop();
});
```

### Python

```bash
uv add --dev testcontainers[postgres,redis,kafka]
```

```python
from testcontainers.postgres import PostgresContainer

def test_db_migration():
    with PostgresContainer("postgres:16") as pg:
        engine = create_engine(pg.get_connection_url())
        # ...
```

Or `pytest-docker` fixture pattern for docker-compose-backed fixtures.

### Go

```bash
go get github.com/testcontainers/testcontainers-go
go get github.com/testcontainers/testcontainers-go/modules/postgres
```

```go
func TestPg(t *testing.T) {
  ctx := context.Background()
  pg, _ := postgres.Run(ctx, "postgres:16")
  defer pg.Terminate(ctx)
  // ...
}
```

### Java / Kotlin

Testcontainers-Java is the *original* — Richard North's project.

```xml
<dependency>
  <groupId>org.testcontainers</groupId>
  <artifactId>postgresql</artifactId>
  <version>1.20.0</version>
  <scope>test</scope>
</dependency>
```

```java
@Testcontainers
class UserRepoTest {
  @Container PostgreSQLContainer<?> pg = new PostgreSQLContainer<>("postgres:16");
  @Test void queries() { /* use pg.getJdbcUrl() */ }
}
```

### Rust

`testcontainers-rs` — less mature than the JVM/Go/JS ecosystems but
functional.

```toml
[dev-dependencies]
testcontainers = "0.21"
testcontainers-modules = { version = "0.7", features = ["postgres"] }
```

### .NET

`Testcontainers` (via NuGet) — high-quality port.

```bash
dotnet add package Testcontainers.PostgreSql
```

### Ruby

`testcontainers-ruby` — community-maintained.

### Philosophy

**Always prefer Testcontainers over mocking** when the integration is
real (database, Redis, S3 with LocalStack, Kafka). The skill's bias is:
mocks are for units, containers are for integration. This avoids the
class of false-confidence tests that pass against a mock but fail
against the real service.

## Database Integration

### SQL databases

- **Raw testcontainers** for the DB server.
- **Migration testing**: run all migrations forward, then backward.
- **Concurrency tests**: 2+ connections competing for a row.
- **Index usage**: assert `EXPLAIN` plans don't regress (pgtap, pt-query-digest).
- **Seed data**: deterministic fixtures per test (rollback between tests).

Python-specific helpers:

- `pytest-postgresql`, `pytest-mysql`, `pytest-mongo`
- `factory_boy` for test data
- `Faker` for plausible data

### NoSQL

- **MongoDB**: testcontainers + mongock (migrations) / migrate-mongo.
- **DynamoDB**: DynamoDB Local (Java, can run in Docker).
- **Redis**: testcontainers; or `fakeredis` for Python unit-ish tests.
- **Cassandra**: `Testcontainers` has a Cassandra module.

## Fake / Stub Services

For external HTTP APIs the repo doesn't own:

| Tool | Ecosystem |
|---|---|
| **WireMock** | JVM + Docker, full record/replay |
| **Mountebank** | Node, multi-protocol (HTTP, TCP, SMTP) |
| **nock** | Node-only, in-process |
| **responses** | Python, `requests`-scoped |
| **vcr.py** / **VCR.rb** | Record live HTTP → replay |
| **Hoverfly** | Go, full simulation + spying |
| **MockServer** | JVM-based, supports HTTP/HTTPS/S |

Principle: **never hit third-party APIs in the test suite.** Record once,
replay forever, refresh cassettes quarterly.

### Contract testing (boundary verification)

- **Pact** — consumer-driven contracts (JVM, JS, Python, Go, Ruby, .NET).
- **Spring Cloud Contract** — Spring-flavored.
- **Schemathesis** — property-based from OpenAPI schema.

These prevent the "my stub agrees with my test" failure mode by
ensuring both sides of the contract verify the same spec.

## Message-Queue Integration

| Queue | Integration test pattern |
|---|---|
| **Kafka** | testcontainers-kafka + assert produced records |
| **RabbitMQ** | testcontainers RabbitMQ; assert queue state |
| **AWS SQS/SNS** | LocalStack via testcontainers |
| **NATS** | testcontainers NATS |
| **Redis pubsub** | testcontainers Redis + subscribe |
| **Azure Service Bus** | Azurite (emulator) |
| **GCP Pub/Sub** | Official `gcloud emulators pubsub` |

## Migration Tests

Database migrations are code. They must be tested like code.

| Framework | Test pattern |
|---|---|
| **Flyway** (JVM) | `flyway migrate && flyway validate` in CI against ephemeral DB |
| **Liquibase** | Same model; dry-run with `updateSQL` |
| **Alembic** (Python) | `alembic upgrade head && alembic downgrade base && alembic upgrade head` |
| **Prisma** (JS) | `prisma migrate deploy` on shadow DB |
| **Sequel** (Ruby) | `sequel -m db/migrations` in CI |
| **sqlx migrate** (Rust) | `sqlx migrate run` + compile-time checks |
| **golang-migrate** | `migrate -path ... up && migrate down` |

Essential tests per migration:

1. **Forward migration succeeds** (up runs cleanly)
2. **Backward migration succeeds** (down runs cleanly)
3. **Idempotency** (up twice is not worse than up once)
4. **Data preservation** (seed data → migrate → data still there)
5. **Performance on realistic data** (large table migration runs in budget)

## Infrastructure-as-Code Tests

Infra code deserves the same test discipline as app code.

### Terraform

| Tool | Model |
|---|---|
| **Terratest** (Gruntwork) | Go library; spin up real infra, assert, tear down. Expensive but authoritative. |
| **kitchen-terraform** | Test Kitchen for Terraform. |
| **rspec-terraform** | Ruby-flavored. |
| **Terraform native testing** (v1.6+) | `terraform test` with `.tftest.hcl` files. |
| **Open Policy Agent + Conftest** | Policy-as-code on plan output. |

Terraform test example:

```hcl
# main.tftest.hcl
run "validate_tags" {
  command = plan
  assert {
    condition     = aws_s3_bucket.main.tags["Owner"] != ""
    error_message = "Every bucket must have an Owner tag"
  }
}
```

### Pulumi

```bash
pulumi preview --policy-pack ../policy
pulumi test  # language-native (Go/Py/TS) test runners
```

### Ansible

- **molecule** — the standard. Runs playbooks against Docker/Vagrant.
- **ansible-lint** — static.
- **idempotency test** — run playbook twice, expect no changes on second run.

### Generic server configuration

- **InSpec** (Chef) — compliance-as-code. 1000s of ready-made profiles (CIS, PCI, HIPAA).
- **Serverspec** — Ruby, precursor to InSpec.
- **goss** — YAML-based server spec.

## Kubernetes Test Layer

| Tool | Purpose |
|---|---|
| **kubeconform** | Schema validation against Kubernetes OpenAPI |
| **kube-score** | Quality/security heuristics on manifests |
| **polaris** | Policy engine, built-in best-practice checks |
| **datree** | Policy-driven manifest validation (deprecated as SaaS, CLI OSS) |
| **kube-bench** | CIS Kubernetes Benchmark |
| **kube-hunter** | Penetration testing for K8s |
| **conftest** | OPA Rego against manifests |
| **pluto** | Detects deprecated API usage pre-upgrade |
| **kyverno** | Policy engine (admission + CLI) |
| **Open Policy Agent / Gatekeeper** | Admission policy enforcement |

Helm-specific:

- `helm lint` (syntax)
- `helm template | kubeconform -` (rendered validation)
- `helm unittest` (Helm chart unit tests)

GitOps (Flux/ArgoCD):

- **flux-kustomization** diff tests
- **argocd-diff-preview** PR comment
- drift-detection via **argocd app sync --dry-run**

## Enforcement Checklist

For every repo with external dependencies, verify:

- [ ] At least one integration test file exists
- [ ] Testcontainers (or equivalent) is a dev dependency
- [ ] Integration tests run in CI in a separate job (parallel to unit)
- [ ] Database migrations are tested forward + backward
- [ ] No integration test hits a production / third-party URL directly
- [ ] Fake/stub services are documented (cassettes, WireMock mappings)
- [ ] Contract tests exist for consumed APIs (Pact, Schemathesis)
- [ ] If the repo has IaC: Terratest / molecule / kitchen / terraform test exists
- [ ] If the repo has K8s: kubeconform + kube-score + polaris run in CI
- [ ] Infra drift detection is wired in (Atlantis / Spacelift / Terraform Cloud plan on PR)

## Sources

- Martin Fowler — "Integration Test" bliki entry (definitions + tradeoffs)
- Richard North — Testcontainers origin talk (JavaOne 2015)
- Mike Cohn — *Succeeding with Agile*, ch. 16 (test pyramid)
- Google SRE Book, ch. 17 "Testing for Reliability"
- "Accelerate" (Forsgren, Humble, Kim) — DORA metrics including deployment-test coverage
- CIS Kubernetes Benchmark (cisecurity.org)
- kubernetes.io test-infra docs
