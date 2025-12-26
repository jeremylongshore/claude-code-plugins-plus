---
name: firestore-setup
description: Initialize Firebase Admin SDK, configure Firestore, and setup A2A/MCP...
model: sonnet
---
# Firestore Setup Command

Initialize Firebase Admin SDK in your project with support for:
- Basic Firestore operations (CRUD, queries)
- A2A (Agent-to-Agent) framework integration
- MCP server communication patterns
- Cloud Run service integration
- Service account authentication

## Your Mission

Set up Firebase Admin SDK with proper configuration for both regular users and AI agents. Guide the user through:

1. **Environment detection** - Check if Firebase is already configured
2. **Dependency installation** - Install firebase-admin package
3. **Credential setup** - Configure service account authentication
4. **Firestore initialization** - Initialize and test connection
5. **A2A/MCP setup** (optional) - Configure for agent communication
6. **Security rules** (optional) - Deploy initial security rules

## Step-by-Step Workflow

### Step 1: Check Existing Setup

First, check if Firebase is already configured:

```bash
# Check if firebase-admin is installed
npm list firebase-admin

# Check for existing Firebase initialization
grep -r "firebase-admin" .

# Check for service account credentials
ls -la *.json | grep -i firebase
```

If Firebase is already set up, ask the user if they want to reconfigure.

### Step 2: Install Dependencies

```bash
# Install firebase-admin
npm install firebase-admin

# For A2A/MCP integration, also install:
npm install @google-cloud/firestore
npm install dotenv  # For environment variables
```

### Step 3: Get Service Account Credentials

Ask the user:

**Option A: Download from Firebase Console**
```
1. Go to https://console.firebase.google.com
2. Select your project
3. Settings (gear icon) → Project Settings → Service Accounts
4. Click "Generate new private key"
5. Save JSON file to your project (e.g., serviceAccountKey.json)
```

**Option B: Use existing GCP credentials**
```bash
# If using Google Cloud SDK
gcloud auth application-default login
```

**Option C: Environment variable (production)**
```bash
# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/serviceAccountKey.json"
```

### Step 4: Create Firebase Initialization File

Create `src/firebase.js` (or `src/firebase.ts` for TypeScript):

```javascript
const admin = require('firebase-admin');

// Initialize Firebase Admin SDK
if (!admin.apps.length) {
  // Option 1: Using service account key file
  const serviceAccount = require('../serviceAccountKey.json');

  admin.initializeApp({
    credential: admin.credential.cert(serviceAccount),
    databaseURL: `https://${serviceAccount.project_id}.firebaseio.com`
  });

  // Option 2: Using environment variable (recommended for production)
  // admin.initializeApp({
  //   credential: admin.credential.applicationDefault(),
  //   projectId: process.env.FIREBASE_PROJECT_ID
  // });
}

const db = admin.firestore();

// Export for use in other files
module.exports = { admin, db };
```

For TypeScript:
```typescript
import * as admin from 'firebase-admin';

if (!admin.apps.length) {
  const serviceAccount = require('../serviceAccountKey.json');

  admin.initializeApp({
    credential: admin.credential.cert(serviceAccount),
    databaseURL: `https://${serviceAccount.project_id}.firebaseio.com`
  });
}

export const db = admin.firestore();
export { admin };
```

### Step 5: Test Connection

Create a test script to verify Firestore works:

```javascript
const { db } = require('./src/firebase');

async function testFirestore() {
  try {
    // Test write
    const testRef = await db.collection('_test').add({
      message: 'Firebase connected successfully!',
      timestamp: admin.firestore.FieldValue.serverTimestamp()
    });

    console.log('✅ Write successful. Document ID:', testRef.id);

    // Test read
    const doc = await testRef.get();
    console.log('✅ Read successful. Data:', doc.data());

    // Clean up test document
    await testRef.delete();
    console.log('✅ Delete successful');

    console.log('\n🎉 Firebase is configured correctly!');
  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  }
}

testFirestore();
```

Run the test:
```bash
node test-firestore.js
```

### Step 6: A2A/MCP Setup (Optional)

If the user needs A2A or MCP integration, create additional configuration:

**A. Create A2A configuration file** (`src/a2a-config.js`):

```javascript
const { db } = require('./firebase');

// A2A Framework Configuration
const A2A_CONFIG = {
  collections: {
    sessions: 'agent_sessions',
    memory: 'agent_memory',
    tasks: 'a2a_tasks',
    messages: 'a2a_messages',
    logs: 'agent_logs'
  },

  serviceAccounts: [
    'mcp-server@project-id.iam.gserviceaccount.com',
    'agent-engine@project-id.iam.gserviceaccount.com'
  ],

  sessionTTL: 3600, // 1 hour in seconds
  messageTTL: 86400, // 24 hours

  rateLimits: {
    maxRequestsPerMinute: 100,
    maxConcurrentSessions: 50
  }
};

