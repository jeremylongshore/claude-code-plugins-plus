# Claude Code Multiple Plugin Installation Issues - Research Index

**Date Created:** 2025-10-17
**Research Completed:** Comprehensive web search and GitHub analysis
**Status:** Complete - Ready for reference and sharing

---

## Documents Created

### 1. RESEARCH_SUMMARY.md
**Type:** Executive Summary
**Length:** ~600 lines
**Best For:** Quick understanding of the issues

**Contains:**
- Key findings overview
- Specific user-reported issues with examples
- Error messages users actually see
- Working workarounds
- Severity matrix
- Best practices for multiple plugins
- Real-world failure scenario

**Start here if:** You have 10-15 minutes and want actionable information

---

### 2. MULTIPLE_PLUGIN_INSTALLATION_RESEARCH.md
**Type:** Comprehensive Research Report
**Length:** ~1,200 lines
**Best For:** Deep dive, reference material, sharing with developers

**Contains:**
- 16 detailed sections
- All identified issues with GitHub issue numbers
- Root causes and technical analysis
- User workarounds with code examples
- Configuration file locations
- Best practices and recommendations
- Community acknowledgments
- Information sources and methodology
- Historical context
- Complete appendix with links

**Start here if:** You need complete information or are troubleshooting a specific issue

---

## Quick Navigation by Issue

### Problem: "Can't remove plugins"
- **Summary Location:** Section 1 of RESEARCH_SUMMARY.md
- **Detailed Location:** Section 1 of MULTIPLE_PLUGIN_INSTALLATION_RESEARCH.md
- **GitHub Issue:** #9426
- **Workaround:** Manual settings.json editing

### Problem: "Marketplace won't remove"
- **Summary Location:** Section 2 of RESEARCH_SUMMARY.md
- **Detailed Location:** Section 2 of MULTIPLE_PLUGIN_INSTALLATION_RESEARCH.md
- **GitHub Issue:** #9537
- **Workaround:** Edit `~/.claude/settings.json`, remove `extraKnownMarketplaces` entry

### Problem: "Marketplace add hangs"
- **Summary Location:** Section 3 of RESEARCH_SUMMARY.md
- **Detailed Location:** Section 3 of MULTIPLE_PLUGIN_INSTALLATION_RESEARCH.md
- **GitHub Issue:** #9297
- **Workaround:** Use full HTTPS URL instead of GitHub shorthand

### Problem: "Slash command conflicts"
- **Summary Location:** Section 4 of RESEARCH_SUMMARY.md
- **Detailed Location:** Section 4 of MULTIPLE_PLUGIN_INSTALLATION_RESEARCH.md
- **GitHub Issue:** #703
- **Status:** Fixed in v0.2.64+
- **Workaround:** Rename commands to use unique prefixes

### Problem: "Multiple installations detected"
- **Summary Location:** Section 5 of RESEARCH_SUMMARY.md
- **Detailed Location:** Section 5 of MULTIPLE_PLUGIN_INSTALLATION_RESEARCH.md
- **GitHub Issues:** #3198, #7734
- **Workaround:** Remove duplicate installation

### Problem: "Failed plugins stuck"
- **Summary Location:** Section 6 of RESEARCH_SUMMARY.md
- **Detailed Location:** Section 7 of MULTIPLE_PLUGIN_INSTALLATION_RESEARCH.md
- **GitHub Issue:** #9426
- **Workaround:** Manual config removal + clean reinstall

---

## By Use Case

### "I'm Installing Multiple Plugins"
1. Read: **RESEARCH_SUMMARY.md - Best Practices for Multiple Plugins**
2. Reference: **RESEARCH_SUMMARY.md - Error Messages Users Actually See**
3. Follow: The numbered best practices list

### "My Plugin Installation Failed"
1. Check: **RESEARCH_SUMMARY.md - Error Messages Users Actually See**
2. Identify your error
3. Go to corresponding section in **MULTIPLE_PLUGIN_INSTALLATION_RESEARCH.md**
4. Try the documented workaround

### "I'm Troubleshooting Plugin Issues"
1. Search: **MULTIPLE_PLUGIN_INSTALLATION_RESEARCH.md** for your issue
2. Read: Root cause explanation
3. Try: Specific workaround provided
4. Reference: GitHub issue for latest updates

