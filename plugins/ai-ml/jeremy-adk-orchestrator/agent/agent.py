# Copyright 2025 Jeremy Longshore
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""ADK Orchestrator Agent - Production-ready A2A protocol manager for Vertex AI Engine"""

from typing import Optional, List, Dict, Any
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from google.adk.runners import Runner
from google.adk.sessions import VertexAiSessionService
from google.adk.memory import VertexAiMemoryBankService
from google.adk.artifacts import InMemoryArtifactService
from google.adk.auth.credential_service import InMemoryCredentialService

from .tools import (
    discover_agents,
    invoke_agent,
    manage_agent_session,
    validate_agent_card,
    deploy_to_vertex_engine,
    monitor_agent_health,
    create_agent_team,
    coordinate_workflow
)


def get_agent() -> LlmAgent:
    """Returns the ADK Orchestrator agent configured for A2A protocol management.

    This agent specializes in:
    - Agent discovery via AgentCards
    - A2A protocol implementation
    - Multi-agent coordination
    - Vertex AI Engine deployment
    - Session and memory management
    - Production monitoring
    """

    # Load system prompt from file
    with open('system-prompt.md', 'r') as f:
        system_instruction = f.read()

    return LlmAgent(
        name="adk-orchestrator",
        model="models/gemini-2.0-flash-exp",  # Latest Gemini for orchestration
        description="Production ADK orchestrator for A2A protocol and multi-agent coordination",
        instruction=system_instruction,
        tools=[
            # Agent Discovery & Management
            FunctionTool(discover_agents),
            FunctionTool(invoke_agent),
            FunctionTool(validate_agent_card),

            # Session & Memory Management
            FunctionTool(manage_agent_session),

            # Deployment & Operations
            FunctionTool(deploy_to_vertex_engine),
            FunctionTool(monitor_agent_health),

            # Multi-Agent Coordination
            FunctionTool(create_agent_team),
            FunctionTool(coordinate_workflow),
        ],
        # Enable features for production
        enable_parallel_tool_calls=True,
        enable_code_execution=True,
        context_window_size=2_000_000,  # 2M token context for Gemini 2.0
        output_key="orchestration_result",
        metadata={
            "version": "1.0.0",
            "deployment_target": "vertex-ai-engine",
            "capabilities": ["a2a", "multi-agent", "session-management", "monitoring"],
            "compliance": "R5-ready"
        }
    )


async def create_runner() -> Runner:
    """Creates a production-ready runner with dual memory (Session + Memory Bank).

    This configuration provides:
    - VertexAiSessionService for conversation state
    - VertexAiMemoryBankService for long-term memory (14-day TTL)
    - Auto-save callback for R5 compliance
    - Proper resource management
    """

    # Initialize services
    session_service = VertexAiSessionService(
        project_id="your-project-id",  # Will be configured via env
        location="us-central1",
        session_ttl_days=30
    )

    memory_service = VertexAiMemoryBankService(
        project_id="your-project-id",
        location="us-central1",
        corpus_name="adk-orchestrator-memory",
        ttl_days=14  # R5 compliance
    )

    # Create runner with production configuration
    return Runner(
        app_name="adk-orchestrator",
        agent=get_agent(),
        session_service=session_service,
        memory_service=memory_service,
        artifact_service=InMemoryArtifactService(),
        credential_service=InMemoryCredentialService(),
        # Auto-save session to memory for R5 compliance
        callbacks={
            "after_session": auto_save_session_to_memory
        }
    )


async def auto_save_session_to_memory(session, memory_service):
    """Callback to automatically save session to memory bank after each interaction.

    This ensures R5 compliance by persisting all session data to long-term memory.
    """
    if session and memory_service:
        await memory_service.save_session(
            session_id=session.id,
            session_data=session.to_dict(),
            metadata={
                "timestamp": session.updated_at,
                "agent": "adk-orchestrator",
                "compliance": "R5"
            }
        )


# Export for ADK CLI
root_agent = get_agent()