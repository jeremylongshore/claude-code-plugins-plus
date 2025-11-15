# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Plugin Overview

**jeremy-firebase** is a production-ready Firebase platform operations plugin with Vertex AI Gemini integration. It provides comprehensive automation for Firebase services including Authentication, Cloud Storage, Hosting, Cloud Functions, Analytics, and AI-powered features.

This plugin is part of the claude-code-plugins marketplace and follows the repository's plugin development standards.

## Plugin Structure

```
jeremy-firebase/
├── .claude-plugin/
│   └── plugin.json              # Plugin metadata and configuration
├── commands/                     # Slash commands for common Firebase operations
├── agents/                       # AI agents for complex Firebase workflows
├── skills/                       # Agent Skills for automatic Firebase task handling
│   └── firebase-vertex-ai/      # Main skill for Firebase + Vertex AI integration
└── examples/                     # Code examples and usage patterns
```

## Quick Commands

### Development Workflow

```bash
# Navigate to plugin directory
cd plugins/community/jeremy-firebase/

# Validate plugin structure
../../scripts/validate-all-plugins.sh .

# Add plugin to marketplace catalog
# Edit .claude-plugin/marketplace.extended.json at repository root

# Sync marketplace catalogs
cd ../.. && pnpm run sync-marketplace

# Validate changes
./scripts/validate-all-plugins.sh plugins/community/jeremy-firebase/
```

### Testing the Plugin

```bash
# Create test marketplace structure
mkdir -p ~/test-marketplace/.claude-plugin

# Create marketplace.json pointing to local plugin
cat > ~/test-marketplace/.claude-plugin/marketplace.json << 'EOF'
{
  "name": "test",
  "owner": {"name": "Test"},
  "plugins": [{
    "name": "jeremy-firebase",
    "source": "/home/jeremy/000-projects/claude-code-plugins/plugins/community/jeremy-firebase"
  }]
}
EOF

# Add test marketplace to Claude Code
/plugin marketplace add ~/test-marketplace

# Install and test
/plugin install jeremy-firebase@test
```

## Plugin Component Standards

### Commands (Slash Commands)

Commands go in `commands/` directory and must have YAML frontmatter:

```markdown
---
name: firebase-deploy-hosting
description: Deploy static site to Firebase Hosting with custom domain configuration
model: sonnet
---

# Firebase Hosting Deployment

[Detailed command instructions...]
```

**Naming Convention:** Use `firebase-` prefix for all commands (e.g., `firebase-init-project.md`, `firebase-deploy-functions.md`)

**Model Selection:**
- Use `sonnet` for complex Firebase operations requiring reasoning (multi-step deployments, security rules, complex queries)
- Use `haiku` for simple, fast operations (status checks, list resources, basic queries)

### Agents (Complex Workflows)

Agents go in `agents/` directory for multi-step Firebase workflows:

```markdown
---
name: firebase-full-stack-deployer
description: End-to-end Firebase app deployment including Auth, Firestore, Functions, and Hosting
model: sonnet
---

# Full Stack Firebase Deployer

[Multi-phase deployment workflow...]
```

**Use Cases for Agents:**
- Complete Firebase project setup from scratch
- Migration from other platforms (Supabase, AWS Amplify) to Firebase
- Multi-service Firebase architecture implementation
- Production deployment with security rules, indexes, and monitoring

### Agent Skills (v1.2.0 Schema)

Skills go in `skills/[skill-name]/SKILL.md` and activate automatically based on trigger phrases:

```markdown
---
name: deploying-firebase-functions
description: |
  Automatically deploys Cloud Functions to Firebase with TypeScript compilation,
  environment configuration, and production optimization.
  Use when requesting "deploy functions", "update cloud functions", or "push functions to Firebase".
allowed-tools: Read, Write, Edit, Bash, Grep
version: 1.0.0
---

## How It Works
[Step-by-step skill workflow]

## When to Use This Skill
- User requests "deploy my Firebase functions"
- User asks to "update cloud functions"
- User mentions "push functions to production"

## Tool Usage
- **Read**: Read Firebase configuration, functions source code
- **Write**: Generate deployment scripts, update package.json
- **Bash**: Execute firebase deploy commands
```