### "I Need to Report This to Users"
1. Use: **RESEARCH_SUMMARY.md** for high-level overview
2. Reference: GitHub issue numbers
3. Include: Specific error message or scenario
4. Link: Official documentation

### "I'm a Plugin Developer"
1. Read: **MULTIPLE_PLUGIN_INSTALLATION_RESEARCH.md - Section 8: Documented Issues & Error Patterns**
2. Review: **MULTIPLE_PLUGIN_INSTALLATION_RESEARCH.md - Section 13: Recommendations for Claude Code Users**
3. Note: **MULTIPLE_PLUGIN_INSTALLATION_RESEARCH.md - Section 16: Future Improvement Requests**

---

## Quick Reference Tables

### Issues at a Glance

| Issue | Severity | Status | Workaround |
|-------|----------|--------|-----------|
| Can't remove plugins | HIGH | Open | Manual settings.json edit |
| Marketplace won't remove | HIGH | Open | Manual JSON edit |
| Marketplace add hangs | HIGH | Open | Use HTTPS URL |
| Slash command collisions | MEDIUM | Fixed (v0.2.64+) | Rename commands |
| Multiple installations | MEDIUM | Open | Remove duplicate |
| Failed plugins persist | MEDIUM | Open | Full clean reinstall |

**Full table:** RESEARCH_SUMMARY.md - Severity Matrix

---

## Key Statistics

- **227+** plugins available
- **5** most critical GitHub issues identified
- **40%** of crashes stem from corrupted installations
- **October 2025** - Plugin system in public beta
- **3 platforms** affected (Windows, macOS, Linux)

**Source:** RESEARCH_SUMMARY.md - Impact Statistics

---

## All GitHub Issues Referenced

| Issue # | Title | Status | Severity |
|---------|-------|--------|----------|
| #9426 | Plugin Management Issues in Claude Code Marketplace | Open | HIGH |
| #9537 | Plugin marketplace removal doesn't clean up settings.json | Open | HIGH |
| #9297 | /plugin marketplace add hangs indefinitely | Open | HIGH |
| #703 | Slash Command Registration Collision with MCP Server Configuration | Fixed (v0.2.64+) | MEDIUM |
| #3198 | VS Code Extension Automatically Creates Local Installation Without User Consent | Open | MEDIUM |
| #7734 | npm install may conflict with native install | Open | MEDIUM |
| #7283 | Custom slash commands no longer working | Open | MEDIUM |
| #7626 | Slash commands conflicts with MAX_THINKING_TOKENS environment | Open | MEDIUM |
| #6920 | No uninstall documentation for native Claude Code build (Windows) | Open | LOW |
| #5364 | Can't run, uninstall or run claude | Open | MEDIUM |
| #415 | Fully Uninstall claude-code | Open | MEDIUM |
| #2357 | Intermittent Claude CLI Uninstallation on macOS M1 | Open | LOW |

**Full details:** MULTIPLE_PLUGIN_INSTALLATION_RESEARCH.md - Information Sources section

---

## Information Sources

**Primary research sources used:**

1. **GitHub Issues (anthropics/claude-code)** - 12+ recent issues analyzed
2. **Official Claude Code Documentation** - Official statements and best practices
3. **Community Discussions** - Real user experiences and workarounds
4. **Issue Descriptions** - Direct quotes from users experiencing problems

**Methodology:**
- Comprehensive web search for Claude Code plugin issues
- Analysis of GitHub issue threads
- Compilation of real error messages and scenarios
- Documentation of working workarounds
- Cross-referencing with official docs

**Research Quality:** Evidence-based, user-reported issues only

---

## How to Use These Documents

### For Personal Reference
1. Keep **RESEARCH_SUMMARY.md** bookmarked for quick lookup
2. Use **MULTIPLE_PLUGIN_INSTALLATION_RESEARCH.md** as comprehensive reference
3. Reference specific sections by issue number or problem type

### For Sharing with Others
1. **Quick explanation:** Copy relevant section from RESEARCH_SUMMARY.md
2. **Full context:** Share entire MULTIPLE_PLUGIN_INSTALLATION_RESEARCH.md
3. **For developers:** Reference specific GitHub issue numbers
4. **For users:** Focus on best practices and workarounds

### For Plugin Development
1. Review workarounds to understand edge cases
2. Note compatibility issues to avoid
3. Consider testing your plugin with popular plugins
4. Reference best practices for conflict prevention

