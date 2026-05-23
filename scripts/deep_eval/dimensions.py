"""
Intent Solutions Deep Evaluation — 10 Weighted Dimensions (Static Layer)

Deterministic scoring across 10 quality dimensions, designed for the
Tons of Skills ecosystem (2,834+ skills). These run without any LLM calls
and produce scores in [0, 100] per dimension.

Dimension weights (sum to 1.0):
    triggering_accuracy:      0.25  — Does description enable correct activation?
    orchestration_fitness:    0.20  — Is it a pure worker, not self-orchestrating?
    output_quality:           0.15  — Are outputs well-specified?
    scope_calibration:        0.12  — Right scope — not too thin, not bloated?
    progressive_disclosure:   0.10  — Detail in references/, not monolithic?
    token_efficiency:         0.06  — Minimal context overhead?
    robustness:               0.05  — Handles errors gracefully?
    structural_completeness:  0.03  — Has all required sections?
    code_template_quality:    0.02  — Copy-paste ready examples?
    ecosystem_coherence:      0.02  — Cross-links with siblings?

Author: Jeremy Longshore <jeremy@intentsolutions.io>
"""

import re
from pathlib import Path
from typing import Dict, Any, Optional


# Dimension weight configuration
DIMENSION_WEIGHTS = {
    "triggering_accuracy": 0.25,
    "orchestration_fitness": 0.20,
    "output_quality": 0.15,
    "scope_calibration": 0.12,
    "progressive_disclosure": 0.10,
    "token_efficiency": 0.06,
    "robustness": 0.05,
    "structural_completeness": 0.03,
    "code_template_quality": 0.02,
    "ecosystem_coherence": 0.02,
}

# Anti-patterns: 5% penalty each, floor at 50%
ANTI_PATTERNS = [
    (
        re.compile(r"\b(I can|I will|I\'m going to|I help)\b", re.IGNORECASE),
        "first_person",
        "Uses first-person voice (should be imperative)",
    ),
    (
        re.compile(r"\b(You can|You should|You will)\b", re.IGNORECASE),
        "second_person",
        "Uses second-person voice in instructions",
    ),
    (re.compile(r"\b(TODO|FIXME|REPLACE_ME|TBD)\b", re.IGNORECASE), "placeholder", "Contains placeholder text"),
    (re.compile(r"\[YOUR_|<insert", re.IGNORECASE), "template_var", "Contains unfilled template variables"),
    (re.compile(r"(?:^|\n)\s*\.\.\.\s*(?:\n|$)"), "ellipsis", "Contains bare ellipsis (truncated content)"),
    (
        re.compile(r"\bmust never\b.*\bmust always\b|\bmust always\b.*\bmust never\b", re.IGNORECASE | re.DOTALL),
        "contradictory",
        "Contains contradictory must-never/must-always pairs",
    ),
]

# Orchestration indicators (skill should NOT self-orchestrate)
ORCHESTRATION_SIGNALS = [
    re.compile(r"\blaunch\s+(?:a\s+)?(?:sub)?agent", re.IGNORECASE),
    re.compile(r"\borchestrat", re.IGNORECASE),
    re.compile(r"\bcoordinat(?:e|ing)\s+(?:multiple|other|several)", re.IGNORECASE),
    re.compile(r"\bdelegate\s+to\b", re.IGNORECASE),
    re.compile(r"\bspawn\s+(?:a\s+)?(?:new\s+)?(?:agent|worker|task)", re.IGNORECASE),
    re.compile(r"\bfork\s+(?:a\s+)?(?:new\s+)?(?:agent|process)", re.IGNORECASE),
]

# Trigger phrase patterns for description quality
TRIGGER_PATTERNS = [
    re.compile(r"\bUse when\b", re.IGNORECASE),
    re.compile(r"\bTrigger with\b", re.IGNORECASE),
    re.compile(r"\bActivate when\b", re.IGNORECASE),
    re.compile(r"\bRun when\b", re.IGNORECASE),
    re.compile(r'["/][\w-]+', re.IGNORECASE),  # Slash command triggers like "/foo"
]

# Required sections for structural completeness
REQUIRED_SECTIONS = [
    "# ",  # title line
    "## Overview",
    "## Prerequisites",
    "## Instructions",
    "## Output",
    "## Error Handling",
    "## Examples",
    "## Resources",
]


