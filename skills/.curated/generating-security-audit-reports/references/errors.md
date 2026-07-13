# Error Handling Reference

**Common Issues and Resolutions**:

1. **Missing Scan Data**
   - Error: "No security scan results found"
   - Resolution: Specify alternate data sources or run preliminary scans
   - Fallback: Generate report from configuration analysis only

2. **Incomplete Compliance Framework**
   - Error: "Cannot assess [STANDARD] compliance - requirements unavailable"
   - Resolution: Request framework checklist or use general best practices
   - Fallback: Note limitation in report with partial assessment

3. **Access Denied to Configuration Files**
   - Error: "Permission denied reading ${CLAUDE_SKILL_DIR}/config/"
   - Resolution: Request elevated permissions or provide configuration exports
   - Fallback: Generate report with available data, note gaps

4. **Large Dataset Processing**
   - Error: "Scan results exceed processing capacity"
   - Resolution: Process in batches by severity or component
   - Fallback: Focus on critical/high findings first

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
