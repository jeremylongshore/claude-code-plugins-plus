#!/bin/bash
# Auto-format code after file edits

# Read hook data from stdin
data=$(cat)

# Extract file path from hook data
file=$(echo "$data" | jq -r '.toolOutput.file // empty')

# Format if file exists and is a supported type
if [[ -f "$file" ]]; then
  case "$file" in
    *.js|*.jsx|*.ts|*.tsx|*.json|*.css|*.md)
      # Check if prettier is available
      if command -v npx &> /dev/null; then
        npx prettier --write "$file" 2>/dev/null
        echo "Formatted: $file"
      fi
      ;;
  esac
fi