// Initialize A2A collections
async function initializeA2ACollections() {
  const collections = Object.values(A2A_CONFIG.collections);

  for (const collection of collections) {
    const ref = db.collection(collection);

    // Create initial document to establish collection
    await ref.doc('_init').set({
      initialized: true,
      timestamp: new Date()
    });

    console.log(`✅ Initialized collection: ${collection}`);
  }
}

module.exports = { A2A_CONFIG, initializeA2ACollections };
```

**B. Create MCP service integration** (`src/mcp-service.js`):

```javascript
const { db } = require('./firebase');
const { A2A_CONFIG } = require('./a2a-config');

class MCPService {
  constructor(serviceAccountEmail) {
    this.serviceAccountEmail = serviceAccountEmail;
    this.db = db;
  }

  // Create a new agent session
  async createSession(sessionData) {
    const sessionRef = this.db.collection(A2A_CONFIG.collections.sessions).doc();

    await sessionRef.set({
      ...sessionData,
      agentId: this.serviceAccountEmail,
      status: 'active',
      createdAt: admin.firestore.FieldValue.serverTimestamp(),
      expiresAt: new Date(Date.now() + A2A_CONFIG.sessionTTL * 1000)
    });

    return sessionRef.id;
  }

  // Store agent memory/context
  async storeContext(sessionId, contextData) {
    const contextRef = this.db
      .collection(A2A_CONFIG.collections.memory)
      .doc(this.serviceAccountEmail)
      .collection('contexts')
      .doc(sessionId);

    await contextRef.set({
      ...contextData,
      agentId: this.serviceAccountEmail,
      sessionId,
      timestamp: admin.firestore.FieldValue.serverTimestamp()
    });
  }

  // Send message to another agent
  async sendMessage(toAgent, payload) {
    await this.db.collection(A2A_CONFIG.collections.messages).add({
      from: this.serviceAccountEmail,
      to: toAgent,
      payload,
      timestamp: admin.firestore.FieldValue.serverTimestamp(),
      status: 'pending'
    });
  }

  // Receive messages for this agent
  async receiveMessages() {
    const snapshot = await this.db
      .collection(A2A_CONFIG.collections.messages)
      .where('to', '==', this.serviceAccountEmail)
      .where('status', '==', 'pending')
      .orderBy('timestamp', 'asc')
      .get();

    const messages = [];
    const batch = this.db.batch();

    snapshot.forEach(doc => {
      messages.push({ id: doc.id, ...doc.data() });
      // Mark as processed
      batch.update(doc.ref, { status: 'processed' });
    });

    await batch.commit();
    return messages;
  }

  // Log agent activity
  async logActivity(activity, level = 'info') {
    await this.db.collection(A2A_CONFIG.collections.logs).add({
      agentId: this.serviceAccountEmail,
      activity,
      level,
      timestamp: admin.firestore.FieldValue.serverTimestamp()
    });
  }
}

module.exports = { MCPService };
```

**C. Create Cloud Run service integration** (`src/cloudrun-service.js`):

```javascript
const { db } = require('./firebase');

class CloudRunService {
  constructor() {
    this.db = db;
  }

  // Log API requests from Cloud Run
  async logRequest(endpoint, method, userId, metadata = {}) {
    await this.db.collection('api_requests').add({
      endpoint,
      method,
      userId,
      metadata,
      timestamp: admin.firestore.FieldValue.serverTimestamp()
    });
  }

  // Store API response
  async storeResponse(requestId, responseData) {
    await this.db.collection('api_responses').doc(requestId).set({
      ...responseData,
      timestamp: admin.firestore.FieldValue.serverTimestamp()
    });
  }

  // Get user data for Cloud Run service
  async getUserData(userId) {
    const doc = await this.db.collection('users').doc(userId).get();
    if (!doc.exists) {
      throw new Error('User not found');
    }
    return doc.data();
  }
}

module.exports = { CloudRunService };
```

### Step 7: Setup Environment Variables

Create `.env` file:

```bash
# Firebase Configuration
GOOGLE_APPLICATION_CREDENTIALS=./serviceAccountKey.json
FIREBASE_PROJECT_ID=your-project-id

# A2A Configuration (if applicable)
MCP_SERVICE_ACCOUNT_EMAIL=mcp-server@project-id.iam.gserviceaccount.com
AGENT_ENGINE_SERVICE_ACCOUNT=agent-engine@project-id.iam.gserviceaccount.com

