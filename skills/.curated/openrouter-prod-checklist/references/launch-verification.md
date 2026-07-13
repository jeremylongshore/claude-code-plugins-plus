# Launch Verification

## Launch Verification

### Pre-Launch Tests

```python
def run_production_verification():
    """Run before going live."""
    tests = []

    # Test 1: API connectivity
    try:
        models = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        tests.append(("API Connectivity", models.status_code == 200))
    except:
        tests.append(("API Connectivity", False))

    # Test 2: Primary model works
    try:
        response = client.chat.completions.create(
            model="anthropic/claude-3.5-sonnet",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5
        )
        tests.append(("Primary Model", True))
    except:
        tests.append(("Primary Model", False))

    # Test 3: Fallback models work
    for fallback in ["openai/gpt-4-turbo", "meta-llama/llama-3.1-70b-instruct"]:
        try:
            response = client.chat.completions.create(
                model=fallback,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            tests.append((f"Fallback: {fallback}", True))
        except:
            tests.append((f"Fallback: {fallback}", False))

    # Test 4: Credit balance
    try:
        key_info = requests.get(
            "https://openrouter.ai/api/v1/auth/key",
            headers={"Authorization": f"Bearer {api_key}"}
        ).json()
        has_credits = key_info["data"]["limit_remaining"] > 10
        tests.append(("Sufficient Credits", has_credits))
    except:
        tests.append(("Sufficient Credits", False))

    # Print results
    print("\nProduction Verification Results:")
    print("-" * 40)
    all_passed = True
    for name, passed in tests:
        status = "✓" if passed else "✗"
        print(f"  {status} {name}")
        if not passed:
            all_passed = False

    return all_passed

if not run_production_verification():
    print("\n⚠️  Some checks failed. Review before going live.")
```
