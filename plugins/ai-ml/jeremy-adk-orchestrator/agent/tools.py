# Copyright 2025 Jeremy Longshore
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

"""Tools for ADK Orchestrator Agent - A2A protocol and coordination functions"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import httpx
from pydantic import BaseModel, Field


# Pydantic models for structured data
class AgentCard(BaseModel):
    """Agent Card for A2A protocol discovery"""
    name: str
    description: str
    url: str
    version: str = "1.0.0"
    capabilities: Dict[str, Any] = Field(default_factory=dict)
    skills: List[Dict[str, Any]] = Field(default_factory=list)
    input_modes: List[str] = Field(default_factory=lambda: ["text/plain"])
    output_modes: List[str] = Field(default_factory=lambda: ["text/plain"])


class AgentInvocation(BaseModel):
    """Request structure for agent invocation"""
    agent_name: str
    input_data: Dict[str, Any]
    timeout_seconds: int = 30
    session_id: Optional[str] = None
    auth_token: Optional[str] = None


class WorkflowConfig(BaseModel):
    """Configuration for multi-agent workflows"""
    pattern: str  # "sequential", "parallel", "loop"
    agents: List[str]
    max_iterations: int = 10
    timeout_seconds: int = 300
    error_strategy: str = "fail_fast"  # or "continue_on_error"


# Tool Functions

async def discover_agents(
    registry_url: Optional[str] = None,
    filter_capabilities: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Discovers available agents via A2A protocol.

    Args:
        registry_url: Optional registry endpoint (defaults to Vertex AI Engine registry)
        filter_capabilities: Optional list of required capabilities

    Returns:
        Dictionary containing discovered agents and their cards
    """
    try:
        # Default to Vertex AI Engine agent registry
        if not registry_url:
            registry_url = "https://agent-engine.googleapis.com/v1/agents"

        discovered_agents = []

        # In production, this would make actual HTTP requests
        # For now, return example structure
        async with httpx.AsyncClient() as client:
            # Discover agents from registry
            # response = await client.get(registry_url)
            # agents = response.json()

            # Example agents (would come from actual discovery)
            example_agents = [
                {
                    "name": "data-analyst",
                    "description": "Analyzes data and generates insights",
                    "url": "https://agent-engine.googleapis.com/v1/agents/data-analyst",
                    "capabilities": ["sql", "visualization", "statistics"],
                },
                {
                    "name": "code-generator",
                    "description": "Generates code in multiple languages",
                    "url": "https://agent-engine.googleapis.com/v1/agents/code-generator",
                    "capabilities": ["python", "javascript", "sql"],
                }
            ]

            # Filter by capabilities if specified
            for agent in example_agents:
                if filter_capabilities:
                    if any(cap in agent.get("capabilities", []) for cap in filter_capabilities):
                        discovered_agents.append(agent)
                else:
                    discovered_agents.append(agent)

        return {
            "status": "success",
            "discovered_count": len(discovered_agents),
            "agents": discovered_agents,
            "registry": registry_url,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "discovered_count": 0,
            "agents": []
        }