**Skill Naming:** Use gerund form (verb+ing) to describe the action: `deploying-firebase-functions`, `configuring-firestore-security`, `analyzing-firebase-usage`

**Tool Categories for Firebase Operations:**
- **Read-only analysis**: `Read, Grep, Glob, Bash` (viewing logs, checking status)
- **Deployment operations**: `Read, Write, Edit, Bash` (deploying, updating configs)
- **Security rule editing**: `Read, Write, Edit, Grep, Bash` (firestore.rules, storage.rules)
- **Data operations**: `Read, Write, Bash` (Firestore imports, exports)

### Examples Directory

The `examples/` directory should contain:
- **Code snippets** for Firebase service integration (Auth, Firestore, Storage, Functions)
- **Configuration templates** (firebase.json, firestore.rules, storage.rules, firestore.indexes.json)
- **Integration patterns** for Firebase + Vertex AI Gemini
- **Testing examples** (Firebase Emulator Suite usage)

## Firebase Services Coverage

This plugin should provide automation for:

### Core Services
- **Firebase Authentication**: User management, custom claims, email/password, OAuth providers
- **Cloud Firestore**: Document CRUD, queries, security rules, indexes
- **Cloud Storage**: File uploads, security rules, signed URLs
- **Firebase Hosting**: Static site deployment, custom domains, SSL
- **Cloud Functions**: TypeScript/JavaScript functions, HTTP/callable/scheduled triggers
- **Firebase Analytics**: Event logging, user properties, conversion tracking

### AI Integration (Vertex AI Gemini)
- **Embeddings Generation**: Text-to-vector for semantic search
- **Content Analysis**: Gemini API for content moderation, classification
- **Chat Integration**: Conversational AI with Firebase data context
- **Model Deployment**: Custom AI models with Firebase ML
- **RAG Implementation**: Retrieval-Augmented Generation with Firestore vector search

### DevOps & Operations
- **Firebase CLI Automation**: Project init, deployment, emulator control
- **Environment Management**: Multiple Firebase projects (dev, staging, prod)
- **Security Rules Testing**: Automated testing of Firestore and Storage rules
- **Performance Monitoring**: Integration with Firebase Performance Monitoring
- **Remote Config**: Feature flags and A/B testing setup

## Command Naming Conventions

**Format:** `firebase-[service]-[action].md`

Examples:
- `firebase-auth-setup-providers.md` (Authentication setup)
- `firebase-firestore-deploy-rules.md` (Deploy security rules)
- `firebase-functions-deploy.md` (Deploy Cloud Functions)
- `firebase-hosting-custom-domain.md` (Configure custom domain)
- `firebase-storage-upload-files.md` (Upload files to Cloud Storage)
- `firebase-vertex-ai-embeddings.md` (Generate embeddings with Vertex AI)

## Integration with Existing Plugins

### Related Plugins in Repository
- **jeremy-genkit-pro**: Firebase Genkit integration for AI workflows
- **jeremy-firestore**: Firestore-specific operations (if this becomes too large, consider extracting Firestore logic)
- **jeremy-vertex-engine**: Vertex AI Agent Engine deployment
- **jeremy-gcp-starter-examples**: GCP/Firebase starter code examples

### Avoid Duplication
Before adding commands/agents, check existing plugins to avoid overlap:
```bash
# Search for Firebase-related content in other plugins
grep -r "firebase" ../../plugins/ --include="*.md" | grep -v jeremy-firebase
```

## Development Best Practices

### Firebase Project Structure Assumptions
This plugin assumes standard Firebase project structure:
```
project-root/
├── firebase.json              # Firebase config
├── .firebaserc               # Project aliases
├── firestore.rules           # Firestore security rules
├── firestore.indexes.json    # Firestore indexes
├── storage.rules             # Storage security rules
├── functions/                # Cloud Functions
│   ├── src/
│   ├── package.json
│   └── tsconfig.json
├── public/                   # Hosting static files (or dist/)
└── .env.local               # Environment variables
```

