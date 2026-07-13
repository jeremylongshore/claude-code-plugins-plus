#!/bin/bash
# Skills Janitor - Duplicate Detection
# Finds skills with overlapping descriptions and trigger keywords

set -euo pipefail

command -v python3 &>/dev/null || { echo "ERROR: python3 required" >&2; exit 1; }

# --- Load platform paths ---
source "$(dirname "$0")/paths.sh"

# Collect all skill descriptions into a temp file
export TMPFILE=$(mktemp)
trap "rm -f $TMPFILE" EXIT

extract_skills() {
    local dir="$1"
    local scope="$2"
    local namespace="${3:-}"
    [[ -d "$dir" ]] || return 0

    for skill_dir in "$dir"/*/; do
        [[ -d "$skill_dir" ]] || continue
        local name
        name=$(basename "$skill_dir")

        # Skip self
        [[ "$name" == "skills-janitor" ]] && continue

        local skill_file=""
        [[ -f "$skill_dir/SKILL.md" ]] && skill_file="$skill_dir/SKILL.md"
        [[ -f "$skill_dir/Skill.md" ]] && skill_file="$skill_dir/Skill.md"
        [[ -z "$skill_file" ]] && continue
        [[ ! -e "$skill_file" ]] && continue  # broken symlink

        # Extract description
        local desc
        desc=$(extract_description "$skill_file" | tr '[:upper:]' '[:lower:]')

        # Resolve symlinks so the same physical SKILL.md gets one record,
        # not one-per-shadow. ~/.claude/skills entries that symlink to
        # ~/.agents/skills (the universal install) would otherwise be
        # compared against themselves and reported as 100% duplicates.
        local realpath
        realpath=$(cd "$skill_dir" 2>/dev/null && pwd -P || echo "$skill_dir")

        # Qualified name: <namespace>:<folder> for plugin/source skills,
        # plain folder otherwise. Two user-scope skills both named "foo"
        # ARE a name collision; user "foo" and plugin "x:foo" are NOT —
        # they have distinct invocation names by Claude's convention.
        local qualified="$name"
        [[ -n "$namespace" ]] && qualified="${namespace}:${name}"

        printf '%s\t%s\t%s\t%s\t%s\n' "$scope" "$qualified" "$realpath" "$desc" "$namespace" >> "$TMPFILE"
    done
}

# Scan all platforms (Claude Code + Codex + plugins + sources)
_dupes_scan() { extract_skills "$1" "$2" "$4"; }
for_each_skill_dir _dupes_scan

echo "=== Skills Janitor - Duplicate Detection ==="
echo ""
total_rows=$(wc -l < "$TMPFILE" | tr -d ' ')
unique_paths=$(awk -F'\t' '{print $3}' "$TMPFILE" | sort -u | wc -l | tr -d ' ')
echo "Total skill records: $total_rows"
echo "Unique skill files (after symlink dedup): $unique_paths"
echo ""

python3 << 'PYEOF'
import re
import sys
import os
from collections import defaultdict

raw_skills = []

tmpfile = os.environ.get("TMPFILE", "")
if not tmpfile:
    tmpfile = sys.argv[1] if len(sys.argv) > 1 else ""

with open(tmpfile) as f:
    for line in f:
        line = line.rstrip("\n")
        if not line:
            continue
        parts = line.split("\t", 4)
        # Tolerate older row shapes for forward compatibility
        while len(parts) < 5:
            parts.append("")
        scope, name, realpath, desc, namespace = parts
        raw_skills.append({
            "scope": scope,
            "name": name,           # qualified name: <ns>:<folder> for plugin, folder otherwise
            "realpath": realpath,
            "desc": desc,
            "namespace": namespace,
        })

if not raw_skills:
    print("No skills found to analyze.")
    sys.exit(0)

# --- Dedupe by realpath ---
# When ~/.claude/skills/foo is a symlink to ~/.agents/skills/foo, the same
# physical SKILL.md is reachable from both Claude and Codex scopes. Without
# dedup, the cross-product comparison flagged every shadow as a 100%
# self-duplicate. Group by realpath; keep one canonical record per file
# but remember every location it was reachable from.
by_realpath = {}
for s in raw_skills:
    key = s["realpath"] or f"{s['scope']}/{s['name']}"
    if key not in by_realpath:
        by_realpath[key] = {
            "name": s["name"],
            "desc": s["desc"],
            "realpath": s["realpath"],
            "locations": [],
        }
    by_realpath[key]["locations"].append({"scope": s["scope"], "name": s["name"]})

skills = list(by_realpath.values())

# --- Detect name collisions across distinct realpaths ---
# Two unrelated skills with the same name living at different paths is the
# situation that confuses skill triggering. Surface these explicitly,
# regardless of description similarity.
by_name = defaultdict(list)
for s in skills:
    by_name[s["name"]].append(s)
name_collisions = sorted(
    [(n, lst) for n, lst in by_name.items() if len(lst) > 1],
    key=lambda t: t[0],
)

def extract_keywords(desc):
    stop_words = {"use", "when", "the", "user", "wants", "to", "or", "and", "a", "an",
                  "this", "skill", "also", "that", "for", "with", "in", "on", "of",
                  "is", "are", "it", "be", "as", "at", "by", "from", "their", "they",
                  "has", "have", "do", "does", "can", "will", "about", "not", "but",
                  "if", "its", "into", "your", "you", "how", "what", "which", "any",
                  "all", "each", "every", "both", "more", "most", "other", "some",
                  "such", "than", "too", "very", "just", "only", "own", "same",
                  "mentions", "says", "asks", "help", "create", "make", "build",
                  "improve", "optimize", "review", "write", "generate", "set", "up"}
    words = re.findall(r'[a-z]+', desc.lower())
    return set(w for w in words if w not in stop_words and len(w) > 2)

# Compare all pairs (now over deduped skills, so each pair is unique)
overlaps = []
for i in range(len(skills)):
    kw_i = extract_keywords(skills[i]["desc"])
    if not kw_i:
        continue
    for j in range(i + 1, len(skills)):
        kw_j = extract_keywords(skills[j]["desc"])
        if not kw_j:
            continue
        common = kw_i & kw_j
        union = kw_i | kw_j
        similarity = len(common) / len(union) if union else 0
        if similarity > 0.3:
            overlaps.append({
                "skill_a": skills[i]["name"],
                "skill_b": skills[j]["name"],
                "similarity": round(similarity * 100),
                "common_keywords": sorted(common)[:10],
                "locations_a": skills[i]["locations"],
                "locations_b": skills[j]["locations"],
            })

overlaps.sort(key=lambda x: x["similarity"], reverse=True)

# --- Output ---
if name_collisions:
    print("--- Name Collisions ---")
    print(f"Found {len(name_collisions)} skill name(s) at multiple distinct paths:\n")
    for name, entries in name_collisions:
        print(f"  {name}")
        for e in entries:
            scopes = ", ".join(sorted({l["scope"] for l in e["locations"]}))
            print(f"    [{scopes}] {e['realpath']}")
        print()

if overlaps:
    print("--- Description Overlap (Jaccard > 30%) ---")
    print(f"Found {len(overlaps)} potential overlap(s):\n")
    for o in overlaps:
        scopes_a = ",".join(sorted({l["scope"] for l in o["locations_a"]}))
        scopes_b = ",".join(sorted({l["scope"] for l in o["locations_b"]}))
        print(f"  [{o['similarity']}%] {o['skill_a']} <-> {o['skill_b']}")
        print(f"       Scopes: {scopes_a} / {scopes_b}")
        print(f"       Shared keywords: {', '.join(o['common_keywords'][:8])}")
        print()

if not name_collisions and not overlaps:
    print("No significant overlaps or name collisions detected.")

PYEOF