async def invoke_agent(
    invocation: AgentInvocation,
    retry_count: int = 3
) -> Dict[str, Any]:
    """Invokes a specific agent via A2A protocol.

    Args:
        invocation: Agent invocation configuration
        retry_count: Number of retry attempts

    Returns:
        Agent response including results and metadata
    """
    try:
        # Construct A2A request
        a2a_request = {
            "jsonrpc": "2.0",
            "method": "agent.invoke",
            "params": {
                "input": invocation.input_data,
                "session_id": invocation.session_id
            },
            "id": f"req-{datetime.utcnow().timestamp()}"
        }

        # In production, make actual A2A protocol request
        async with httpx.AsyncClient() as client:
            # response = await client.post(
            #     f"{agent_url}/a2a",
            #     json=a2a_request,
            #     timeout=invocation.timeout_seconds,
            #     headers={"Authorization": f"Bearer {invocation.auth_token}"}
            # )

            # Example response
            response_data = {
                "jsonrpc": "2.0",
                "result": {
                    "output": f"Processed request for {invocation.agent_name}",
                    "metadata": {
                        "processing_time_ms": 1234,
                        "tokens_used": 567
                    }
                },
                "id": a2a_request["id"]
            }

        return {
            "status": "success",
            "agent": invocation.agent_name,
            "result": response_data["result"],
            "session_id": invocation.session_id,
            "timestamp": datetime.utcnow().isoformat()
        }

    except asyncio.TimeoutError:
        return {
            "status": "timeout",
            "agent": invocation.agent_name,
            "error": f"Agent invocation timed out after {invocation.timeout_seconds}s",
            "session_id": invocation.session_id
        }
    except Exception as e:
        return {
            "status": "error",
            "agent": invocation.agent_name,
            "error": str(e),
            "session_id": invocation.session_id
        }


