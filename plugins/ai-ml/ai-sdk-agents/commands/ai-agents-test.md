---
name: ai-agents-test
description: Test your multi-agent system with a sample task, showing agent handoffs,...
model: sonnet
---
You are an expert in multi-agent system testing and observability.

# Mission
Test a multi-agent orchestration system by:
- Running a sample task through the agent network
- Showing real-time agent handoffs and routing
- Displaying performance metrics (time, handoff count)
- Validating agent coordination and output quality
- Identifying bottlenecks or issues

# Usage

User invokes: `/ai-agents-test "Task description"`

Examples:
- `/ai-agents-test "Build a REST API with authentication"`
- `/ai-agents-test "Research best practices for React performance"`
- `/ai-agents-test "Debug this authentication error"`

# Test Process

## 1. Validate Setup

First check if the multi-agent project exists:

```bash
# Check for required files
if [ -f "index.ts" ] && [ -d "agents" ]; then
  echo "✅ Multi-agent project found"
else
  echo "❌ Multi-agent project not found"
  echo "💡 Run /ai-agents-setup first to create the project"
  exit 1
fi
```

## 2. Parse Test Query

Extract the task from user input:
- If provided: Use their task
- If empty: Use default test task

Default tasks by category:
- **Code generation**: "Build a TODO API with CRUD operations"
- **Research**: "Research microservices best practices"
- **Debug**: "Why is my JWT authentication failing?"
- **Review**: "Review this code for security issues"

## 3. Start Test Execution

Create a test runner script:

### test-runner.ts
```typescript
import { runMultiAgentTask } from './index';

interface TestMetrics {
  startTime: number;
  endTime?: number;
  handoffs: Array<{
    from: string;
    to: string;
    reason: string;
    timestamp: number;
  }>;
  agentsInvolved: Set<string>;
  totalDuration?: number;
}

async function testMultiAgentSystem(task: string) {
  console.log('🚀 Multi-Agent System Test\n');
  console.log('━'.repeat(60));
  console.log(`📋 Task: ${task}`);
  console.log('━'.repeat(60));
  console.log('');

  const metrics: TestMetrics = {
    startTime: Date.now(),
    handoffs: [],
    agentsInvolved: new Set()
  };

  try {
    const result = await runMultiAgentTask(task);

    metrics.endTime = Date.now();
    metrics.totalDuration = metrics.endTime - metrics.startTime;

    // Display results
    displayResults(result, metrics);

    return { success: true, result, metrics };
  } catch (error) {
    console.error('❌ Test failed:', error);
    return { success: false, error, metrics };
  }
}

function displayResults(result: any, metrics: TestMetrics) {
  console.log('\n' + '━'.repeat(60));
  console.log('📊 Test Results');
  console.log('━'.repeat(60));
  console.log('');

  // Success indicator
  console.log('✅ Status: Task completed successfully\n');

  // Metrics
  console.log('⏱️  Performance Metrics:');
  console.log(`   Total duration: ${metrics.totalDuration}ms (${(metrics.totalDuration! / 1000).toFixed(2)}s)`);
  console.log(`   Handoff count: ${metrics.handoffs.length}`);
  console.log(`   Agents involved: ${metrics.agentsInvolved.size}`);
  console.log(`   Avg time per handoff: ${(metrics.totalDuration! / Math.max(metrics.handoffs.length, 1)).toFixed(0)}ms`);
  console.log('');

  // Agent flow
  if (metrics.handoffs.length > 0) {
    console.log('🔄 Agent Flow:');
    const agentFlow = ['coordinator'];
    metrics.handoffs.forEach(h => {
      if (!agentFlow.includes(h.to)) {
        agentFlow.push(h.to);
      }
    });
    console.log(`   ${agentFlow.join(' → ')}`);
    console.log('');
  }

  // Handoff details
  if (metrics.handoffs.length > 0) {
    console.log('🔀 Handoff Details:');
    metrics.handoffs.forEach((handoff, i) => {
      const duration = i < metrics.handoffs.length - 1
        ? metrics.handoffs[i + 1].timestamp - handoff.timestamp
        : metrics.endTime! - handoff.timestamp;

      console.log(`   ${i + 1}. ${handoff.from} → ${handoff.to}`);
      console.log(`      Reason: ${handoff.reason}`);
      console.log(`      Duration: ${duration}ms`);
      console.log('');
    });
  }

  // Output summary
  console.log('📝 Output Summary:');
  const output = typeof result.output === 'string' ? result.output : JSON.stringify(result.output, null, 2);
  const lines = output.split('\n');

  if (lines.length > 20) {
    console.log(lines.slice(0, 10).join('\n'));
    console.log(`   ... (${lines.length - 20} more lines) ...`);
    console.log(lines.slice(-10).join('\n'));
  } else {
    console.log(output);
  }
  console.log('');

  // Quality assessment
  console.log('🎯 Quality Assessment:');
  const qualityScore = assessQuality(result, metrics);
  console.log(`   Overall score: ${qualityScore.score}/100`);
  console.log(`   Completeness: ${qualityScore.completeness}`);
  console.log(`   Efficiency: ${qualityScore.efficiency}`);
  console.log(`   Coordination: ${qualityScore.coordination}`);
  console.log('');
}

function assessQuality(result: any, metrics: TestMetrics) {
  let score = 100;
  let completeness = '✅ Excellent';
  let efficiency = '✅ Excellent';
  let coordination = '✅ Excellent';

  // Check completeness
  const outputLength = JSON.stringify(result.output).length;
  if (outputLength < 100) {
    score -= 30;
    completeness = '⚠️  Incomplete';
  } else if (outputLength < 500) {
    score -= 10;
    completeness = '✅ Good';
  }

  // Check efficiency
  const avgHandoffTime = metrics.totalDuration! / Math.max(metrics.handoffs.length, 1);
  if (avgHandoffTime > 5000) {
    score -= 20;
    efficiency = '⚠️  Slow';
  } else if (avgHandoffTime > 3000) {
    score -= 10;
    efficiency = '✅ Good';
  }

  // Check coordination
  if (metrics.handoffs.length === 0) {
    score -= 20;
    coordination = '⚠️  No handoffs';
  } else if (metrics.handoffs.length > 10) {
    score -= 10;
    coordination = '⚠️  Too many handoffs';
  }

  return {
    score: Math.max(0, score),
    completeness,
    efficiency,
    coordination
  };
}

// CLI interface
const task = process.argv[2];

if (!task) {
  console.error('❌ Error: Please provide a task to test');
  console.log('');
  console.log('Usage: ts-node test-runner.ts "Your task description"');
  console.log('');
  console.log('Examples:');
  console.log('  ts-node test-runner.ts "Build a REST API with authentication"');
  console.log('  ts-node test-runner.ts "Research React performance best practices"');
  console.log('');
  process.exit(1);
}

testMultiAgentSystem(task)
  .then(({ success }) => {
    process.exit(success ? 0 : 1);
  })
  .catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
```

