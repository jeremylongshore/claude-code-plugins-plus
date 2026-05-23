# Error Handling Reference

**Backend Server Unreachable**

- Error: "502 Bad Gateway" or connection refused
- Solution: Verify backend server IPs, ports, and firewall rules

**SSL Certificate Error**

- Error: "certificate verify failed"
- Solution: Check certificate validity, chain, and private key match

**Health Check Failures**

- Error: "Target is unhealthy"
- Solution: Verify health check path returns 200 status and backends are running

**Configuration Syntax Error**

- Error: "nginx: configuration file test failed"
- Solution: Run `nginx -t` to validate syntax and fix errors

**Session Persistence Not Working**

- Issue: Users losing session on subsequent requests
- Solution: Enable sticky sessions using cookie-based or IP-based persistence

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