### Environment Variable Handling
Never hardcode Firebase credentials. Commands should:
1. Check for `.env.local` file with `FIREBASE_PROJECT_ID`, `GOOGLE_APPLICATION_CREDENTIALS`
2. Use Firebase CLI authentication (`firebase login`)
3. Prompt for project selection if multiple projects exist

### Error Handling Patterns
Firebase commands should include:
- **Validation**: Check for `firebase.json`, verify Firebase CLI is installed
- **Graceful degradation**: Fallback to manual steps if automation fails
- **Clear error messages**: Explain what went wrong and how to fix it

Example error handling:
```bash
# Check Firebase CLI installed
if ! command -v firebase &> /dev/null; then
  echo "Firebase CLI not installed. Install with: npm install -g firebase-tools"
  exit 1
fi

# Check project initialized
if [ ! -f firebase.json ]; then
  echo "No firebase.json found. Initialize with: firebase init"
  exit 1
fi
```

### Security Considerations
- **Never expose API keys** in examples or commands
- **Use environment variables** for sensitive data
- **Include security rule templates** with least-privilege defaults
- **Validate inputs** before Firebase operations
- **Warn about production deployments** before destructive operations

## Vertex AI Gemini Integration Patterns

### Authentication
All Vertex AI operations should use Google Cloud Application Default Credentials:
```bash
# Set up ADC for local development
gcloud auth application-default login

# For production (use service account)
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

### Common Vertex AI Use Cases
- **Content Moderation**: Analyze user-generated content with Gemini before storing in Firestore
- **Semantic Search**: Generate embeddings for documents, store in Firestore, query by similarity
- **Chatbots**: Build conversational AI with Firebase data context
- **Image Analysis**: Use Gemini Vision API for image content understanding
- **Data Enrichment**: Automatically enhance Firestore documents with AI-generated metadata

### Example Integration Pattern
```javascript
// Cloud Function with Vertex AI Gemini
const {VertexAI} = require('@google-cloud/vertexai');
const admin = require('firebase-admin');

const vertex = new VertexAI({project: 'PROJECT_ID', location: 'us-central1'});
const model = vertex.getGenerativeModel({model: 'gemini-2.0-flash-exp'});

exports.analyzeContent = functions.firestore
  .document('posts/{postId}')
  .onCreate(async (snap, context) => {
    const content = snap.data().text;
    const result = await model.generateContent(content);

    // Store analysis back to Firestore
    await snap.ref.update({
      aiAnalysis: result.response.text()
    });
  });
```

## Testing Strategy

### Firebase Emulator Suite
Commands should support running against Firebase emulators:
```bash
# Start emulators
firebase emulators:start

# Deploy to emulators
firebase deploy --only functions --project demo-project
```

### Manual Testing Checklist
Before submitting plugin:
- [ ] Test all commands against a test Firebase project
- [ ] Verify Vertex AI integration with valid GCP credentials
- [ ] Test security rules deployment and validation
- [ ] Verify Cloud Functions deploy and execute correctly
- [ ] Test Hosting deployment with custom domain (if applicable)
- [ ] Validate error handling for missing dependencies
- [ ] Test skill activation with trigger phrases

## Documentation Requirements

### README.md Structure
The plugin README should include:
1. **Overview**: What this plugin does and why it's useful
2. **Installation**: How to install from marketplace
3. **Prerequisites**: Firebase CLI, GCP project, Node.js version requirements
4. **Quick Start**: 5-minute setup example
5. **Available Commands**: List all slash commands with descriptions
6. **Available Agents**: Complex workflows
7. **Agent Skills**: Automatic task handling with trigger phrases
8. **Configuration**: Environment variables, firebase.json setup
9. **Examples**: Real-world usage scenarios
10. **Troubleshooting**: Common issues and solutions

### Code Examples
All examples should:
- Be complete and runnable (no pseudo-code)
- Include error handling
- Follow Firebase best practices
- Use TypeScript where applicable
- Include comments explaining key steps

## Deployment Workflow

### Pre-commit Checklist
```bash
# 1. Validate plugin structure
../../scripts/validate-all-plugins.sh .

