# Examples — Ollama Local AI Setup

## Example 1: Developer Workstation Setup (macOS Apple Silicon)

Install Ollama on a macOS M2 machine, pull a code generation model, and integrate with Python.

### System Assessment

```bash
# Check hardware
uname -s
# Darwin

sysctl -n machdep.cpu.brand_string
# Apple M2

sysctl -n hw.memsize | awk '{print $1/1024/1024/1024 " GB"}'
# 16 GB

# Check for existing Ollama installation
which ollama && ollama --version || echo "Ollama not installed"
# Ollama not installed
```

### Installation

```bash
# Install via Homebrew
brew install ollama

# Start the Ollama service
brew services start ollama

# Verify the service is running
brew services list | grep ollama
# ollama  started  ~/Library/LaunchAgents/homebrew.mxcl.ollama.plist

# Confirm REST API is accessible
curl -s http://localhost:11434/api/tags | python3 -m json.tool
# {
#     "models": []
# }
```

### Model Selection and Download

```bash
# For 16 GB RAM + Apple Silicon, codellama:13b is optimal for code tasks
ollama pull codellama:13b
# pulling manifest
# pulling 3a43f93b78ec... 100% |██████████████████████| 7.4 GB
# pulling 8c17c2ebb0ea... 100% |██████████████████████| 7.0 KB
# verifying sha256 digest
# writing manifest
# success

# Also pull a general-purpose model
ollama pull llama3.2
# pulling manifest
# pulling 9f438cb9cd58... 100% |██████████████████████| 4.7 GB
# success

# Verify models are available
ollama list
# NAME              ID            SIZE    MODIFIED
# codellama:13b     3a43f93b78ec  7.4 GB  30 seconds ago
# llama3.2:latest   9f438cb9cd58  4.7 GB  10 seconds ago

# Quick test
ollama run codellama:13b "Write a Python function to check if a number is prime"
# def is_prime(n: int) -> bool:
#     if n < 2:
#         return False
#     if n < 4:
#         return True
#     if n % 2 == 0 or n % 3 == 0:
#         return False
#     i = 5
#     while i * i <= n:
#         if n % i == 0 or n % (i + 2) == 0:
#             return False
#         i += 6
#     return True
```

### Python Integration

```python
# Install the Python client
# pip install ollama

import ollama

# Simple generation
response = ollama.generate(
    model="codellama:13b",
    prompt="Write a Python decorator that retries a function 3 times on exception",
)
print(response["response"])

# Expected output:
# import functools
# import time
#
# def retry(max_attempts=3, delay=1.0):
#     def decorator(func):
#         @functools.wraps(func)
#         def wrapper(*args, **kwargs):
#             for attempt in range(1, max_attempts + 1):
#                 try:
#                     return func(*args, **kwargs)
#                 except Exception as e:
#                     if attempt == max_attempts:
#                         raise
#                     time.sleep(delay * attempt)
#         return wrapper
#     return decorator

# Chat with conversation history
messages = [
    {"role": "system", "content": "You are a Python expert. Be concise."},
    {"role": "user", "content": "What is the difference between a list and a tuple?"},
]

response = ollama.chat(model="llama3.2", messages=messages)
print(response["message"]["content"])
# Lists are mutable (can be modified after creation), tuples are immutable.
# Lists use [], tuples use (). Tuples are faster and can be used as dict keys.

# Streaming response for real-time output
stream = ollama.chat(
    model="llama3.2",
    messages=[{"role": "user", "content": "Explain async/await in Python"}],
    stream=True,
)
for chunk in stream:
    print(chunk["message"]["content"], end="", flush=True)
print()  # Newline after stream completes
```

### Performance Benchmark

```python
import ollama
import time

def benchmark_model(model: str, prompt: str, runs: int = 3) -> dict:
    """Benchmark a model's throughput on Apple Silicon."""
    results = []
    for i in range(runs):
        start = time.time()
        response = ollama.generate(model=model, prompt=prompt)
        elapsed = time.time() - start

        # Token count from response metadata
        eval_count = response.get("eval_count", 0)
        eval_duration_ns = response.get("eval_duration", 1)
        tokens_per_sec = eval_count / (eval_duration_ns / 1e9) if eval_duration_ns else 0

        results.append({
            "run": i + 1,
            "tokens": eval_count,
            "wall_time_s": round(elapsed, 2),
            "tokens_per_sec": round(tokens_per_sec, 1),
        })

    avg_tps = sum(r["tokens_per_sec"] for r in results) / len(results)
    print(f"\n{model} benchmark ({runs} runs):")
    for r in results:
        print(f"  Run {r['run']}: {r['tokens']} tokens in {r['wall_time_s']}s ({r['tokens_per_sec']} tok/s)")
    print(f"  Average: {avg_tps:.1f} tokens/sec")
    return {"model": model, "avg_tokens_per_sec": avg_tps, "runs": results}

benchmark_model("codellama:13b", "Write a binary search function in Python with tests")
# codellama:13b benchmark (3 runs):
#   Run 1: 245 tokens in 6.12s (40.0 tok/s)
#   Run 2: 238 tokens in 5.89s (40.4 tok/s)
#   Run 3: 251 tokens in 6.31s (39.8 tok/s)
#   Average: 40.1 tokens/sec
```

