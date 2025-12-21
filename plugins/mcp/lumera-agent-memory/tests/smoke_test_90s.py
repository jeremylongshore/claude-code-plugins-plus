"""
90-second smoke test: store → query → retrieve with memory_card.
"""

import asyncio
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp_server import LumeraMemoryServer


async def smoke_test():
    """End-to-end smoke test."""
    print("\n" + "="*60)
    print("LUMERA AGENT MEMORY - 90 SECOND SMOKE TEST")
    print("="*60 + "\n")

    # Create server instance
    server = LumeraMemoryServer()

    # Use temp storage
    import tempfile
    temp_dir = tempfile.mkdtemp(prefix="lumera_smoke_")
    server.cascade_mock.storage_dir = Path(temp_dir) / "cascade"
    server.index.db_path = Path(temp_dir) / "index.db"
    server.index._init_db()

    print(f"✓ Using temp storage: {temp_dir}\n")

    # Test 1: Store session
    print("TEST 1: Store session to Cascade")
    print("-" * 40)

    store_args = {
        "session_id": "test_session_001",
        "tags": ["deployment", "aws", "production"],
        "metadata": {"project": "api-gateway"},
        "mode": "mock"
    }

    result = await server._store_session(store_args)

    print(f"Session ID: {result['session_id']}")
    print(f"Cascade URI: {result['cascade_uri']}")
    print(f"Redaction rules fired: {len(result['redaction']['rules_fired'])}")
    for rule in result['redaction']['rules_fired']:
        print(f"  - {rule['rule']}: {rule['count']} occurrence(s)")
    print(f"Crypto: {result['crypto']['enc']} ({result['crypto']['bytes']} bytes)")
    print(f"\nMemory Card:")
    print(f"  Title: {result['memory_card']['title']}")
    print(f"  Keywords: {', '.join(result['memory_card']['keywords'][:5])}")
    print(f"  Entities: {', '.join(list(result['memory_card']['entities'])[:5])}")

    assert result["ok"], "Store failed"
    cascade_uri = result["cascade_uri"]

    print("\n✓ PASS: Session stored successfully\n")

    # Test 2: Query memories
    print("TEST 2: Query memories via FTS")
    print("-" * 40)

    query_args = {
        "query": "deploy aws production",
        "tags": ["deployment"],
        "limit": 5
    }

    result = await server._query_memories(query_args)

    print(f"Query: '{query_args['query']}'")
    print(f"Hits: {len(result['hits'])}")

    for i, hit in enumerate(result['hits'], 1):
        print(f"\n  Hit {i}:")
        print(f"    Session: {hit['cass_session_id']}")
        print(f"    Title: {hit['title']}")
        print(f"    Snippet: {hit['snippet'][:100]}...")
        print(f"    Score: {hit['score']:.4f}")
        print(f"    URI: {hit['cascade_uri']}")

    assert result["ok"], "Query failed"
    assert len(result["hits"]) > 0, "No results found"

    print("\n✓ PASS: Query returned results\n")

    # Test 3: Retrieve session
    print("TEST 3: Retrieve session from Cascade")
    print("-" * 40)

    retrieve_args = {
        "cascade_uri": cascade_uri,
        "mode": "mock"
    }

    result = await server._retrieve_session(retrieve_args)

    print(f"Retrieved URI: {result['cascade_uri']}")
    print(f"Crypto verified: {result['crypto']['verified']}")
    print(f"Session messages: {len(result['session']['messages'])}")
    print(f"\nMemory Card (from index):")
    print(f"  Title: {result['memory_card']['title']}")
    print(f"  Summary bullets: {len(result['memory_card']['summary_bullets'])}")
    print(f"  Decisions: {len(result['memory_card']['decisions'])}")
    print(f"  TODOs: {len(result['memory_card']['todos'])}")

    # Check redaction worked
    session_str = json.dumps(result['session'])
    print(f"\nRedaction check:")
    if "[REDACTED:AWS_ACCESS_KEY]" in session_str:
        print("  ✓ AWS access key redacted")
    if "[REDACTED:EMAIL]" in session_str:
        print("  ✓ Email redacted")

    assert result["ok"], "Retrieve failed"
    assert result["crypto"]["verified"], "Crypto verification failed"

    print("\n✓ PASS: Session retrieved and verified\n")

    # Test 4: Cost estimation
    print("TEST 4: Estimate storage cost")
    print("-" * 40)

    cost_args = {
        "bytes": result['crypto']['bytes'],  # Use actual encrypted size
        "redundancy": 3
    }

    result = await server._estimate_cost(cost_args)

    print(f"Data size: {result['bytes']} bytes ({result['gb']:.6f} GB)")
    print(f"Redundancy: {result['assumptions']['redundancy']}x")
    print(f"Monthly storage: ${result['monthly_storage_usd']:.4f}")
    print(f"Estimated requests: ${result['estimated_request_usd']:.4f}")
    print(f"Total estimated: ${result['total_estimated_usd']:.4f}/month")

    assert result["ok"], "Cost estimation failed"

    print("\n✓ PASS: Cost estimation complete\n")

    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)

    print("="*60)
    print("ALL TESTS PASSED ✓")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(smoke_test())
