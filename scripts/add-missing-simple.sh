#!/bin/bash
set -e

# Manually add the 8 missing plugins with proper data

plugins=(
  '{"name":"agent-context-manager","source":"./plugins/productivity/agent-context-manager","description":"Automatically detects and loads AGENTS.md files to provide agent-specific instructions","version":"1.0.0","category":"productivity","keywords":["agents","context","automation"],"author":{"name":"Jeremy Longshore"}}'
  
  '{"name":"ai-experiment-logger","source":"./plugins/mcp/ai-experiment-logger","description":"Track and analyze AI experiments with a web dashboard and MCP tools","version":"1.0.0","category":"ai-ml","keywords":["ai","experiments","logging","mcp"],"author":{"name":"Claude Code Plugins"}}'
  
  '{"name":"calendar-to-workflow","source":"./plugins/skill-enhancers/calendar-to-workflow","description":"Enhances calendar Skills by automating meeting prep and workflow triggers","version":"0.1.0","category":"skill-enhancers","keywords":["calendar","automation","meetings","productivity"],"author":{"name":"Claude Code Plugins Team"}}'
  
  '{"name":"fairdb-operations-kit","source":"./plugins/fairdb-operations-kit","description":"Production PostgreSQL operations toolkit with health monitoring and emergency response","version":"1.0.0","category":"database","keywords":["database","postgresql","operations","devops"],"author":{"name":"Jeremy Longshore"}}'
  
  '{"name":"fairdb-ops-manager","source":"./plugins/community/fairdb-ops-manager","description":"Database operations management for FairDB PostgreSQL clusters","version":"1.0.0","category":"database","keywords":["database","postgresql","operations"],"author":{"name":"Community"}}'
  
  '{"name":"file-to-code","source":"./plugins/skill-enhancers/file-to-code","description":"Converts file references into executable code implementations","version":"0.1.0","category":"skill-enhancers","keywords":["files","automation","code-generation"],"author":{"name":"Claude Code Plugins Team"}}'
  
  '{"name":"research-to-deploy","source":"./plugins/skill-enhancers/research-to-deploy","description":"Transforms research findings into deployed solutions automatically","version":"0.1.0","category":"skill-enhancers","keywords":["research","automation","deployment"],"author":{"name":"Claude Code Plugins Team"}}'
  
  '{"name":"search-to-slack","source":"./plugins/skill-enhancers/search-to-slack","description":"Automatically posts search results to Slack channels","version":"0.1.0","category":"skill-enhancers","keywords":["search","slack","automation","integration"],"author":{"name":"Claude Code Plugins Team"}}'
)

echo "Adding 8 missing plugins..."

for entry in "${plugins[@]}"; do
  name=$(echo "$entry" | jq -r '.name')
  echo "  Adding: $name"
  jq --argjson entry "$entry" '.plugins += [$entry]' .claude-plugin/marketplace.extended.json > .claude-plugin/marketplace.extended.json.tmp
  mv .claude-plugin/marketplace.extended.json.tmp .claude-plugin/marketplace.extended.json
done

echo "✅ Done! Added 8 plugins"
