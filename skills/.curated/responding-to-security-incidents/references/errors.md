# Error Handling Reference

**Common Issues and Resolutions**:

1. **Incomplete Log Data**
   - Error: "Critical logs missing from ${CLAUDE_SKILL_DIR}/logs/"
   - Resolution: Work with available data, note gaps in report
   - Action: Improve logging for future incidents

2. **Evidence Contamination**
   - Error: "System state modified before evidence collection"
   - Resolution: Document contamination, collect remaining evidence
   - Best Practice: Immediately isolate before investigation

3. **Ongoing Active Threat**
   - Error: "Attacker still has access during investigation"
   - Resolution: Prioritize containment over investigation
   - Action: Implement emergency containment procedures first

4. **Insufficient Access for Forensics**
   - Error: "Permission denied accessing system memory"
   - Resolution: Escalate to obtain necessary privileges
   - Fallback: Use available logs and network data

5. **Backup Corruption**
   - Error: "Backups also encrypted by ransomware"
   - Resolution: Identify offline/air-gapped backups
   - Contingency: Assess rebuild from scratch vs ransom payment

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
