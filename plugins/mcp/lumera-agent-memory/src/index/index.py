"""
Local SQLite FTS5 index for memory search.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


class MemoryIndex:
    """SQLite FTS5-based memory index."""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize memory index.

        Args:
            db_path: Path to SQLite database (default: ~/.lumera/index.db)
        """
        if db_path is None:
            db_path = Path.home() / ".lumera" / "index.db"

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

    def _init_db(self):
        """Initialize database schema with FTS5."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        # Main memories table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                cascade_uri TEXT NOT NULL,
                memory_card TEXT,
                tags TEXT,
                metadata TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # FTS5 virtual table for full-text search
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                session_id,
                title,
                content,
                keywords,
                tokenize='porter unicode61'
            )
        """)

        # Index for cascade_uri lookups
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_cascade_uri
            ON memories(cascade_uri)
        """)

        # Index for tags
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at
            ON memories(created_at)
        """)

        conn.commit()
        conn.close()

    def store_memory(
        self,
        session_id: str,
        cascade_uri: str,
        memory_card: dict,
        tags: list[str] = None,
        metadata: dict = None
    ) -> bool:
        """
        Store memory in index.

        Returns:
            True if stored successfully
        """
        conn = sqlite3.connect(self.db_path)
        now = datetime.utcnow().isoformat()

        try:
            # Insert into main table
            conn.execute("""
                INSERT OR REPLACE INTO memories
                (session_id, cascade_uri, memory_card, tags, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                cascade_uri,
                json.dumps(memory_card),
                json.dumps(tags or []),
                json.dumps(metadata or {}),
                now,
                now
            ))

            # Insert into FTS table
            title = memory_card.get("title", "")
            content = " ".join(memory_card.get("summary_bullets", []))
            keywords = " ".join(memory_card.get("keywords", []))

            conn.execute("""
                INSERT OR REPLACE INTO memories_fts
                (rowid, session_id, title, content, keywords)
                VALUES (
                    (SELECT id FROM memories WHERE session_id = ?),
                    ?, ?, ?, ?
                )
            """, (session_id, session_id, title, content, keywords))

            conn.commit()
            return True

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def search(
        self,
        query: str,
        tags: Optional[list[str]] = None,
        time_range: Optional[dict] = None,
        limit: int = 10
    ) -> list[dict]:
        """
        Search memories using FTS5.

        Args:
            query: Search query text
            tags: Optional tag filters
            time_range: Optional time range {start, end}
            limit: Max results

        Returns:
            List of search hits with scores
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        # Build FTS query
        sql_parts = ["""
            SELECT
                m.session_id,
                m.cascade_uri,
                m.memory_card,
                m.tags,
                m.created_at,
                fts.rank as score
            FROM memories m
            JOIN memories_fts fts ON m.id = fts.rowid
            WHERE memories_fts MATCH ?
        """]

        params = [query]

        # Add tag filter
        if tags:
            sql_parts.append("AND (" + " OR ".join(["m.tags LIKE ?" for _ in tags]) + ")")
            params.extend([f'%"{tag}"%' for tag in tags])

        # Add time range filter
        if time_range:
            if time_range.get("start"):
                sql_parts.append("AND m.created_at >= ?")
                params.append(time_range["start"])
            if time_range.get("end"):
                sql_parts.append("AND m.created_at <= ?")
                params.append(time_range["end"])

        sql_parts.append("ORDER BY fts.rank LIMIT ?")
        params.append(limit)

        sql = " ".join(sql_parts)

        cursor = conn.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()

        # Format results
        hits = []
        for row in rows:
            memory_card = json.loads(row["memory_card"])
            tags_list = json.loads(row["tags"])

            # Create snippet from memory card
            snippet = memory_card.get("title", "")
            if memory_card.get("summary_bullets"):
                snippet += " - " + memory_card["summary_bullets"][0][:100]

            hits.append({
                "session_id": row["session_id"],
                "cascade_uri": row["cascade_uri"],
                "title": memory_card.get("title", ""),
                "snippet": snippet,
                "tags": tags_list,
                "created_at": row["created_at"],
                "score": abs(row["score"])  # FTS5 rank is negative
            })

        return hits

    def get_by_cascade_uri(self, cascade_uri: str) -> Optional[dict]:
        """Get memory entry by Cascade URI."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        cursor = conn.execute("""
            SELECT * FROM memories WHERE cascade_uri = ?
        """, (cascade_uri,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "session_id": row["session_id"],
            "cascade_uri": row["cascade_uri"],
            "memory_card": json.loads(row["memory_card"]),
            "tags": json.loads(row["tags"]),
            "metadata": json.loads(row["metadata"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }
