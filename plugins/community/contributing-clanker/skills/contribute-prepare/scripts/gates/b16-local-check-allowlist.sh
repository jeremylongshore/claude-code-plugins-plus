#!/usr/bin/env bash
# Catalog: B16 — Dossier injection via local_check_command
# Mitigates: Security review GAP #1 — `local_check_command:` is free-text from
# upstream CONTRIBUTING.md. Malicious repo could inject `make test; rm -rf ~`.
# Briefing surfaces the recommendation, gate B14 may exec it. This gate refuses
# to proceed if the dossier's command doesn't match the safe-runner allowlist.
source "$(dirname "$0")/lib/preamble.sh"

gate_read_input

if [[ -z "$GATE_DOSSIER_PATH" || ! -f "$GATE_DOSSIER_PATH" ]]; then
  gate_skip "no dossier — no command to validate"
fi

CMD=$(fm_field "$GATE_DOSSIER_PATH" "local_check_command")
if [[ -z "$CMD" || "$CMD" == "(not detected)" ]]; then
  gate_pass "no local_check_command in dossier (nothing to validate)"
fi

# Allowlist: known-safe runners + their typical args. Composed commands (&&, ||,
# ;, |, $(), backticks) are denied unconditionally — they're the injection vector.
if /usr/bin/printf '%s' "$CMD" | /usr/bin/grep -qE '[;|`$(){}<>]|&&|\|\|'; then
  gate_block "dossier local_check_command contains shell metacharacters: $CMD" "researcher-build.sh extracted this from upstream CONTRIBUTING.md. Treat as untrusted. Manually verify the command and edit the dossier; rerun this gate."
fi

# Allowlist regex: starts with a known-safe runner + simple alphanum args.
ALLOW_REGEX='^(make|pnpm|npm|yarn|cargo|pytest|python|python3|go|sbt|mix|dotnet|uv|hatch|tox|just|task|bundle|ruby) [a-zA-Z0-9 _:.,/\-]+$'
if ! /usr/bin/printf '%s' "$CMD" | /usr/bin/grep -qE "$ALLOW_REGEX" ; then
  gate_block "dossier local_check_command not in allowlist: $CMD" "expected pattern: <make|pnpm|npm|yarn|cargo|pytest|...> followed by alphanumeric args. Edit the dossier to match the actual safe command, or override if you've manually verified."
fi

gate_pass "local_check_command matches safe-runner allowlist"
