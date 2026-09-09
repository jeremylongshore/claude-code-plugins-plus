#!/bin/sh
# SessionStart hook: emit hyperfocus rules as additionalContext when persistent
# mode is enabled. Silent, zero-output exit on any missing/disabled/error state.

data_dir=
root_dir=
project_dir=

while [ "$#" -gt 0 ]; do
  case "$1" in
    --data)
      data_dir=$2
      shift 2
      ;;
    --root)
      root_dir=$2
      shift 2
      ;;
    --project)
      project_dir=$2
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

[ -n "$root_dir" ] || exit 0

if [ -n "$data_dir" ]; then
  global_state="$data_dir/state"
elif [ -n "$CLAUDE_PLUGIN_DATA" ]; then
  global_state="$CLAUDE_PLUGIN_DATA/state"
elif [ -n "$PLUGIN_DATA" ]; then
  global_state="$PLUGIN_DATA/state"
else
  global_state="$HOME/.claude/plugins/data/hyperfocus/state"
fi

project_state=
if [ -n "$project_dir" ]; then
  project_state="$project_dir/.claude/hyperfocus.state"
fi

state_file=
if [ -n "$project_state" ] && [ -f "$project_state" ]; then
  state_file=$project_state
elif [ -f "$global_state" ]; then
  state_file=$global_state
else
  exit 0
fi

[ -r "$state_file" ] || exit 0

enabled=
mode=
while IFS='=' read -r key value || [ -n "$key" ]; do
  case "$key" in
    enabled) enabled=$value ;;
    mode) mode=$value ;;
  esac
done < "$state_file"

[ "$enabled" = "true" ] || exit 0

case "$mode" in
  clean|flow|zen) ;;
  *) mode=flow ;;
esac

core_file="$root_dir/skills/hyperfocus/references/core.md"
mode_file="$root_dir/skills/hyperfocus/references/$mode.md"

[ -f "$core_file" ] || exit 0
[ -f "$mode_file" ] || exit 0

escaped=$(awk '
{
  line = $0
  gsub(/\\/, "\\\\", line)
  gsub(/"/, "\\\"", line)
  gsub(/\t/, "\\t", line)
  printf "%s\\n", line
}' "$core_file" "$mode_file" 2>/dev/null) || exit 0

printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' "$escaped"
exit 0
