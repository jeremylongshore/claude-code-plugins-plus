# figma-deploy-integration: Error Handling

Error reference for the `figma-deploy-integration` skill — extracted from the skill's Error Handling guidance.

| Issue | Cause | Solution |
|-------|-------|----------|
| Secret not found in runtime | Wrong env name | Verify with platform CLI (`vercel env ls`) |
| Webhook timeout | Processing too slow | Return 200 immediately, process async |
| Cold start latency | Serverless cold boot | Use Fly.io `min_machines_running: 1` or Cloud Run min instances |
| Health check fails | PAT expired | Rotate token via platform secret management |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
