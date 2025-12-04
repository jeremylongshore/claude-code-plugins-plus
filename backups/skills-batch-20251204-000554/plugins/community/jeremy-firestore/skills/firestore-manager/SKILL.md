---
name: firestore-operations-manager
description: |
  Manages Firebase/Firestore operations including CRUD, queries, batch processing, A2A agent communication, MCP server integration, and Cloud Run service coordination.
  Activates when you request "firestore operations", "create firestore document", "query firestore", "A2A agent communication", "MCP server setup", "agent-to-agent messaging", or "Cloud Run firestore integration".
  Handles both basic database operations for regular users and advanced A2A framework patterns for AI agents.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
version: 1.0.0
---

# Firestore Operations Manager

## Overview

This skill manages Firebase/Firestore operations for both regular web/mobile applications and AI agent-to-agent (A2A) frameworks. It handles:

- **Basic Operations**: CRUD, queries, batch processing for standard applications
- **A2A Framework**: Agent-to-agent communication patterns using Firestore as state store
- **MCP Integration**: Model Context Protocol server communication via Firestore
- **Cloud Run Services**: Integration patterns for Cloud Run services accessing Firestore
- **Security**: Proper authentication, validation, and security rules for both humans and agents

## Core Capabilities

### For Everyone (Basic Firestore)
- Create, read, update, delete documents
- Complex queries with filters and ordering
- Batch operations for efficiency
- Collection management and organization
- Security rules generation and validation
- Data migrations and transformations

### For AI Power Users (A2A/MCP)
- Agent session management with Firestore state
- Agent-to-agent messaging and task coordination
- MCP server communication patterns
- Agent memory and context storage
- Cloud Run service integration
- Multi-agent workflow orchestration

## When to Use This Skill

This skill activates when users mention:

- **Basic operations**: "create a firestore document", "query users collection", "batch update documents"
- **A2A patterns**: "setup agent communication", "A2A task queue", "agent-to-agent messaging"
- **MCP integration**: "MCP server firestore", "agent memory storage", "session management"
- **Cloud Run**: "Cloud Run firestore integration", "service account access"
- **Security**: "firestore security rules", "agent authentication", "service account permissions"

## Workflow

### Phase 1: Setup and Initialization

**For basic users:**
1. Check if Firebase Admin SDK is installed
2. Guide through credential setup (service account JSON)
3. Initialize Firestore connection
4. Run connection test
5. Create basic usage examples

**For A2A/MCP users:**
1. Perform basic setup (above)
2. Install additional dependencies (@google-cloud/firestore)
3. Create A2A collection structure (sessions, memory, tasks, messages, logs)
4. Configure service account whitelisting
5. Setup security rules for agent access
6. Create MCP service wrapper classes

Example setup:
```bash
# Basic setup
npm install firebase-admin

# A2A/MCP setup
npm install firebase-admin @google-cloud/firestore dotenv

# Set credentials
export GOOGLE_APPLICATION_CREDENTIALS="./serviceAccountKey.json"

# Run setup command
/firestore-setup
```

### Phase 2: Basic CRUD Operations

For standard database operations:

**Create documents:**
```javascript
const { db, admin } = require('./src/firebase');

// Single document
await db.collection('users').add({
  name: 'John Doe',
  email: '[email protected]',
  createdAt: admin.firestore.FieldValue.serverTimestamp()
});

// With custom ID
await db.collection('users').doc('user123').set({
  name: 'Jane Doe',
  email: '[email protected]'
});
```

**Read documents:**
```javascript
// Single document
const doc = await db.collection('users').doc('user123').get();
const userData = doc.data();

// Query
const snapshot = await db.collection('users')
  .where('status', '==', 'active')
  .orderBy('createdAt', 'desc')
  .limit(10)
  .get();

snapshot.forEach(doc => console.log(doc.data()));
```

**Update documents:**
```javascript
// Partial update
await db.collection('users').doc('user123').update({
  status: 'active',
  updatedAt: admin.firestore.FieldValue.serverTimestamp()
});

// Increment counter
await db.collection('stats').doc('views').update({
  count: admin.firestore.FieldValue.increment(1)
});
```

**Delete documents:**
```javascript
// Single delete
await db.collection('users').doc('user123').delete();

// Batch delete
const batch = db.batch();
const docs = await db.collection('temp').limit(500).get();
docs.forEach(doc => batch.delete(doc.ref));
await batch.commit();
```

### Phase 3: A2A Framework Operations

For agent-to-agent communication patterns:

**1. Create Agent Session:**
```javascript
const { MCPService } = require('./src/mcp-service');
const mcp = new MCPService('mcp-server@project.iam.gserviceaccount.com');

// Create session for agent workflow
const sessionId = await mcp.createSession({
  task: 'process_user_data',
  priority: 'high',
  metadata: { userId: 'user123' }
});

console.log(`Session created: ${sessionId}`);
```