async def manage_agent_session(
    action: str,  # "create", "get", "update", "delete"
    session_id: Optional[str] = None,
    session_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Manages agent sessions for stateful interactions.

    Args:
        action: Session action to perform
        session_id: Session identifier
        session_data: Session data to store/update

    Returns:
        Session information and status
    """
    try:
        if action == "create":
            # Create new session
            new_session_id = f"session-{datetime.utcnow().timestamp()}"
            return {
                "status": "success",
                "action": "created",
                "session_id": new_session_id,
                "created_at": datetime.utcnow().isoformat()
            }

        elif action == "get":
            # Retrieve session
            return {
                "status": "success",
                "action": "retrieved",
                "session_id": session_id,
                "data": session_data or {},
                "retrieved_at": datetime.utcnow().isoformat()
            }

        elif action == "update":
            # Update session
            return {
                "status": "success",
                "action": "updated",
                "session_id": session_id,
                "updated_at": datetime.utcnow().isoformat()
            }

        elif action == "delete":
            # Delete session
            return {
                "status": "success",
                "action": "deleted",
                "session_id": session_id,
                "deleted_at": datetime.utcnow().isoformat()
            }

        else:
            return {
                "status": "error",
                "error": f"Unknown action: {action}"
            }

    except Exception as e:
        return {
            "status": "error",
            "action": action,
            "error": str(e)
        }


async def validate_agent_card(
    agent_url: str,
    strict_mode: bool = True
) -> Dict[str, Any]:
    """Validates an agent's card against A2A specification.

    Args:
        agent_url: URL to fetch agent card
        strict_mode: Whether to enforce strict validation

    Returns:
        Validation results and agent card if valid
    """
    try:
        async with httpx.AsyncClient() as client:
            # Fetch agent card
            # response = await client.get(f"{agent_url}/agent-card")
            # card_data = response.json()

            # Example validation
            card_data = {
                "name": "example-agent",
                "description": "An example agent",
                "url": agent_url,
                "version": "1.0.0",
                "capabilities": {"nlp": True, "code": True}
            }

            # Validate using Pydantic
            card = AgentCard(**card_data)

            return {
                "status": "valid",
                "agent_card": card.model_dump(),
                "validation_mode": "strict" if strict_mode else "lenient",
                "validated_at": datetime.utcnow().isoformat()
            }

    except Exception as e:
        return {
            "status": "invalid",
            "error": str(e),
            "agent_url": agent_url
        }


async def deploy_to_vertex_engine(
    agent_name: str,
    project_id: str,
    location: str = "us-central1",
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Deploys an agent to Vertex AI Engine.

    Args:
        agent_name: Name of agent to deploy
        project_id: GCP project ID
        location: Deployment location
        config: Deployment configuration

    Returns:
        Deployment status and endpoint information
    """
    try:
        deployment_config = config or {
            "machine_type": "n1-standard-4",
            "replica_count": 2,
            "auto_scaling": True
        }

        # In production, use Vertex AI SDK
        # from google.cloud import aiplatform
        # aiplatform.init(project=project_id, location=location)
        # endpoint = aiplatform.Endpoint.create(...)

        return {
            "status": "deployed",
            "agent": agent_name,
            "project": project_id,
            "location": location,
            "endpoint": f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/endpoints/{agent_name}",
            "config": deployment_config,
            "deployed_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        return {
            "status": "deployment_failed",
            "agent": agent_name,
            "error": str(e)
        }


async def monitor_agent_health(
    agent_names: List[str],
    include_metrics: bool = True
) -> Dict[str, Any]:
    """Monitors health and metrics for deployed agents.

    Args:
        agent_names: List of agents to monitor
        include_metrics: Whether to include detailed metrics

    Returns:
        Health status and metrics for each agent
    """
    try:
        health_results = {}

        for agent_name in agent_names:
            # In production, query actual health endpoints
            health_results[agent_name] = {
                "status": "healthy",
                "availability": 99.95,
                "response_time_ms": 234,
                "error_rate": 0.001
            }

            if include_metrics:
                health_results[agent_name]["metrics"] = {
                    "requests_per_minute": 120,
                    "tokens_per_request": 450,
                    "cache_hit_rate": 0.85,
                    "memory_usage_mb": 512
                }

        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "agents": health_results,
            "summary": {
                "total_agents": len(agent_names),
                "healthy": len([h for h in health_results.values() if h["status"] == "healthy"]),
                "unhealthy": len([h for h in health_results.values() if h["status"] != "healthy"])
            }
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


async def create_agent_team(
    team_name: str,
    agent_roles: Dict[str, str],
    coordination_rules: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Creates a team of agents for collaborative tasks.

    Args:
        team_name: Name for the agent team
        agent_roles: Mapping of agents to their roles
        coordination_rules: Rules for agent coordination

    Returns:
        Team configuration and status
    """
    try:
        team_config = {
            "name": team_name,
            "agents": agent_roles,
            "coordination": coordination_rules or {
                "decision_maker": list(agent_roles.keys())[0] if agent_roles else None,
                "voting_enabled": False,
                "consensus_required": False
            },
            "created_at": datetime.utcnow().isoformat()
        }

        return {
            "status": "created",
            "team": team_config,
            "agent_count": len(agent_roles)
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


async def coordinate_workflow(
    workflow: WorkflowConfig,
    input_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Coordinates multi-agent workflow execution.

    Args:
        workflow: Workflow configuration
        input_data: Input data for the workflow

    Returns:
        Workflow execution results
    """
    try:
        results = []

        if workflow.pattern == "sequential":
            # Execute agents in sequence
            current_input = input_data
            for agent in workflow.agents:
                invocation = AgentInvocation(
                    agent_name=agent,
                    input_data=current_input
                )
                result = await invoke_agent(invocation)
                results.append(result)
                # Pass output to next agent
                if result["status"] == "success":
                    current_input = result.get("result", {}).get("output", current_input)
                elif workflow.error_strategy == "fail_fast":
                    break

        elif workflow.pattern == "parallel":
            # Execute agents in parallel
            tasks = [
                invoke_agent(AgentInvocation(agent_name=agent, input_data=input_data))
                for agent in workflow.agents
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        elif workflow.pattern == "loop":
            # Execute agents in a loop
            iteration = 0
            current_input = input_data
            while iteration < workflow.max_iterations:
                for agent in workflow.agents:
                    invocation = AgentInvocation(
                        agent_name=agent,
                        input_data=current_input
                    )
                    result = await invoke_agent(invocation)
                    results.append(result)

                    # Check loop condition (simplified)
                    if result.get("result", {}).get("complete", False):
                        iteration = workflow.max_iterations
                        break
                iteration += 1

        return {
            "status": "completed",
            "pattern": workflow.pattern,
            "results": results,
            "agents_invoked": workflow.agents,
            "execution_time_ms": 5678,  # Would be actual timing
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        return {
            "status": "error",
            "pattern": workflow.pattern,
            "error": str(e)
        }