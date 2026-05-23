"""
LLM-as-Judge via Groq (Llama 3.3 70B)

Provides semantic quality assessment that goes beyond deterministic
static analysis. Uses Groq's free tier (30 req/min, 14,400 req/day).

Evaluates 4 dimensions that require language understanding:
1. Triggering precision/recall (generate synthetic prompts)
2. Orchestration fitness (is this a pure worker?)
3. Scope calibration (right size for the task?)
4. Output quality (would instructions produce good results?)

Gracefully degrades when Groq API is unavailable — all LLM scoring
is optional and composited with weight renormalization.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
"""

import json
import os
import time
from typing import Dict, Any, Optional, List


# Rate limiting
GROQ_RATE_LIMIT = 30  # requests per minute
_last_request_times: List[float] = []


def _rate_limit():
    """Enforce 30 req/min rate limit for Groq free tier."""
    now = time.time()
    # Prune requests older than 60 seconds
    while _last_request_times and _last_request_times[0] < now - 60:
        _last_request_times.pop(0)

    if len(_last_request_times) >= GROQ_RATE_LIMIT:
        sleep_time = 60 - (now - _last_request_times[0]) + 0.1
        if sleep_time > 0:
            time.sleep(sleep_time)

    _last_request_times.append(time.time())


def _get_groq_client():
    """Get Groq client, or None if unavailable."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return None
    try:
        from groq import Groq

        return Groq(api_key=api_key)
    except ImportError:
        return None


def _query_llm(
    prompt: str,
    system_prompt: str = "You are a skill quality evaluator. Respond only with valid JSON.",
    model: str = "llama-3.3-70b-versatile",
    max_tokens: int = 1024,
) -> Optional[Dict]:
    """
    Send a query to Groq and parse JSON response.

    Returns parsed JSON dict or None on failure.
    """
    client = _get_groq_client()
    if not client:
        return None

    _rate_limit()

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.1,  # Low temp for consistent rubric scoring
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception:
        return None


def judge_triggering_quality(
    skill_name: str,
    description: str,
    body_preview: str,
) -> Optional[Dict[str, Any]]:
    """
    LLM judges triggering quality by generating synthetic prompts and
    evaluating whether the skill would activate correctly.

    Returns:
        {
            'score': 0-100,
            'positive_prompts': [prompts that SHOULD trigger this skill],
            'negative_prompts': [prompts that should NOT trigger],
            'precision_estimate': float,
            'recall_estimate': float,
            'reasoning': str,
        }
    """
    prompt = f"""Evaluate the triggering quality of this Claude Code skill.

SKILL NAME: {skill_name}
DESCRIPTION:
{description}

BODY PREVIEW (first 500 chars):
{body_preview[:500]}

Tasks:
1. Generate 5 user prompts that SHOULD trigger this skill (true positives)
2. Generate 5 user prompts that should NOT trigger it (true negatives)
3. Estimate precision (0-1): if it triggers, how often is it correct?
4. Estimate recall (0-1): when it should trigger, how often does it?
5. Score overall triggering quality 0-100

Respond with JSON:
{{
    "score": <int 0-100>,
    "positive_prompts": ["prompt1", "prompt2", ...],
    "negative_prompts": ["prompt1", "prompt2", ...],
    "precision_estimate": <float 0-1>,
    "recall_estimate": <float 0-1>,
    "reasoning": "<one paragraph>"
}}"""

    return _query_llm(prompt)


def judge_orchestration_fitness(
    skill_name: str,
    description: str,
    body: str,
) -> Optional[Dict[str, Any]]:
    """
    LLM judges whether the skill is a pure worker or self-orchestrating.

    Pure workers: focused, single-purpose, no agent delegation.
    Orchestrators: launch agents, coordinate workflows, manage state.

    Returns:
        {
            'score': 0-100 (100 = pure worker, 0 = full orchestrator),
            'worker_signals': [evidence of pure worker behavior],
            'orchestrator_signals': [evidence of orchestration],
            'recommendation': str,
        }
    """
    prompt = f"""Evaluate whether this Claude Code skill is a pure worker or a self-orchestrating agent.

Skills should be PURE WORKERS — focused, single-purpose units that do one thing well.
They should NOT orchestrate other agents, manage multi-step workflows, or coordinate
between multiple tools in complex sequences.

SKILL NAME: {skill_name}
DESCRIPTION:
{description}

FULL BODY:
{body[:2000]}

Score 0-100 where:
- 100 = Perfect pure worker (focused, single task, clear scope)
- 70 = Mostly worker with minor orchestration tendencies
- 40 = Hybrid — does its own work but also coordinates
- 0 = Full orchestrator (launches agents, manages workflows)

