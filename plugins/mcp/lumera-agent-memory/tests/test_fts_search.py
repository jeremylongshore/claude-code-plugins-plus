"""
Test SQLite FTS5 search functionality.
"""

import pytest
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from index.index import MemoryIndex


@pytest.fixture
def temp_index():
    """Create temporary index for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    index = MemoryIndex(db_path=db_path)
    yield index

    # Cleanup
    Path(db_path).unlink(missing_ok=True)


def test_store_and_search_basic(temp_index):
    """Basic store and search should work."""
    # Store a memory
    memory_card = {
        "title": "Deploy API to production",
        "summary_bullets": ["User requested deployment", "Using AWS infrastructure"],
        "keywords": ["deploy", "api", "production", "aws"]
    }

    temp_index.store_memory(
        session_id="sess_001",
        cascade_uri="cascade://sha256:abc123",
        memory_card=memory_card,
        tags=["deployment", "aws"]
    )

    # Search for it
    results = temp_index.search("deploy production")

    assert len(results) == 1
    assert results[0]["session_id"] == "sess_001"
    assert results[0]["cascade_uri"] == "cascade://sha256:abc123"
    assert "Deploy API" in results[0]["title"]


def test_fts_ranking(temp_index):
    """FTS should rank results by relevance."""
    # Store multiple memories
    memories = [
        ("sess_001", "Deploy production API", ["deploy", "production", "api"], "cascade://sha256:aaa"),
        ("sess_002", "Production deployment checklist", ["production", "deploy"], "cascade://sha256:bbb"),
        ("sess_003", "Development environment setup", ["dev", "setup"], "cascade://sha256:ccc"),
    ]

    for session_id, title, keywords, uri in memories:
        temp_index.store_memory(
            session_id=session_id,
            cascade_uri=uri,
            memory_card={"title": title, "keywords": keywords},
            tags=[]
        )

    # Search for "production deploy"
    results = temp_index.search("production deploy", limit=10)

    # Should find production-related sessions first
    assert len(results) >= 2
    assert results[0]["session_id"] in ["sess_001", "sess_002"]
    assert results[0]["score"] > 0


def test_tag_filtering(temp_index):
    """Tag filtering should work."""
    # Store memories with different tags
    temp_index.store_memory(
        session_id="sess_001",
        cascade_uri="cascade://sha256:aaa",
        memory_card={"title": "AWS deployment", "keywords": ["aws"]},
        tags=["aws", "deployment"]
    )

    temp_index.store_memory(
        session_id="sess_002",
        cascade_uri="cascade://sha256:bbb",
        memory_card={"title": "GCP deployment", "keywords": ["gcp"]},
        tags=["gcp", "deployment"]
    )

    # Search with tag filter
    results = temp_index.search("deployment", tags=["aws"])

    assert len(results) == 1
    assert results[0]["session_id"] == "sess_001"


def test_time_range_filtering(temp_index):
    """Time range filtering should work."""
    from datetime import datetime, timedelta

    # Store memory
    temp_index.store_memory(
        session_id="sess_001",
        cascade_uri="cascade://sha256:aaa",
        memory_card={"title": "Test memory", "keywords": ["test"]},
        tags=[]
    )

    # Search with future time range (should find nothing)
    future_start = (datetime.utcnow() + timedelta(days=1)).isoformat()
    results = temp_index.search(
        "test",
        time_range={"start": future_start}
    )

    assert len(results) == 0

    # Search with past time range (should find the memory)
    past_start = (datetime.utcnow() - timedelta(days=1)).isoformat()
    results = temp_index.search(
        "test",
        time_range={"start": past_start}
    )

    assert len(results) == 1


def test_limit_results(temp_index):
    """Result limiting should work."""
    # Store many memories
    for i in range(20):
        temp_index.store_memory(
            session_id=f"sess_{i:03d}",
            cascade_uri=f"cascade://sha256:{i:03d}",
            memory_card={"title": f"Memory {i}", "keywords": ["test"]},
            tags=[]
        )

    # Search with limit
    results = temp_index.search("test", limit=5)

    assert len(results) == 5


def test_get_by_cascade_uri(temp_index):
    """Lookup by Cascade URI should work."""
    memory_card = {"title": "Test", "keywords": ["test"]}
    cascade_uri = "cascade://sha256:test123"

    temp_index.store_memory(
        session_id="sess_001",
        cascade_uri=cascade_uri,
        memory_card=memory_card,
        tags=["test"],
        metadata={"custom": "data"}
    )

    # Retrieve by URI
    entry = temp_index.get_by_cascade_uri(cascade_uri)

    assert entry is not None
    assert entry["session_id"] == "sess_001"
    assert entry["memory_card"] == memory_card
    assert entry["tags"] == ["test"]
    assert entry["metadata"]["custom"] == "data"


def test_snippet_in_search_results(temp_index):
    """Search results should include snippets."""
    memory_card = {
        "title": "Deploy API to AWS",
        "summary_bullets": ["User requested deployment to production", "Using ECS clusters"],
        "keywords": ["deploy", "aws", "ecs"]
    }

    temp_index.store_memory(
        session_id="sess_001",
        cascade_uri="cascade://sha256:abc",
        memory_card=memory_card,
        tags=[]
    )

    results = temp_index.search("deploy")

    assert len(results) == 1
    assert "snippet" in results[0]
    assert len(results[0]["snippet"]) > 0