def score_triggering_accuracy(
    body: str,
    fm: dict,
    skill_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Triggering Accuracy (weight: 0.25)

    Evaluates whether the skill's description enables correct activation.
    Static analysis checks:
    - Description length and quality
    - Presence of trigger phrases ("Use when", "Trigger with")
    - Negative examples (when NOT to use)
    - Specificity vs vagueness
    """
    score = 0
    details = []
    desc = str(fm.get("description", ""))

    # Description length: 50-200 chars is ideal
    desc_len = len(desc.strip())
    if desc_len == 0:
        details.append("No description — triggering impossible")
        return {"score": 0, "details": details}
    elif desc_len < 30:
        score += 10
        details.append(f"Description too short ({desc_len} chars) — vague triggering")
    elif desc_len < 50:
        score += 30
        details.append(f"Description short ({desc_len} chars)")
    elif desc_len <= 300:
        score += 50
        details.append(f"Description length good ({desc_len} chars)")
    else:
        score += 40
        details.append(f"Description long ({desc_len} chars) — may consume token budget")

    # Trigger phrases present?
    trigger_count = sum(1 for pat in TRIGGER_PATTERNS if pat.search(desc))
    if trigger_count >= 2:
        score += 25
        details.append(f"Has {trigger_count} trigger phrases (excellent)")
    elif trigger_count == 1:
        score += 15
        details.append("Has 1 trigger phrase")
    else:
        details.append("No trigger phrases in description")

    # Action verb in description start
    action_verbs = re.compile(
        r"^\s*(?:Use|Trigger|Activate|Run|Execute|Build|Create|Generate|Validate|"
        r"Analyze|Check|Deploy|Test|Debug|Monitor|Review|Scan|Audit)",
        re.IGNORECASE | re.MULTILINE,
    )
    if action_verbs.search(desc):
        score += 10
        details.append("Description starts with action verb")
    else:
        score += 3

    # Negative examples (when NOT to use) — advanced precision
    negative_patterns = re.compile(r"\b(?:do not|don\'t|not for|except when|unless)\b", re.IGNORECASE)
    if negative_patterns.search(desc):
        score += 15
        details.append("Has negative trigger guidance (precision)")
    elif negative_patterns.search(body):
        score += 8
        details.append("Negative guidance in body (not description)")

    return {"score": min(100, score), "details": details}


def score_orchestration_fitness(
    body: str,
    fm: dict,
    skill_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Orchestration Fitness (weight: 0.20)

    Skills should be pure workers — focused, single-purpose units.
    They should NOT self-orchestrate (launch agents, coordinate workflows).
    Orchestration belongs in agents/*.md, not skills.
    """
    score = 100  # Start perfect, deduct for violations
    details = []

    # Check for orchestration signals in body
    orch_hits = []
    for pattern in ORCHESTRATION_SIGNALS:
        matches = pattern.findall(body)
        if matches:
            orch_hits.extend(matches)

    if orch_hits:
        penalty = min(50, len(orch_hits) * 15)
        score -= penalty
        details.append(f"Orchestration signals found ({len(orch_hits)} hits): {', '.join(orch_hits[:3])}")
    else:
        details.append("No orchestration signals — pure worker")

    # Check if context: fork is set (subagent delegation)
    if fm.get("context") == "fork":
        # fork + agent is fine (skill delegates to a subagent type)
        if fm.get("agent"):
            score -= 5
            details.append(f"Delegates to subagent type: {fm['agent']} (minor deduction)")
        else:
            score -= 15
            details.append("context: fork without agent type specified")

    # Check allowed-tools breadth — too many tools = might be over-scoped
    tools_str = str(fm.get("allowed-tools", ""))
    tools = [t.strip() for t in tools_str.split(",") if t.strip()] if tools_str else []
    if len(tools) > 8:
        score -= 10
        details.append(f"Broad tool access ({len(tools)} tools) — may indicate scope creep")
    elif len(tools) == 0 and not fm.get("disable-model-invocation"):
        score -= 5
        details.append("No allowed-tools specified")

    # Check for multi-step workflow language
    re.compile(
        r"\b(?:step\s+\d+|phase\s+\d+|stage\s+\d+)\b.*"
        r"\b(?:step\s+\d+|phase\s+\d+|stage\s+\d+)\b",
        re.IGNORECASE | re.DOTALL,
    )
    # Only penalize if there are many numbered steps (>5 = workflow, not a skill)
    step_count = len(re.findall(r"\b(?:step|phase|stage)\s+\d+\b", body, re.IGNORECASE))
    if step_count > 5:
        score -= 10
        details.append(f"Multi-step workflow ({step_count} steps) — consider splitting into multiple skills")

    return {"score": max(0, min(100, score)), "details": details}


def score_output_quality(
    body: str,
    fm: dict,
    skill_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Output Quality (weight: 0.15)

    Checks whether the skill specifies expected outputs clearly.
    """
    score = 0
    details = []

    # Has ## Output section?
    has_output = bool(re.search(r"^##\s+Output", body, re.MULTILINE | re.IGNORECASE))
    if has_output:
        score += 35
        details.append("Has ## Output section")

        # Check for format specification in output section
        output_section = _extract_section(body, "Output")
        if output_section:
            has_format = bool(
                re.search(
                    r"\b(?:format|table|JSON|markdown|YAML|CSV|list|report|summary)\b", output_section, re.IGNORECASE
                )
            )
            if has_format:
                score += 15
                details.append("Output section specifies format")

            # Has example output?
            has_example_output = bool(re.search(r"```", output_section))
            if has_example_output:
                score += 15
                details.append("Output section has code example")
    else:
        details.append("No ## Output section")

    # Code blocks in body (general output examples)
    code_blocks = len(re.findall(r"```", body)) // 2
    if code_blocks >= 3:
        score += 20
        details.append(f"{code_blocks} code blocks (rich examples)")
    elif code_blocks >= 1:
        score += 10
        details.append(f"{code_blocks} code block(s)")
    else:
        details.append("No code blocks")

    # Structured output indicators
    structured = re.compile(r"\b(?:JSON|YAML|CSV|table|columns?|rows?|fields?|schema)\b", re.IGNORECASE)
    if structured.search(body):
        score += 15
        details.append("References structured output format")

    return {"score": min(100, score), "details": details}


def score_scope_calibration(
    body: str,
    fm: dict,
    skill_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Scope Calibration (weight: 0.12)

    Evaluates whether the skill is properly scoped:
    - Not too thin (stub with no real content)
    - Not too bloated (monolithic, should be split)
    """
    score = 0
    details = []

    lines = body.strip().splitlines()
    len(lines)
    word_count = len(body.split())

    # Word count calibration
    if word_count < 50:
        score += 10
        details.append(f"Stub: only {word_count} words")
    elif word_count < 150:
        score += 30
        details.append(f"Thin: {word_count} words")
    elif word_count <= 800:
        score += 70
        details.append(f"Well-scoped: {word_count} words")
    elif word_count <= 1500:
        score += 50
        details.append(f"Verbose: {word_count} words (consider splitting)")
    else:
        score += 25
        details.append(f"Bloated: {word_count} words (should split into references/)")

    # Section count — 4-8 sections is ideal
    sections = re.findall(r"^##\s+", body, re.MULTILINE)
    section_count = len(sections)
    if 4 <= section_count <= 8:
        score += 20
        details.append(f"{section_count} sections (well-organized)")
    elif section_count < 3:
        score += 5
        details.append(f"Only {section_count} sections (understructured)")
    elif section_count > 10:
        score += 10
        details.append(f"{section_count} sections (overstructured, consider merging)")
    else:
        score += 15

    # If long but has references/, scope is better
    if skill_path:
        refs_dir = skill_path.parent / "references"
        if refs_dir.exists() and word_count > 500:
            score += 10
            details.append("Long skill but has references/ (progressive disclosure)")

    return {"score": min(100, score), "details": details}


def score_progressive_disclosure(
    body: str,
    fm: dict,
    skill_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Progressive Disclosure (weight: 0.10)

    Content layering: SKILL.md is the summary, references/ has depth.
    """
    score = 0
    details = []
    skill_dir = skill_path.parent if skill_path else None

    # Has references/ or resources/?
    refs_dir = None
    if skill_dir:
        for dirname in ("references", "resources"):
            candidate = skill_dir / dirname
            if candidate.exists():
                refs_dir = candidate
                break

    if refs_dir:
        ref_files = list(refs_dir.glob("*.md"))
        if ref_files:
            score += 40
            details.append(f"Has {len(ref_files)} reference files")
            # Bonus for well-named refs
            good_names = {
                "errors.md",
                "examples.md",
                "implementation.md",
                "implementation-guide.md",
                "api-reference.md",
                "configuration.md",
                "troubleshooting.md",
            }
            named_well = [f.name for f in ref_files if f.name in good_names]
            if named_well:
                score += 15
                details.append(f"Well-named refs: {', '.join(named_well)}")
        else:
            score += 5
            details.append("references/ exists but is empty")
    else:
        lines = len(body.strip().splitlines())
        if lines <= 80:
            score += 30
            details.append("No references/ (acceptable — skill is concise)")
        else:
            details.append("No references/ directory")

    # Relative markdown links (references to supporting files)
    md_links = re.findall(r"\[([^\]]*)\]\((?!https?://|#)([^)]+)\)", body)
    if md_links:
        score += 20
        details.append(f"{len(md_links)} relative markdown link(s)")

    # Dynamic context injection
    dci_pattern = re.compile(r"(?m)^!\`[^`]+\`\s*$")
    if dci_pattern.search(body):
        score += 15
        details.append("Uses dynamic context injection")

    # SKILL_DIR references
    skilldir_refs = re.findall(r"\$\{CLAUDE_SKILL_DIR\}", body)
    if skilldir_refs:
        score += 10
        details.append(f"{len(skilldir_refs)} CLAUDE_SKILL_DIR reference(s)")

    return {"score": min(100, score), "details": details}


def score_token_efficiency(
    body: str,
    fm: dict,
    skill_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Token Efficiency (weight: 0.06)

    Minimal context overhead — skill loads into context on every activation.
    """
    score = 0
    details = []

    lines = len(body.strip().splitlines())
    desc_len = len(str(fm.get("description", "")))

    # SKILL.md line count (per Anthropic: concise is better)
    if lines <= 80:
        score += 40
        details.append(f"{lines} lines — excellent token economy")
    elif lines <= 150:
        score += 30
        details.append(f"{lines} lines — good")
    elif lines <= 300:
        score += 15
        details.append(f"{lines} lines — consider moving detail to references/")
    else:
        score += 5
        details.append(f"{lines} lines — heavy context load")

    # Description token budget (aggregated across all installed skills)
    if desc_len <= 100:
        score += 25
        details.append(f"Description {desc_len} chars — lean")
    elif desc_len <= 200:
        score += 20
        details.append(f"Description {desc_len} chars — moderate")
    elif desc_len <= 400:
        score += 10
        details.append(f"Description {desc_len} chars — verbose")
    else:
        score += 5
        details.append(f"Description {desc_len} chars — consumes token budget")

    # Redundancy check: does body repeat description?
    desc_text = str(fm.get("description", "")).strip()
    if desc_text and len(desc_text) > 30:
        # Check if first paragraph of body is very similar to description
        first_para = body.split("\n\n")[0] if body else ""
        # Simple overlap: if >60% of description words appear in first para
        desc_words = set(desc_text.lower().split())
        para_words = set(first_para.lower().split())
        if desc_words and para_words:
            overlap = len(desc_words & para_words) / len(desc_words)
            if overlap > 0.7:
                score -= 5
                details.append("Body repeats description (redundant tokens)")
            else:
                score += 10
                details.append("Body adds value beyond description")
        else:
            score += 10
    else:
        score += 10

    # Frontmatter field count efficiency
    fm_field_count = len(fm)
    if fm_field_count <= 10:
        score += 15
        details.append(f"{fm_field_count} frontmatter fields — efficient")
    elif fm_field_count <= 15:
        score += 10
        details.append(f"{fm_field_count} frontmatter fields")
    else:
        score += 5
        details.append(f"{fm_field_count} frontmatter fields — heavy")

    return {"score": min(100, max(0, score)), "details": details}


def score_robustness(
    body: str,
    fm: dict,
    skill_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Robustness (weight: 0.05)

    Handles errors gracefully — has error handling section, fallback strategies.
    """
    score = 0
    details = []

    # Has ## Error Handling section?
    has_error_section = bool(re.search(r"^##\s+Error\s+Handling", body, re.MULTILINE | re.IGNORECASE))
    if has_error_section:
        score += 40
        details.append("Has ## Error Handling section")
    else:
        details.append("No ## Error Handling section")

    # Error handling language in body
    error_patterns = re.compile(
        r"\b(?:error|fail|exception|catch|retry|fallback|graceful|recover|timeout)\b",
        re.IGNORECASE,
    )
    error_mentions = len(error_patterns.findall(body))
    if error_mentions >= 5:
        score += 25
        details.append(f"{error_mentions} error handling references")
    elif error_mentions >= 2:
        score += 15
        details.append(f"{error_mentions} error handling references")
    elif error_mentions >= 1:
        score += 5
        details.append("Minimal error handling references")

    # Bash error handling patterns
    bash_safety = re.compile(r"(?:set -e|2>/dev/null|\|\| echo|\|\| true|trap\s)")
    if bash_safety.search(body):
        score += 15
        details.append("Has bash error handling patterns")

    # Edge case coverage
    edge_patterns = re.compile(
        r"\b(?:edge case|corner case|empty|missing|invalid|malformed|not found)\b",
        re.IGNORECASE,
    )
    if edge_patterns.search(body):
        score += 20
        details.append("Addresses edge cases")

    return {"score": min(100, score), "details": details}


def score_structural_completeness(
    body: str,
    fm: dict,
    skill_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Structural Completeness (weight: 0.03)

    Has all recommended sections per the Intent Solutions standard.
    """
    score = 0
    details = []

    present = 0
    missing = []
    for section in REQUIRED_SECTIONS:
        if section == "# ":
            if re.search(r"^#\s+\S", body, re.MULTILINE):
                present += 1
            else:
                missing.append("Title")
        else:
            section_name = section.replace("## ", "")
            if re.search(rf"^##\s+{re.escape(section_name)}", body, re.MULTILINE | re.IGNORECASE):
                present += 1
            else:
                missing.append(section_name)

    total = len(REQUIRED_SECTIONS)
    pct = present / total if total else 0

    score = int(pct * 100)
    details.append(f"{present}/{total} sections present")
    if missing:
        details.append(f"Missing: {', '.join(missing[:4])}")

    return {"score": min(100, score), "details": details}


def score_code_template_quality(
    body: str,
    fm: dict,
    skill_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Code Template Quality (weight: 0.02)

    Copy-paste ready code examples.
    """
    score = 0
    details = []

    # Count code blocks with language tags
    code_blocks = re.findall(r"```(\w+)?", body)
    total_blocks = len(code_blocks)
    tagged_blocks = sum(1 for lang in code_blocks if lang)

    if total_blocks == 0:
        score += 20
        details.append("No code blocks (may be acceptable for non-code skills)")
        # Check if this is a code-oriented skill
        code_oriented = re.search(
            r"\b(?:code|script|function|class|API|endpoint|query|command)\b",
            str(fm.get("description", "")),
            re.IGNORECASE,
        )
        if code_oriented:
            score = 10
            details.append("Code-oriented skill without examples")
    else:
        # Language tags on code blocks
        if tagged_blocks == total_blocks:
            score += 40
            details.append(f"All {total_blocks} code blocks have language tags")
        elif tagged_blocks > 0:
            score += 25
            details.append(f"{tagged_blocks}/{total_blocks} code blocks tagged")
        else:
            score += 10
            details.append("Code blocks without language tags")

        # Code block size (not too short = stub, not too long = should be in refs)
        code_content = re.findall(r"```\w*\n(.*?)```", body, re.DOTALL)
        if code_content:
            avg_lines = sum(len(c.strip().splitlines()) for c in code_content) / len(code_content)
            if 3 <= avg_lines <= 30:
                score += 30
                details.append(f"Code blocks avg {avg_lines:.0f} lines (copy-paste ready)")
            elif avg_lines < 3:
                score += 15
                details.append("Code blocks very short")
            else:
                score += 15
                details.append(f"Code blocks avg {avg_lines:.0f} lines (consider moving to references/)")

        # Bash examples for CLI-oriented skills
        bash_blocks = sum(1 for lang in code_blocks if lang and lang.lower() in ("bash", "sh", "shell", "zsh"))
        if bash_blocks > 0:
            score += 15
            details.append(f"{bash_blocks} bash example(s)")

    # Has ## Examples section?
    if re.search(r"^##\s+Examples?", body, re.MULTILINE | re.IGNORECASE):
        score += 15
        details.append("Has ## Examples section")

    return {"score": min(100, score), "details": details}


def score_ecosystem_coherence(
    body: str,
    fm: dict,
    skill_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Ecosystem Coherence (weight: 0.02)

    Cross-links with sibling skills, related plugins, ecosystem awareness.
    """
    score = 0
    details = []

    # Tags present?
    tags = fm.get("tags", [])
    if isinstance(tags, list) and tags:
        score += 30
        details.append(f"{len(tags)} tags for discoverability")
    else:
        details.append("No tags")

    # compatible-with field?
    compat = fm.get("compatible-with", "")
    if compat:
        score += 20
        details.append(f"compatible-with: {compat}")
    else:
        details.append("No compatible-with field")

    # Cross-references to other skills/plugins in body
    cross_refs = re.findall(
        r"\b(?:see also|related|companion|pairs with|works with|complements)\b",
        body,
        re.IGNORECASE,
    )
    if cross_refs:
        score += 25
        details.append(f"{len(cross_refs)} cross-reference(s)")

    # References to marketplace or ecosystem
    marketplace_refs = re.findall(
        r"\b(?:marketplace|tonsofskills|plugin hub|ecosystem)\b",
        body,
        re.IGNORECASE,
    )
    if marketplace_refs:
        score += 10
        details.append("References marketplace/ecosystem")

    # Sibling skill awareness (references other SKILL.md or commands)
    sibling_refs = re.findall(r"/[\w-]+(?:\s|$|[,.])", body)
    if sibling_refs:
        score += 15
        details.append(f"{len(sibling_refs)} possible sibling reference(s)")

    return {"score": min(100, score), "details": details}


def calculate_anti_pattern_penalty(body: str) -> Dict[str, Any]:
    """
    Anti-pattern detection: 5% penalty per pattern, floor at 50%.

    Returns penalty info without modifying scores directly.
    """
    hits = []
    for pattern, name, description in ANTI_PATTERNS:
        if pattern.search(body):
            hits.append({"name": name, "description": description})

    penalty_pct = min(0.50, len(hits) * 0.05)

    return {
        "penalty_pct": penalty_pct,
        "hits": hits,
        "count": len(hits),
    }


def score_all_dimensions(
    body: str,
    fm: dict,
    skill_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Score all 10 dimensions and return composite results.

    Returns:
        {
            'dimensions': {dim_name: {'score': 0-100, 'details': [...]}},
            'anti_patterns': {...},
            'composite_score': float,
            'dimension_weights': {dim_name: weight},
        }
    """
    dimensions = {
        "triggering_accuracy": score_triggering_accuracy(body, fm, skill_path),
        "orchestration_fitness": score_orchestration_fitness(body, fm, skill_path),
        "output_quality": score_output_quality(body, fm, skill_path),
        "scope_calibration": score_scope_calibration(body, fm, skill_path),
        "progressive_disclosure": score_progressive_disclosure(body, fm, skill_path),
        "token_efficiency": score_token_efficiency(body, fm, skill_path),
        "robustness": score_robustness(body, fm, skill_path),
        "structural_completeness": score_structural_completeness(body, fm, skill_path),
        "code_template_quality": score_code_template_quality(body, fm, skill_path),
        "ecosystem_coherence": score_ecosystem_coherence(body, fm, skill_path),
    }

    # Calculate weighted composite
    from .stats import weighted_composite

    scores = {dim: data["score"] for dim, data in dimensions.items()}
    composite = weighted_composite(scores, DIMENSION_WEIGHTS)

    # Apply anti-pattern penalty
    anti = calculate_anti_pattern_penalty(body)
    if anti["penalty_pct"] > 0:
        composite = composite * (1 - anti["penalty_pct"])

    return {
        "dimensions": dimensions,
        "anti_patterns": anti,
        "composite_score": round(composite, 2),
        "dimension_weights": DIMENSION_WEIGHTS,
    }


def _extract_section(body: str, section_name: str) -> Optional[str]:
    """Extract content of a named ## section from markdown body."""
    pattern = re.compile(
        rf"^##\s+{re.escape(section_name)}\s*\n(.*?)(?=^##\s+|\Z)",
        re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    match = pattern.search(body)
    return match.group(1).strip() if match else None
