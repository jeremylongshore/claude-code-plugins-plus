#!/bin/bash
# Skills Janitor - Market Comparison
# Compares a local skill against alternatives found online

set -euo pipefail

command -v python3 &>/dev/null || { echo "ERROR: python3 required" >&2; exit 1; }
command -v curl &>/dev/null || { echo "ERROR: curl required" >&2; exit 1; }

# --- Defaults ---
SKILL_NAME=""
JSON_OUTPUT=false
DATA_DIR="$(cd "$(dirname "$0")/.." && pwd)/data"

# --- Load platform paths ---
source "$(dirname "$0")/paths.sh"

USER_SKILLS="$CLAUDE_USER_SKILLS"
INSTALL_COUNTS="$HOME/.claude/plugins/install-counts-cache.json"

# --- Parse args ---
while [[ $# -gt 0 ]]; do
    case "$1" in
        --json) JSON_OUTPUT=true; shift ;;
        -h|--help)
            echo "Usage: compare.sh <skill-name> [--json]"
            echo ""
            echo "Compares a local skill against alternatives on GitHub."
            echo "Also shows marketplace install counts when available."
            exit 0
            ;;
        -*) echo "Unknown option: $1" >&2; exit 1 ;;
        *)
            if [[ -z "$SKILL_NAME" ]]; then
                SKILL_NAME="$1"
            fi
            shift
            ;;
    esac
done

if [[ -z "$SKILL_NAME" ]]; then
    echo "ERROR: Skill name required. Usage: compare.sh <skill-name> [--json]" >&2
    exit 1
fi

# --- Find the skill locally ---
SKILL_PATH=""
for dir in "$CLAUDE_USER_SKILLS/$SKILL_NAME" "$CLAUDE_PROJECT_SKILLS/$SKILL_NAME" "$CODEX_USER_SKILLS/$SKILL_NAME" "$CODEX_PROJECT_SKILLS/$SKILL_NAME"; do
    if [[ -d "$dir" ]]; then
        SKILL_PATH="$dir"
        break
    fi
done

if [[ -z "$SKILL_PATH" ]]; then
    echo "ERROR: Skill '$SKILL_NAME' not found in any skill directory" >&2
    exit 1
fi

SKILL_FILE=""
[[ -f "$SKILL_PATH/SKILL.md" ]] && SKILL_FILE="$SKILL_PATH/SKILL.md"
[[ -f "$SKILL_PATH/Skill.md" ]] && SKILL_FILE="$SKILL_PATH/Skill.md"

if [[ -z "$SKILL_FILE" || ! -f "$SKILL_FILE" ]]; then
    echo "ERROR: No SKILL.md found in $SKILL_PATH" >&2
    exit 1
fi

# --- Extract description ---
SKILL_DESC=$(extract_description "$SKILL_FILE")

# --- Ensure data dir ---
mkdir -p "$DATA_DIR"

# --- Export for Python ---
export SKILL_NAME SKILL_DESC JSON_OUTPUT DATA_DIR USER_SKILLS INSTALL_COUNTS

python3 << 'PYEOF'
import json
import math
import os
import re
import sys
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timezone

