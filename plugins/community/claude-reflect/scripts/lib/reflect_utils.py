#!/usr/bin/env python3
"""Shared utilities for claude-reflect hooks and scripts.

Cross-platform compatible (Windows, macOS, Linux).
"""
import json
import re
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

# =============================================================================
# Path utilities
# =============================================================================

def get_queue_path(project_dir: Optional[str] = None) -> Path:
    """Get path to learnings queue file, scoped to the current project.

    Queue files are stored per-project to prevent cross-project leakage:
      ~/.claude/projects/<encoded>/learnings-queue.json

    Falls back to global path if project directory cannot be determined.
    """
    try:
        folder_name = get_project_folder_name(project_dir)
        return get_claude_dir() / "projects" / folder_name / "learnings-queue.json"
    except Exception:
        # Fallback to global path if encoding fails
        return Path.home() / ".claude" / "learnings-queue.json"


def get_global_queue_path() -> Path:
    """Get path to the legacy global learnings queue file.

    Used for migration: items from the old global queue are distributed
    to their per-project queues on first access.
    """
    return Path.home() / ".claude" / "learnings-queue.json"


def migrate_global_queue() -> None:
    """Migrate items from the legacy global queue to per-project queues.

    Each queue item has a 'project' field with the original cwd.
    Items are distributed to their respective project queues, then
    the global queue is cleared.
    """
    global_path = get_global_queue_path()
    if not global_path.exists():
        return

    try:
        items = json.loads(global_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, IOError):
        return

    if not items:
        # Empty global queue — remove file so future calls skip immediately
        global_path.unlink(missing_ok=True)
        return

    # Group items by project
    by_project: Dict[str, List[Dict[str, Any]]] = {}
    for item in items:
        project = item.get("project", "")
        if project not in by_project:
            by_project[project] = []
        by_project[project].append(item)

    # Write each group to its project queue
    for project, project_items in by_project.items():
        if not project:
            continue
        try:
            project_queue_path = get_queue_path(project)
            # Merge with any existing project queue
            existing = []
            if project_queue_path.exists():
                try:
                    existing = json.loads(
                        project_queue_path.read_text(encoding="utf-8")
                    )
                except (json.JSONDecodeError, IOError):
                    existing = []
            existing.extend(project_items)
            project_queue_path.parent.mkdir(parents=True, exist_ok=True)
            project_queue_path.write_text(
                json.dumps(existing, indent=2), encoding="utf-8"
            )
        except Exception:
            continue

    # Remove global queue after successful migration so future calls skip via exists() check
    global_path.unlink(missing_ok=True)


def get_backup_dir() -> Path:
    """Get path to learnings backup directory."""
    return Path.home() / ".claude" / "learnings-backups"


def get_claude_dir() -> Path:
    """Get path to .claude directory."""
    return Path.home() / ".claude"


def get_cleanup_period_days() -> Optional[int]:
    """Get cleanupPeriodDays from ~/.claude/settings.json. Returns None if not set."""
    settings_path = get_claude_dir() / "settings.json"
    if not settings_path.exists():
        return None
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        return settings.get("cleanupPeriodDays")
    except (json.JSONDecodeError, IOError):
        return None


# Directories to exclude when searching for CLAUDE.md files
EXCLUDED_DIRS = {
    'node_modules', '.git', '.svn', '.hg', 'venv', '.venv', 'env', '.env',
    '__pycache__', '.pytest_cache', '.mypy_cache', 'dist', 'build',
    '.next', '.nuxt', 'coverage', '.coverage', 'htmlcov',
    'vendor', 'target', 'out', 'bin', 'obj',
}


def _parse_rule_frontmatter(filepath: Path) -> Optional[Dict[str, Any]]:
    """Parse YAML-like frontmatter from a .claude/rules/*.md file.

    Extracts 'paths:' list without requiring PyYAML. Frontmatter is delimited
    by '---' lines at the start of the file.

    Returns:
        Dict with parsed fields (e.g. {"paths": ["src/", "lib/"]}), or None
        if no frontmatter is found.
    """
    try:
        text = filepath.read_text(encoding="utf-8")
    except (IOError, OSError):
        return None

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None

    # Find closing ---
    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        return None

    result: Dict[str, Any] = {}
    current_key = None
    current_list: List[str] = []

    for line in lines[1:end_idx]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Check for "key: value" or "key:" (start of list)
        if ":" in stripped and not stripped.startswith("-"):
            # Save previous list if any
            if current_key and current_list:
                result[current_key] = current_list
                current_list = []

            key, _, value = stripped.partition(":")
            current_key = key.strip()
            value = value.strip()
            if value:
                result[current_key] = value
                current_key = None
        elif stripped.startswith("- ") and current_key:
            current_list.append(stripped[2:].strip().strip('"').strip("'"))

    # Save final list
    if current_key and current_list:
        result[current_key] = current_list

    return result if result else None