Respond with JSON:
{{
    "score": <int 0-100>,
    "worker_signals": ["signal1", "signal2"],
    "orchestrator_signals": ["signal1", "signal2"],
    "recommendation": "<one sentence>"
}}"""

    return _query_llm(prompt)


def judge_scope_calibration(
    skill_name: str,
    description: str,
    body: str,
    word_count: int,
    has_references: bool,
) -> Optional[Dict[str, Any]]:
    """
    LLM judges whether the skill is properly scoped.

    Returns:
        {
            'score': 0-100,
            'scope_assessment': 'stub' | 'thin' | 'well-scoped' | 'verbose' | 'bloated',
            'split_recommendations': [suggestions for splitting if too broad],
            'expansion_recommendations': [suggestions for expanding if too thin],
        }
    """
    prompt = f"""Evaluate the scope of this Claude Code skill.

A well-scoped skill:
- Does ONE thing well (not a Swiss Army knife)
- Has enough content to be useful (not a stub)
- Keeps detail in references/ files, not the main SKILL.md
- Can be understood in under 2 minutes

SKILL NAME: {skill_name}
DESCRIPTION:
{description}

WORD COUNT: {word_count}
HAS REFERENCES DIR: {has_references}

BODY:
{body[:2000]}

Assess scope on a 0-100 scale:
- 90-100: Perfectly scoped — right size, right depth
- 70-89: Good scope with minor issues
- 50-69: Scope problems — too thin or too broad
- 0-49: Major scope issues — stub or monolith

Respond with JSON:
{{
    "score": <int 0-100>,
    "scope_assessment": "<stub|thin|well-scoped|verbose|bloated>",
    "split_recommendations": ["rec1"],
    "expansion_recommendations": ["rec1"],
    "reasoning": "<one paragraph>"
}}"""

    return _query_llm(prompt)


def judge_output_quality(
    skill_name: str,
    description: str,
    body: str,
) -> Optional[Dict[str, Any]]:
    """
    LLM simulates 3 realistic tasks and judges whether the skill's
    instructions would produce quality outputs.

    Returns:
        {
            'score': 0-100,
            'simulated_tasks': [{task, expected_quality, issues}],
            'instruction_clarity': float 0-1,
            'completeness': float 0-1,
        }
    """
    prompt = f"""You are evaluating a Claude Code skill's instruction quality.

Imagine 3 realistic scenarios where a developer would use this skill.
For each scenario, assess whether the skill's instructions would lead
to correct, complete, well-formatted output.

SKILL NAME: {skill_name}
DESCRIPTION:
{description}

INSTRUCTIONS:
{body[:2500]}

For each simulated task:
1. Describe the realistic scenario (1 sentence)
2. Rate expected output quality 0-100
3. List any issues that would cause poor output

Then give an overall score.

Respond with JSON:
{{
    "score": <int 0-100>,
    "simulated_tasks": [
        {{
            "task": "<scenario>",
            "expected_quality": <int 0-100>,
            "issues": ["issue1"]
        }}
    ],
    "instruction_clarity": <float 0-1>,
    "completeness": <float 0-1>,
    "reasoning": "<one paragraph>"
}}"""

    return _query_llm(prompt)


def run_llm_evaluation(
    skill_name: str,
    description: str,
    body: str,
    skill_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run all LLM judge evaluations for a skill.

    Returns results for all 4 LLM dimensions, with None for any that failed.
    The engine handles weight renormalization for missing dimensions.
    """
    results = {
        "available": False,
        "dimensions": {},
    }

    # Check if Groq is available
    if not os.environ.get("GROQ_API_KEY"):
        results["reason"] = "GROQ_API_KEY not set"
        return results

    try:
        from groq import Groq  # noqa: F401 — capability probe; client built in _get_groq_client
    except ImportError:
        results["reason"] = "groq package not installed (pip install groq)"
        return results

    results["available"] = True
    word_count = len(body.split())
    has_refs = False
    if skill_path:
        from pathlib import Path

        has_refs = (Path(skill_path).parent / "references").exists()

    body_preview = body[:500]

    # Run evaluations sequentially (rate limit aware)
    triggering = judge_triggering_quality(skill_name, description, body_preview)
    if triggering:
        results["dimensions"]["triggering_accuracy"] = triggering

    orchestration = judge_orchestration_fitness(skill_name, description, body)
    if orchestration:
        results["dimensions"]["orchestration_fitness"] = orchestration

    scope = judge_scope_calibration(skill_name, description, body, word_count, has_refs)
    if scope:
        results["dimensions"]["scope_calibration"] = scope

    output = judge_output_quality(skill_name, description, body)
    if output:
        results["dimensions"]["output_quality"] = output

    return results