SKILL_NAME = os.environ.get("SKILL_NAME", "")
SKILL_DESC = os.environ.get("SKILL_DESC", "")
JSON_OUTPUT = os.environ.get("JSON_OUTPUT", "false") == "true"
DATA_DIR = os.environ.get("DATA_DIR", "")
INSTALL_COUNTS_FILE = os.environ.get("INSTALL_COUNTS", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# --- Keyword extraction (same as detect_dupes.sh) ---
STOP_WORDS = {
    "use", "when", "the", "user", "wants", "to", "or", "and", "a", "an",
    "this", "skill", "also", "that", "for", "with", "in", "on", "of",
    "is", "are", "it", "be", "as", "at", "by", "from", "their", "they",
    "has", "have", "do", "does", "can", "will", "about", "not", "but",
    "if", "its", "into", "your", "you", "how", "what", "which", "any",
    "all", "each", "every", "both", "more", "most", "other", "some",
    "such", "than", "too", "very", "just", "only", "own", "same",
    "mentions", "says", "asks", "help", "create", "make", "build",
    "improve", "optimize", "review", "write", "generate", "set", "up",
    "see", "page", "content", "product", "want", "like", "need",
    "would", "should", "could", "get", "using", "used", "new", "way"
}

def extract_keywords(text):
    words = re.findall(r'[a-z]+', text.lower())
    return set(w for w in words if w not in STOP_WORDS and len(w) > 2)

my_keywords = extract_keywords(SKILL_DESC)
# Also add the skill name words
name_words = set(SKILL_NAME.replace("-", " ").split())
my_keywords.update(w.lower() for w in name_words if len(w) > 2)

# --- GitHub API helper ---
def github_api(url):
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "skills-janitor/1.2.0"
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            remaining = resp.headers.get("X-RateLimit-Remaining", "?")
            if remaining != "?" and int(remaining) < 5:
                print(f"WARNING: GitHub API rate limit low ({remaining} remaining)", file=sys.stderr)
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        if e.code in (403, 422):
            return None
        raise
    except urllib.error.URLError:
        return None

# --- Search for alternatives ---
search_terms = " ".join(list(my_keywords)[:5])
q = urllib.parse.quote(f"{search_terms} claude skill")
url = f"https://api.github.com/search/repositories?q={q}+in:name,description,readme&sort=stars&per_page=15"
data = github_api(url)

alternatives = []
now = datetime.now(timezone.utc)

if data and "items" in data:
    for item in data["items"]:
        repo_name = item.get("name", "").lower()
        repo_desc = (item.get("description") or "").lower()
        stars = item.get("stargazers_count", 0)
        forks = item.get("forks_count", 0)
        pushed = item.get("pushed_at", "")
        updated = item.get("updated_at", "")

        # Compute keyword overlap
        alt_keywords = extract_keywords(f"{repo_name} {repo_desc}")
        common = my_keywords & alt_keywords
        union = my_keywords | alt_keywords
        overlap = len(common) / len(union) if union else 0

        # Compute days since last update
        last_date = pushed or updated
        days_since = 999
        if last_date:
            try:
                dt = datetime.fromisoformat(last_date.replace("Z", "+00:00"))
                days_since = (now - dt).days
            except ValueError:
                pass

        # Composite relevance score
        kw_score = overlap * 40
        pop_score = min(math.log10(max(stars, 1)) / 5, 1.0) * 30
        rec_score = max(0, (365 - days_since) / 365) * 15
        act_score = min(forks / max(stars, 1) * 5, 1.0) * 15 if stars > 0 else 0
        score = kw_score + pop_score + rec_score + act_score

        alternatives.append({
            "full_name": item.get("full_name", ""),
            "name": item.get("name", ""),
            "description": (item.get("description") or "")[:150],
            "stars": stars,
            "forks": forks,
            "updated_at": (pushed or updated or "")[:10],
            "overlap_pct": round(overlap * 100),
            "common_keywords": sorted(common)[:8],
            "score": round(score, 1),
            "url": item.get("html_url", ""),
        })

# Sort by score descending
alternatives.sort(key=lambda x: -x["score"])
alternatives = alternatives[:10]

# --- Load marketplace install counts ---
install_counts = {}
if INSTALL_COUNTS_FILE and os.path.isfile(INSTALL_COUNTS_FILE):
    try:
        with open(INSTALL_COUNTS_FILE) as f:
            ic_data = json.load(f)
            for entry in ic_data.get("counts", []):
                plugin = entry.get("plugin", "")
                name = plugin.split("@")[0].lower()
                install_counts[name] = entry.get("unique_installs", 0)
    except (json.JSONDecodeError, IOError):
        pass

# Find relevant install counts (skills that share keywords with ours)
relevant_installs = []
for plugin_name, count in install_counts.items():
    plugin_kw = set(plugin_name.replace("-", " ").split())
    common = my_keywords & plugin_kw
    if common and len(common) >= 1:
        relevant_installs.append({"plugin": plugin_name, "installs": count, "shared": sorted(common)})

relevant_installs.sort(key=lambda x: -x["installs"])
relevant_installs = relevant_installs[:5]

# --- Output ---
if JSON_OUTPUT:
    output = {
        "skill": SKILL_NAME,
        "keywords": sorted(my_keywords),
        "alternatives": alternatives,
        "marketplace_installs": relevant_installs,
    }
    print(json.dumps(output, indent=2))
else:
    print(f"=== Skills Janitor - Market Analysis ===")
    print(f"Analyzing: {SKILL_NAME}")
    print()
    print(f"Your skill keywords: {', '.join(sorted(my_keywords)[:12])}")
    print()

    if alternatives:
        print("--- Alternatives Found ---")
        print()
        print(f"  {'#':<3} {'Repository':<40} {'Score':>5} {'Stars':>7} {'Overlap':>7} {'Updated':<10}")
        print(f"  {'─'*3} {'─'*40} {'─'*5} {'─'*7} {'─'*7} {'─'*10}")
        for i, alt in enumerate(alternatives, 1):
            print(f"  {i:<3} {alt['full_name']:<40} {alt['score']:>5} {alt['stars']:>7} {alt['overlap_pct']:>5}%  {alt['updated_at']:<10}")
        print()

        # Market position summary
        top = alternatives[0]
        print("--- Market Position ---")
        if top["overlap_pct"] > 50:
            print(f"  Closest alternative: {top['full_name']} ({top['overlap_pct']}% keyword overlap, {top['stars']} stars)")
        elif top["overlap_pct"] > 20:
            print(f"  Partial overlap: {top['full_name']} ({top['overlap_pct']}% keyword overlap)")
            print(f"  Your skill may be more specialized in its niche.")
        else:
            print(f"  Low overlap with top results - your skill occupies a unique niche.")
        print()
    else:
        print("No alternatives found on GitHub.")
        print()

    if relevant_installs:
        print("--- Related Marketplace Plugins (install counts) ---")
        for ri in relevant_installs:
            print(f"  {ri['installs']:>8,}  {ri['plugin']} (shared: {', '.join(ri['shared'])})")
        print()

        # Check if our skill is in marketplace
        my_installs = install_counts.get(SKILL_NAME.lower())
        if my_installs:
            print(f"  Your skill install count: {my_installs:,}")
        else:
            print(f"  Your skill is not in the official marketplace.")
        print()

PYEOF
