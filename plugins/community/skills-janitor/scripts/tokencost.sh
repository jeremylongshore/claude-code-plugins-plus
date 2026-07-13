#!/bin/bash
# Skills Janitor - Context Window Token Cost
# Shows how many tokens each skill's system prompt consumes

set -euo pipefail

command -v python3 &>/dev/null || { echo "ERROR: python3 required" >&2; exit 1; }

# --- Load platform paths ---
source "$(dirname "$0")/paths.sh"

# --- Defaults ---
JSON_OUTPUT=false
BUDGET=200000
WEEKS=4
DATA_DIR="$(cd "$(dirname "$0")/.." && pwd)/data"

# --- Parse args ---
while [[ $# -gt 0 ]]; do
    case "$1" in
        --json) JSON_OUTPUT=true; shift ;;
        --budget) BUDGET="$2"; shift 2 ;;
        --weeks) WEEKS="$2"; shift 2 ;;
        -h|--help)
            echo "Usage: tokencost.sh [--budget N] [--weeks N] [--json]"
            echo ""
            echo "Show context window token cost per skill."
            echo "  --budget N   Context window size (default: 200000)"
            echo "  --weeks N    Usage lookback period (default: 4)"
            echo "  --json       Output as JSON"
            exit 0
            ;;
        -*) echo "Unknown option: $1" >&2; exit 1 ;;
        *) shift ;;
    esac
done

# --- Collect skill data ---
export TMPFILE=$(mktemp)
trap "rm -f $TMPFILE" EXIT

