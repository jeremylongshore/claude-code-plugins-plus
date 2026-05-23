"""
Intent Solutions Deep Evaluation Engine — Main Orchestrator

Three-layer evaluation:
  Layer 1: Static dimension scoring (deterministic, fast, always runs)
  Layer 2: LLM quality assessment via Groq (optional, --deep)
  Layer 3: Competitive ranking via Elo (optional, needs 2+ skills per category)

Weight renormalization: when Layer 2 is unavailable, Layer 1 weights are
renormalized to sum to 1.0 automatically.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
"""

import time
from pathlib import Path
from typing import Dict, Any, List, Optional

from .dimensions import score_all_dimensions, DIMENSION_WEIGHTS
from .llm_judge import run_llm_evaluation
from .stats import bootstrap_ci
from .badges import assign_badge, badge_info, grade_to_badge_comparison
from .ranking import category_rankings, run_round_robin, rank_skills


# Layer blending weights
# When all layers available: static=0.5, llm=0.4, ranking=0.1
# When only static: static=1.0
# When static+llm: static=0.55, llm=0.45
LAYER_WEIGHTS = {
    "static": 0.50,
    "llm": 0.40,
    "ranking_bonus": 0.10,
}


class DeepEvalEngine:
    """
    Main orchestrator for the Intent Solutions Deep Evaluation Engine.

    Usage:
        engine = DeepEvalEngine(use_llm=True)
        result = engine.evaluate_skill(path, body, frontmatter)
        results = engine.evaluate_batch(skills_data)
        rankings = engine.rank_by_category(results)
    """

    def __init__(
        self,
        use_llm: bool = False,
        verbose: bool = False,
    ):
        self.use_llm = use_llm
        self.verbose = verbose
        self._eval_cache: Dict[str, Dict] = {}

    def evaluate_skill(
        self,
        skill_path: Path,
        body: str,
        fm: dict,
        letter_grade: Optional[str] = None,
        deterministic_score: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Run deep evaluation on a single skill.

        Args:
            skill_path: Path to SKILL.md
            body: Parsed body content (after frontmatter)
            fm: Parsed frontmatter dict
            letter_grade: Existing validator letter grade (for comparison)
            deterministic_score: Existing validator 100-point score

        Returns:
            Complete evaluation result with all available layers.
        """
        start = time.time()
        skill_name = fm.get("name", skill_path.stem)
        description = str(fm.get("description", ""))

        # Layer 1: Static dimension scoring (always runs)
        static_result = score_all_dimensions(body, fm, skill_path)

        # Layer 2: LLM quality assessment (optional)
        llm_result = None
        if self.use_llm:
            llm_result = run_llm_evaluation(
                skill_name=skill_name,
                description=description,
                body=body,
                skill_path=str(skill_path),
            )

        # Composite scoring with layer blending
        composite = self._blend_layers(static_result, llm_result)

        # Badge assignment
        badge = assign_badge(composite)
        badge_data = badge_info(badge)

        # Grade comparison (if existing grade available)
        comparison = None
        if letter_grade:
            comparison = grade_to_badge_comparison(letter_grade, badge)

        elapsed = time.time() - start

        result = {
            "skill_path": str(skill_path),
            "skill_name": skill_name,
            "composite_score": round(composite, 2),
            "badge": badge,
            "badge_info": badge_data,
            "layers": {
                "static": {
                    "score": static_result["composite_score"],
                    "dimensions": {
                        dim: {
                            "score": data["score"],
                            "weight": DIMENSION_WEIGHTS.get(dim, 0),
                            "details": data["details"],
                        }
                        for dim, data in static_result["dimensions"].items()
                    },
                    "anti_patterns": static_result["anti_patterns"],
                },
            },
            "grade_comparison": comparison,
            "deterministic_score": deterministic_score,
            "elapsed_seconds": round(elapsed, 3),
        }

        # Add LLM layer if available
        if llm_result and llm_result.get("available"):
            result["layers"]["llm"] = {
                "available": True,
                "dimensions": llm_result.get("dimensions", {}),
            }
        elif llm_result:
            result["layers"]["llm"] = {
                "available": False,
                "reason": llm_result.get("reason", "Unknown"),
            }

        # Cache for ranking
        self._eval_cache[str(skill_path)] = result

        return result

    def _blend_layers(
        self,
        static_result: Dict,
        llm_result: Optional[Dict],
    ) -> float:
        """
        Blend layer scores with automatic weight renormalization.

        When LLM layer is unavailable, its weight redistributes to static.
        """
        static_score = static_result["composite_score"]

        if llm_result and llm_result.get("available") and llm_result.get("dimensions"):
            # Extract LLM dimension scores
            llm_scores = {}
            for dim, data in llm_result["dimensions"].items():
                if isinstance(data, dict) and "score" in data:
                    llm_scores[dim] = data["score"]

            if llm_scores:
                # Average LLM dimension scores
                llm_avg = sum(llm_scores.values()) / len(llm_scores)

                # Blend: static * 0.55 + llm * 0.45
                composite = static_score * 0.55 + llm_avg * 0.45
                return max(0.0, min(100.0, composite))

        # Fallback: static only (weight = 1.0)
        return static_score

    def evaluate_batch(
        self,
        skills: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Evaluate a batch of skills.

        Args:
            skills: List of dicts with keys: path, body, fm, grade, score

        Returns:
            List of evaluation results
        """
        results = []
        total = len(skills)

        for i, skill in enumerate(skills):
            path = Path(skill["path"])
            if self.verbose:
                print(f"  [{i + 1}/{total}] Deep eval: {skill.get('name', path.stem)}")

            result = self.evaluate_skill(
                skill_path=path,
                body=skill["body"],
                fm=skill["fm"],
                letter_grade=skill.get("grade"),
                deterministic_score=skill.get("score"),
            )
            results.append(result)

        return results

    def rank_results(
        self,
        results: List[Dict[str, Any]],
        category_map: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Run Elo ranking on evaluation results.

        Args:
            results: Output from evaluate_batch()
            category_map: {skill_path: category} for grouping.
                          If None, derives from directory structure.

        Returns:
            {
                'global_ranking': [(skill_id, rank_data)],
                'category_rankings': {category: [(skill_id, rank_data)]},
                'statistics': {category: {mean, std, ci}},
            }
        """
        # Build category groupings
        skills_by_cat: Dict[str, Dict[str, float]] = {}

        for result in results:
            path = result["skill_path"]
            score = result["composite_score"]

            # Determine category
            if category_map and path in category_map:
                cat = category_map[path]
            else:
                cat = self._infer_category(path)

            if cat not in skills_by_cat:
                skills_by_cat[cat] = {}
            skills_by_cat[cat][path] = score

        # Run per-category tournaments
        cat_rankings = category_rankings(skills_by_cat)

        # Global ranking (flat across all categories)
        all_scores = {r["skill_path"]: r["composite_score"] for r in results}
        global_results = run_round_robin(all_scores) if len(all_scores) >= 2 else {}
        global_ranking = (
            rank_skills(global_results)
            if global_results
            else [
                (
                    r["skill_path"],
                    {"rating": 1500, "composite_score": r["composite_score"], "wins": 0, "losses": 0, "draws": 0},
                )
                for r in results
            ]
        )

        # Per-category statistics
        stats = {}
        for cat, skills in skills_by_cat.items():
            scores = list(skills.values())
            if scores:
                mean = sum(scores) / len(scores)
                ci = bootstrap_ci(scores) if len(scores) >= 2 else (mean, mean)
                stats[cat] = {
                    "mean": round(mean, 2),
                    "count": len(scores),
                    "ci_lower": round(ci[0], 2),
                    "ci_upper": round(ci[1], 2),
                }

        return {
            "global_ranking": global_ranking,
            "category_rankings": cat_rankings,
            "statistics": stats,
        }

    def _infer_category(self, skill_path: str) -> str:
        """Infer category from skill path (plugins/[category]/[plugin]/...)."""
        parts = Path(skill_path).parts
        try:
            plugins_idx = parts.index("plugins")
            if plugins_idx + 1 < len(parts):
                return parts[plugins_idx + 1]
        except ValueError:
            pass
        return "uncategorized"

    def summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate summary statistics from batch evaluation.
        """
        if not results:
            return {"count": 0}

        scores = [r["composite_score"] for r in results]
        badges = [r["badge"] for r in results]

        badge_counts = {}
        for b in badges:
            key = b or "none"
            badge_counts[key] = badge_counts.get(key, 0) + 1

        # Grade alignment analysis
        aligned = 0
        divergent = 0
        for r in results:
            comp = r.get("grade_comparison")
            if comp:
                if comp["alignment"] == "aligned":
                    aligned += 1
                else:
                    divergent += 1

        mean_score = sum(scores) / len(scores)
        ci = bootstrap_ci(scores) if len(scores) >= 2 else (mean_score, mean_score)

        return {
            "count": len(results),
            "mean_composite": round(mean_score, 2),
            "ci_95": (round(ci[0], 2), round(ci[1], 2)),
            "min_composite": round(min(scores), 2),
            "max_composite": round(max(scores), 2),
            "badge_distribution": badge_counts,
            "grade_alignment": {
                "aligned": aligned,
                "divergent": divergent,
            },
            "llm_available": any(r.get("layers", {}).get("llm", {}).get("available", False) for r in results),
        }
