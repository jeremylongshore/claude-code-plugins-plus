## Examples

### Quick Pitfall Scan

```bash
# Check for common pitfalls
grep -r "sk_live_" --include="*.ts" src/        # Key leakage
grep -r "console.log" --include="*.ts" src/     # Potential PII logging
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
