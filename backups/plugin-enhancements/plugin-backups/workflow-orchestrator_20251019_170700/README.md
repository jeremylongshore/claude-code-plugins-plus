# Workflow Orchestrator

**DAG-based workflow orchestration with parallel execution and run history**

Automate complex multi-step workflows with dependency management, parallel execution, and comprehensive run tracking.

##  Features

- **DAG Execution** - Directed Acyclic Graph task dependencies
- **Parallel Tasks** - Execute independent tasks concurrently
- **Run History** - Track all workflow executions
- **Status Monitoring** - Real-time workflow progress
- **Error Handling** - Graceful failure management

##  Installation

```bash
/plugin install workflow-orchestrator@claude-code-plugins-plus
```

##  4 MCP Tools

### 1. `create_workflow`
Define workflow with tasks and dependencies.

```json
{
  "name": "Build and Deploy",
  "tasks": [
    {"id": "lint", "name": "Lint code", "command": "npm run lint", "dependencies": []},
    {"id": "test", "name": "Run tests", "command": "npm test", "dependencies": ["lint"]},
    {"id": "build", "name": "Build", "command": "npm run build", "dependencies": ["test"]},
    {"id": "deploy", "name": "Deploy", "command": "npm run deploy", "dependencies": ["build"]}
  ]
}
```

### 2. `execute_workflow`
Run workflow with parallel execution.

```json
{
  "workflowId": "wf_1234567890",
  "parallel": true
}
```

### 3. `get_workflow`
Get workflow status and task details.

```json
{
  "workflowId": "wf_1234567890"
}
```

### 4. `list_workflows`
List all workflows with optional filtering.

```json
{
  "status": "completed"
}
```

##  Quick Start

```javascript
// 1. Create workflow
const workflow = await create_workflow({
  name: "CI/CD Pipeline",
  tasks: [
    { id: "lint", name: "Lint", command: "npm run lint", dependencies: [] },
    { id: "test", name: "Test", command: "npm test", dependencies: ["lint"] },
    { id: "build", name: "Build", command: "npm run build", dependencies: ["test"] }
  ]
});

// 2. Execute workflow
const result = await execute_workflow({
  workflowId: workflow.workflowId,
  parallel: true
});

// 3. Check status
const status = await get_workflow({
  workflowId: workflow.workflowId
});
```

##  DAG Execution

Tasks execute based on dependency graph:

```
  lint
    ↓
  test ← test:integration (parallel)
    ↓        ↓
  build ←───┘
    ↓
  deploy
```

Independent tasks (test + test:integration) run in parallel.

##  Use Cases

1. **CI/CD Pipelines** - Automated build, test, deploy
2. **Data Pipelines** - ETL workflows with dependencies
3. **Deployment Automation** - Multi-stage deployments
4. **Testing Workflows** - Parallel test execution
5. **Batch Processing** - Complex job orchestration

##  License

MIT License

---

**Made with ️ by [Intent Solutions](https://intentsolutions.io)**