**2. Store Agent Context:**
```javascript
// Store agent memory/context in Firestore
await mcp.storeContext(sessionId, {
  conversation: [...messages],
  userPreferences: { theme: 'dark' },
  currentStep: 'data_validation'
});

// Retrieve context later
const context = await db
  .collection('agent_memory')
  .doc('mcp-server@project.iam.gserviceaccount.com')
  .collection('contexts')
  .doc(sessionId)
  .get();
```

**3. Agent-to-Agent Messaging:**
```javascript
// Send message from one agent to another
await mcp.sendMessage(
  'agent-engine@project.iam.gserviceaccount.com',
  {
    action: 'analyze_data',
    data: { userId: 'user123', fields: ['name', 'email'] }
  }
);

// Receive messages (in receiving agent)
const messages = await mcp.receiveMessages();
messages.forEach(msg => {
  console.log(`From: ${msg.from}, Payload:`, msg.payload);
});
```

**4. Task Queue Management:**
```javascript
// Create task for another agent
await db.collection('a2a_tasks').add({
  taskType: 'data_processing',
  assignedTo: 'worker-agent@project.iam.gserviceaccount.com',
  status: 'pending',
  priority: 1,
  payload: { userId: 'user123' },
  createdAt: admin.firestore.FieldValue.serverTimestamp()
});

// Agent claims and processes task
const taskQuery = await db.collection('a2a_tasks')
  .where('assignedTo', '==', 'worker-agent@project.iam.gserviceaccount.com')
  .where('status', '==', 'pending')
  .orderBy('priority', 'asc')
  .limit(1)
  .get();

if (!taskQuery.empty) {
  const task = taskQuery.docs[0];
  await task.ref.update({ status: 'in_progress' });
  // Process task...
  await task.ref.update({ status: 'completed' });
}
```

**5. Agent Activity Logging:**
```javascript
// Log agent activities for audit trail
await mcp.logActivity({
  action: 'processed_data',
  userId: 'user123',
  duration: 1500, // ms
  result: 'success'
}, 'info');
```

### Phase 4: Cloud Run Integration

For Cloud Run services accessing Firestore:

**Setup Cloud Run service class:**
```javascript
const { CloudRunService } = require('./src/cloudrun-service');
const cloudrun = new CloudRunService();

// In your Cloud Run endpoint
app.post('/api/users/:userId/data', async (req, res) => {
  const { userId } = req.params;

  try {
    // Log request
    await cloudrun.logRequest('/api/users/data', 'POST', userId);

    // Get user data from Firestore
    const userData = await cloudrun.getUserData(userId);

    // Store response
    await cloudrun.storeResponse(req.id, {
      userId,
      data: userData,
      status: 'success'
    });

    res.json({ success: true, data: userData });
  } catch (error) {
    await cloudrun.storeResponse(req.id, {
      userId,
      error: error.message,
      status: 'error'
    });

    res.status(500).json({ error: error.message });
  }
});
```

### Phase 5: Security Rules Management

Generate and deploy security rules for both users and agents:

**For basic users:**
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
  }
}
```

**For A2A/MCP (service accounts):**
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    function isServiceAccount() {
      return request.auth.token.email.matches('.*@.*\\.iam\\.gserviceaccount\\.com$');
    }

    function isAuthorizedAgent() {
      return isServiceAccount() && request.auth.token.email in [
        'mcp-server@project-id.iam.gserviceaccount.com',
        'agent-engine@project-id.iam.gserviceaccount.com'
      ];
    }

    // Agent sessions
    match /agent_sessions/{sessionId} {
      allow read, write: if isAuthorizedAgent();
    }

    // Agent memory
    match /agent_memory/{agentId}/{document=**} {
      allow read, write: if isAuthorizedAgent();
    }

    // A2A messages
    match /a2a_messages/{messageId} {
      allow create: if isAuthorizedAgent();
      allow read: if isAuthorizedAgent() &&
                     (resource.data.from == request.auth.token.email ||
                      resource.data.to == request.auth.token.email);
    }
  }
}
```

Deploy rules:
```bash
firebase deploy --only firestore:rules
```

## Advanced Patterns

### Pattern 1: Multi-Agent Workflow Orchestration

```javascript
// Coordinator agent creates workflow
const workflowId = await db.collection('workflows').add({
  name: 'user_data_processing',
  steps: [
    { agent: 'validator@project.iam.gserviceaccount.com', status: 'pending' },
    { agent: 'processor@project.iam.gserviceaccount.com', status: 'pending' },
    { agent: 'notifier@project.iam.gserviceaccount.com', status: 'pending' }
  ],
  createdAt: admin.firestore.FieldValue.serverTimestamp()
});

// Each agent listens for their step
const unsubscribe = db.collection('workflows')
  .doc(workflowId)
  .onSnapshot(async (doc) => {
    const workflow = doc.data();
    const myStep = workflow.steps.find(s => s.agent === myEmail && s.status === 'pending');

    if (myStep) {
      // Process step
      await processStep(myStep);

      // Mark complete and notify next agent
      myStep.status = 'completed';
      await doc.ref.update({ steps: workflow.steps });
    }
  });
```

