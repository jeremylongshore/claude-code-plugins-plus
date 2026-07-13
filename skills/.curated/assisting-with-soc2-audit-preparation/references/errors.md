# Error Handling Reference

**Common Issues and Resolutions**:

1. **Missing Evidence Files**
   - Error: "Cannot locate security policy in ${CLAUDE_SKILL_DIR}/docs/"
   - Resolution: Request document locations from user
   - Fallback: Mark as evidence gap in report

2. **Incomplete Access Logs**
   - Error: "Log retention < SOC 2 requirement (1 year)"
   - Resolution: Note current retention period, flag as gap
   - Remediation: Extend retention, backfill if possible

3. **Undocumented Procedures**
   - Error: "No incident response playbook found"
   - Resolution: Flag as critical gap requiring documentation
   - Assistance: Provide template for creating procedure

4. **Cloud Provider Access Required**
   - Error: "Cannot assess AWS controls without API access"
   - Resolution: Request CloudTrail exports or console screenshots
   - Alternative: Provide manual checklist for cloud controls

5. **Multiple Environments Not Distinguished**
   - Error: "Production and dev configs mixed in ${CLAUDE_SKILL_DIR}/"
   - Resolution: Request environment separation or clear labeling
   - Risk: May audit wrong environment

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
