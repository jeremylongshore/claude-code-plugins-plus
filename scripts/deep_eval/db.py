"""
Freshie database integration for deep evaluation results.

Writes to new tables in freshie/inventory.sqlite:
  - deep_eval_results: Per-skill composite scores, badges, layer data
  - deep_eval_dimensions: Per-skill per-dimension breakdowns
  - deep_eval_rankings: Elo ratings per category
  - deep_eval_runs: Run metadata (timestamp, config, summary stats)

Author: Jeremy Longshore <jeremy@intentsolutions.io>
"""

import json
import sqlite3
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


VALIDATOR_VERSION = "deep-eval-1.0.0"


def populate_deep_eval_db(
    db_path: str,
    results: List[Dict[str, Any]],
    summary: Dict[str, Any],
    rankings: Optional[Dict] = None,
    run_config: Optional[Dict] = None,
) -> int:
    """
    Write deep evaluation results to freshie SQLite database.

    Args:
        db_path: Path to inventory.sqlite
        results: List of per-skill evaluation results
        summary: Summary statistics
        rankings: Optional ranking data
        run_config: Optional run configuration metadata

    Returns:
        run_id for this evaluation run
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Create tables if they don't exist
    _create_tables(c)

    now = datetime.now(timezone.utc).isoformat()

    # Insert run metadata
    c.execute(
        """INSERT INTO deep_eval_runs
        (run_timestamp, skill_count, mean_composite, ci_lower, ci_upper,
         llm_available, config_json, validator_version)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            now,
            summary.get("count", 0),
            summary.get("mean_composite", 0),
            summary.get("ci_95", (0, 0))[0],
            summary.get("ci_95", (0, 0))[1],
            1 if summary.get("llm_available") else 0,
            json.dumps(run_config or {}),
            VALIDATOR_VERSION,
        ),
    )

    run_id = c.lastrowid

    # Insert per-skill results
    for result in results:
        skill_path = result.get("skill_path", "")
        composite = result.get("composite_score", 0)
        badge = result.get("badge")
        det_score = result.get("deterministic_score")
        elapsed = result.get("elapsed_seconds", 0)

        # Grade comparison
        comparison = result.get("grade_comparison", {})
        letter_grade = comparison.get("letter_grade") if comparison else None
        alignment = comparison.get("alignment") if comparison else None

        # Anti-patterns
        anti = result.get("layers", {}).get("static", {}).get("anti_patterns", {})
        anti_count = anti.get("count", 0) if anti else 0
        anti_penalty = anti.get("penalty_pct", 0) if anti else 0

        # LLM layer availability
        llm_layer = result.get("layers", {}).get("llm", {})
        llm_available = 1 if llm_layer.get("available") else 0

        c.execute(
            """INSERT OR REPLACE INTO deep_eval_results
            (run_id, skill_path, composite_score, badge, deterministic_score,
             letter_grade, alignment, anti_pattern_count, anti_pattern_penalty,
             llm_available, elapsed_seconds, evaluated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                run_id,
                skill_path,
                composite,
                badge,
                det_score,
                letter_grade,
                alignment,
                anti_count,
                anti_penalty,
                llm_available,
                elapsed,
                now,
            ),
        )

        result_id = c.lastrowid

        # Insert dimension breakdowns
        static_dims = result.get("layers", {}).get("static", {}).get("dimensions", {})
        for dim_name, dim_data in static_dims.items():
            c.execute(
                """INSERT INTO deep_eval_dimensions
                (run_id, result_id, skill_path, dimension_name, layer,
                 score, weight, details_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    run_id,
                    result_id,
                    skill_path,
                    dim_name,
                    "static",
                    dim_data.get("score", 0),
                    dim_data.get("weight", 0),
                    json.dumps(dim_data.get("details", [])),
                ),
            )

        # Insert LLM dimensions if available
        llm_dims = llm_layer.get("dimensions", {}) if llm_layer else {}
        for dim_name, dim_data in llm_dims.items():
            if isinstance(dim_data, dict):
                c.execute(
                    """INSERT INTO deep_eval_dimensions
                    (run_id, result_id, skill_path, dimension_name, layer,
                     score, weight, details_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (run_id, result_id, skill_path, dim_name, "llm", dim_data.get("score", 0), 0, json.dumps(dim_data)),
                )

    # Insert rankings if available
    if rankings:
        # Global rankings
        global_ranking = rankings.get("global_ranking", [])
        for rank_pos, (skill_id, rank_data) in enumerate(global_ranking):
            c.execute(
                """INSERT INTO deep_eval_rankings
                (run_id, skill_path, category, elo_rating, rank_position,
                 wins, losses, draws, composite_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    run_id,
                    skill_id,
                    "__global__",
                    rank_data.get("rating", 1500),
                    rank_pos + 1,
                    rank_data.get("wins", 0),
                    rank_data.get("losses", 0),
                    rank_data.get("draws", 0),
                    rank_data.get("composite_score", 0),
                ),
            )

        # Category rankings
        for cat, ranked in rankings.get("category_rankings", {}).items():
            for rank_pos, (skill_id, rank_data) in enumerate(ranked):
                c.execute(
                    """INSERT INTO deep_eval_rankings
                    (run_id, skill_path, category, elo_rating, rank_position,
                     wins, losses, draws, composite_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        run_id,
                        skill_id,
                        cat,
                        rank_data.get("rating", 1500),
                        rank_pos + 1,
                        rank_data.get("wins", 0),
                        rank_data.get("losses", 0),
                        rank_data.get("draws", 0),
                        rank_data.get("composite_score", 0),
                    ),
                )

    conn.commit()
    conn.close()

    return run_id


def _create_tables(cursor):
    """Create deep_eval tables if they don't exist."""
    cursor.execute("""CREATE TABLE IF NOT EXISTS deep_eval_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_timestamp TEXT NOT NULL,
        skill_count INTEGER,
        mean_composite REAL,
        ci_lower REAL,
        ci_upper REAL,
        llm_available INTEGER DEFAULT 0,
        config_json TEXT,
        validator_version TEXT
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS deep_eval_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id INTEGER NOT NULL,
        skill_path TEXT NOT NULL,
        composite_score REAL,
        badge TEXT,
        deterministic_score INTEGER,
        letter_grade TEXT,
        alignment TEXT,
        anti_pattern_count INTEGER DEFAULT 0,
        anti_pattern_penalty REAL DEFAULT 0,
        llm_available INTEGER DEFAULT 0,
        elapsed_seconds REAL,
        evaluated_at TEXT,
        FOREIGN KEY (run_id) REFERENCES deep_eval_runs(id),
        UNIQUE(run_id, skill_path)
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS deep_eval_dimensions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id INTEGER NOT NULL,
        result_id INTEGER,
        skill_path TEXT NOT NULL,
        dimension_name TEXT NOT NULL,
        layer TEXT NOT NULL,
        score REAL,
        weight REAL,
        details_json TEXT,
        FOREIGN KEY (run_id) REFERENCES deep_eval_runs(id),
        FOREIGN KEY (result_id) REFERENCES deep_eval_results(id)
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS deep_eval_rankings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id INTEGER NOT NULL,
        skill_path TEXT NOT NULL,
        category TEXT NOT NULL,
        elo_rating REAL,
        rank_position INTEGER,
        wins INTEGER DEFAULT 0,
        losses INTEGER DEFAULT 0,
        draws INTEGER DEFAULT 0,
        composite_score REAL,
        FOREIGN KEY (run_id) REFERENCES deep_eval_runs(id)
    )""")

    # Indexes for common queries
    cursor.execute("""CREATE INDEX IF NOT EXISTS idx_deep_eval_results_run
        ON deep_eval_results(run_id)""")
    cursor.execute("""CREATE INDEX IF NOT EXISTS idx_deep_eval_results_path
        ON deep_eval_results(skill_path)""")
    cursor.execute("""CREATE INDEX IF NOT EXISTS idx_deep_eval_dims_run
        ON deep_eval_dimensions(run_id)""")
    cursor.execute("""CREATE INDEX IF NOT EXISTS idx_deep_eval_rankings_run
        ON deep_eval_rankings(run_id, category)""")