### Pattern 2: Agent Context Sharing

```javascript
// Agent 1 stores context
await db.collection('shared_context').doc('task_abc').set({
  sharedBy: 'agent1@project.iam.gserviceaccount.com',
  sharedWith: ['agent2@project.iam.gserviceaccount.com'],
  context: {
    userId: 'user123',
    analysis: { sentiment: 'positive', score: 0.85 }
  },
  expiresAt: new Date(Date.now() + 3600000) // 1 hour
});

// Agent 2 retrieves context
const contextDoc = await db.collection('shared_context').doc('task_abc').get();
if (contextDoc.exists && contextDoc.data().sharedWith.includes(myEmail)) {
  const context = contextDoc.data().context;
  // Use context...
}
```

### Pattern 3: Rate Limiting for Agents

```javascript
// Check and enforce rate limits
const rateLimitRef = db.collection('rate_limits').doc(agentEmail);
const rateLimitDoc = await rateLimitRef.get();

if (rateLimitDoc.exists) {
  const { count, resetAt } = rateLimitDoc.data();

  if (Date.now() < resetAt && count >= 100) {
    throw new Error('Rate limit exceeded');
  }

  if (Date.now() >= resetAt) {
    // Reset counter
    await rateLimitRef.set({
      count: 1,
      resetAt: Date.now() + 60000 // 1 minute
    });
  } else {
    // Increment counter
    await rateLimitRef.update({
      count: admin.firestore.FieldValue.increment(1)
    });
  }
} else {
  // First request
  await rateLimitRef.set({
    count: 1,
    resetAt: Date.now() + 60000
  });
}
```

## Performance Optimization

### For Basic Users:
1. **Use batch operations** - Write/update 500 docs at once
2. **Create indexes** - Required for complex queries
3. **Paginate results** - Use cursor-based pagination
4. **Cache frequently read data** - Reduce read costs

### For A2A/MCP Users:
1. **Connection pooling** - Reuse Firestore connections
2. **Batch agent messages** - Combine multiple messages
3. **TTL for agent data** - Clean up expired sessions automatically
4. **Denormalize agent state** - Avoid cross-collection queries

## Cost Optimization

Firestore costs:
- Document reads: $0.06 per 100k
- Document writes: $0.18 per 100k
- Document deletes: $0.02 per 100k

Reduce costs:
- Use batch writes (1 operation vs 500)
- Cache agent context locally
- Archive old agent logs to Cloud Storage
- Set up billing alerts

## Security Best Practices

1. **Never allow open access** - Always require authentication
2. **Whitelist service accounts** - Don't allow all service accounts
3. **Validate all inputs** - Check types, formats, required fields
4. **Make logs immutable** - Prevent tampering with audit trails
5. **Rotate credentials** - Change service account keys every 90 days
6. **Monitor usage** - Set up Firebase console alerts
7. **Test rules** - Use Firebase Emulator before deploying

## Troubleshooting

### Issue: Permission Denied
- Check security rules allow the operation
- Verify service account is whitelisted
- Ensure GOOGLE_APPLICATION_CREDENTIALS is set

### Issue: A2A Messages Not Delivered
- Verify recipient agent email is correct
- Check message status in Firestore console
- Ensure security rules allow cross-agent messaging

### Issue: Rate Limit Errors
- Implement exponential backoff
- Use batch operations
- Increase rate limits in configuration

### Issue: Cloud Run Connection Fails
- Verify service account has Firestore permissions
- Check VPC connectivity if using private IP
- Ensure project ID matches in code and credentials

## Examples

See `examples/firestore-usage.js` for complete code examples covering:
- Basic CRUD operations
- Complex queries and pagination
- Batch operations
- A2A agent communication
- MCP server integration
- Cloud Run service patterns
- Security rules testing

## Resources

- [Firestore Documentation](https://firebase.google.com/docs/firestore)
- [A2A Protocol Specification](https://github.com/google/vertex-ai-agents)
- [MCP Documentation](https://github.com/anthropics/mcp)
- [Cloud Run Integration](https://cloud.google.com/run/docs/tutorials)

## Summary

This skill provides comprehensive Firestore operations for:
- **Everyone**: Standard database CRUD, queries, batch ops, security
- **AI Power Users**: A2A communication, MCP integration, Cloud Run services, multi-agent workflows

Use `/firestore-setup` to initialize, then leverage the agents and commands for specific operations!
