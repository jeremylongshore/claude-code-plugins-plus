# Error Handling Reference

| Issue | Cause | Solution |
|-------|-------|----------|
| k6 timeout | Rate limited | Reduce RPS |
| HPA not scaling | Wrong metrics | Verify metric name |
| Connection refused | Pool exhausted | Increase pool size |
| Inconsistent results | Warm-up needed | Add ramp-up phase |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