scan_skills() {
    local dir="$1"
    local scope="$2"
    local namespace="${3:-}"
    [[ -d "$dir" ]] || return 0

    for skill_dir in "$dir"/*/; do
        [[ -d "$skill_dir" ]] || continue
        local name
        name=$(basename "$skill_dir")
        [[ "$name" == "skills-janitor" ]] && continue

        local skill_file=""
        [[ -f "$skill_dir/SKILL.md" ]] && skill_file="$skill_dir/SKILL.md"
        [[ -f "$skill_dir/Skill.md" ]] && skill_file="$skill_dir/Skill.md"
        [[ -z "$skill_file" ]] && continue
        [[ ! -e "$skill_file" ]] && continue

        local word_count
        word_count=$(wc -w < "$skill_file" | tr -d ' ')

        local desc
        desc=$(extract_description "$skill_file")

        # Description word count, measured separately: ONLY the description is
        # always loaded into the system prompt (progressive disclosure) — the
        # body costs tokens only when the skill actually triggers.
        local desc_words
        desc_words=$(echo "$desc" | wc -w | tr -d ' ')

        # Resolve symlinks so a single physical SKILL.md is counted once.
        # ~/.claude/skills/foo and ~/.agents/skills/foo can be the same
        # underlying file, which would otherwise inflate the total cost.
        local realpath
        realpath=$(cd "$skill_dir" 2>/dev/null && pwd -P || echo "$skill_dir")

        # Display name uses Claude's namespaced convention for plugin skills
        local display_name="$name"
        [[ -n "$namespace" ]] && display_name="${namespace}:${name}"

        printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$scope" "$display_name" "$realpath" "$word_count" "$desc_words" "$desc" >> "$TMPFILE"
    done
}

# Scan all platforms (Claude Code + Codex + plugins + sources)
_token_scan() { scan_skills "$1" "$2" "$4"; }
for_each_skill_dir _token_scan

# --- Subagents: their descriptions are always-loaded too (~/.claude/agents) ---
export AGENTS_TMPFILE=$(mktemp)
trap "rm -f $TMPFILE $AGENTS_TMPFILE" EXIT
# Realpath dedup: from $HOME, ./.claude/agents IS ~/.claude/agents — without
# this the always-loaded agents total doubles.
_seen_agents_dirs=""
for _agents_dir in "$HOME/.claude/agents" "./.claude/agents"; do
    [[ -d "$_agents_dir" ]] || continue
    _agents_real=$(cd "$_agents_dir" 2>/dev/null && pwd -P || echo "$_agents_dir")
    case "|$_seen_agents_dirs|" in *"|$_agents_real|"*) continue ;; esac
    _seen_agents_dirs="$_seen_agents_dirs|$_agents_real"
    for _agent_file in "$_agents_dir"/*.md; do
        [[ -f "$_agent_file" ]] || continue
        _a_name=$(basename "$_agent_file" .md)
        _a_words=$(wc -w < "$_agent_file" | tr -d ' ')
        # Shared helper: handles block-scalar descriptions
        _a_desc=$(extract_description "$_agent_file")
        _a_desc_words=$(echo "$_a_desc" | wc -w | tr -d ' ')
        printf '%s\t%s\t%s\n' "$_a_name" "$_a_words" "$_a_desc_words" >> "$AGENTS_TMPFILE"
    done
done

# --- Export for Python ---
export JSON_OUTPUT BUDGET WEEKS DATA_DIR

python3 << 'PYEOF'
import json
import os
import sys

JSON_OUTPUT = os.environ.get("JSON_OUTPUT", "false") == "true"
BUDGET = int(os.environ.get("BUDGET", "200000"))
WEEKS = int(os.environ.get("WEEKS", "4"))
TMPFILE = os.environ.get("TMPFILE", "")
DATA_DIR = os.environ.get("DATA_DIR", "")

# Token approximation: ~1.3 tokens per word for English markdown
TOKEN_RATIO = 1.3

# --- Load skill data, deduping by realpath ---
# Skills installed into both ~/.claude/skills and ~/.agents/skills (e.g. via
# `npx skills add`) are usually one physical SKILL.md reachable from two
# locations via symlink. The previous implementation counted both, doubling
# the reported token cost and inflating "% of budget wasted".
seen_paths = {}
if TMPFILE and os.path.isfile(TMPFILE):
    with open(TMPFILE) as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            parts = line.split("\t", 5)
            # Tolerate older row shapes (no realpath / no desc_words).
            if len(parts) == 4:
                scope, name, word_count, desc = parts
                realpath, desc_words = "", "0"
            elif len(parts) == 5:
                scope, name, realpath, word_count, desc = parts
                desc_words = "0"
            elif len(parts) == 6:
                scope, name, realpath, word_count, desc_words, desc = parts
            else:
                continue
            key = realpath or f"{scope}/{name}"
            if key in seen_paths:
                seen_paths[key]["scopes"].add(scope)
                continue
            tokens = int(round(int(word_count) * TOKEN_RATIO))
            desc_tokens = int(round(int(desc_words or 0) * TOKEN_RATIO))
            seen_paths[key] = {
                "name": name,
                "scope": scope,
                "scopes": {scope},
                "realpath": realpath,
                "words": int(word_count),
                "tokens": tokens,                    # full SKILL.md (loaded on trigger)
                "desc_tokens": desc_tokens,          # always in the system prompt
                "body_tokens": max(0, tokens - desc_tokens),
                "description": desc[:80],
            }

skills = list(seen_paths.values())
for s in skills:
    s["scope"] = ",".join(sorted(s.pop("scopes")))

# Sort by tokens descending
skills.sort(key=lambda x: -x["tokens"])

# --- Cross-reference with usage data ---
usage_data = {}
usage_file = os.path.join(DATA_DIR, "usage-history.json") if DATA_DIR else ""
if usage_file and os.path.isfile(usage_file):
    try:
        with open(usage_file) as f:
            ud = json.load(f)
            usage_data = ud.get("skills", {})
    except (json.JSONDecodeError, IOError):
        pass

for s in skills:
    u = usage_data.get(s["name"], {})
    s["used"] = u.get("total", 0) > 0
    s["usage_count"] = u.get("total", 0)
    s["last_used"] = u.get("last_used", "never")

# --- Agents (descriptions always loaded, like skill descriptions) ---
agents = []
agents_file = os.environ.get("AGENTS_TMPFILE", "")
if agents_file and os.path.isfile(agents_file):
    with open(agents_file) as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 3:
                continue
            a_name, a_words, a_desc_words = parts
            agents.append({
                "name": a_name,
                "tokens": int(round(int(a_words or 0) * TOKEN_RATIO)),
                "desc_tokens": int(round(int(a_desc_words or 0) * TOKEN_RATIO)),
            })

# --- Compute totals ---
# The honest budget number is `desc_tokens`: only descriptions sit in the
# system prompt permanently. Bodies load on demand when a skill triggers.
total_tokens = sum(s["tokens"] for s in skills)
total_desc_tokens = sum(s["desc_tokens"] for s in skills)
total_body_tokens = sum(s["body_tokens"] for s in skills)
agents_desc_tokens = sum(a["desc_tokens"] for a in agents)
always_loaded = total_desc_tokens + agents_desc_tokens
total_used_tokens = sum(s["tokens"] for s in skills if s["used"])
total_unused_tokens = sum(s["tokens"] for s in skills if not s["used"])
unused_desc_tokens = sum(s["desc_tokens"] for s in skills if not s["used"])
budget_pct = (total_tokens / BUDGET * 100) if BUDGET > 0 else 0
always_pct = (always_loaded / BUDGET * 100) if BUDGET > 0 else 0
waste_pct = (total_unused_tokens / BUDGET * 100) if BUDGET > 0 else 0

used_count = sum(1 for s in skills if s["used"])
unused_count = len(skills) - used_count

# --- Output ---
if JSON_OUTPUT:
    output = {
        "budget": BUDGET,
        "total_tokens": total_tokens,
        "always_loaded_tokens": always_loaded,
        "desc_tokens": total_desc_tokens,
        "body_tokens": total_body_tokens,
        "agents_desc_tokens": agents_desc_tokens,
        "total_used_tokens": total_used_tokens,
        "total_unused_tokens": total_unused_tokens,
        "budget_pct": round(budget_pct, 1),
        "always_pct": round(always_pct, 1),
        "waste_pct": round(waste_pct, 1),
        "skill_count": len(skills),
        "agent_count": len(agents),
        "used_count": used_count,
        "unused_count": unused_count,
        "skills": skills,
        "agents": agents,
    }
    print(json.dumps(output, indent=2))
else:
    print("=== Skills Janitor - Context Window Cost ===")
    print(f"Budget: {BUDGET:,} tokens")
    print()

    if not skills:
        print("No skills found.")
        sys.exit(0)

    # Table — Always = description tokens (permanently in the system prompt),
    # Body = the rest of SKILL.md (loaded only when the skill triggers).
    print(f"  {'Skill':<35} {'Always':>7} {'Body':>8} {'Used?':>6} {'Last Used':<10}")
    print(f"  {'─'*35} {'─'*7} {'─'*8} {'─'*6} {'─'*10}")

    for s in skills:
        used_marker = "yes" if s["used"] else "NO"
        lu = s["last_used"] if s["last_used"] != "never" else "never"
        print(f"  {s['name']:<35} {s['desc_tokens']:>7,} {s['body_tokens']:>8,} {used_marker:>6} {lu:<10}")

    print()
    print("─" * 78)
    print(f"  {'TOTAL':<35} {total_desc_tokens:>7,} {total_body_tokens:>8,}")
    print()

    # Summary — the always-loaded number is the real context rent; the body
    # total is what a triggered skill can pull in on top.
    print("--- Summary ---")
    print(f"  Skills: {len(skills)} ({used_count} active, {unused_count} unused)")
    print(f"  Always-loaded (skill descriptions): {total_desc_tokens:,} tokens")
    if agents:
        print(f"  Always-loaded (agent descriptions): {agents_desc_tokens:,} tokens ({len(agents)} agents)")
    print(f"  Always-loaded TOTAL: {always_loaded:,} ({always_pct:.1f}% of {BUDGET:,} budget)")
    print(f"  On-demand skill bodies: {total_body_tokens:,} tokens (loaded only when a skill triggers)")
    print(f"  Unused skills: {unused_count} — {unused_desc_tokens:,} always-loaded tokens + {total_unused_tokens - unused_desc_tokens:,} body tokens you never trigger")
    print()

    if total_unused_tokens > 0:
        # Top unused wasters, ranked by the tokens their SKILL.md holds
        unused_skills = [s for s in skills if not s["used"]]
        if unused_skills:
            print("--- Top Unused (always-loaded + body) ---")
            for s in unused_skills[:5]:
                print(f"  {s['desc_tokens']:>6,} + {s['body_tokens']:>7,} body  {s['name']}")
            if len(unused_skills) > 5:
                rest_desc = sum(s["desc_tokens"] for s in unused_skills[5:])
                print(f"  {rest_desc:>6,} (desc)        ... and {len(unused_skills) - 5} more")
            print()
            print(f"  Removing unused skills frees {unused_desc_tokens:,} always-loaded tokens and {total_unused_tokens - unused_desc_tokens:,} potential body tokens")

PYEOF
