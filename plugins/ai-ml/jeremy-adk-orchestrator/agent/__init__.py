# Copyright 2025 Jeremy Longshore
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

"""ADK Orchestrator Agent - A2A protocol manager for Vertex AI Engine"""

from .agent import get_agent, create_runner, root_agent

__all__ = ["get_agent", "create_runner", "root_agent"]

__version__ = "1.0.0"