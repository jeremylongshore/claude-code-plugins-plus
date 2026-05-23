# Configuration

## Configuration

### .cursorignore File

```gitignore
# .cursorignore - at project root

# Dependencies (large, not your code)
node_modules/
vendor/
.venv/
__pycache__/
*.pyc

# Build outputs (generated)
dist/
build/
out/
.next/
.nuxt/
target/

# Version control
.git/

# Large data files
*.csv
*.json  # Be selective - config jsons may be useful
*.sql
*.sqlite
*.db

# Logs
*.log
logs/

# Assets (binary)
*.png
*.jpg
*.gif
*.ico
*.woff
*.ttf

# IDE/Editor
.idea/
.vscode/
*.swp
*.swo

# OS files
.DS_Store
Thumbs.db

# Test fixtures (if large)
test/fixtures/
__fixtures__/
```

### Selective Indexing

```gitignore
# Index only specific directories
*
!src/
!lib/
!app/

# Include configs
!*.config.js
!*.config.ts
!package.json
!tsconfig.json
```
