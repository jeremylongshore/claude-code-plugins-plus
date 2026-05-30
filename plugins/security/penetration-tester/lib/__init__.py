"""Shared utility module for penetration-tester v3.x narrow skills.

Per AT-ADEC at 000-docs/001-AT-ADEC-skill-taxonomy.md, every per-skill script
imports from this module so the per-skill scripts stay narrow (≤200 LOC of
skill-specific logic, not 200 LOC of plumbing per skill).

Modules:
    http_client    request setup with timeouts, redirects, UA
    finding        Finding dataclass + severity enum
    severity       normalize severities across upstream tools
    report         JSON + Markdown emitters
    authz_check    authorization-attestation gate for active-scan skills
    cli_args       shared argparse helpers
"""

__version__ = "3.0.0-dev"