# 2. Check for hardcoded secrets
grep -r "AIza" . --exclude-dir=node_modules
grep -r "AAAA" . --exclude-dir=node_modules

# 3. Ensure all scripts are executable
find . -name "*.sh" -exec chmod +x {} \;

# 4. Validate JSON files
find . -name "*.json" -exec jq empty {} \;

# 5. Check YAML frontmatter in markdown files
python3 ../../scripts/validate-frontmatter.py

# 6. Add to marketplace catalog (if not already done)
# Edit .claude-plugin/marketplace.extended.json at repo root

# 7. Sync marketplace
cd ../.. && pnpm run sync-marketplace
```

### Adding to Marketplace Catalog
Edit `.claude-plugin/marketplace.extended.json` at repository root:
```json
{
  "plugins": [
    {
      "name": "jeremy-firebase",
      "source": "./plugins/community/jeremy-firebase",
      "description": "Production-ready Firebase platform operations with Vertex AI Gemini integration",
      "version": "1.0.0",
      "category": "integration",
      "keywords": [
        "firebase",
        "vertex-ai",
        "gemini",
        "authentication",
        "firestore",
        "cloud-functions",
        "hosting",
        "ai-integration"
      ],
      "author": {
        "name": "Jeremy Longshore",
        "email": "[email protected]"
      }
    }
  ]
}
```

## Common Firebase CLI Commands

Reference for building plugin commands:

```bash
# Project Management
firebase login                               # Authenticate
firebase projects:list                       # List projects
firebase use <project-id>                    # Switch project
firebase init                                # Initialize project

# Deployment
firebase deploy                              # Deploy everything
firebase deploy --only hosting              # Deploy hosting only
firebase deploy --only functions            # Deploy functions only
firebase deploy --only firestore:rules      # Deploy Firestore rules
firebase deploy --only storage:rules        # Deploy Storage rules

# Emulators
firebase emulators:start                    # Start all emulators
firebase emulators:start --only functions,firestore  # Start specific emulators

# Functions
firebase functions:log                      # View function logs
firebase functions:config:set key="value"  # Set function config

# Hosting
firebase hosting:channel:deploy <channel>  # Deploy to preview channel
firebase hosting:clone <source>:<dest>     # Clone hosting version

# Firestore
firebase firestore:delete <path>           # Delete Firestore document
firebase firestore:indexes                 # Deploy indexes
```

## Performance Considerations

- **Batch Firestore Operations**: Use batch writes for multiple document updates
- **Firebase Functions Cold Starts**: Implement function warming strategies
- **Vertex AI Rate Limits**: Implement exponential backoff and retry logic
- **Storage Upload Optimization**: Use resumable uploads for large files
- **Hosting Cache Headers**: Configure proper caching in firebase.json

## Security Best Practices

### Firestore Security Rules Template
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Helper functions
    function isAuthenticated() {
      return request.auth != null;
    }

    function isOwner(userId) {
      return isAuthenticated() && request.auth.uid == userId;
    }

    // Example: User-specific data
    match /users/{userId} {
      allow read: if isOwner(userId);
      allow write: if isOwner(userId);
    }
  }
}
```

### Storage Security Rules Template
```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    // User uploads
    match /users/{userId}/{allPaths=**} {
      allow read: if request.auth != null;
      allow write: if request.auth.uid == userId
                   && request.resource.size < 10 * 1024 * 1024; // 10MB limit
    }
  }
}
```

## Version History

- **1.0.0** (Initial Release): Core Firebase services integration with Vertex AI Gemini support

---

**Plugin Type:** AI Instruction Plugin + Agent Skills
**Target Users:** Full-stack developers, Firebase practitioners, GCP users
**Complexity Level:** Intermediate to Advanced
**Related Technologies:** Firebase, Google Cloud Platform, Vertex AI, TypeScript, Node.js