## 4. Enhanced Orchestration with Metrics

Update `index.ts` to emit events for testing:

```typescript
export async function runMultiAgentTask(task: string, options?: {
  onHandoff?: (event: HandoffEvent) => void;
  onComplete?: (result: any) => void;
  verbose?: boolean;
}) {
  const verbose = options?.verbose ?? true;

  if (verbose) {
    console.log(`\n🤖 Starting multi-agent task: ${task}\n`);
  }

  const handoffs: Array<{
    from: string;
    to: string;
    reason: string;
    timestamp: number;
  }> = [];

  const result = await orchestrate({
    agents,
    task,
    coordinator,
    maxDepth: 10,
    timeout: 300000,

    onHandoff: (event) => {
      const handoffData = {
        from: event.from,
        to: event.to,
        reason: event.reason,
        timestamp: Date.now()
      };

      handoffs.push(handoffData);

      if (verbose) {
        console.log(`\n🔄 Handoff: ${event.from} → ${event.to}`);
        console.log(`   Reason: ${event.reason}\n`);
      }

      options?.onHandoff?.(event);
    },

    onComplete: (result) => {
      if (verbose) {
        console.log(`\n✅ Task complete!`);
        console.log(`   Total handoffs: ${handoffs.length}`);
        console.log(`   Agents: ${new Set(handoffs.flatMap(h => [h.from, h.to])).size}\n`);
      }

      options?.onComplete?.(result);
    }
  });

  return {
    ...result,
    metrics: {
      handoffs,
      agentCount: new Set(handoffs.flatMap(h => [h.from, h.to])).size
    }
  };
}
```

## 5. Execute Test

Run the test:

```bash
# Using ts-node
ts-node test-runner.ts "Build a REST API with authentication"

# Or using npm script
npm run test:agents "Build a REST API with authentication"
```

## 6. Display Real-Time Progress

Show live updates during execution:

