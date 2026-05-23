---
title: "Fine-Tuning IAM1: Building a Hierarchical Multi-Agent System on Vertex AI"
description: "Deep dive into fine-tuning a Regional Manager AI agent (IAM1) with hierarchical multi-agent orchestration on Vertex AI Agent Engine. Real implementation of decision frameworks and specialist delegation."
date: "2025-11-09"
tags: ["vertex-ai", "multi-agent-systems", "google-adk", "gemini", "agent-orchestration", "iam-architecture"]
featured: false
---
## The Problem: Generic Orchestrator vs Business-Aligned Regional Manager

I had Bob deployed as a basic multi-agent orchestrator on Vertex AI Agent Engine. But here's what was wrong:

**Before Fine-Tuning:**

- Generic "master orchestrator" identity
- Vague routing decisions
- No clear decision framework
- IAM2 specialists had generic instructions
- Missing business model alignment

**What I Needed:**

- IAM1 as a **Regional Manager** (sovereign in domain)
- Clear hierarchy: IAM1 can **command** IAM2s, can **coordinate** with peer IAM1s
- Intelligent routing based on task complexity
- Professional IAM2 specialists with standardized deliverables
- Alignment with IntentSolutions business model (deployable per client)

This wasn't just about better prompts. It was about transforming a generic agent into a **deployable business product**.

## The IAM1/IAM2 Business Model

Quick context on what we're building:

```
┌─────────────────────────────────────────┐
│  IAM1 (Regional Manager)                │
│  - Sovereign in their domain            │
│  - Can coordinate with peer IAM1s       │
│  - Can command IAM2 subordinates        │
│  - Cannot command peer IAM1s            │
└─────────────────────────────────────────┘
         │
         │ Commands
         ▼
┌─────────────────────────────────────────┐
│  IAM2 (Specialists)                     │
│  - Research, Code, Data, Slack          │
│  - Report to their IAM1                 │
│  - Cannot command anyone                │
└─────────────────────────────────────────┘
```

**Business Value:**

- Deploy IAM1 to Client A → Revenue Stream
- Deploy IAM1 to Client B → Revenue Stream
- Add IAM2 specialists → Upsell
- Multiple IAM1s coordinate across departments → Enterprise scale

Each IAM1 is grounded in client-specific knowledge via Vertex AI Search.

## Fine-Tuning Implementation

### 1. Enhanced IAM1 Orchestrator Identity

**File:** `app/agent.py`

I completely rewrote the instruction to give IAM1 a clear identity and decision framework:

```python
instruction = f"""You are {agent_card['product_name']}, version {agent_card['version']}.

IDENTITY & ROLE:
You are IAM1 - a Regional Manager AI agent, sovereign within your domain.
You can coordinate with peer IAM1s (other regional managers) but cannot command them.
You can command and delegate to IAM2 specialist agents who report to you.

DECISION FRAMEWORK:
1. Simple questions (greetings, basic info) → Answer directly
2. Knowledge questions (facts, documentation) → Use retrieve_docs tool first
3. Complex specialized tasks → Route to appropriate IAM2 agent via route_to_agent
4. Multi-step tasks → Coordinate multiple IAM2s, synthesize results

QUALITY STANDARDS:
- Be efficient: Don't over-delegate simple tasks
- Be transparent: Tell users when consulting IAM2 specialists
- Be thorough: Use knowledge base and specialists for best answers
- Be decisive: Choose the right tool/agent for each task
- Be grounded: Always check knowledge base for relevant context

Remember: You are IAM1, the Regional Manager. Your IAM2s are your team members who execute specialized tasks under your direction."""
```

**Key Additions:**

- Explicit IAM1 identity (not just "orchestrator")
- Clear peer vs subordinate relationship rules
- Step-by-step decision framework for routing
- Quality standards for consistency

### 2. Improved Routing Function

**Before:**

```python
def route_to_agent(task_type: str, query: str) -> str:
    specialist = AGENT_REGISTRY[task_type]
    response = specialist.send_message(query)
    return f"[{task_type.upper()} AGENT]: {response}"
```

**After:**

