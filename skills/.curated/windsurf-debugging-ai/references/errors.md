# Error Handling Reference

| Error | Cause | Solution |
|-------|-------|----------|
| Debugger not attaching | Port conflict | Check debug port, kill conflicting processes |
| Breakpoint not hitting | Source maps issue | Verify source maps, rebuild |
| Variable undefined | Wrong scope | Check breakpoint location, scope context |
| Cascade missing context | Insufficient code shared | Include more relevant files |
| Fix introduced regression | Incomplete analysis | Add more test coverage, review fix scope |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