def find_claude_files(root_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Find all memory tier files in the project tree.

    Args:
        root_dir: Root directory to search from (defaults to cwd)

    Returns:
        List of dicts with {path, relative_path, type, ...} for each file found.
        Types: 'global', 'root', 'local', 'subdirectory', 'rule', 'user-rule'.
        Rule files include a 'frontmatter' field with parsed YAML frontmatter.
    """
    root = Path(root_dir) if root_dir else Path.cwd()
    results = []

    # Always include global CLAUDE.md
    global_claude = get_claude_dir() / "CLAUDE.md"
    if global_claude.exists():
        results.append({
            "path": str(global_claude),
            "relative_path": "~/.claude/CLAUDE.md",
            "type": "global",
        })

    # Check root CLAUDE.md
    root_claude = root / "CLAUDE.md"
    if root_claude.exists():
        results.append({
            "path": str(root_claude),
            "relative_path": "./CLAUDE.md",
            "type": "root",
        })

    # Check CLAUDE.local.md (personal, gitignored)
    local_claude = root / "CLAUDE.local.md"
    if local_claude.exists():
        results.append({
            "path": str(local_claude),
            "relative_path": "./CLAUDE.local.md",
            "type": "local",
        })

    # Search for CLAUDE.md in subdirectories
    for dirpath, dirnames, filenames in os.walk(root):
        # Skip excluded directories
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]

        # Skip root (already handled)
        if Path(dirpath) == root:
            continue

        if "CLAUDE.md" in filenames:
            full_path = Path(dirpath) / "CLAUDE.md"
            rel_path = full_path.relative_to(root)
            # Use as_posix() for consistent forward slashes on all platforms
            results.append({
                "path": str(full_path),
                "relative_path": f"./{rel_path.as_posix()}",
                "type": "subdirectory",
            })

    # Discover project rule files: .claude/rules/*.md
    project_rules_dir = root / ".claude" / "rules"
    if project_rules_dir.is_dir():
        for rule_file in sorted(project_rules_dir.glob("*.md")):
            frontmatter = _parse_rule_frontmatter(rule_file)
            rel_path = rule_file.relative_to(root)
            results.append({
                "path": str(rule_file),
                "relative_path": f"./{rel_path.as_posix()}",
                "type": "rule",
                "frontmatter": frontmatter,
            })

    # Discover user-level rule files: ~/.claude/rules/*.md
    user_rules_dir = get_claude_dir() / "rules"
    if user_rules_dir.is_dir():
        for rule_file in sorted(user_rules_dir.glob("*.md")):
            frontmatter = _parse_rule_frontmatter(rule_file)
            results.append({
                "path": str(rule_file),
                "relative_path": f"~/.claude/rules/{rule_file.name}",
                "type": "user-rule",
                "frontmatter": frontmatter,
            })

    return results


def suggest_claude_file(
    learning: str,
    claude_files: List[Dict[str, Any]],
    learning_type: Optional[str] = None,
) -> Optional[str]:
    """
    Suggest which memory file a learning should go to.

    This is a hint for Claude to use when reasoning about placement.
    Returns the relative_path of the suggested file, or None to let Claude decide.

    Args:
        learning: The learning text.
        claude_files: List from find_claude_files().
        learning_type: Optional type hint — 'guardrail', 'auto', 'explicit', etc.
    """
    learning_lower = learning.lower()

    # Guardrails → .claude/rules/guardrails.md
    if learning_type == "guardrail":
        # Check if a guardrails rule file already exists
        for cf in claude_files:
            if cf["type"] == "rule" and "guardrail" in Path(cf["path"]).stem.lower():
                return cf["relative_path"]
        # Suggest creating one
        return "./.claude/rules/guardrails.md"

    # Model indicators → existing model-preferences rule or global CLAUDE.md
    model_indicators = ['gpt-', 'claude-', 'gemini-', 'o3', 'o4']
    if any(ind in learning_lower for ind in model_indicators):
        for cf in claude_files:
            if cf["type"] in ("rule", "user-rule") and "model" in Path(cf["path"]).stem.lower():
                return cf["relative_path"]
        return "~/.claude/CLAUDE.md"

    # Global behavioral (always/never/prefer) → global CLAUDE.md
    global_behavioral = ['always ', 'never ', 'prefer ']
    if any(ind in learning_lower for ind in global_behavioral):
        return "~/.claude/CLAUDE.md"

    # Path-scoped rule match: learning mentions a directory covered by a rule's paths
    for cf in claude_files:
        if cf["type"] == "rule" and cf.get("frontmatter"):
            paths = cf["frontmatter"].get("paths", [])
            if isinstance(paths, list):
                for p in paths:
                    if p.lower().rstrip("/") in learning_lower:
                        return cf["relative_path"]

    # Check if learning mentions a specific subdirectory
    for cf in claude_files:
        if cf["type"] == "subdirectory":
            # Extract directory name from path
            dir_name = Path(cf["relative_path"]).parent.name.lower()
            if dir_name in learning_lower:
                return cf["relative_path"]

    # Default: let Claude decide (return None)
    return None


# =============================================================================
# Auto memory utilities
# =============================================================================

def get_project_folder_name(project_dir: Optional[str] = None) -> str:
    """Encode a project directory path using Claude Code's folder naming convention.

    /Users/bob/myapp → -Users-bob-myapp
    """
    project_path = Path(project_dir).resolve() if project_dir else Path.cwd().resolve()
    folder_name = str(project_path).replace("/", "-").replace("\\", "-")
    if folder_name.startswith("-"):
        folder_name = folder_name[1:]
    return "-" + folder_name


def get_auto_memory_path(project_dir: Optional[str] = None) -> Path:
    """Get the auto memory directory path for a project.

    Returns ~/.claude/projects/<encoded>/memory/
    """
    folder_name = get_project_folder_name(project_dir)
    return get_claude_dir() / "projects" / folder_name / "memory"


def read_auto_memory(project_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """Read all .md files from the project's auto memory directory.

    Returns list of {file, name, entries} where entries are non-empty lines.
    """
    memory_path = get_auto_memory_path(project_dir)
    results = []

    if not memory_path.is_dir():
        return results

    for md_file in sorted(memory_path.glob("*.md")):
        try:
            text = md_file.read_text(encoding="utf-8")
            entries = [line.strip() for line in text.splitlines() if line.strip()]
            results.append({
                "file": str(md_file),
                "name": md_file.stem,
                "entries": entries,
            })
        except (IOError, OSError):
            continue

    return results


# Topic keywords for auto memory file naming
_AUTO_MEMORY_TOPICS = {
    "model-preferences": ["gpt-", "claude-", "gemini-", "o3", "o4", "model", "llm"],
    "tool-usage": ["mcp", "tool", "plugin", "api", "endpoint"],
    "coding-style": ["indent", "format", "style", "naming", "convention", "lint"],
    "environment": ["venv", "env", "docker", "port", "database", "redis", "postgres"],
    "workflow": ["commit", "deploy", "test", "build", "ci", "cd", "pipeline"],
    "debugging": ["debug", "error", "log", "trace", "breakpoint"],
}


def suggest_auto_memory_topic(learning: str) -> str:
    """Suggest a topic filename for an auto memory entry based on keywords.

    Returns a filename stem like 'model-preferences' or 'general'.
    """
    learning_lower = learning.lower()
    best_topic = "general"
    best_score = 0

    for topic, keywords in _AUTO_MEMORY_TOPICS.items():
        score = sum(1 for kw in keywords if kw in learning_lower)
        if score > best_score:
            best_score = score
            best_topic = topic

    return best_topic


def read_all_memory_entries(
    root_dir: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Read bullet-point entries from ALL memory tiers for cross-tier deduplication.

    Scans: CLAUDE.md files, rule files, CLAUDE.local.md, and auto memory.

    Returns list of {text, source_file, source_type, line_number}.
    """
    claude_files = find_claude_files(root_dir)
    entries: List[Dict[str, Any]] = []

    # Read entries from each CLAUDE.md / rule / local file
    for cf in claude_files:
        filepath = Path(cf["path"])
        if cf["type"] == "global":
            filepath = Path(cf["path"])
        try:
            text = filepath.read_text(encoding="utf-8")
        except (IOError, OSError):
            continue

        for line_num, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("- "):
                entries.append({
                    "text": stripped[2:].strip(),
                    "source_file": cf["relative_path"],
                    "source_type": cf["type"],
                    "line_number": line_num,
                })

    # Read auto memory entries
    auto_memory = read_auto_memory(root_dir)
    for mem in auto_memory:
        for idx, entry_text in enumerate(mem["entries"]):
            clean = entry_text.lstrip("- ").strip()
            if clean and not clean.startswith("#"):
                entries.append({
                    "text": clean,
                    "source_file": f"~/.claude/projects/.../memory/{mem['name']}.md",
                    "source_type": "auto-memory",
                    "line_number": idx + 1,
                })

    return entries


# =============================================================================
# Queue operations
# =============================================================================

def load_queue(project_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """Load learnings queue from the project-scoped file.

    On first call, migrates any items from the legacy global queue.
    """
    # Migrate legacy global queue if it has items
    migrate_global_queue()

    path = get_queue_path(project_dir)
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, IOError):
        return []


def save_queue(items: List[Dict[str, Any]], project_dir: Optional[str] = None) -> None:
    """Save learnings queue to the project-scoped file."""
    path = get_queue_path(project_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(items, indent=2), encoding="utf-8")


def append_to_queue(item: Dict[str, Any], project_dir: Optional[str] = None) -> None:
    """Append a single item to the project-scoped queue."""
    items = load_queue(project_dir)
    items.append(item)
    save_queue(items, project_dir)


# =============================================================================
# Timestamp utilities
# =============================================================================

def iso_timestamp() -> str:
    """Get current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def backup_timestamp() -> str:
    """Get timestamp for backup filenames."""
    return datetime.now().strftime("%Y%m%d-%H%M%S")


# =============================================================================
# Pattern definitions (from capture-learning.sh)
# =============================================================================

# Explicit marker patterns (highest confidence)
EXPLICIT_PATTERNS = [
    (r"remember:", "remember:", 0.90, 120),  # pattern, name, confidence, decay_days
]

# Positive feedback patterns
POSITIVE_PATTERNS = [
    (r"perfect!|exactly right|that's exactly", "perfect", 0.70, 90),
    (r"that's what I wanted|great approach", "great-approach", 0.70, 90),
    (r"keep doing this|love it|excellent|nailed it", "keep-doing", 0.70, 90),
]

# Correction patterns (conservative set to minimize false positives)
# Format: (regex_pattern, pattern_name, is_strong)
#
# DESIGN NOTES:
# - These patterns are English-centric as a FAST first-pass filter
# - Non-English corrections are caught by semantic filtering during /reflect
# - We use STRUCTURAL signals (length, questions, task requests) for language-agnostic filtering
# - Users can use explicit markers like "remember:" in any language
#
CORRECTION_PATTERNS = [
    (r"^no[,. ]+", "no,", True),  # Starts with "no," - common correction opener
    (r"^don't\b|^do not\b", "don't", True),  # Starts with don't/do not
    (r"^stop\b|^never\b", "stop/never", True),  # Starts with stop/never
    (r"that's (wrong|incorrect)|that is (wrong|incorrect)", "that's-wrong", True),
    (r"^actually[,. ]", "actually", False),  # Starts with "actually"
    (r"^I meant\b|^I said\b", "I-meant/said", True),  # Clarification
    (r"^I told you\b|^I already told\b", "I-told-you", True),  # Higher confidence
    (r"use .{1,30} not\b", "use-X-not-Y", True),  # "use X not Y" - limited gap
]

# Guardrail patterns - "don't do X unless" constraints (highest confidence for corrections)
# These detect user frustrations about Claude making unwanted changes
# Format: (regex_pattern, pattern_name, confidence, decay_days)
GUARDRAIL_PATTERNS = [
    (r"don't (?:add|include|create) .{1,40} unless", "dont-unless-asked", 0.90, 120),
    (r"only (?:change|modify|edit|touch) what I (?:asked|requested|said)", "only-what-asked", 0.90, 120),
    (r"stop (?:refactoring|changing|modifying|editing) (?:unrelated|other|surrounding)", "stop-unrelated", 0.90, 120),
    (r"don't (?:over-engineer|add extra|be too|make unnecessary)", "dont-over-engineer", 0.85, 90),
    (r"don't (?:refactor|reorganize|restructure) (?:unless|without)", "dont-refactor-unless", 0.85, 90),
    (r"leave .{1,30} (?:alone|unchanged|as is)", "leave-alone", 0.85, 90),
    (r"don't (?:add|include) (?:comments|docstrings|type hints|annotations) (?:unless|to code)", "dont-add-annotations", 0.85, 90),
    (r"(?:minimal|minimum|only necessary) changes", "minimal-changes", 0.80, 90),
]

# Structural patterns indicating FALSE POSITIVES (language-agnostic)
# These focus on MESSAGE STRUCTURE rather than specific words
FALSE_POSITIVE_PATTERNS = [
    r"[?\uff1f]$",  # Ends with question mark (ASCII ? or full-width ？)
    r"[\u55ce\u5417\u5462\u304b\uae4c]$",  # Ends with CJK question particle (嗎吗呢か까)
    r"^(please|can you|could you|would you|help me)\b",  # Task request openers
    r"(help|fix|check|review|figure out|set up)\s+(this|that|it|the)\b",  # Task verbs
    r"(error|failed|could not|cannot|can't|unable to)\s+\w+",  # Error descriptions
    r"(is|was|are|were)\s+(not|broken|failing)",  # Bug reports
    r"^I (need|want|would like)\b",  # Task requests
    r"^(ok|okay|alright)[,.]?\s+(so|now|let)",  # Task continuations
]

# English phrases that look like correction openers but are NOT corrections
# Especially important for CJK-mixed text where these appear naturally
NON_CORRECTION_PHRASES = [
    r"^no\s+problem",        # "No problem" - agreement
    r"^no\s+worries",        # "No worries" - agreement
    r"^no\s+need\b",         # "No need" - acknowledgment
    r"^no\s+way\b",          # "No way!" - surprise/exclamation
    r"^don't\s+worry",       # "Don't worry" - reassurance
    r"^don't\s+mind",        # "Don't mind" - agreement
    r"^don't\s+bother",      # "Don't bother" - polite decline
    r"^never\s+mind",        # "Never mind" - dismissal
    r"^stop\s+worrying",     # "Stop worrying" - reassurance
]

# CJK correction patterns (parallel to English CORRECTION_PATTERNS)
# These detect explicit corrections in CJK languages
# Format: (regex_pattern, pattern_name, is_strong)
CJK_CORRECTION_PATTERNS = [
    # Japanese
    (r"^いや[、,.\s]|^いや違", "iya", True),       # いや、〜 / いや違う - "no, ..."
    (r"^違う[、，,.\s！!。]|^ちがう[、,.\s]", "chigau", True),  # 違う、〜 - "wrong, ..."
    (r"そうじゃなく[てけ]|そっちじゃなく[てけ]", "souja-nakute", True),  # "not that"
    (r"間違[いえっ]て", "machigatte", True),       # 間違ってる - "it's wrong"
    (r"じゃなくて.{0,30}にして", "janakute-nishite", True),  # 〜じゃなくて〜にして
    (r"^やめて[。！!]?\s*$", "yamete", True),      # やめて - "stop"
    (r"^そうじゃない", "souja-nai", True),          # そうじゃない - "that's not right"
    (r"って言った[のよでじゃ]", "tte-itta", True),   # って言ったのに - "I told you"
    # Chinese
    (r"^不是[，,. ]", "bushi", True),              # 不是、〜 - "no, ..."
    (r"^错了|^錯了", "cuole", True),               # 错了 - "wrong"
    (r"不要.{0,20}要", "buyao-yao", True),         # 不要X要Y - "don't X, use Y"
    # Korean
    (r"^아니[,. ]", "ani", True),                  # 아니, - "no, ..."
    (r"틀렸", "teullyeoss", True),                 # 틀렸 - "wrong"
]

# Maximum prompt length for live capture (UserPromptSubmit hook)
# Prompts longer than this are almost certainly system content, not user corrections.
# Exception: explicit "remember:" markers are always processed regardless of length.
MAX_CAPTURE_PROMPT_LENGTH = 500

# Maximum message length for weak patterns (structural heuristic)
# Long messages are more likely to be context/tasks than corrections
MAX_WEAK_PATTERN_LENGTH = 150

# Very short messages without question marks are more likely corrections
MIN_SHORT_CORRECTION_LENGTH = 80


def detect_patterns(text: str) -> Tuple[Optional[str], str, float, str, int]:
    """
    Detect patterns in text and return classification.

    Returns:
        Tuple of (type, matched_patterns, confidence, sentiment, decay_days)
        type: "explicit", "positive", "auto", "guardrail", or None
        matched_patterns: Space-separated pattern names
        confidence: 0.0 to 1.0
        sentiment: "correction" or "positive"
        decay_days: Number of days until decay
    """
    # Too short to be actionable (e.g. "OK", "好", "yes")
    # CJK characters carry more meaning per char, so use a lower threshold
    stripped = text.strip()
    has_cjk = bool(re.search(r'[\u3000-\u9fff\uf900-\ufaff\uac00-\ud7af]', stripped))
    short_threshold = 2 if has_cjk else 4
    if len(stripped) <= short_threshold:
        return (None, "", 0.0, "correction", 90)

    # Check for explicit "remember:" - always highest priority
    for pattern, name, confidence, decay in EXPLICIT_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return ("explicit", name, confidence, "correction", decay)

    # Check for guardrail patterns - "don't do X unless" constraints
    # These are high-confidence corrections about unwanted behavior
    for pattern, name, confidence, decay in GUARDRAIL_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return ("guardrail", name, confidence, "correction", decay)

    # Check for FALSE POSITIVE patterns - skip these messages
    for fp_pattern in FALSE_POSITIVE_PATTERNS:
        if re.search(fp_pattern, text, re.IGNORECASE):
            return (None, "", 0.0, "correction", 90)

    # Check for non-correction English phrases (before correction patterns)
    # Prevents "No problem", "Don't worry" etc. from being caught as corrections
    for nc_pattern in NON_CORRECTION_PHRASES:
        if re.search(nc_pattern, text, re.IGNORECASE):
            return (None, "", 0.0, "correction", 90)

    # Check for positive patterns
    matched_positive = []
    for pattern, name, confidence, decay in POSITIVE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            matched_positive.append(name)

    if matched_positive:
        return ("positive", " ".join(matched_positive), 0.70, "positive", 90)

    # Skip long messages for weak patterns (likely task requests)
    text_length = len(text)

    # Check for CJK correction patterns (language-specific)
    # Use stripped text for anchor patterns (^/$) to handle leading/trailing whitespace
    matched_cjk = []
    cjk_strong = False
    for pattern, name, is_strong in CJK_CORRECTION_PATTERNS:
        if re.search(pattern, stripped):
            matched_cjk.append(name)
            if is_strong:
                cjk_strong = True

    if matched_cjk:
        confidence = 0.75 if cjk_strong else 0.60
        decay_days = 90 if cjk_strong else 60
        if text_length < MIN_SHORT_CORRECTION_LENGTH:
            confidence = min(0.90, confidence + 0.10)
        elif text_length > 300:
            confidence = max(0.50, confidence - 0.15)
        return ("auto", " ".join(matched_cjk), confidence, "correction", decay_days)

    # Check for English correction patterns
    matched_corrections = []
    pattern_count = 0
    has_strong_pattern = False
    has_i_told_you = False

    for pattern, name, is_strong in CORRECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            # Skip weak patterns in long messages
            if not is_strong and text_length > MAX_WEAK_PATTERN_LENGTH:
                continue
            matched_corrections.append(name)
            pattern_count += 1
            if is_strong:
                has_strong_pattern = True
            if name == "I-told-you":
                has_i_told_you = True

    if matched_corrections:
        # Calculate confidence based on pattern count, type, and length
        if has_i_told_you:
            confidence = 0.85
            decay_days = 120
        elif pattern_count >= 3:
            confidence = 0.85
            decay_days = 120
        elif pattern_count >= 2:
            confidence = 0.75
            decay_days = 90
        elif has_strong_pattern:
            confidence = 0.70
            decay_days = 60
        else:
            confidence = 0.55  # Reduced for weak single patterns
            decay_days = 45

        # Adjust confidence based on message length (structural signal)
        # Short messages are more likely to be direct corrections
        if text_length < MIN_SHORT_CORRECTION_LENGTH:
            confidence = min(0.90, confidence + 0.10)  # Boost for short messages
        elif text_length > 300:
            confidence = max(0.50, confidence - 0.15)  # Reduce for long messages
        elif text_length > 150:
            confidence = max(0.55, confidence - 0.10)

        return ("auto", " ".join(matched_corrections), confidence, "correction", decay_days)

    return (None, "", 0.0, "correction", 90)


def create_queue_item(
    message: str,
    item_type: str,
    patterns: str,
    confidence: float,
    sentiment: str,
    decay_days: int,
    project: Optional[str] = None
) -> Dict[str, Any]:
    """Create a properly formatted queue item."""
    return {
        "type": item_type,
        "message": message,
        "timestamp": iso_timestamp(),
        "project": project or os.getcwd(),
        "patterns": patterns,
        "confidence": confidence,
        "sentiment": sentiment,
        "decay_days": decay_days,
    }


# =============================================================================
# Session file utilities
# =============================================================================

def extract_user_messages(session_file: Path, corrections_only: bool = False) -> List[str]:
    """
    Extract user messages from a Claude Code session file (JSONL format).

    Args:
        session_file: Path to the session JSONL file
        corrections_only: If True, only return messages matching correction patterns

    Returns:
        List of user message texts
    """
    if not session_file.exists():
        return []

    messages = []

    try:
        with open(session_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # Filter: type=user, not isMeta
                if entry.get("type") != "user":
                    continue
                if entry.get("isMeta"):
                    continue

                # Extract text from content (can be string or list)
                content = entry.get("message", {}).get("content", [])

                # Handle string content directly
                if isinstance(content, str):
                    if content and _should_include_message(content):
                        messages.append(content)
                # Handle list of content items
                elif isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            text = item.get("text", "")
                            if text:
                                # Apply filters (same as bash script)
                                if _should_include_message(text):
                                    messages.append(text)
    except IOError:
        return []

    if corrections_only:
        # Filter for correction patterns
        correction_pattern = (
            r"(no,? use|don't use|stop using|never use|that's wrong|that's incorrect|"
            r"not right|not correct|actually[,. ]|I meant|I said|I told you|"
            r"I already told|you should use|you need to use|use .+ not|not .+, use|remember:)"
        )
        messages = [m for m in messages if re.search(correction_pattern, m, re.IGNORECASE)]

    return messages


def should_include_message(text: str) -> bool:
    """Check if a message should be included in learning detection.

    Filters out system content like XML tags, JSON, tool results, and
    session continuations that should never be treated as user corrections.

    Used by both session file extraction and live capture (UserPromptSubmit hook).
    """
    # Skip empty lines
    if not text.strip():
        return False

    # Skip lines starting with certain patterns
    skip_patterns = [
        r"^<",              # XML tags (<task-notification>, <system-reminder>, etc.)
        r"^\[",             # Brackets
        r"^\{",             # JSON
        r"tool_result",
        r"tool_use_id",
        r"<command-",
        r"<task-notification>",
        r"<system-reminder>",
        r"This session is being continued",
        r"^Analysis:",
        r"^\*\*",           # Bold text
        r"^   -",           # Indented lists
    ]

    for pattern in skip_patterns:
        if re.search(pattern, text):
            return False

    return True


# Backward-compatible alias
_should_include_message = should_include_message


def extract_tool_rejections(session_file: Path) -> List[str]:
    """
    Extract user corrections from tool rejections in session files.

    Matches the behavior of the legacy bash script which looks for:
    - type == "user" entries
    - message.content[] array with type == "tool_result"
    - is_error == true
    - content containing "The user doesn't want to proceed"

    Args:
        session_file: Path to the session JSONL file

    Returns:
        List of user correction texts from tool rejections
    """
    if not session_file.exists():
        return []

    rejections = []

    try:
        with open(session_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # Must be a user entry (matches bash: select(.type=="user"))
                if entry.get("type") != "user":
                    continue

                # Get message.content array (matches bash: select(.message.content | type == "array"))
                content = entry.get("message", {}).get("content", [])
                if not isinstance(content, list):
                    continue

                # Look for tool_result items in content array
                for item in content:
                    if not isinstance(item, dict):
                        continue

                    # Must be type == "tool_result" (matches bash: select(.type=="tool_result"))
                    if item.get("type") != "tool_result":
                        continue

                    # Must have is_error == true (matches bash: select(.is_error==true))
                    if not item.get("is_error"):
                        continue

                    # Get the content string
                    tool_content = item.get("content", "")
                    if not isinstance(tool_content, str):
                        continue

                    # Must contain rejection message (matches bash: select(.content | contains(...)))
                    if "The user doesn't want to proceed" not in tool_content:
                        continue

                    # Extract text after "the user said:" (matches bash: awk '/the user said:/{getline; print}')
                    # Note: bash uses lowercase "the user said:", let's be case-insensitive
                    lower_content = tool_content.lower()
                    if "the user said:" in lower_content:
                        # Find the position case-insensitively
                        idx = lower_content.find("the user said:")
                        after_marker = tool_content[idx + len("the user said:"):]
                        # Get the next line (bash uses getline)
                        lines = after_marker.strip().split("\n")
                        if lines and lines[0].strip():
                            rejections.append(lines[0].strip())

    except IOError:
        return []

    return rejections


# =============================================================================
# Tool execution error patterns
# =============================================================================

# EXCLUDE: Claude Code guardrails AND global Claude behavior (not project-specific)
TOOL_ERROR_EXCLUDE_PATTERNS = [
    # Claude Code guardrails - system enforcing its rules
    r"File has not been read yet",
    r"exceeds maximum allowed tokens",
    r"InputValidationError",
    r"not valid JSON",
    r"The user doesn't want to proceed",  # User rejections handled separately
    # Global Claude behavior issues - not project-specific
    r"unexpected EOF while looking for matching",  # Bash quoting
    r"EISDIR|illegal operation on a directory",    # File vs dir confusion
    r"syntax error.*eval",                          # Bash syntax errors
]

# PROJECT-SPECIFIC error patterns that reveal env/config/structure issues
# Format: (error_type, regex_pattern, suggested_guideline_template)
PROJECT_SPECIFIC_ERROR_PATTERNS = [
    # Connection/service errors - often reveal env/config issues
    ("connection_refused",
     r"Connection refused|ECONNREFUSED|connect ECONNREFUSED",
     "Check .env for service URLs - don't assume localhost"),
    ("env_undefined",
     r"(\w+_URL|DATABASE_URL|API_KEY|SECRET).*undefined|not set|is not defined",
     "Load .env file before accessing environment variables"),
    # Database-specific errors
    ("supabase_error",
     r"supabase|Supabase|SUPABASE",
     "Check SUPABASE_URL and SUPABASE_KEY in .env"),
    ("postgres_error",
     r"postgres|PostgreSQL|PGHOST|:5432|password authentication failed",
     "Check DATABASE_URL in .env for PostgreSQL connection"),
    ("redis_error",
     r"redis|REDIS|:6379",
     "Check REDIS_URL in .env for Redis connection"),
    # Path/module errors - reveal project structure
    ("module_not_found",
     r"ModuleNotFoundError|Cannot find module|No module named",
     "Check import paths - verify project structure"),
    ("venv_not_found",
     r"venv.*No such file|activate: No such file|\.venv.*not found",
     "Check virtual environment location"),
    # Port/service conflicts
    ("port_in_use",
     r"address already in use|EADDRINUSE|port.*already.*use",
     "Check if service is already running on this port"),
]


def extract_tool_errors(
    session_file: Path,
    project_specific_only: bool = True
) -> List[Dict[str, Any]]:
    """
    Extract tool execution errors from session files.

    Unlike extract_tool_rejections(), this captures TECHNICAL errors where:
    - is_error == true
    - NOT a user rejection (no "doesn't want to proceed")
    - Optionally filtered for project-specific patterns only

    Args:
        session_file: Path to the session JSONL file
        project_specific_only: If True, only return errors matching project-specific patterns

    Returns:
        List of dicts with {error_type, content, project, timestamp, suggested_guideline}
    """
    if not session_file.exists():
        return []

    errors = []

    try:
        with open(session_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # Must be a user entry (tool results come back as user messages)
                if entry.get("type") != "user":
                    continue

                # Get message.content array
                content = entry.get("message", {}).get("content", [])
                if not isinstance(content, list):
                    continue

                # Look for tool_result items with is_error
                for item in content:
                    if not isinstance(item, dict):
                        continue

                    if item.get("type") != "tool_result":
                        continue

                    if not item.get("is_error"):
                        continue

                    tool_content = item.get("content", "")
                    if not isinstance(tool_content, str):
                        continue

                    # Skip if matches exclude patterns
                    should_exclude = False
                    for exclude_pattern in TOOL_ERROR_EXCLUDE_PATTERNS:
                        if re.search(exclude_pattern, tool_content, re.IGNORECASE):
                            should_exclude = True
                            break

                    if should_exclude:
                        continue

                    # If project_specific_only, check for matching patterns
                    error_type = "unknown"
                    suggested_guideline = None

                    for etype, pattern, guideline in PROJECT_SPECIFIC_ERROR_PATTERNS:
                        if re.search(pattern, tool_content, re.IGNORECASE):
                            error_type = etype
                            suggested_guideline = guideline
                            break

                    # Skip unknown errors if project_specific_only
                    if project_specific_only and error_type == "unknown":
                        continue

                    errors.append({
                        "error_type": error_type,
                        "content": tool_content[:500],  # Truncate long errors
                        "project": str(session_file.parent.name),
                        "timestamp": entry.get("timestamp", ""),
                        "suggested_guideline": suggested_guideline,
                    })

    except IOError:
        return []

    return errors


def aggregate_tool_errors(
    errors: List[Dict[str, Any]],
    min_occurrences: int = 2
) -> List[Dict[str, Any]]:
    """
    Group errors by type and return those with multiple occurrences.

    Only repeated errors are valuable for CLAUDE.md - one-off errors are noise.

    Args:
        errors: List of error dicts from extract_tool_errors()
        min_occurrences: Minimum times an error type must occur

    Returns:
        List of aggregated errors with {error_type, count, suggested_guideline,
        confidence, sample_errors}
    """
    from collections import Counter

    # Count by error type
    type_counts = Counter(e["error_type"] for e in errors)

    # Group errors by type
    errors_by_type: Dict[str, List[Dict]] = {}
    for error in errors:
        etype = error["error_type"]
        if etype not in errors_by_type:
            errors_by_type[etype] = []
        errors_by_type[etype].append(error)

    # Build aggregated results for types meeting threshold
    aggregated = []
    for error_type, count in type_counts.items():
        if count < min_occurrences:
            continue

        samples = errors_by_type[error_type][:3]  # Keep up to 3 samples
        suggested_guideline = samples[0].get("suggested_guideline") if samples else None

        # Higher confidence for more occurrences
        if count >= 5:
            confidence = 0.90
        elif count >= 3:
            confidence = 0.85
        else:
            confidence = 0.70

        aggregated.append({
            "error_type": error_type,
            "count": count,
            "suggested_guideline": suggested_guideline,
            "confidence": confidence,
            "decay_days": 180,  # Tool error learnings decay slower
            "sample_errors": [s["content"][:200] for s in samples],
        })

    # Sort by count descending
    aggregated.sort(key=lambda x: x["count"], reverse=True)

    return aggregated
