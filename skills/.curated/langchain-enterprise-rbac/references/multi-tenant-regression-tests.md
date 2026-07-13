# Multi-tenant Regression Tests

The tests that would have caught **P33** on day one. Run them in CI on every PR that touches the chain / agent / retriever factory. A regression back to import-time retriever binding fails the suite immediately.

## Fixture: two tenants with distinct documents

```python
import pytest
from langchain_pinecone import PineconeVectorStore

@pytest.fixture(scope="module")
def two_tenant_store(pinecone_test_index):
    """Seeds Tenant A and Tenant B with distinct documents in separate namespaces."""
    acme = PineconeVectorStore(index_name=pinecone_test_index, namespace="acme", embedding=emb)
    initech = PineconeVectorStore(index_name=pinecone_test_index, namespace="initech", embedding=emb)

    acme.add_texts(
        ["Acme revenue Q3 was $42M", "Acme CEO is Wile E. Coyote"],
        ids=["acme-doc-1", "acme-doc-2"],
        metadatas=[{"tenant_id": "acme"}] * 2,
    )
    initech.add_texts(
        ["Initech revenue Q3 was $17M", "Initech CEO is Bill Lumbergh"],
        ids=["initech-doc-1", "initech-doc-2"],
        metadatas=[{"tenant_id": "initech"}] * 2,
    )
    yield
    # Cleanup — delete the test namespaces so the next run starts clean.
    acme.delete(delete_all=True)
    initech.delete(delete_all=True)
```

## The golden-query isolation test

```python
GOLDEN_QUERIES = [
    "what was Q3 revenue?",
    "who is the CEO?",
    "give me any document",
]

@pytest.mark.parametrize("query", GOLDEN_QUERIES)
def test_tenant_isolation(two_tenant_store, query):
    acme_result = chain.invoke(
        {"query": query},
        config={"configurable": {"tenant_id": "acme", "user_id": "t_u1"}},
    )
    initech_result = chain.invoke(
        {"query": query},
        config={"configurable": {"tenant_id": "initech", "user_id": "t_u1"}},
    )

    acme_ids    = {d.id for d in acme_result["documents"]}
    initech_ids = {d.id for d in initech_result["documents"]}

    # Hard assertion — no overlap, ever.
    overlap = acme_ids & initech_ids
    assert not overlap, f"CROSS-TENANT LEAK for query {query!r}: overlap={overlap}"

    # Positive assertion — each tenant sees only its own.
    assert all(i.startswith("acme-")    for i in acme_ids)
    assert all(i.startswith("initech-") for i in initech_ids)
```

The `overlap` set being non-empty is a P33 incident in CI. Fail the build.

## Test: missing tenant_id must raise

```python
def test_missing_tenant_raises_permission_error():
    with pytest.raises(PermissionError, match="tenant_id"):
        chain.invoke({"query": "anything"}, config={"configurable": {}})

def test_none_tenant_raises_permission_error():
    with pytest.raises(PermissionError, match="tenant_id"):
        chain.invoke({"query": "anything"}, config={"configurable": {"tenant_id": None}})

def test_empty_string_tenant_raises_permission_error():
    with pytest.raises(PermissionError, match="tenant_id"):
        chain.invoke({"query": "anything"}, config={"configurable": {"tenant_id": ""}})
```

The bug pattern this catches: a silent default like `tenant_id = config.get("tenant_id", "public")` that looks harmless but creates a shared namespace.

## Test: tool allowlist strictly enforced

```python
def test_viewer_agent_has_no_write_tools():
    agent = agent_for(user_role="viewer")
    tool_names = {t.name for t in agent.get_tools()}
    assert "delete_note" not in tool_names
    assert "create_note" not in tool_names
    assert tool_names == {"search_docs"}

def test_admin_agent_has_all_tools():
    agent = agent_for(user_role="admin")
    tool_names = {t.name for t in agent.get_tools()}
    assert tool_names == {"search_docs", "create_note", "delete_note", "export_audit"}

def test_unknown_role_raises():
    with pytest.raises(PermissionError, match="no tool access"):
        agent_for(user_role="nonexistent_role")
```

## Test: audit log emits on failure path

```python
def test_audit_log_emitted_on_exception(capsys):
    with pytest.raises(ValueError):
        with audit({"user_id": "u_1", "tenant_id": "t_1", "chain_name": "test"}):
            raise ValueError("boom")

    captured = capsys.readouterr()
    record = json.loads(captured.out.strip())
    assert record["outcome"] == "error"
    assert record["error_class"] == "ValueError"
    assert record["latency_ms"] >= 0
    assert "trace_id" in record

def test_audit_log_emitted_on_tool_denied(capsys):
    with pytest.raises(PermissionError):
        with audit({"user_id": "u_1", "tenant_id": "t_1", "chain_name": "test"}):
            raise PermissionError("SQL DROP forbidden")

    record = json.loads(capsys.readouterr().out.strip())
    assert record["outcome"] == "tool_denied"
```

The bug pattern this catches: audit logging inside the `try` block without a `finally` clause. The error path silently omits the record, so incident responders cannot see denied calls.

## Test: rate limiter is per-tenant, not global

```python
def test_rate_limiter_is_per_tenant():
    l1 = limiter_for("acme")
    l2 = limiter_for("initech")
    assert l1 is not l2, "limiter is a process-global singleton — tenants share quota"

def test_same_tenant_reuses_limiter():
    l1a = limiter_for("acme")
    l1b = limiter_for("acme")
    assert l1a is l1b, "limiter should be cached per tenant_id"
```

## Running in CI

```yaml
# .github/workflows/rbac-regression.yml (excerpt)
- name: Run RBAC regression suite
  env:
    PINECONE_API_KEY: ${{ secrets.PINECONE_TEST_KEY }}
    PINECONE_TEST_INDEX: ${{ vars.PINECONE_TEST_INDEX }}
  run: pytest tests/rbac/ -v --tb=short
```

Gate merges on this suite. Tag every RBAC-relevant test with `@pytest.mark.rbac` so you can also run `pytest -m rbac` locally.

## Mutation-testing angle

For extra assurance, run `mutmut` on the retriever factory and the allowlist code. The isolation tests should fail on every meaningful mutation — if they don't, your test coverage has a blind spot.

## What the tests do not cover

- Live rate-limiter behavior under load (needs a load test, not a unit test)
- Cloud-side RLS enforcement (needs an integration test against a real Postgres)
- Network-level tenant isolation (firewall / VPC concerns, out of scope)

These belong in a separate integration / security-review checklist, not the unit suite.

## Related

- [Retriever-per-request](retriever-per-request.md) — the factory these tests exercise
- [Role-scoped tool allowlist](role-scoped-tool-allowlist.md) — allowlist tests
- [Audit-log schema](audit-log-schema.md) — audit emission tests
- [Vector-store isolation](vector-store-isolation.md) — PGVector RLS integration test pattern
