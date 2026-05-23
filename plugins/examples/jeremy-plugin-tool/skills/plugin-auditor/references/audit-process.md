# Audit Process

## Audit Process

When activated, I will:

1. **Security Scan**

   ```bash
   # Run security checks
   grep -r "password\|secret\|api_key" plugins/plugin-name/
   grep -r "AKIA[0-9A-Z]{16}" plugins/plugin-name/
   grep -r "BEGIN.*PRIVATE KEY" plugins/plugin-name/
   grep -r "rm -rf /" plugins/plugin-name/
   grep -r "eval\(" plugins/plugin-name/
   ```

2. **Structure Validation**

   ```bash
   # Check required files
   test -f .claude-plugin/plugin.json
   test -f README.md
   test -f LICENSE

   # Check component directories
   ls -d commands/ agents/ skills/ hooks/ mcp/ 2>/dev/null
   ```

3. **Best Practices Check**

   ```bash
   # Check for TODO/FIXME
   grep -r "TODO\|FIXME" --exclude=README.md

   # Check for console.log
   grep -r "console\.log" --exclude=README.md

   # Check script permissions
   find . -name "*.sh" ! -perm -u+x
   ```

4. **Compliance Verification**

   ```bash
   # Check marketplace entry
   jq '.plugins[] | select(.name == "plugin-name")' .claude-plugin/marketplace.extended.json

   # Verify version consistency
   plugin_version=$(jq -r '.version' .claude-plugin/plugin.json)
   market_version=$(jq -r '.plugins[] | select(.name == "plugin-name") | .version' .claude-plugin/marketplace.extended.json)
   ```

5. **Generate Audit Report**
