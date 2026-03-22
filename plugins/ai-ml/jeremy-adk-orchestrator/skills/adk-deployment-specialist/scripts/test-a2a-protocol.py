#!/usr/bin/env python3
"""
test-a2a-protocol.py - Test A2A protocol endpoints for deployed ADK agent

Tests:
- AgentCard retrieval
- Task submission
- Status polling
- Protocol compliance
"""

import json
import sys
import time
from typing import Dict, Optional
import subprocess


def get_access_token() -> str:
    """Get GCP access token"""
    result = subprocess.run(
        ["gcloud", "auth", "print-access-token"],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()


def test_agent_card(agent_url: str, token: str) -> Dict:
    """Test AgentCard endpoint"""
    import urllib.request
    import urllib.error

    print("Testing AgentCard endpoint...")
    agent_card_url = f"{agent_url}/.well-known/agent-card"

    try:
        req = urllib.request.Request(
            agent_card_url,
            headers={"Authorization": f"Bearer {token}"}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            agent_card = json.loads(response.read().decode())

        print("✓ AgentCard retrieved successfully")
        print(f"  Name: {agent_card.get('name', 'unknown')}")
        print(f"  Description: {agent_card.get('description', 'unknown')}")
        print(f"  Version: {agent_card.get('version', 'unknown')}")

        # Validate required fields
        required_fields = ["name", "description", "capabilities"]
        missing = [f for f in required_fields if f not in agent_card]

        if missing:
            print(f"⚠ Missing required fields: {', '.join(missing)}")
            return {"status": "partial", "card": agent_card, "missing": missing}

        print("✓ All required fields present")
        return {"status": "success", "card": agent_card}

    except urllib.error.HTTPError as e:
        print(f"✗ AgentCard request failed: {e.code} {e.reason}")
        return {"status": "failed", "error": str(e)}
    except Exception as e:
        print(f"✗ Error retrieving AgentCard: {e}")
        return {"status": "failed", "error": str(e)}


def test_task_submission(agent_url: str, token: str, message: str) -> Optional[str]:
    """Test task submission"""
    import urllib.request
    import urllib.error

    print("\nTesting Task Submission API (A2A JSON-RPC)...")
    task_url = agent_url  # A2A uses a single endpoint with JSON-RPC methods

    payload = {
        "jsonrpc": "2.0",
        "method": "tasks/send",
        "params": {
            "id": f"test-task-{int(time.time())}",
            "message": {
                "role": "user",
                "parts": [{"text": message}],
            },
        },
        "id": f"req-{int(time.time())}",
    }

    try:
        req = urllib.request.Request(
            task_url,
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode())

        task_id = result.get("task_id")
        print(f"✓ Task submitted successfully")
        print(f"  Task ID: {task_id}")
        print(f"  Status: {result.get('status', 'unknown')}")

        return task_id

    except urllib.error.HTTPError as e:
        print(f"✗ Task submission failed: {e.code} {e.reason}")
        try:
            error_body = e.read().decode()
            print(f"  Error details: {error_body}")
        except Exception:
            pass
        return None
    except Exception as e:
        print(f"✗ Error submitting task: {e}")
        return None


def test_task_status(agent_url: str, token: str, task_id: str, max_wait: int = 60) -> bool:
    """Test task status polling"""
    import urllib.request
    import urllib.error

    print("\nTesting Task Status API (A2A JSON-RPC tasks/get)...")
    status_url = agent_url  # A2A uses single endpoint with JSON-RPC methods

    start_time = time.time()

    while time.time() - start_time < max_wait:
        try:
            status_payload = json.dumps({
                "jsonrpc": "2.0",
                "method": "tasks/get",
                "params": {"id": task_id},
                "id": f"status-{int(time.time())}",
            }).encode()

            req = urllib.request.Request(
                status_url,
                data=status_payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode())

            # A2A task statuses: submitted, working, input-required, completed, failed, canceled
            task_result = result.get("result", {})
            status = task_result.get("status", {}).get("state", "unknown")

            print(f"  Status: {status}")

            if status == "completed":
                print("Task completed successfully")
                artifacts = task_result.get("artifacts", [])
                if artifacts:
                    first_part = artifacts[0].get("parts", [{}])[0].get("text", "")
                    if first_part:
                        print(f"  Response: {first_part[:100]}...")
                return True

            elif status == "failed":
                error_msg = task_result.get("status", {}).get("message", "unknown error")
                print(f"Task failed: {error_msg}")
                return False

            elif status in ["submitted", "working"]:
                time.sleep(5)
                continue

            else:
                print(f"Unknown status: {status}")
                time.sleep(5)

        except urllib.error.HTTPError as e:
            print(f"✗ Status check failed: {e.code} {e.reason}")
            return False
        except Exception as e:
            print(f"✗ Error checking status: {e}")
            return False

    print(f"⚠ Timeout waiting for task completion ({max_wait}s)")
    return False


def run_protocol_tests(agent_url: str, test_message: str = "Hello, test message"):
    """Run all A2A protocol tests"""
    print("=" * 70)
    print("A2A Protocol Compliance Test")
    print("=" * 70)
    print(f"Agent URL: {agent_url}")
    print(f"Test Message: {test_message}")
    print("=" * 70)
    print()

    # Get access token
    token = get_access_token()
    if not token:
        print("✗ Failed to get access token")
        sys.exit(1)

    # Test 1: AgentCard
    card_result = test_agent_card(agent_url, token)

    # Test 2: Task Submission
    task_id = test_task_submission(agent_url, token, test_message)

    # Test 3: Status Polling (if task was submitted)
    status_success = False
    if task_id:
        status_success = test_task_status(agent_url, token, task_id)

    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)

    tests_passed = 0
    tests_total = 3

    if card_result.get("status") == "success":
        print("✓ AgentCard Test: PASSED")
        tests_passed += 1
    else:
        print("✗ AgentCard Test: FAILED")

    if task_id:
        print("✓ Task Submission Test: PASSED")
        tests_passed += 1
    else:
        print("✗ Task Submission Test: FAILED")

    if status_success:
        print("✓ Task Status Test: PASSED")
        tests_passed += 1
    else:
        print("✗ Task Status Test: FAILED")

    print(f"\nResult: {tests_passed}/{tests_total} tests passed")

    if tests_passed == tests_total:
        print("🟢 A2A Protocol: COMPLIANT")
        sys.exit(0)
    elif tests_passed >= 2:
        print("🟡 A2A Protocol: PARTIALLY COMPLIANT")
        sys.exit(1)
    else:
        print("🔴 A2A Protocol: NOT COMPLIANT")
        sys.exit(2)


def main():
    if len(sys.argv) < 2:
        print("Usage: test-a2a-protocol.py <AGENT_URL> [TEST_MESSAGE]")
        print("\nTest A2A protocol compliance for deployed ADK agent")
        print("\nExample:")
        print("  test-a2a-protocol.py https://my-agent-xyz.run.app")
        print("  test-a2a-protocol.py https://my-agent-xyz.run.app 'Deploy a GKE cluster'")
        sys.exit(1)

    agent_url = sys.argv[1].rstrip("/")
    test_message = sys.argv[2] if len(sys.argv) > 2 else "Hello, this is a test message"

    run_protocol_tests(agent_url, test_message)


if __name__ == "__main__":
    main()
