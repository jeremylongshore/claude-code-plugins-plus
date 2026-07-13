# Error Handling Reference

| Error | Cause | Solution |
|-------|-------|----------|
| SAML Response Invalid | Certificate expired or clock skew | Check certificate, sync time |
| User Not Authorized | Not assigned in IdP or domain mismatch | Assign user to app, verify domain |
| Session Timeout | IdP session shorter than expected | Adjust session settings in IdP |
| Attribute Missing | Incorrect claim mapping | Update attribute statements in IdP |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