---

## Example 2: Air-Gapped Server Deployment (Ubuntu)

Install Ollama on an offline server using pre-downloaded binaries.

### On a Machine with Internet Access

```bash
# Download the Ollama binary
curl -L https://ollama.com/download/ollama-linux-amd64 -o ollama-linux-amd64
chmod +x ollama-linux-amd64

# Download model weights
# First install Ollama temporarily to pull the model
./ollama-linux-amd64 serve &
sleep 3
./ollama-linux-amd64 pull llama3.2
kill %1

# Package the model files
tar czf ollama-models.tar.gz -C ~/.ollama/models .

# Transfer both files to the air-gapped server via USB
# ollama-linux-amd64 (binary, ~120MB)
# ollama-models.tar.gz (model weights, ~4.7GB)
```

### On the Air-Gapped Server

```bash
# Install the binary
sudo cp /media/usb/ollama-linux-amd64 /usr/local/bin/ollama
sudo chmod +x /usr/local/bin/ollama

# Restore model weights
mkdir -p ~/.ollama/models
tar xzf /media/usb/ollama-models.tar.gz -C ~/.ollama/models/

# Create systemd service for auto-restart
sudo tee /etc/systemd/system/ollama.service > /dev/null << 'EOF'
[Unit]
Description=Ollama Local AI Server
After=network.target

[Service]
Type=simple
User=ollama
Group=ollama
ExecStart=/usr/local/bin/ollama serve
Restart=always
RestartSec=5
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_MODELS=/home/ollama/.ollama/models"

# Resource limits
LimitNOFILE=65535
LimitMEMLOCK=infinity

[Install]
WantedBy=multi-user.target
EOF

# Create service user and set permissions
sudo useradd -r -s /bin/false -m -d /home/ollama ollama
sudo cp -r ~/.ollama/models /home/ollama/.ollama/
sudo chown -R ollama:ollama /home/ollama/.ollama

# Start and enable the service
sudo systemctl daemon-reload
sudo systemctl enable ollama
sudo systemctl start ollama

# Verify
sudo systemctl status ollama
# ● ollama.service - Ollama Local AI Server
#   Loaded: loaded (/etc/systemd/system/ollama.service; enabled)
#   Active: active (running) since Mon 2025-03-17 10:00:00 UTC

# Test from any machine on the network
curl http://10.0.0.50:11434/api/tags
# {"models":[{"name":"llama3.2:latest","size":4661224676,...}]}

ollama list
# NAME              ID            SIZE    MODIFIED
# llama3.2:latest   9f438cb9cd58  4.7 GB  2 minutes ago
```

### Serve to Internal Team via REST API

```bash
# Test generation via REST API
curl -s http://10.0.0.50:11434/api/generate -d '{
  "model": "llama3.2",
  "prompt": "Summarize the key principles of zero-trust security",
  "stream": false
}' | python3 -m json.tool
```

### Expected Output

```json
{
  "model": "llama3.2",
  "response": "Zero-trust security operates on the principle of 'never trust, always verify.' Key principles include:\n\n1. **Verify explicitly**: Authenticate and authorize every access request using all available data points (identity, location, device health).\n2. **Least-privilege access**: Limit user access to only what is needed, using just-in-time and just-enough-access policies.\n3. **Assume breach**: Minimize blast radius by segmenting networks, verifying end-to-end encryption, and using analytics for threat detection.\n4. **Continuous validation**: Re-evaluate trust continuously rather than granting persistent access.\n5. **Micro-segmentation**: Divide networks into small zones to contain lateral movement.",
  "done": true,
  "total_duration": 4821000000,
  "eval_count": 152,
  "eval_duration": 3800000000
}
```

---

## Example 3: Docker-Based CI Pipeline Integration

Run Ollama in Docker for automated code review in CI/CD.

### Docker Setup

```yaml
# docker-compose.yml
services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama-ci
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        limits:
          memory: 8G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  ollama_data:
```

```bash
# Start Ollama in Docker
docker compose up -d

# Wait for service to be healthy
docker compose exec ollama ollama pull mistral:7b
# pulling manifest... done
```

### Node.js CI Test Harness

