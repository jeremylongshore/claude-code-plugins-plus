# Error Handling Reference

- Missing config: instruct the user to copy `${CLAUDE_PLUGIN_ROOT}/config/changelog-config.example.json` to `.changelog-config.json`.
- Missing token env var: show which `token_env` is required and how to export it.
- Missing template: fall back to `${CLAUDE_SKILL_DIR}/assets/default-changelog.md` and note it in output.
- No changes found: produce an empty changelog with a short “No user-visible changes” note.

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
