# Speak Debug Bundle - Implementation Guide

Detailed implementation reference for the speak-debug-bundle skill.

## Instructions

### Step 1: Create Debug Bundle Script
```bash
#!/bin/bash
# speak-debug-bundle.sh

BUNDLE_DIR="speak-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

echo "=== Speak Debug Bundle ===" > "$BUNDLE_DIR/summary.txt"
echo "Generated: $(date)" >> "$BUNDLE_DIR/summary.txt"
echo "Hostname: $(hostname)" >> "$BUNDLE_DIR/summary.txt"
```

### Step 2: Collect Environment Info
```bash
# Environment info
echo "--- Environment ---" >> "$BUNDLE_DIR/summary.txt"
echo "Node version:" >> "$BUNDLE_DIR/summary.txt"
node --version >> "$BUNDLE_DIR/summary.txt" 2>&1
echo "npm version:" >> "$BUNDLE_DIR/summary.txt"
npm --version >> "$BUNDLE_DIR/summary.txt" 2>&1
echo "Python version:" >> "$BUNDLE_DIR/summary.txt"
python3 --version >> "$BUNDLE_DIR/summary.txt" 2>&1
echo "" >> "$BUNDLE_DIR/summary.txt"

# API credentials status (not values!)
echo "--- Credentials Status ---" >> "$BUNDLE_DIR/summary.txt"
echo "SPEAK_API_KEY: ${SPEAK_API_KEY:+[SET]}" >> "$BUNDLE_DIR/summary.txt"
echo "SPEAK_APP_ID: ${SPEAK_APP_ID:+[SET]}" >> "$BUNDLE_DIR/summary.txt"
echo "SPEAK_TARGET_LANGUAGE: ${SPEAK_TARGET_LANGUAGE:-[NOT SET]}" >> "$BUNDLE_DIR/summary.txt"
```

### Step 3: Gather SDK and Session Info
```bash
# SDK version
echo "--- SDK Version ---" >> "$BUNDLE_DIR/summary.txt"
npm list @speak/language-sdk 2>/dev/null >> "$BUNDLE_DIR/summary.txt" || echo "SDK not found in npm" >> "$BUNDLE_DIR/summary.txt"
pip show speak-language-sdk 2>/dev/null >> "$BUNDLE_DIR/summary.txt" || echo "SDK not found in pip" >> "$BUNDLE_DIR/summary.txt"

# Recent logs (redacted)
echo "--- Recent Logs ---" >> "$BUNDLE_DIR/summary.txt"
if [ -f "logs/speak.log" ]; then
  # Redact sensitive info
  tail -100 logs/speak.log | \
    sed 's/api_key=.*/api_key=***REDACTED***/g' | \
    sed 's/"apiKey":"[^"]*"/"apiKey":"***REDACTED***"/g' | \
    sed 's/Bearer [^ ]*/Bearer ***REDACTED***/g' \
    >> "$BUNDLE_DIR/logs.txt"
fi

# Session history (last 10 sessions)
echo "--- Recent Sessions ---" >> "$BUNDLE_DIR/summary.txt"
grep -h "session" logs/*.log 2>/dev/null | \
  tail -50 | \
  sed 's/userId=.*/userId=***REDACTED***/g' \
  >> "$BUNDLE_DIR/sessions.txt"
```

### Step 4: Network Diagnostics
```bash
# Network connectivity test
echo "--- Network Tests ---" >> "$BUNDLE_DIR/summary.txt"

echo -n "API Health: " >> "$BUNDLE_DIR/summary.txt"
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer ${SPEAK_API_KEY}" \
  -H "X-App-ID: ${SPEAK_APP_ID}" \
  https://api.speak.com/v1/health >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"

echo -n "Status Page: " >> "$BUNDLE_DIR/summary.txt"
curl -s -o /dev/null -w "%{http_code}" https://status.speak.com >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"

echo -n "DNS Resolution: " >> "$BUNDLE_DIR/summary.txt"
nslookup api.speak.com 2>&1 | grep -E "^(Name|Address)" >> "$BUNDLE_DIR/summary.txt"

echo -n "Latency (ms): " >> "$BUNDLE_DIR/summary.txt"
curl -s -o /dev/null -w "%{time_total}" https://api.speak.com/v1/health | \
  awk '{print $1 * 1000}' >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"
```

### Step 5: Collect Audio Diagnostics (if applicable)
```bash
# Audio system info
echo "--- Audio System ---" >> "$BUNDLE_DIR/summary.txt"

# Check for audio devices (Linux)
if command -v arecord &> /dev/null; then
  echo "Recording devices:" >> "$BUNDLE_DIR/summary.txt"
  arecord -l 2>&1 >> "$BUNDLE_DIR/summary.txt"
fi

# Check audio sample (if exists)
if [ -f "last_recording.wav" ]; then
  echo "Last recording info:" >> "$BUNDLE_DIR/summary.txt"
  file last_recording.wav >> "$BUNDLE_DIR/summary.txt"
  # Get duration
  ffprobe -i last_recording.wav -show_entries format=duration -v quiet -of csv="p=0" 2>/dev/null >> "$BUNDLE_DIR/summary.txt" || echo "ffprobe not available" >> "$BUNDLE_DIR/summary.txt"
fi
```