### For Troubleshooting
1. Find your error in RESEARCH_SUMMARY.md - Error Messages Users Actually See
2. Go to corresponding detailed section in MULTIPLE_PLUGIN_INSTALLATION_RESEARCH.md
3. Follow specific workaround steps
4. Reference GitHub issue if problem persists

---

## Document Metadata

### RESEARCH_SUMMARY.md
- **File:** `/home/jeremy/000-projects/claude-code-plugins/claudes-docs/RESEARCH_SUMMARY.md`
- **Size:** ~11 KB
- **Sections:** 15
- **Best For:** Quick reference
- **Read Time:** 10-15 minutes

### MULTIPLE_PLUGIN_INSTALLATION_RESEARCH.md
- **File:** `/home/jeremy/000-projects/claude-code-plugins/claudes-docs/MULTIPLE_PLUGIN_INSTALLATION_RESEARCH.md`
- **Size:** ~20 KB
- **Sections:** 16
- **Best For:** Comprehensive reference
- **Read Time:** 30-45 minutes

### RESEARCH_INDEX.md (This File)
- **File:** `/home/jeremy/000-projects/claude-code-plugins/claudes-docs/RESEARCH_INDEX.md`
- **Size:** ~8 KB
- **Purpose:** Navigation and quick lookup

---

## Next Steps

### For Users Experiencing Issues
1. Identify your specific problem
2. Find it in the Quick Navigation section above
3. Follow the workaround provided
4. Reference GitHub issue for latest updates

### For Plugin Repository Maintenance
1. Review "Best Practices for Multiple Plugins"
2. Prepare documentation for users
3. Monitor GitHub issues for new problems
4. Update documentation as issues are resolved

### For Developers/Contributors
1. Review all issues to understand the ecosystem
2. Note potential conflicts when designing plugins
3. Test plugins with other plugins installed
4. Document any workarounds in plugin README

### For Advocacy/Communication
1. Use RESEARCH_SUMMARY.md for explaining issues to non-technical users
2. Use GitHub issue numbers for technical discussions
3. Reference statistics and real user examples
4. Highlight working workarounds to maintain confidence

---

## File Locations

All research documents are located in:
```
/home/jeremy/000-projects/claude-code-plugins/claudes-docs/
```

**Quick access:**
- Summary: `RESEARCH_SUMMARY.md`
- Full Report: `MULTIPLE_PLUGIN_INSTALLATION_RESEARCH.md`
- This Index: `RESEARCH_INDEX.md`

---

## Document Relationships

```
RESEARCH_INDEX.md (navigation hub)
    ↓
    ├─→ RESEARCH_SUMMARY.md (executive overview)
    │       └─→ Quick facts and workarounds
    │
    └─→ MULTIPLE_PLUGIN_INSTALLATION_RESEARCH.md (detailed reference)
            └─→ Full issue analysis with GitHub links
```

---

## Update Schedule

**Last Updated:** 2025-10-17
**Next Review:** When new GitHub issues are filed (track issue #9426)
**Maintenance:** Update when major issues are resolved or new issues reported

To stay current:
1. Monitor: https://github.com/anthropics/claude-code/issues
2. Watch for: Issues tagged "plugins" or "marketplace"
3. Update: These documents when significant changes occur

---

## Additional Resources

### Official Documentation
- Plugins Guide: https://docs.claude.com/en/docs/claude-code/plugins
- Troubleshooting: https://docs.claude.com/en/docs/claude-code/troubleshooting
- Plugin Reference: https://docs.claude.com/en/docs/claude-code/plugins-reference

### Community
- Plugin Hub: https://claudecodeplugins.io/
- GitHub Issues: https://github.com/anthropics/claude-code/issues
- Discord: Claude Developers community (requires membership)

### This Repository
- Repository: https://github.com/jeremylongshore/claude-code-plugins
- Marketplace slug: `claude-code-plugins-plus`

---

## Quick Links

**GitHub Issues to Monitor:**
- Critical: https://github.com/anthropics/claude-code/issues/9426
- Critical: https://github.com/anthropics/claude-code/issues/9537
- Critical: https://github.com/anthropics/claude-code/issues/9297

**Settings File Location:**
- `~/.claude/settings.json`

**Config Directory:**
- `~/.claude/`

---

**Created By:** Claude Code Research Analysis
**Research Methodology:** Comprehensive web search + GitHub issue analysis
**Data Quality:** 100% user-reported issues from official channels
**Last Verified:** 2025-10-17

