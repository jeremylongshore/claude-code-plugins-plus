#!/bin/bash
# Skills Janitor - Skill Discovery
# Searches GitHub for Claude Code skills by keyword

set -euo pipefail

command -v python3 &>/dev/null || { echo "ERROR: python3 required" >&2; exit 1; }
command -v curl &>/dev/null || { echo "ERROR: curl required" >&2; exit 1; }

# --- Defaults ---
KEYWORD=""
COMPARE=""
LIMIT=10
JSON_OUTPUT=false
DATA_DIR="$(cd "$(dirname "$0")/.." && pwd)/data"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# --- Load platform paths ---
source "$(dirname "$0")/paths.sh"

USER_SKILLS="$CLAUDE_USER_SKILLS"

# --- Parse args ---
while [[ $# -gt 0 ]]; do
    case "$1" in
        --limit) LIMIT="$2"; shift 2 ;;
        --json) JSON_OUTPUT=true; shift ;;
        --compare) COMPARE="$2"; shift 2 ;;
        -h|--help)
            echo "Usage: search.sh <keyword> [--limit N] [--json]"
            echo "       search.sh --compare <skill-name> [--json]"
            echo ""
            echo "Searches GitHub for Claude Code skills matching the keyword."
            echo "Use --compare to analyze a local skill against GitHub alternatives."
            echo "Set GITHUB_TOKEN env var for higher rate limits and code search."
            exit 0
            ;;
        -*) echo "Unknown option: $1" >&2; exit 1 ;;
        *)
            if [[ -z "$KEYWORD" ]]; then
                KEYWORD="$1"
            else
                echo "ERROR: Only one keyword argument supported" >&2; exit 1
            fi
            shift
            ;;
    esac
done

# If --compare mode, delegate to compare.sh
if [[ -n "$COMPARE" ]]; then
    COMPARE_ARGS=("$COMPARE")
    [[ "$JSON_OUTPUT" == "true" ]] && COMPARE_ARGS+=("--json")
    exec bash "$SCRIPT_DIR/compare.sh" "${COMPARE_ARGS[@]}"
fi

if [[ -z "$KEYWORD" ]]; then
    echo "ERROR: Keyword required. Usage: search.sh <keyword> [--limit N] [--json]" >&2
    exit 1
fi

# --- Ensure data dir ---
mkdir -p "$DATA_DIR"

# --- Export for Python ---
export KEYWORD LIMIT JSON_OUTPUT DATA_DIR USER_SKILLS

python3 << 'PYEOF'
import json
import os
import sys
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timezone

KEYWORD = os.environ.get("KEYWORD", "")
LIMIT = int(os.environ.get("LIMIT", "10"))
JSON_OUTPUT = os.environ.get("JSON_OUTPUT", "false") == "true"
DATA_DIR = os.environ.get("DATA_DIR", "")
USER_SKILLS = os.environ.get("USER_SKILLS", "")

# --- Check for auth ---
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

