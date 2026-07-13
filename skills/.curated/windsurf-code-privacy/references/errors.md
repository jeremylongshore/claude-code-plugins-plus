# Error Handling Reference

| Error | Cause | Solution |
|-------|-------|----------|
| Data transmission blocked | Exclusion pattern matched | Review pattern, whitelist if safe |
| Retention violation | Data not deleted on schedule | Check deletion job, manual cleanup |
| Consent missing | User not opted in | Prompt for consent, block until granted |
| Region mismatch | Data sent to wrong region | Update residency configuration |
| Audit gap | Logging disabled | Enable audit logging, investigate gap |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
