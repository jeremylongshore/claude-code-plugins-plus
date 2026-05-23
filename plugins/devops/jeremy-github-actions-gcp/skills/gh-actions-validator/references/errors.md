# Error Handling Reference

**WIF Authentication Failed**

- Error: "Failed to generate Google Cloud access token"
- Solution: Verify WIF provider and service account email are correct

**OIDC Token Error**

- Error: "Unable to get ACTIONS_ID_TOKEN_REQUEST_URL env variable"
- Solution: Add `id-token: write` permission to workflow

**IAM Permission Denied**

- Error: "does not have required permission"
- Solution: Grant service account minimum required roles (run.admin, aiplatform.user)

**Attribute Condition Failed**

- Error: "Token does not match attribute condition"
- Solution: Update attribute mapping to include repository restriction

**Deployment Validation Failed**

- Error: "Agent not in RUNNING state"
- Solution: Check agent configuration and deployment logs

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