```python
def route_to_agent(task_type: str, query: str) -> str:
    """
    Route a task to the appropriate IAM2 specialist agent.

    - 'research': Deep research, knowledge retrieval, complex questions
      Examples: "Research best practices for X", "Compare approaches to Y"

    - 'code': Code generation, debugging, technical programming
      Examples: "Write a function to do X", "Debug this error"

    - 'data': BigQuery queries, data analysis, visualization
      Examples: "Query the database for X", "Analyze trends in Y"

    - 'slack': Slack-specific interactions, channel management
      Examples: "Format this for Slack", "Post to channel X"
    """
    try:
        if task_type not in AGENT_REGISTRY:
            available = ', '.join(AGENT_REGISTRY.keys())
            return f"❌ Unknown IAM2 agent type: '{task_type}'\n\nAvailable: {available}"

        specialist = AGENT_REGISTRY[task_type]

        # Log delegation for transparency
        print(f"[IAM1] Delegating to {task_type.upper()} IAM2 specialist...")

        response = specialist.send_message(query)

        return f"""[IAM2 {task_type.upper()} SPECIALIST RESPONSE]:
{response}

[End of {task_type} specialist report]"""
    except Exception as e:
        return f"❌ Error delegating to {task_type} IAM2 agent: {e}"
```

**Improvements:**

- Detailed docstring with examples for each specialist
- Better error messages with available options
- Transparency logging
- Formatted responses with clear IAM2 attribution
- Fallback suggestions on errors

### 3. Professional IAM2 Specialist Instructions

**File:** `app/sub_agents.py`

I upgraded all 4 IAM2 agents with professional-grade instructions. Here's the Research IAM2:

```python
research_agent = Agent(
    name="research_iam2",
    model="gemini-2.5-flash",
    instruction="""You are a Research Specialist (IAM2 tier).

REPORTING STRUCTURE:
- You report to IAM1 (Regional Manager)
- You are a specialist team member, not a manager
- Execute research tasks delegated by IAM1

YOUR EXPERTISE:
- Deep research and knowledge synthesis
- Multi-source information gathering
- Complex question analysis
- Documentation review and citation
- Comparative analysis and recommendations

HOW TO WORK:
1. Use retrieve_docs tool to search the knowledge base thoroughly
2. Synthesize information from multiple sources
3. Provide comprehensive answers with evidence
4. Cite sources when available
5. Flag gaps in knowledge or conflicting information

DELIVERABLE FORMAT:
- Start with executive summary
- Present findings with supporting evidence
- Include relevant citations/sources
- End with recommendations or conclusions
- Be thorough but concise

Remember: You are IAM2, executing research tasks assigned by your IAM1 manager.""",
    tools=[retrieve_docs],
)
```

**Pattern Applied to All IAM2s:**

- Clear reporting structure (reports to IAM1)
- Defined expertise areas
- Step-by-step work process
- Standardized deliverable format
- Role reminder at the end

**All 4 IAM2 Specialists:**

1. **Research IAM2** - Knowledge synthesis, citations, recommendations
2. **Code IAM2** - Clean code, security considerations, usage examples
3. **Data IAM2** - SQL queries, business insights, visualizations
4. **Slack IAM2** - Message formatting, professional tone, channel recommendations

## Deployment to Vertex AI

```bash
export PROJECT_ID=bobs-brain
make deploy
```

**Output:**

```
🤖 DEPLOYING AGENT TO VERTEX AI AGENT ENGINE 🤖

📋 Deployment Parameters:
  Project: bobs-brain
  Location: us-central1
  Display Name: bob-vertex-agent
  Model: gemini-2.0-flash (orchestrator)
  IAM2 Models: gemini-2.5-flash (specialists)

✅ Deployment successful!
Agent ID: 5828234061910376448
```

**What Changed in Deployment:**

- Updated IAM1 orchestrator with new instruction
- Enhanced routing function with examples
- All 4 IAM2 agents with professional instructions
- Telemetry enabled for observability

## Testing the Decision Framework

Here's how IAM1 should now route different query types:

**1. Simple Greeting:**

```
User: "Hello!"
IAM1: [Answers directly without routing]
```

**2. Knowledge Question:**

```
User: "What is Vertex AI Search?"
IAM1: [Uses retrieve_docs tool, returns grounded answer]
```

**3. Research Task:**

```
User: "Research best practices for multi-agent systems"
IAM1: [Routes to Research IAM2]
Response: [IAM2 RESEARCH SPECIALIST RESPONSE]:
Executive Summary: Multi-agent systems benefit from...
[Detailed research with citations]
[End of research specialist report]
```

