# Error Handling Reference

| Error | Cause | Solution |
|-------|-------|----------|
| No completions appearing | Language server not running | Start language server, check logs |
| Slow completions | Large context or network | Reduce context window, check connection |
| Irrelevant suggestions | Missing project context | Add .windsurfrules with patterns |
| Type errors in completions | Incomplete type information | Improve type annotations in code |
| Completions cut off | Max length exceeded | Increase suggestion length limit |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