### Step 6: Configuration Snapshot
```bash
# Configuration (redacted - secrets masked)
echo "--- Config (redacted) ---" >> "$BUNDLE_DIR/summary.txt"

if [ -f ".env" ]; then
  cat .env 2>/dev/null | \
    sed 's/=.*/=***REDACTED***/' \
    >> "$BUNDLE_DIR/config-redacted.txt"
fi

# Package.json Speak dependencies
if [ -f "package.json" ]; then
  echo "Dependencies:" >> "$BUNDLE_DIR/summary.txt"
  grep -A5 '"dependencies"' package.json | grep -i speak >> "$BUNDLE_DIR/summary.txt"
fi
```

### Step 7: Package Bundle
```bash
# Create final archive
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
rm -rf "$BUNDLE_DIR"

echo "========================================"
echo "Debug bundle created: $BUNDLE_DIR.tar.gz"
echo "========================================"
echo ""
echo "Contents:"
tar -tzf "$BUNDLE_DIR.tar.gz"
echo ""
echo "Size: $(du -h "$BUNDLE_DIR.tar.gz" | cut -f1)"
echo ""
echo "IMPORTANT: Review bundle before sharing to ensure no sensitive data leaked"
```


## Complete Script

```bash
#!/bin/bash
# speak-debug-bundle.sh - Complete debug bundle generator

set -e

BUNDLE_DIR="speak-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

echo "Generating Speak debug bundle..."

# Summary header
cat > "$BUNDLE_DIR/summary.txt" << EOF
=== Speak Debug Bundle ===
Generated: $(date)
Hostname: $(hostname)
Platform: $(uname -s) $(uname -r)

--- Environment ---
Node: $(node --version 2>/dev/null || echo "N/A")
npm: $(npm --version 2>/dev/null || echo "N/A")
Python: $(python3 --version 2>/dev/null || echo "N/A")

--- Credentials Status ---
SPEAK_API_KEY: ${SPEAK_API_KEY:+[SET]}${SPEAK_API_KEY:-[NOT SET]}
SPEAK_APP_ID: ${SPEAK_APP_ID:+[SET]}${SPEAK_APP_ID:-[NOT SET]}
SPEAK_TARGET_LANGUAGE: ${SPEAK_TARGET_LANGUAGE:-[NOT SET]}

--- SDK Version ---
EOF

npm list @speak/language-sdk 2>/dev/null >> "$BUNDLE_DIR/summary.txt" || echo "npm: Not installed" >> "$BUNDLE_DIR/summary.txt"
pip show speak-language-sdk 2>/dev/null >> "$BUNDLE_DIR/summary.txt" || echo "pip: Not installed" >> "$BUNDLE_DIR/summary.txt"

# Network tests
echo -e "\n--- Network Tests ---" >> "$BUNDLE_DIR/summary.txt"
echo -n "API Status: " >> "$BUNDLE_DIR/summary.txt"
curl -s -o /dev/null -w "%{http_code}\n" https://api.speak.com/v1/health >> "$BUNDLE_DIR/summary.txt" 2>&1 || echo "FAILED" >> "$BUNDLE_DIR/summary.txt"

# Collect logs (if available)
if [ -d "logs" ]; then
  grep -rh "speak\|Speak\|SPEAK" logs/ 2>/dev/null | \
    tail -100 | \
    sed 's/api_key=.*/api_key=REDACTED/g' | \
    sed 's/"apiKey":"[^"]*"/"apiKey":"REDACTED"/g' \
    > "$BUNDLE_DIR/logs.txt" 2>/dev/null || true
fi

# Package
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
rm -rf "$BUNDLE_DIR"

echo "Bundle created: $BUNDLE_DIR.tar.gz"
```


## Sensitive Data Handling
| Category | Handling |
|----------|----------|
| API Keys | NEVER include |
| User IDs | Redact or anonymize |
| Audio files | Include only with permission |
| Error messages | Safe to include |
| Stack traces | Safe to include (redacted) |
| Session IDs | Safe to include |
| SDK versions | Safe to include |

**ALWAYS REDACT:**
- API keys and tokens
- Passwords and secrets
- PII (emails, names, IDs)
- Audio containing speech

**Safe to Include:**
- Error messages and codes
- Stack traces (with paths redacted)
- SDK/runtime versions
- Network response codes


## Submit to Support

1. Create bundle: `bash speak-debug-bundle.sh`
2. Review for sensitive data: `tar -tzf speak-debug-*.tar.gz`
3. Upload to Speak support portal
4. Include:
   - Brief problem description
   - Steps to reproduce
   - Expected vs actual behavior
   - Request ID (if available)

