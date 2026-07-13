# Prod Checklist — Runnable Verification Examples

## Python — Pre-Launch Verification Script

```python
import os
import sys
import time
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY", ""),
)

results = []

def check(name: str, ok: bool, detail: str = "") -> None:
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {name}" + (f": {detail}" if detail else ""))
    results.append(ok)


# 1. Environment
print("\n1. Environment Variables")
key = os.environ.get("OPENROUTER_API_KEY", "")
check("OPENROUTER_API_KEY set", bool(key))
check("key format (sk-or-...)", key.startswith("sk-or-"), key[:12] if key else "empty")

# 2. API Connectivity
print("\n2. API Connectivity")
try:
    start = time.perf_counter()
    resp = client.chat.completions.create(
        model="openai/gpt-3.5-turbo",
        messages=[{"role": "user", "content": "ping"}],
        max_tokens=5,
    )
    latency = (time.perf_counter() - start) * 1000
    check("API reachable", True, f"{latency:.0f}ms")
    check("response has content", bool(resp.choices[0].message.content))
    check("usage data present", resp.usage is not None)
except Exception as e:
    check("API reachable", False, str(e)[:60])

# 3. Model Availability
print("\n3. Model Availability")
try:
    available = {m.id for m in client.models.list().data}
    for model in ["openai/gpt-3.5-turbo"]:
        check(f"{model} available", model in available)
except Exception as e:
    check("models endpoint", False, str(e)[:60])

# 4. Security
print("\n4. Security")
from pathlib import Path
env_file = Path(".env")
if env_file.exists():
    gi = Path(".gitignore")
    gi_content = gi.read_text() if gi.exists() else ""
    check(".env in .gitignore", ".env" in gi_content)
    check("no plaintext keys in .env", "sk-or-" not in env_file.read_text())
else:
    check(".env not committed", True, "no .env file")

# Summary
print(f"\n{'='*40}")
passed = sum(results)
total = len(results)
print(f"Results: {passed}/{total} checks passed")
if passed < total:
    print("Fix all failures before deploying.")
    sys.exit(1)
else:
    print("All checks passed. Ready for production.")
```

## Bash — Smoke Test After Deployment

```bash
#!/bin/bash
API_URL="https://openrouter.ai/api/v1/chat/completions"
echo "Running OpenRouter smoke tests..."

response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL" \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"openai/gpt-3.5-turbo","messages":[{"role":"user","content":"Say OK"}],"max_tokens":5}')

http_code=$(echo "$response" | tail -1)
body=$(echo "$response" | head -1)

if [ "$http_code" = "200" ]; then
  echo "[PASS] Basic completion: HTTP $http_code"
else
  echo "[FAIL] Basic completion: HTTP $http_code"
  echo "Body: $body"
  exit 1
fi

if echo "$body" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['choices'][0]['message']['content']" 2>/dev/null; then
  echo "[PASS] Response structure valid"
else
  echo "[FAIL] Response structure invalid"
  exit 1
fi

echo "All smoke tests passed."
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
