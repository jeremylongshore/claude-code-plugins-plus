# Error Handling Reference

**Build Failures**

- Error: "Cloud Function build failed"
- Solution: Check package.json dependencies and Node.js runtime version

**Cold Start Latency**

- Warning: "High latency on first request"
- Solution: Set min_instance_count >= 1 to keep warm instances

**Secret Access Denied**

- Error: "Permission denied accessing secret"
- Solution: Grant secretAccessor role to Cloud Run/Functions service account

**Memory Exceeded**

- Error: "Container killed: out of memory"
- Solution: Increase available_memory or optimize Genkit flow memory usage

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
