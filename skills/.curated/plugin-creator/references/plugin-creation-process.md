# Plugin Creation Process

## Plugin Creation Process

When activated, I will:

1. **Gather Requirements**
   - Plugin name (kebab-case)
   - Category (productivity, security, devops, etc.)
   - Type (commands, agents, skills, MCP, or combination)
   - Description and keywords
   - Author information

2. **Create Directory Structure**

   ```
   plugins/[category]/[plugin-name]/
   ├── .claude-plugin/
   │   └── plugin.json
   ├── README.md
   ├── LICENSE
   └── [commands|agents|skills|hooks|mcp]/
   ```

3. **Generate Required Files**
   - **plugin.json** with proper schema (name, version, description, author)
   - **README.md** with comprehensive documentation
   - **LICENSE** (MIT by default)
   - Component files based on type

4. **Add to Marketplace Catalog**
   - Update `.claude-plugin/marketplace.extended.json`
   - Run `npm run sync-marketplace` automatically
   - Validate catalog schema

5. **Validate Everything**
   - Run `./scripts/validate-all.sh` on new plugin
   - Check JSON syntax with `jq`
   - Verify frontmatter in markdown files
   - Ensure scripts are executable
