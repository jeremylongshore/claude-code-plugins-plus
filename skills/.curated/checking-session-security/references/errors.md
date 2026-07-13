# Error Handling Reference

**Common Issues and Resolutions**:

1. **Cannot Locate Session Management Code**
   - Error: "No session handling code found in ${CLAUDE_SKILL_DIR}/"
   - Resolution: Search for framework-specific patterns
   - Fallback: Request explicit file paths from user

2. **Framework Not Recognized**
   - Error: "Unknown session framework"
   - Resolution: Apply generic session security checks
   - Note: Framework-specific recommendations unavailable

3. **Encrypted or Obfuscated Code**
   - Error: "Cannot analyze minified/compiled code"
   - Resolution: Request source code or unminified version
   - Limitation: Document inability to fully audit

4. **Custom Session Implementation**
   - Error: "Non-standard session management detected"
   - Resolution: Apply fundamental security principles
   - Extra Scrutiny: Custom implementations often have flaws

5. **Configuration in Environment Variables**
   - Error: "Session config in environment, not code"
   - Resolution: Request .env.example or config documentation
   - Fallback: Provide general configuration recommendations

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