```
🚀 Multi-Agent System Test

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Task: Build a REST API with authentication
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔄 Handoff: coordinator → researcher
   Reason: Need to research authentication best practices

🔄 Handoff: researcher → coder
   Reason: Research complete, ready to implement

🔄 Handoff: coder → reviewer
   Reason: Implementation complete, needs review

🔄 Handoff: reviewer → coordinator
   Reason: Review complete, all checks passed

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Test Results
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Status: Task completed successfully

⏱️  Performance Metrics:
   Total duration: 47823ms (47.82s)
   Handoff count: 4
   Agents involved: 4
   Avg time per handoff: 11956ms

🔄 Agent Flow:
   coordinator → researcher → coder → reviewer → coordinator

🔀 Handoff Details:
   1. coordinator → researcher
      Reason: Need to research authentication best practices
      Duration: 8234ms

   2. researcher → coder
      Reason: Research complete, ready to implement
      Duration: 23456ms

   3. coder → reviewer
      Reason: Implementation complete, needs review
      Duration: 12389ms

   4. reviewer → coordinator
      Reason: Review complete, all checks passed
      Duration: 3744ms

📝 Output Summary:
{
  "api": "REST API with JWT authentication",
  "features": [
    "User registration",
    "User login",
    "JWT token generation",
    "Protected routes",
    "Token refresh"
  ],
  "security": {
    "passwordHashing": "bcrypt",
    "tokenExpiry": "1h",
    "refreshToken": "7d"
  },
  "endpoints": [
    "POST /api/auth/register",
    "POST /api/auth/login",
    "POST /api/auth/refresh",
    "GET /api/users/me (protected)"
  ],
  "tests": "95% coverage"
}

🎯 Quality Assessment:
   Overall score: 95/100
   Completeness: ✅ Excellent
   Efficiency: ✅ Excellent
   Coordination: ✅ Excellent
```

## 7. Add Test Script to package.json

```json
{
  "scripts": {
    "test:agents": "ts-node test-runner.ts"
  }
}
```

## 8. Create Pre-defined Test Scenarios

Create `tests/scenarios.json`:

```json
{
  "scenarios": [
    {
      "name": "Code Generation",
      "task": "Build a REST API with authentication and CRUD operations",
      "expectedAgents": ["coordinator", "researcher", "coder", "reviewer"],
      "expectedHandoffs": 4,
      "maxDuration": 60000
    },
    {
      "name": "Research Task",
      "task": "Research best practices for microservices architecture",
      "expectedAgents": ["coordinator", "researcher"],
      "expectedHandoffs": 2,
      "maxDuration": 20000
    },
    {
      "name": "Debug Task",
      "task": "Debug JWT authentication failing with 401 errors",
      "expectedAgents": ["coordinator", "researcher", "security-auditor"],
      "expectedHandoffs": 3,
      "maxDuration": 30000
    },
    {
      "name": "Complex Pipeline",
      "task": "Design, implement, test, and document a payment processing API",
      "expectedAgents": ["coordinator", "api-designer", "coder", "test-writer", "reviewer"],
      "expectedHandoffs": 6,
      "maxDuration": 120000
    }
  ]
}
```

## 9. Troubleshooting

If test fails, check:

```bash
# 1. Environment variables
if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "❌ Error: ANTHROPIC_API_KEY not set"
  echo "💡 Add your API key to .env file"
  exit 1
fi

# 2. Dependencies installed
if [ ! -d "node_modules/@ai-sdk-tools/agents" ]; then
  echo "❌ Error: Dependencies not installed"
  echo "💡 Run: npm install"
  exit 1
fi

# 3. Agents registered
if ! grep -q "researcher" index.ts; then
  echo "⚠️  Warning: Not all agents registered in index.ts"
fi
```

# Output Summary

After test completion, show:

```
✅ Multi-agent test complete!

📊 Results:
   Status: Success
   Duration: 47.8s
   Agents: 4 (coordinator, researcher, coder, reviewer)
   Handoffs: 4
   Quality: 95/100

🎯 Assessment:
   ✅ All agents coordinated successfully
   ✅ Task completed within expected time
   ✅ Output quality meets standards

💡 Recommendations:
   - System is functioning optimally
   - Consider adding more specialized agents for complex tasks
   - Average handoff time is excellent (11.9s)

📁 Full test output saved to: test-results-[timestamp].json
```

# Test Validation Criteria

A successful test should have:
- ✅ At least 2 agents involved (coordinator + 1 specialist)
- ✅ Meaningful handoffs with clear reasons
- ✅ Completion within timeout (5 minutes default)
- ✅ Quality output (not just "task complete")
- ✅ No errors or exceptions

# Performance Benchmarks

Expected performance ranges:
- **Simple tasks** (research): 10-20 seconds, 2-3 handoffs
- **Medium tasks** (code generation): 30-60 seconds, 3-5 handoffs
- **Complex tasks** (full pipeline): 60-120 seconds, 5-8 handoffs

If actual performance exceeds these by 2x, investigate:
- API rate limiting
- Model selection (use faster models for testing)
- Network latency
- Agent prompt optimization
