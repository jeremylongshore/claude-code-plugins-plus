#!/usr/bin/env python3
"""bundle-grant-retry.py — PostToolUse hook for the Databricks Asset Bundles
schema-GRANT-ordering bug (databricks-bundle-medic, AP03 / pain D6).

Pain D6 (databricks/cli#4573): DAB's resource graph does not encode the implicit
dependency that GRANTs supplying create-time privileges must apply BEFORE the
resources that exercise them. So the FIRST `databricks bundle deploy` to a fresh
workspace fails with "User does not have CREATE TABLE on Schema '<catalog.schema>'"
— but the SECOND deploy succeeds, because the failed first deploy applied the grants
before it died. It is a known-transient, single-retry-fixable failure.

This hook runs AFTER a Bash tool call and, ONLY when BOTH hold:
  1. the command was `databricks bundle deploy`, and
  2. the output carries the EXACT D6 grant-ordering signature,
adds context recommending exactly ONE retry, with the reason.

DESIGN — surface, never mask (the hard constraint on this hook):
  * It does NOT swallow, retry, or hide the error. It only ADDS context via
    additionalContext; the original failure remains fully visible.
  * It fires ONLY on the precise D6 signature on a bundle deploy — any other error
    class (auth, network, a real missing grant that a retry won't fix, a different
    permission) produces NO output, so a genuine failure is never re-characterised
    as "just retry".
  * A retry is recommended ONCE. If the SAME failure appears after a retry it is no
    longer the transient D6 (the grants would already exist) — the hook still only
    advises, so the operator/agent sees the persistent error and stops.

Protocol: reads the PostToolUse event JSON on stdin, writes PostToolUse JSON on
stdout (additionalContext only), exits 0.
"""

import json
import re
import sys

BUNDLE_DEPLOY = re.compile(r"\bdatabricks\s+bundle\s+deploy\b", re.IGNORECASE)

# The D6 signature, specific to the create-time-privilege / schema-grant class:
# "User does not have <PRIVILEGE> on Schema '<catalog.schema>'". Requiring both the
# "does not have ... on Schema" shape AND a create-class privilege keeps it from
# firing on unrelated permission errors (e.g. SELECT on a table, USE CATALOG).
D6_SIGNATURE = re.compile(
    r"does not have\s+(?:CREATE(?:\s+\w+)?|MODIFY|APPLY\s+TAG)\b[^\n]*\bon\s+Schema\b",
    re.IGNORECASE,
)


def is_bundle_deploy(command):
    return bool(command and isinstance(command, str) and BUNDLE_DEPLOY.search(command))


def extract_output(tool_response):
    """Pull the text output from a PostToolUse tool_response (string or dict)."""
    if tool_response is None:
        return ""
    if isinstance(tool_response, str):
        return tool_response
    if isinstance(tool_response, dict):
        parts = []
        for key in ("stdout", "stderr", "output", "content", "error"):
            v = tool_response.get(key)
            if isinstance(v, str):
                parts.append(v)
        return "\n".join(parts)
    return str(tool_response)


def is_d6_grant_ordering(command, output):
    """True iff this is a bundle deploy that failed with the exact D6 signature. Pure —
    the whole no-mask precision contract lives here."""
    if not is_bundle_deploy(command):
        return False
    return bool(D6_SIGNATURE.search(output or ""))


RETRY_ADVICE = (
    "bundle-medic: this is the known-transient DAB schema-GRANT-ordering bug "
    "(databricks/cli#4573) — the resource graph applied the GRANTs *while* failing, "
    "so they now exist. Re-run `databricks bundle deploy` EXACTLY ONCE; it should "
    "succeed. If the SAME 'does not have ... on Schema' error persists after one "
    "retry, it is NOT this transient (the grants would already be present) — stop and "
    "treat it as a real missing privilege, do not keep retrying."
)


def decide(event):
    """Return a PostToolUse dict (additionalContext) or None."""
    command = (event.get("tool_input") or {}).get("command", "")
    output = extract_output(event.get("tool_response"))
    if is_d6_grant_ordering(command, output):
        return {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": RETRY_ADVICE,
            }
        }
    return None


def main():
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    if event.get("tool_name") != "Bash":
        return 0
    result = decide(event)
    if result:
        json.dump(result, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
