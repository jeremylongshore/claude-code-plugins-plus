# Error Handling Reference

**Common Issues and Resolutions**:

1. **Unable to Parse Configuration File**
   - Error: "Syntax error in ${CLAUDE_SKILL_DIR}/terraform/main.tf"
   - Resolution: Validate file syntax first, report parse errors separately
   - Fallback: Skip malformed files, note in report

2. **Missing Cloud Provider Context**
   - Error: "Cannot determine cloud provider from configuration"
   - Resolution: Look for provider blocks, file naming conventions
   - Fallback: Apply generic security checks only

3. **Encrypted or Binary Configuration Files**
   - Error: "Cannot read encrypted configuration"
   - Resolution: Request decrypted version or configuration export
   - Note: Document inability to audit in report

4. **Large Configuration Sets**
   - Error: "Too many files to analyze (${CLAUDE_SKILL_DIR}/ has 500+ configs)"
   - Resolution: Prioritize by file type and location
   - Strategy: Start with IaC, then app configs, then system configs

5. **False Positives**
   - Error: "Flagged configuration is intentional (dev environment)"
   - Resolution: Allow environment-specific exceptions
   - Enhancement: Support ignore/exception rules file

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