# Cloud Run Configuration (if applicable)
CLOUD_RUN_SERVICE_URL=https://your-service-abc123-uc.a.run.app
```

Add to `.gitignore`:
```
serviceAccountKey.json
.env
```

### Step 8: Deploy Security Rules (Optional)

Ask if the user wants to deploy initial security rules:

```bash
# Install Firebase CLI
npm install -g firebase-tools

# Login
firebase login

# Initialize Firestore rules
firebase init firestore
```

Then use the `firestore-security-agent` to generate appropriate rules based on their use case.

### Step 9: Create Example Usage File

Create `examples/firestore-usage.js`:

```javascript
const { db, admin } = require('../src/firebase');

// Example 1: Basic CRUD
async function basicCRUD() {
  // Create
  const docRef = await db.collection('users').add({
    name: 'John Doe',
    email: '[email protected]',
    createdAt: admin.firestore.FieldValue.serverTimestamp()
  });

  // Read
  const doc = await docRef.get();
  console.log('User data:', doc.data());

  // Update
  await docRef.update({
    name: 'John Updated',
    updatedAt: admin.firestore.FieldValue.serverTimestamp()
  });

  // Delete
  await docRef.delete();
}

// Example 2: Queries
async function queryExamples() {
  // Simple query
  const activeUsers = await db.collection('users')
    .where('status', '==', 'active')
    .limit(10)
    .get();

  activeUsers.forEach(doc => {
    console.log(doc.id, doc.data());
  });

  // Complex query
  const recentOrders = await db.collection('orders')
    .where('userId', '==', 'user123')
    .where('status', '==', 'pending')
    .orderBy('createdAt', 'desc')
    .limit(5)
    .get();
}

// Example 3: Batch operations
async function batchOperations() {
  const batch = db.batch();

  // Add multiple documents
  for (let i = 0; i < 10; i++) {
    const ref = db.collection('items').doc();
    batch.set(ref, {
      name: `Item ${i}`,
      createdAt: admin.firestore.FieldValue.serverTimestamp()
    });
  }

  await batch.commit();
  console.log('Batch write completed');
}

// Example 4: A2A usage (if configured)
async function a2aExample() {
  const { MCPService } = require('../src/mcp-service');
  const mcp = new MCPService('mcp-server@project.iam.gserviceaccount.com');

  // Create session
  const sessionId = await mcp.createSession({
    task: 'process_user_data',
    priority: 'high'
  });

  // Store context
  await mcp.storeContext(sessionId, {
    userId: 'user123',
    action: 'data_processing'
  });

  // Send message to another agent
  await mcp.sendMessage(
    'agent-engine@project.iam.gserviceaccount.com',
    { action: 'analyze', data: { userId: 'user123' } }
  );

  // Log activity
  await mcp.logActivity('Processed user data', 'info');
}

module.exports = { basicCRUD, queryExamples, batchOperations, a2aExample };
```

## Post-Setup Checklist

Verify the following after setup:

- [ ] Firebase Admin SDK installed
- [ ] Service account credentials configured
- [ ] `.gitignore` includes serviceAccountKey.json and .env
- [ ] Connection test passes
- [ ] Example usage file works
- [ ] A2A collections initialized (if applicable)
- [ ] Security rules deployed (if applicable)
- [ ] Environment variables set
- [ ] Documentation updated

## Next Steps

Tell the user:

1. **Test the setup** - Run `node test-firestore.js`
2. **Read the examples** - Check `examples/firestore-usage.js`
3. **Deploy security rules** - Use `/firestore-security-agent` to generate rules
4. **Start building** - Use `/firebase-operations-agent` for CRUD operations

## Common Issues

### Issue 1: "Permission denied" errors
- Check service account has Firestore permissions
- Verify security rules allow the operation
- Ensure GOOGLE_APPLICATION_CREDENTIALS is set correctly

### Issue 2: "Firebase app already initialized"
- This is normal - only initialize once
- Check if Firebase is initialized in multiple files

### Issue 3: "Cannot find module 'firebase-admin'"
- Run `npm install firebase-admin`
- Check package.json includes firebase-admin

### Issue 4: A2A collections not accessible
- Verify service account email is whitelisted in security rules
- Check firestore.rules includes A2A patterns
- Test with Firebase Emulator first

## Security Reminders

1. **Never commit serviceAccountKey.json** to version control
2. **Use environment variables** in production
3. **Whitelist service accounts** in security rules
4. **Rotate credentials regularly** (every 90 days recommended)
5. **Monitor usage** with Firebase console
6. **Set up billing alerts** to avoid surprises

Congratulations! Your Firestore setup is complete! 🎉