```typescript
// ci/code-review.ts
import { Ollama } from "ollama";

const ollama = new Ollama({ host: "http://localhost:11434" });

interface ReviewResult {
  file: string;
  issues: Array<{
    line: number;
    severity: "error" | "warning" | "info";
    message: string;
  }>;
  summary: string;
}

async function reviewDiff(diff: string): Promise<ReviewResult> {
  const response = await ollama.chat({
    model: "mistral:7b",
    messages: [
      {
        role: "system",
        content: `You are a code reviewer. Analyze the git diff and return a JSON object:
{
  "file": "filename from the diff",
  "issues": [{"line": number, "severity": "error|warning|info", "message": "description"}],
  "summary": "one-sentence summary"
}
Only return valid JSON, no other text.`,
      },
      {
        role: "user",
        content: `Review this diff:\n\n${diff}`,
      },
    ],
    format: "json",
  });

  return JSON.parse(response.message.content);
}

// Integration with CI pipeline
async function reviewPR(diffs: string[]): Promise<void> {
  console.log(`Reviewing ${diffs.length} file(s)...`);

  let totalIssues = 0;
  let hasErrors = false;

  for (const diff of diffs) {
    const result = await reviewDiff(diff);
    console.log(`\n--- ${result.file} ---`);
    console.log(`Summary: ${result.summary}`);

    for (const issue of result.issues) {
      const icon = { error: "XX", warning: "!!", info: "--" }[issue.severity];
      console.log(`  [${icon}] L${issue.line}: ${issue.message}`);
      totalIssues++;
      if (issue.severity === "error") hasErrors = true;
    }
  }

  console.log(`\nTotal issues: ${totalIssues}`);
  if (hasErrors) {
    console.error("CI FAILED: Critical issues found");
    process.exit(1);
  }
}

// Example usage in CI
const exampleDiff = `
diff --git a/src/auth.ts b/src/auth.ts
index abc1234..def5678 100644
--- a/src/auth.ts
+++ b/src/auth.ts
@@ -10,6 +10,8 @@ export function authenticate(token: string) {
+  // TODO: fix this later
+  const secret = "sk-prod-abc123xyz";
   const decoded = jwt.verify(token, secret);
   return decoded;
 }
`;

reviewPR([exampleDiff]);
```

### Expected Output

```
Reviewing 1 file(s)...

--- src/auth.ts ---
Summary: Critical security issue with hardcoded production secret and incomplete TODO.
  [XX] L11: Hardcoded production secret "sk-prod-abc123xyz" — move to environment variable or secret manager
  [!!] L10: TODO comment in production code — resolve before merging
  [--] L12: Consider adding token expiration validation after jwt.verify

Total issues: 3
CI FAILED: Critical issues found
```

### GitHub Actions Integration

```yaml
# .github/workflows/ai-review.yml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    services:
      ollama:
        image: ollama/ollama:latest
        ports:
          - 11434:11434
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Pull review model
        run: |
          curl -s http://localhost:11434/api/pull -d '{"name": "mistral:7b"}' | tail -1

      - name: Get PR diff
        run: git diff origin/${{ github.base_ref }}...HEAD > pr.diff

      - name: Run AI review
        run: npx tsx ci/code-review.ts < pr.diff
```

---

## Example 4: Custom Modelfile for Specialized Tasks

Create a custom model with specific system prompts and parameters.

```bash
# Create a custom Modelfile for SQL generation
cat > Modelfile << 'EOF'
FROM codellama:13b

PARAMETER temperature 0.2
PARAMETER top_p 0.9
PARAMETER num_ctx 4096

SYSTEM """You are a SQL expert. Given a natural language question and a database schema,
generate the correct SQL query. Rules:
- Use standard SQL syntax (PostgreSQL compatible)
- Always use explicit JOINs (never implicit joins)
- Include comments explaining complex logic
- Use CTEs for readability when queries have 3+ joins
- Never use SELECT * in production queries
Only output the SQL query, nothing else."""
EOF

# Create the custom model
ollama create sql-expert -f Modelfile
# transferring model data
# creating model layer
# success

# Test it
ollama run sql-expert "Find the top 5 customers by total order value in the last 30 days.
Schema: customers(id, name, email), orders(id, customer_id, total, created_at)"

# Expected output:
# -- Top 5 customers by total order value (last 30 days)
# SELECT
#     c.id,
#     c.name,
#     c.email,
#     SUM(o.total) AS total_order_value,
#     COUNT(o.id) AS order_count
# FROM customers c
# INNER JOIN orders o ON o.customer_id = c.id
# WHERE o.created_at >= CURRENT_DATE - INTERVAL '30 days'
# GROUP BY c.id, c.name, c.email
# ORDER BY total_order_value DESC
# LIMIT 5;
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