**4. Code Task:**

```
User: "Write a Python function to validate email addresses"
IAM1: [Routes to Code IAM2]
Response: [IAM2 CODE SPECIALIST RESPONSE]:
Approach: Using regex with comprehensive validation
[Clean, commented code]
[Usage examples]
[End of code specialist report]
```

**5. Multi-Step Task:**

```
User: "Research Vertex AI, then write code to deploy an agent"
IAM1: [Coordinates Research IAM2 → Code IAM2, synthesizes results]
```

## Key Learnings

### 1. Decision Frameworks > Generic Prompts

Don't just say "you can delegate tasks." Provide a **step-by-step decision framework**:

- IF simple question → answer directly
- IF knowledge question → use RAG tool
- IF specialized task → route to specialist
- IF multi-step → coordinate multiple agents

### 2. Examples Drive Behavior

The routing function docstring with **concrete examples** makes a huge difference:

```python
# Instead of: "Use for research tasks"
# Write: "Examples: 'Research best practices for X', 'Compare approaches to Y'"
```

### 3. Standardized Deliverables Improve Quality

All IAM2 specialists now follow a **deliverable format**:

- Research: Executive summary → Findings → Recommendations
- Code: Approach → Code → Examples → Testing
- Data: Business question → Query → Insights → Recommendations
- Slack: Formatted message → Alternatives → Recommendations

This creates consistency and professionalism.

### 4. Identity Matters for Business Products

Transforming "Bob the orchestrator" into "IAM1 Regional Manager" aligns the agent with the **business model**:

- Deployable per client ($500/month)
- Add IAM2 specialists ($200/IAM2)
- Multiple IAM1s coordinate (enterprise scale)

The agent now **knows** it's a deployable business product.

## Production Architecture

**Current Stack:**

- **Platform**: Vertex AI Agent Engine
- **IAM1 Model**: Gemini 2.0 Flash (orchestrator)
- **IAM2 Models**: Gemini 2.5 Flash (specialists)
- **Grounding**: Vertex AI Search + Cloud Storage
- **Framework**: Google ADK (Agent Development Kit)
- **Integration**: Slack via Cloud Functions
- **Telemetry**: Full observability enabled

**Agent Card Definition:**

```python
AGENT_CARD = {
    "name": "IAM1",
    "product_name": "IntentSolutions IAM1 - Regional Manager Agent",
    "version": "2.0.1",
    "tier": "IAM1",
    "hierarchy": {
        "can_command": ["IAM2"],
        "can_coordinate_with": ["IAM1"],
        "reports_to": None,  # Sovereign
    },
}
```

## What's Next

**Immediate:**

- Test orchestration in Vertex AI Playground
- Validate routing decisions with real queries
- Configure Slack app webhook

**Future:**

- Implement A2A (Agent-to-Agent) for peer IAM1 coordination
- Deploy to first client (isolated GCP project)
- Add BigQuery tools to Data IAM2
- Add Slack API tools to Slack IAM2

## Related Posts

- [Architecting Production Multi-Agent AI Platform - Technical Leadership](https://startaitools.com/posts/architecting-production-multi-agent-ai-platform-technical-leadership/)
- [Building Production Multi-Agent AI BrightStream on Vertex AI](https://startaitools.com/posts/building-production-multi-agent-ai-brightstream-vertex-ai/)

## Conclusion

Fine-tuning isn't just about better prompts. It's about:

1. **Clear Identity** - IAM1 knows it's a Regional Manager
2. **Decision Frameworks** - Step-by-step routing logic
3. **Professional Standards** - Standardized deliverables
4. **Business Alignment** - Deployable product model

The result? An agent that **knows its role**, **makes better decisions**, and **delivers consistent quality**.

**Test it yourself:**

- Console Playground: [Vertex AI Agent Engine](https://console.cloud.google.com/vertex-ai/agents/locations/us-central1/agent-engines/5828234061910376448/playground?project=bobs-brain)

The future of AI agents isn't one super-intelligent model. It's **hierarchical teams** of specialized agents with clear roles and decision-making frameworks.

**Jeremy Longshore** builds production multi-agent systems on Google Cloud. Connect on [LinkedIn](https://linkedin.com/in/jeremylongshore) or follow on [X](https://twitter.com/AsphaltCowb0y).