def github_api(url, token=""):
    """Make a GitHub API request with rate limit awareness."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "skills-janitor/1.5.0"
    }
    if token:
        headers["Authorization"] = f"token {token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            remaining = resp.headers.get("X-RateLimit-Remaining", "?")
            if remaining != "?" and int(remaining) < 5:
                print(f"WARNING: GitHub API rate limit low ({remaining} remaining)", file=sys.stderr)
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 403:
            print("ERROR: GitHub API rate limit exceeded. Set GITHUB_TOKEN for higher limits.", file=sys.stderr)
            return None
        elif e.code == 422:
            return None
        raise
    except urllib.error.URLError as e:
        print(f"ERROR: Network error: {e.reason}", file=sys.stderr)
        return None

# --- Check cache ---
cache_file = os.path.join(DATA_DIR, "search-cache.json") if DATA_DIR else ""
cache = {}
if cache_file and os.path.isfile(cache_file):
    try:
        with open(cache_file) as f:
            cache = json.load(f)
    except (json.JSONDecodeError, IOError):
        cache = {}

cache_key = KEYWORD.lower().strip()
cached_entry = cache.get("queries", {}).get(cache_key)
if cached_entry:
    fetched_at = datetime.fromisoformat(cached_entry["fetched_at"].replace("Z", "+00:00"))
    age_hours = (datetime.now(timezone.utc) - fetched_at).total_seconds() / 3600
    if age_hours < 24:
        results = cached_entry["results"]
        from_cache = True
    else:
        results = None
        from_cache = False
else:
    results = None
    from_cache = False

if results is None:
    # --- Search GitHub ---
    all_repos = {}

    # Query 1: repo search with keyword + claude + skill
    q = urllib.parse.quote(f"{KEYWORD} claude skill")
    url = f"https://api.github.com/search/repositories?q={q}+in:name,description,readme&sort=stars&per_page={LIMIT}"
    data = github_api(url, GITHUB_TOKEN)
    if data and "items" in data:
        for item in data["items"]:
            fn = item["full_name"]
            if fn not in all_repos:
                all_repos[fn] = item

    # Query 2: topic-based search
    q2 = urllib.parse.quote(f"topic:claude-code {KEYWORD}")
    url2 = f"https://api.github.com/search/repositories?q={q2}&sort=stars&per_page={LIMIT}"
    data2 = github_api(url2, GITHUB_TOKEN)
    if data2 and "items" in data2:
        for item in data2["items"]:
            fn = item["full_name"]
            if fn not in all_repos:
                all_repos[fn] = item

    # Query 3: broader search for claude-code plugins/skills
    q3 = urllib.parse.quote(f"{KEYWORD} claude-code")
    url3 = f"https://api.github.com/search/repositories?q={q3}+in:name,description,readme&sort=stars&per_page={LIMIT}"
    data3 = github_api(url3, GITHUB_TOKEN)
    if data3 and "items" in data3:
        for item in data3["items"]:
            fn = item["full_name"]
            if fn not in all_repos:
                all_repos[fn] = item

    # Build results — with a relevance gate. GitHub's search matches loosely
    # ("n8n claude skill" happily returns firecrawl), and a plain stars sort
    # lets mega-repos crowd out actual skills. Require a skill signal in the
    # repo metadata, then rank by (relevance, stars).
    SKILL_TOPICS = {"claude-code-skills", "agent-skills", "claude-skills",
                    "claude-code-plugin", "claude-code", "skills"}

    def relevance(item):
        name = (item.get("name") or "").lower()
        desc = (item.get("description") or "").lower()
        topics = set(t.lower() for t in item.get("topics", []))
        score = 0
        if topics & SKILL_TOPICS:
            score += 3
        if "skill" in name:
            score += 2
        if "skill" in desc:
            score += 1
        if "claude" in name or "claude" in desc or "claude-code" in " ".join(topics):
            score += 1
        return score

    results = []
    for fn, item in all_repos.items():
        rel = relevance(item)
        if rel == 0:
            continue  # no skill signal at all — noise from the loose search
        results.append({
            "full_name": fn,
            "name": item.get("name", ""),
            "description": (item.get("description") or "")[:200],
            "stars": item.get("stargazers_count", 0),
            "forks": item.get("forks_count", 0),
            "updated_at": (item.get("pushed_at") or item.get("updated_at", ""))[:10],
            "topics": item.get("topics", []),
            "url": item.get("html_url", ""),
            "language": item.get("language", ""),
            "relevance": rel,
        })

    # Rank by relevance first, stars second
    results.sort(key=lambda x: (-x["relevance"], -x["stars"]))
    results = results[:LIMIT]
    from_cache = False

    # --- Save to cache ---
    if cache_file:
        if "queries" not in cache:
            cache["queries"] = {}
        cache["queries"][cache_key] = {
            "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "results": results
        }
        cache["version"] = 1
        with open(cache_file, "w") as f:
            json.dump(cache, f, indent=2)

# --- Cross-reference with installed skills ---
installed_skills = set()
# Check Claude Code skills
if USER_SKILLS and os.path.isdir(USER_SKILLS):
    for name in os.listdir(USER_SKILLS):
        if os.path.isdir(os.path.join(USER_SKILLS, name)):
            installed_skills.add(name.lower())
# Check Codex skills
codex_skills = os.path.expanduser("~/.agents/skills")
if os.path.isdir(codex_skills):
    for name in os.listdir(codex_skills):
        if os.path.isdir(os.path.join(codex_skills, name)):
            installed_skills.add(name.lower())

# Also check installed plugins
plugins_file = os.path.expanduser("~/.claude/plugins/installed_plugins.json")
installed_plugins = set()
if os.path.isfile(plugins_file):
    try:
        with open(plugins_file) as f:
            data = json.load(f)
            # v2 format: {"plugins": {"name@source": [...]}}
            if isinstance(data, dict) and "plugins" in data:
                for key in data["plugins"]:
                    plugin_name = key.split("@")[0].lower()
                    installed_plugins.add(plugin_name)
            # v1 format: [{"name": "...", ...}]
            elif isinstance(data, list):
                for p in data:
                    if isinstance(p, dict):
                        installed_plugins.add(p.get("name", "").lower())
    except (json.JSONDecodeError, IOError):
        pass

for r in results:
    name_lower = r["name"].lower()
    if name_lower in installed_skills or name_lower in installed_plugins:
        r["status"] = "INSTALLED"
    else:
        r["status"] = "AVAILABLE"

# --- Output ---
if JSON_OUTPUT:
    output = {
        "keyword": KEYWORD,
        "total_results": len(results),
        "from_cache": from_cache,
        "auth_level": "authenticated" if GITHUB_TOKEN else "unauthenticated",
        "results": results,
    }
    print(json.dumps(output, indent=2))
else:
    cache_note = " (cached)" if from_cache else ""
    auth_note = "" if GITHUB_TOKEN else " (unauthenticated - set GITHUB_TOKEN for better results)"

    print(f"=== Skills Janitor - Skill Discovery ===")
    print(f'Search: "{KEYWORD}"{cache_note}{auth_note}')
    print()

    if not results:
        print("No results found.")
    else:
        installed_count = sum(1 for r in results if r["status"] == "INSTALLED")
        available_count = len(results) - installed_count

        print(f"  {'#':<3} {'Repository':<40} {'Stars':>6} {'Updated':<12} {'Status':<10}")
        print(f"  {'─'*3} {'─'*40} {'─'*6} {'─'*12} {'─'*10}")
        for i, r in enumerate(results, 1):
            print(f"  {i:<3} {r['full_name']:<40} {r['stars']:>6} {r['updated_at']:<12} {r['status']:<10}")

        print()
        print(f"Total: {len(results)} results ({installed_count} installed, {available_count} available)")

        if not GITHUB_TOKEN:
            print()
            print("Tip: Set GITHUB_TOKEN env var for better search results and higher rate limits")

PYEOF
