"""PR file-level component classifier.

Given a list of files changed in a PR, emit a structured JSON object
describing what kind of contribution it is — which plugins, skills,
agents, MCP servers, hooks, workflows, scripts, docs, and catalog
additions are affected.

The classifier is deterministic. Same input → same output, always.
Downstream consumers (the prescreen, the per-domain CI workflows)
use this output to route per-contribution-type evaluation without
each re-implementing the file-path-to-component mapping.
"""

from .rules import RULE_DESCRIPTIONS, classify_files

__all__ = ["RULE_DESCRIPTIONS", "classify_files"]
