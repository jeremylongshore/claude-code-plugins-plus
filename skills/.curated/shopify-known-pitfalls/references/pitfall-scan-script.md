# Quick Pitfall Scan Script

Run these commands against your Shopify codebase to detect the most common anti-patterns.

```bash
# Run these against your Shopify codebase
echo "=== Shopify Pitfall Scan ==="
echo -n "REST API usage: "; grep -rc "clients.Rest\|admin-rest" app/ src/ 2>/dev/null | grep -v ":0" | wc -l
echo -n "Missing userErrors check: "; grep -rn "mutation\|Mutation" app/ src/ --include="*.ts" | wc -l
echo -n "Old API versions: "; grep -rn "2023-\|2022-" app/ src/ --include="*.ts" 2>/dev/null | wc -l
echo -n "Hardcoded tokens: "; grep -rc "shpat_" app/ src/ 2>/dev/null | grep -v ":0" | wc -l
echo -n "first: 250: "; grep -rn "first: 250\|first:250" app/ src/ --include="*.ts" 2>/dev/null | wc -l
```
