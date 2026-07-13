# Step 1: Verbose Request Inspection

Deep-dive reference for the `figma-advanced-troubleshooting` skill — extracted from the 'Step 1: Verbose Request Inspection' step of the workflow.

```bash
# Full HTTP request/response trace for a Figma API call
curl -v -H "X-Figma-Token: ${FIGMA_PAT}" \
  "https://api.figma.com/v1/files/${FIGMA_FILE_KEY}?depth=1" 2>&1 \
  | tee figma-debug-trace.txt

# Extract key diagnostic info:
# - TLS version and cipher
# - Response status and headers
# - Timing breakdown
curl -w "
DNS:        %{time_namelookup}s
Connect:    %{time_connect}s
TLS:        %{time_appconnect}s
TTFB:       %{time_starttransfer}s
Total:      %{time_total}s
Size:       %{size_download} bytes
Status:     %{http_code}
" -s -o /dev/null \
  -H "X-Figma-Token: ${FIGMA_PAT}" \
  "https://api.figma.com/v1/files/${FIGMA_FILE_KEY}?depth=1"
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
