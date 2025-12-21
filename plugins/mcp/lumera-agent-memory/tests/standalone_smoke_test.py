#!/usr/bin/env python3
"""
Standalone smoke test: store → query → retrieve with memory_card.
Tests core functionality without requiring MCP SDK.
"""

import asyncio
import json
import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from security.redact import redact_session
from security.encrypt import encrypt_data, decrypt_data
from cascade.mock_fs import MockCascadeFS
from index.index import MemoryIndex


async def smoke_test():
    """End-to-end smoke test."""
    print("\n" + "="*60)
    print("LUMERA AGENT MEMORY - STANDALONE SMOKE TEST")
    print("="*60 + "\n")

    # Use temp storage
    temp_dir = Path(tempfile.mkdtemp(prefix="lumera_smoke_"))
    cascade = MockCascadeFS(storage_dir=str(temp_dir / "cascade"))
    index = MemoryIndex(db_path=str(temp_dir / "index.db"))

    print(f"✓ Using temp storage: {temp_dir}\n")

    # Test 1: Store session
    print("TEST 1: Store session to Cascade")
    print("-" * 40)

    # Mock session from CASS
    session_data = {
        "session_id": "test_session_001",
        "messages": [
            {
                "role": "user",
                "content": "Deploy the new API with my AWS key AKIAIOSFODNN7EXAMPLE",
                "timestamp": "2025-01-15T10:30:00Z"
            },
            {
                "role": "assistant",
                "content": "I'll help deploy the API. What region?",
                "timestamp": "2025-01-15T10:30:15Z"
            },
            {
                "role": "user",
                "content": "us-east-1, my email is john@example.com for notifications",
                "timestamp": "2025-01-15T10:31:00Z"
            }
        ],
        "metadata": {
            "started_at": "2025-01-15T10:30:00Z",
            "ended_at": "2025-01-15T10:35:00Z"
        }
    }

    # Redact
    redacted_data, redaction_report = redact_session(session_data)
    print(f"Redaction rules fired: {len(redaction_report.rules_fired)}")
    for rule in redaction_report.rules_fired:
        print(f"  - {rule.rule_name}: {rule.count} occurrence(s)")

    # Generate memory card
    def generate_memory_card(session_data):
        messages = session_data.get("messages", [])
        text_parts = []
        for msg in messages:
            if isinstance(msg.get("content"), str):
                text_parts.append(msg["content"])

        full_text = " ".join(text_parts)

        title = "Untitled Session"
        for msg in messages:
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if isinstance(content, str) and len(content) > 0:
                    title = content[:80] + ("..." if len(content) > 80 else "")
                    break

        words = full_text.lower().split()
        word_freq = {}
        for word in words:
            if len(word) > 4:
                word_freq[word] = word_freq.get(word, 0) + 1

        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        keywords = [w[0] for w in keywords]

        entities = set()
        for word in full_text.split():
            if word and word[0].isupper() and len(word) > 2:
                entities.add(word)

        return {
            "title": title,
            "keywords": keywords,
            "entities": list(entities)[:10]
        }

    memory_card = generate_memory_card(redacted_data)

    # Encrypt
    crypto_result = encrypt_data(json.dumps(redacted_data))
    print(f"Crypto: {crypto_result.algorithm} ({len(crypto_result.ciphertext)} bytes)")

    # Upload to Cascade
    cascade_uri = await cascade.upload_blob(crypto_result.ciphertext)
    print(f"Cascade URI: {cascade_uri}")

    # Index locally
    index.store_memory(
        session_id="test_session_001",
        cascade_uri=cascade_uri,
        memory_card=memory_card,
        tags=["deployment", "aws", "production"],
        metadata={
            "crypto": {
                "key_id": crypto_result.key_id,
                "plaintext_sha256": crypto_result.plaintext_sha256,
                "ciphertext_sha256": crypto_result.ciphertext_sha256
            },
            "redaction": redaction_report.to_dict()
        }
    )

    print(f"\nMemory Card:")
    print(f"  Title: {memory_card['title']}")
    print(f"  Keywords: {', '.join(memory_card['keywords'][:5])}")
    print(f"  Entities: {', '.join(memory_card['entities'])}")

    print("\n✓ PASS: Session stored successfully\n")

    # Test 2: Query memories
    print("TEST 2: Query memories via FTS")
    print("-" * 40)

    hits = index.search("deploy aws", tags=["deployment"], limit=5)
    print(f"Query: 'deploy aws'")
    print(f"Hits: {len(hits)}")

    for i, hit in enumerate(hits, 1):
        print(f"\n  Hit {i}:")
        print(f"    Session: {hit['session_id']}")
        print(f"    Title: {hit['title']}")
        print(f"    Snippet: {hit['snippet'][:100]}...")
        print(f"    Score: {hit['score']:.4f}")

    assert len(hits) > 0, "No results found"
    print("\n✓ PASS: Query returned results\n")

    # Test 3: Retrieve session
    print("TEST 3: Retrieve session from Cascade")
    print("-" * 40)

    # Download
    encrypted_blob = await cascade.download_blob(cascade_uri)

    # Get metadata
    index_entry = index.get_by_cascade_uri(cascade_uri)
    expected_sha256 = index_entry["metadata"]["crypto"]["ciphertext_sha256"]

    # Decrypt
    session_json = decrypt_data(encrypted_blob, expected_ciphertext_sha256=expected_sha256)
    retrieved_session = json.loads(session_json)

    print(f"Retrieved URI: {cascade_uri}")
    print(f"Crypto verified: True")
    print(f"Session messages: {len(retrieved_session['messages'])}")
    print(f"\nMemory Card (from index):")
    print(f"  Title: {index_entry['memory_card']['title']}")

    # Check redaction worked
    session_str = json.dumps(retrieved_session)
    print(f"\nRedaction check:")
    if "[REDACTED:AWS_ACCESS_KEY]" in session_str:
        print("  ✓ AWS access key redacted")
    if "[REDACTED:EMAIL]" in session_str:
        print("  ✓ Email redacted")

    print("\n✓ PASS: Session retrieved and verified\n")

    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)

    print("="*60)
    print("ALL TESTS PASSED ✓")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(smoke_test())
