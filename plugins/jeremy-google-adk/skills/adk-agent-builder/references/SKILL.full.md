---
name: adk-agent-builder
description: |
  Build production-ready AI agents using Google's Agent Development Kit with AI assistant integration, React patterns, multi-agent orchestration, and comprehensive tool libraries. Use when appropriate context detected. Trigger with relevant phrases based on skill purpose.
allowed-tools: Read, Write, Edit, Grep, Bash(cmd:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---
# ADK Agent Builder Skill



This skill provides automated assistance for adk agent builder tasks.

## Prerequisites

- Appropriate file access permissions
- Required dependencies installed

## Instructions

1. Invoke this skill when the trigger conditions are met
2. Provide necessary context and parameters
3. Review the generated output
4. Apply modifications as needed

## Output

The skill produces structured output relevant to the task.

## Error Handling

- Invalid input: Prompts for correction
- Missing dependencies: Lists required components
- Permission errors: Suggests remediation steps

## Resources

- Project documentation
- Related skills and commands
## Overview


This skill provides automated assistance for adk agent builder tasks.
The ADK Agent Builder accelerates AI agent development using Google's Agent Development Kit (ADK) framework integrated with Claude API. This skill provides production-ready scaffolding for:

- **React-pattern agents** (Reasoning + Acting loops)
- **Multi-agent systems** (Orchestrated agent teams)
- **Tool-augmented agents** (LinkedIn, Apollo, Clearbit, etc.)
- **Workflow automation** (Deterministic multi-step processes)
- **State management** (Context persistence across iterations)
- **Testing frameworks** (Unit, integration, E2E)

## Installation

```bash
# Install Google ADK SDK
pip install google-adk anthropic>=0.18.0

# Install this plugin
/plugin install jeremy-google-adk@jeremylongshore

# Verify installation
adk-agent --version
```

## Quick Start (5 Minutes)

### Create Your First Agent

```bash
# Generate a LinkedIn intelligence agent
adk-agent create \
  --name linkedin-intelligence \
  --pattern react \
  --llm claude-3-5-sonnet \
  --tools linkedin-scraper,profile-analyzer \
  --output ./my-agent/

# Navigate and run
cd my-agent/
pip install -r requirements.txt
python linkedin_intelligence.py
```

### Generated Structure

```
my-agent/
├── linkedin_intelligence.py    # Main agent implementation
├── tools/                      # Tool implementations
│   ├── linkedin_scraper.py
│   └── profile_analyzer.py
├── tests/                      # Test suite
│   └── test_agent.py
├── config/                     # Configuration
│   └── agent_config.yaml
├── requirements.txt            # Dependencies
├── Dockerfile                  # Container ready
└── README.md                   # Documentation
```

## Agent Patterns

### 1. React Pattern (Single Agent)

Best for: Autonomous agents that think and act iteratively

```python
from google_adk import ReactAgent, ToolRegistry
from anthropic import Anthropic
import os

class LinkedInIntelligenceAgent(ReactAgent):
    """
    Autonomous agent that researches LinkedIn profiles
    Uses React pattern: Thought -> Action -> Observation loop
    """

    def __init__(self):
        super().__init__()
        self.claude = Anthropic(api_key=os.getenv('CLAUDE_API_KEY'))
        self.model = "claude-3-5-sonnet-20241022"
        self.max_iterations = 10

        # Register tools
        self.tools = ToolRegistry([
            LinkedInScraperTool(),
            ProfileAnalyzerTool(),
            CompanyResearchTool(),
        ])

    async def run(self, profile_url: str) -> dict:
        """Execute React loop"""
        context = self.create_context(goal=f"Analyze {profile_url}")

        while not self.is_complete(context) and context.iterations < self.max_iterations:
            # Think: What should I do next?
            thought = await self.think(context)

            # Act: Execute the decided action
            observation = await self.act(thought)

            # Update: Store observation
            context.add_observation(observation)
            context.iterations += 1

        return self.synthesize_results(context)

    async def think(self, context):
        """Use Claude to reason about next action"""
        prompt = f"""You are analyzing a LinkedIn profile.

Goal: {context.goal}

Observations so far:
{self._format_observations(context.observations)}

Available tools: {', '.join(self.tools.list_tools())}

What should you do next? Respond with:
THOUGHT: [Your reasoning]
ACTION: [Tool to use]
PARAMS: [Tool parameters as JSON]
"""

        response = await self.claude.messages.create(
            model=self.model,
            max_tokens=1024,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )

        return self._parse_thought(response.content[0].text)
```

### 2. Multi-Agent System

Best for: Complex workflows requiring specialization

```python
from google_adk import MultiAgentOrchestrator, Agent

class SDRAgentTeam:
    """
    Orchestrated team of specialized agents for sales development
    """

    def __init__(self):
        self.orchestrator = MultiAgentOrchestrator()

        # Initialize specialized agents
        self.research_agent = ResearchAgent()
        self.qualification_agent = QualificationAgent()
        self.outreach_agent = OutreachAgent()
        self.followup_agent = FollowUpAgent()

        # Define workflow
        self.workflow = [
            ("research", self.research_agent),
            ("qualify", self.qualification_agent),
            ("outreach", self.outreach_agent),
            ("followup", self.followup_agent),
        ]

    async def process_leads(self, lead_list: list) -> dict:
        """Process leads through the SDR pipeline"""
        results = {
            "researched": [],
            "qualified": [],
            "contacted": [],
            "meetings_booked": []
        }

        for lead in lead_list:
            # Research phase
            research = await self.research_agent.run(lead)
            results["researched"].append(research)

            # Qualification phase
            if research["score"] > 0.7:
                qualified = await self.qualification_agent.run(research)
                results["qualified"].append(qualified)

                # Outreach phase
                if qualified["is_icp"]:
                    outreach = await self.outreach_agent.run(qualified)
                    results["contacted"].append(outreach)

                    # Follow-up phase
                    if outreach["response_received"]:
                        followup = await self.followup_agent.run(outreach)
                        if followup["meeting_booked"]:
                            results["meetings_booked"].append(followup)

        return results
```

### 3. Workflow Pattern

Best for: Deterministic, repeatable processes

```python
from google_adk import Workflow, Step

class DataEnrichmentWorkflow(Workflow):
    """
    Deterministic workflow for lead enrichment
    """

    def __init__(self):
        super().__init__()

        # Define workflow steps
        self.add_step(Step("validate", self.validate_input))
        self.add_step(Step("enrich_company", self.enrich_company_data))
        self.add_step(Step("enrich_person", self.enrich_person_data))
        self.add_step(Step("score", self.calculate_score))
        self.add_step(Step("route", self.route_to_team))

    async def validate_input(self, data):
        """Validate and clean input data"""
        # Implementation
        pass

    async def enrich_company_data(self, data):
        """Add company information from Clearbit/Apollo"""
        # Implementation
        pass

    async def enrich_person_data(self, data):
        """Add person information from LinkedIn/ContactOut"""
        # Implementation
        pass

    async def calculate_score(self, data):
        """Calculate lead score based on ICP criteria"""
        # Implementation
        pass

    async def route_to_team(self, data):
        """Route to appropriate sales team"""
        # Implementation
        pass
```

## Tool Development

### Creating Custom Tools

```python
from google_adk import Tool, ToolResult

class LinkedInScraperTool(Tool):
    """
    Tool for scraping LinkedIn profiles
    """

    name = "linkedin_scraper"
    description = "Scrapes public LinkedIn profile data"

    def __init__(self):
        super().__init__()
        self.rate_limit = 60  # requests per minute
        self.cache_ttl = 3600  # 1 hour cache

    @property
    def input_schema(self):
        return {
            "type": "object",
            "properties": {
                "profile_url": {
                    "type": "string",
                    "description": "LinkedIn profile URL"
                },
                "include_activity": {
                    "type": "boolean",
                    "description": "Include recent activity",
                    "default": False
                }
            },
            "required": ["profile_url"]
        }

    async def call(self, profile_url: str, include_activity: bool = False) -> ToolResult:
        """Execute the tool"""
        try:
            # Check cache first
            cached = self.get_from_cache(profile_url)
            if cached:
                return ToolResult(success=True, data=cached)

            # Scrape profile
            profile_data = await self._scrape_profile(profile_url)

            if include_activity:
                activity = await self._scrape_activity(profile_url)
                profile_data["recent_activity"] = activity

            # Cache result
            self.cache_result(profile_url, profile_data)

            return ToolResult(
                success=True,
                data=profile_data,
                metadata={"source": "linkedin", "cached": False}
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                metadata={"tool": self.name}
            )

    async def _scrape_profile(self, url: str) -> dict:
        """Actual scraping logic"""
        # Implementation using Selenium/Playwright
        pass
```

### Built-in Tools Library

```python
# Available tools out of the box
from google_adk.tools import (
    # Web & Search
    WebSearchTool,           # Google search
    WebScraperTool,         # Generic web scraping

    # Sales & Marketing
    LinkedInTool,           # LinkedIn profiles/companies
    ApolloTool,            # Apollo.io enrichment
    ClearbitTool,          # Clearbit enrichment
    HunterTool,            # Email finder

    # Communication
    EmailTool,             # Send emails via SMTP/SendGrid
    SlackTool,             # Slack messaging
    CalendlyTool,          # Schedule meetings

    # Data & Analytics
    GoogleSheetsTool,      # Read/write sheets
    BigQueryTool,          # Query BigQuery

    # AI & Processing
    ClaudeTool,            # Claude API wrapper
    VertexAITool,          # Vertex AI integration

    # Utilities
    CalculatorTool,        # Math operations
    DateTimeTool,          # Date/time operations
    JSONTool,              # JSON parsing/manipulation
)
```

## Claude Integration

### Basic Claude Setup

```python
from anthropic import Anthropic
from google_adk import ClaudeIntegration

class ClaudePoweredAgent:
    def __init__(self):
        self.claude = ClaudeIntegration(
            api_key=os.getenv('CLAUDE_API_KEY'),
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            temperature=0.3
        )

    async def process(self, input_text: str) -> str:
        """Process input using Claude"""
        response = await self.claude.complete(
            prompt=self.build_prompt(input_text),
            system="You are a helpful AI agent."
        )
        return response
```

### Tool Calling with Claude

```python
# Define tools for Claude
tools = [
    {
        "name": "search_linkedin",
        "description": "Search LinkedIn for profiles",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "filters": {"type": "object"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "analyze_profile",
        "description": "Analyze a LinkedIn profile",
        "input_schema": {
            "type": "object",
            "properties": {
                "profile_url": {"type": "string"}
            },
            "required": ["profile_url"]
        }
    }
]

# Use tools in conversation
response = await self.claude.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=4096,
    tools=tools,
    messages=[
        {
            "role": "user",
            "content": "Find and analyze the LinkedIn profile of the CEO of OpenAI"
        }
    ]
)

# Process tool calls
if response.stop_reason == "tool_use":
    for tool_use in response.content:
        if tool_use.type == "tool_use":
            result = await self.execute_tool(
                tool_use.name,
                tool_use.input
            )
            # Continue conversation with result
```

## Configuration

### Agent Configuration (agent_config.yaml)

```yaml
agent:
  name: linkedin-intelligence-agent
  version: 1.0.0
  description: Analyzes LinkedIn profiles for sales intelligence

llm:
  provider: anthropic
  model: claude-3-5-sonnet-20241022
  max_tokens: 4096
  temperature: 0.3

tools:
  - name: linkedin_scraper
    enabled: true
    rate_limit: 60
    cache_ttl: 3600

  - name: clearbit_enrichment
    enabled: true
    api_key: ${CLEARBIT_API_KEY}

  - name: email_finder
    enabled: true
    provider: hunter

behavior:
  max_iterations: 10
  timeout_seconds: 300
  retry_on_error: true
  max_retries: 3

observability:
  logging:
    level: INFO
    format: json
    destination: stdout

  metrics:
    enabled: true
    provider: prometheus
    port: 9090

  tracing:
    enabled: true
    provider: opentelemetry
    endpoint: http://localhost:4317
```

### Environment Variables

```bash
# Claude API
CLAUDE_API_KEY=sk-ant-your-key-here
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# Google Cloud
GOOGLE_PROJECT_ID=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# Third-party APIs
CLEARBIT_API_KEY=your-clearbit-key
APOLLO_API_KEY=your-apollo-key
HUNTER_API_KEY=your-hunter-key

# Observability
ENABLE_METRICS=true
METRICS_PORT=9090
LOG_LEVEL=INFO
```

## Testing

### Unit Tests

```python
import pytest
from unittest.mock import Mock, patch
from linkedin_intelligence import LinkedInIntelligenceAgent

@pytest.fixture
def agent():
    """Create test agent instance"""
    return LinkedInIntelligenceAgent()

@pytest.mark.asyncio
async def test_agent_initialization(agent):
    """Test agent initializes correctly"""
    assert agent.model == "claude-3-5-sonnet-20241022"
    assert agent.max_iterations == 10
    assert len(agent.tools.list_tools()) > 0

@pytest.mark.asyncio
async def test_think_generates_valid_thought(agent):
    """Test thinking process generates valid action"""
    context = agent.create_context(goal="Test goal")

    with patch.object(agent.claude, 'messages') as mock_claude:
        mock_claude.create.return_value.content = [
            Mock(text="THOUGHT: Need to scrape\nACTION: linkedin_scraper\nPARAMS: {}")
        ]

        thought = await agent.think(context)

        assert thought["action"] == "linkedin_scraper"
        assert "thought" in thought
        assert "params" in thought

@pytest.mark.asyncio
async def test_complete_workflow(agent):
    """Test complete agent workflow"""
    profile_url = "https://linkedin.com/in/test"

    with patch.object(agent, 'tools') as mock_tools:
        mock_tools.execute.return_value = {
            "name": "Test User",
            "title": "CEO",
            "company": "Test Corp"
        }

        result = await agent.run(profile_url)

        assert result["success"] == True
        assert "observations" in result
        assert result["iterations"] > 0
```

### Integration Tests

```python
@pytest.mark.integration
class TestMultiAgentSystem:
    @pytest.mark.asyncio
    async def test_sdr_team_processes_leads(self):
        """Test SDR team processes leads correctly"""
        team = SDRAgentTeam()

        test_leads = [
            {"name": "John Doe", "company": "Tech Corp"},
            {"name": "Jane Smith", "company": "Sales Inc"}
        ]

        results = await team.process_leads(test_leads)

        assert len(results["researched"]) == 2
        assert len(results["qualified"]) > 0
        assert "meetings_booked" in results

    @pytest.mark.asyncio
    async def test_agent_coordination(self):
        """Test agents coordinate properly"""
        team = SDRAgentTeam()

        # Test research agent passes data to qualification
        research_output = await team.research_agent.run({"name": "Test"})
        qualification_input = await team.qualification_agent.validate_input(research_output)

        assert qualification_input is not None
```

### End-to-End Tests

```python
@pytest.mark.e2e
@pytest.mark.skipif(not os.getenv('CLAUDE_API_KEY'), reason="No API key")
class TestRealAgentExecution:
    @pytest.mark.asyncio
    async def test_real_linkedin_analysis(self):
        """Test real LinkedIn profile analysis"""
        agent = LinkedInIntelligenceAgent()

        # Use a public profile for testing
        result = await agent.run("https://linkedin.com/in/jeffweiner08")

        assert result["success"] == True
        assert "name" in result["data"]
        assert "company" in result["data"]
        assert result["data"]["name"] == "Jeff Weiner"
```

## Deployment

### Container Deployment

```dockerfile
# Multi-stage build for agent
FROM python:3.11-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim
RUN useradd -m -u 1000 agent

WORKDIR /app
COPY --from=builder /root/.local {baseDir}
COPY --chown=agent:agent . .

USER agent
ENV PATH={baseDir}

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8080/health || exit 1

CMD ["python", "-m", "agent.main"]
```

### Cloud Run Deployment

```bash
# Build and push container
docker build -t gcr.io/my-project/linkedin-agent:latest .
docker push gcr.io/my-project/linkedin-agent:latest

# Deploy to Cloud Run
gcloud run deploy linkedin-agent \
  --image gcr.io/my-project/linkedin-agent:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="CLAUDE_API_KEY=${CLAUDE_API_KEY}"
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: linkedin-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: linkedin-agent
  template:
    metadata:
      labels:
        app: linkedin-agent
    spec:
      containers:
      - name: agent
        image: gcr.io/my-project/linkedin-agent:latest
        ports:
        - containerPort: 8080
        env:
        - name: CLAUDE_API_KEY
          valueFrom:
            secretKeyRef:
              name: agent-secrets
              key: claude-api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1"
```

## Best Practices

### 1. Agent Design

- **Single Responsibility**: Each agent should have one clear purpose
- **Stateless**: Agents should be stateless; use external storage for state
- **Idempotent**: Operations should be safe to retry
- **Timeout**: Always set timeouts for agent operations
- **Rate Limiting**: Respect API rate limits

### 2. Error Handling

```python
class RobustAgent:
    async def run_with_retry(self, input_data):
        """Run with exponential backoff retry"""
        max_retries = 3
        base_delay = 1

        for attempt in range(max_retries):
            try:
                return await self.run(input_data)
            except RateLimitError as e:
                wait_time = base_delay * (2 ** attempt)
                logger.warning(f"Rate limited, waiting {wait_time}s")
                await asyncio.sleep(wait_time)
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise
```

### 3. Observability

```python
from prometheus_client import Counter, Histogram
import structlog

# Metrics
agent_runs = Counter('agent_runs_total', 'Total agent runs')
agent_duration = Histogram('agent_duration_seconds', 'Agent run duration')

# Structured logging
logger = structlog.get_logger()

class ObservableAgent:
    @agent_duration.time()
    async def run(self, input_data):
        """Run with observability"""
        agent_runs.inc()

        logger.info(
            "agent_started",
            agent_name=self.__class__.__name__,
            input_size=len(str(input_data))
        )

        try:
            result = await self._execute(input_data)
            logger.info(
                "agent_completed",
                success=True,
                result_size=len(str(result))
            )
            return result
        except Exception as e:
            logger.error(
                "agent_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            raise
```

### 4. Security

- **API Key Management**: Use Secret Manager, never hardcode
- **Input Validation**: Always validate and sanitize inputs
- **Rate Limiting**: Implement rate limiting for public endpoints
- **Authentication**: Use proper authentication for agent APIs
- **Least Privilege**: Grant minimal necessary permissions

## Performance Tuning

### Optimization Strategies

```python
class OptimizedAgent:
    def __init__(self):
        # Connection pooling
        self.session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=100)
        )

        # Caching
        self.cache = TTLCache(maxsize=1000, ttl=3600)

        # Batch processing
        self.batch_size = 10
        self.queue = asyncio.Queue(maxsize=100)

    async def process_batch(self, items):
        """Process items in batches for efficiency"""
        tasks = []
        for batch in self.chunk(items, self.batch_size):
            tasks.append(self.process_chunk(batch))

        results = await asyncio.gather(*tasks)
        return self.flatten(results)

    @lru_cache(maxsize=128)
    def expensive_computation(self, input_data):
        """Cache expensive computations"""
        # Computation logic
        pass
```

### Resource Management

```yaml
# Resource limits for Kubernetes
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "1Gi"
    cpu: "1"

# Autoscaling
autoscaling:
  minReplicas: 1
  maxReplicas: 10
  targetCPU: 70
  targetMemory: 80
```

## Integration Examples

### With Docker Plugin

```bash
# Generate agent
adk-agent create --name my-agent --output ./my-agent/

# Containerize with Docker plugin
docker-agent create \
  --name my-agent \
  --base-image python:3.11-slim \
  --source ./my-agent/
```

### With Terraform Plugin

```bash
# Generate infrastructure
terraform-gcp create \
  --name my-agent \
  --deploy-target cloud-run \
  --source ./my-agent/
```

### With CI/CD

```yaml
# GitHub Actions workflow
name: Deploy Agent
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Agent
        run: |
          adk-agent build --name my-agent

      - name: Run Tests
        run: |
          pytest tests/ --cov=agent --cov-report=xml

      - name: Build Container
        run: |
          docker build -t gcr.io/${{ secrets.GCP_PROJECT }}/my-agent:${{ github.sha }} .

      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy my-agent \
            --image gcr.io/${{ secrets.GCP_PROJECT }}/my-agent:${{ github.sha }} \
            --region us-central1
```

## Troubleshooting

### Common Issues

#### Agent Not Responding
```bash
# Check logs
kubectl logs -f deployment/my-agent

# Check health
curl http://agent-service:8080/health

# Debug mode
AGENT_DEBUG=true python agent.py
```

#### High Latency
- Check Claude API response times
- Review tool execution times
- Enable caching for repeated operations
- Use batch processing where possible

#### Memory Issues
```python
# Memory profiling
from memory_profiler import profile

@profile
def memory_intensive_function():
    # Your code
    pass

# Garbage collection tuning
import gc
gc.set_threshold(700, 10, 10)
```

## Cost Optimization

### Claude API Costs

```python
class CostOptimizedAgent:
    def __init__(self):
        # Use smaller model for simple tasks
        self.models = {
            "simple": "claude-3-haiku-20240307",  # Cheapest
            "standard": "claude-3-5-sonnet-20241022",  # Balanced
            "complex": "claude-3-5-opus-20241022"  # Most capable
        }

    def select_model(self, task_complexity):
        """Select appropriate model based on task"""
        if task_complexity < 0.3:
            return self.models["simple"]
        elif task_complexity < 0.7:
            return self.models["standard"]
        else:
            return self.models["complex"]
```

### Resource Optimization

- Use Cloud Run with scale-to-zero for development
- Implement request batching to reduce API calls
- Cache frequently accessed data
- Use preemptible VMs for batch processing

## Examples Repository

Complete examples available at: `/examples/`

- `simple-react-agent/` - Basic React pattern agent
- `sdr-team/` - Multi-agent SDR team
- `enrichment-workflow/` - Data enrichment pipeline
- `real-time-agent/` - WebSocket-based real-time agent
- `batch-processor/` - High-volume batch processing

## Support

- GitHub Issues: https://github.com/jeremylongshore/jeremy-google-adk/issues
- Documentation: https://claudecodeplugins.io/plugins/jeremy-google-adk
- Community: Discord/Slack channel

---

**Version:** 1.0.0
**Last Updated:** October 2025
**Author:** Jeremy Longshore
**License:** MIT