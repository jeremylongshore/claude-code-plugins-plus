# Error Handling Reference

**Common Issues and Resolutions**:

1. **Framework Not Recognized**
   - Error: "Unknown ORM or database framework"
   - Resolution: Apply generic SQL injection pattern detection
   - Note: Framework-specific recommendations unavailable

2. **Obfuscated or Minified Code**
   - Error: "Cannot analyze compiled/minified code"
   - Resolution: Request source code or unminified version
   - Limitation: Reduced detection accuracy

3. **False Positives on Sanitized Input**
   - Error: "Flagged code that uses proper sanitization"
   - Resolution: Manual review required, check sanitization implementation
   - Enhancement: Whitelist known-safe patterns

4. **Dynamic Query Construction**
   - Error: "Complex query building logic difficult to analyze"
   - Resolution: Trace data flow manually, flag for manual review
   - Recommendation: Refactor to simpler, auditable patterns

5. **Stored Procedures**
   - Error: "Cannot analyze stored procedure definitions"
   - Resolution: Request SQL files or database exports
   - Alternative: Focus on application-level code

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
