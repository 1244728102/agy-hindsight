"""SQLite-backed Hindsight project memory bank for Antigravity."""

from __future__ import annotations

import json
import os
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

USER_REQ_RE = re.compile(r"<USER_REQUEST>\s*(.*?)\s*</USER_REQUEST>", re.DOTALL)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_brain_dir() -> Path:
    env_dir = os.environ.get("AGY_BRAIN_DIR")
    if env_dir:
        return Path(env_dir)
    return Path.home() / ".gemini" / "antigravity" / "brain"


def _clean_user(raw: str) -> str:
    m = USER_REQ_RE.search(raw or "")
    txt = m.group(1) if m else (raw or "")
    txt = re.sub(r"<ADDITIONAL_METADATA>.*?</ADDITIONAL_METADATA>", "", txt, flags=re.DOTALL)
    return txt.strip()


class MemoryBank:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "hindsight.db"
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pages (
                    id TEXT PRIMARY KEY,
                    project TEXT NOT NULL DEFAULT 'default',
                    category TEXT NOT NULL DEFAULT 'architecture',
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tags TEXT NOT NULL DEFAULT '[]',
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT NOT NULL,
                    project TEXT NOT NULL DEFAULT 'default',
                    kind TEXT NOT NULL DEFAULT 'conversation',
                    snippet TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mem_src ON memories(source_id)")

    def list_pages(self, project: str | None = None, category: str | None = None) -> list[dict[str, Any]]:
        sql = "SELECT id, project, category, title, tags, updated_at, substr(content, 1, 180) AS preview FROM pages WHERE 1=1"
        params: list[Any] = []
        if project:
            sql += " AND project = ?"
            params.append(project)
        if category:
            sql += " AND category = ?"
            params.append(category)
        sql += " ORDER BY updated_at DESC"
        with self._conn() as conn:
            rows = conn.execute(sql, params).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["tags"] = json.loads(d.get("tags") or "[]")
            out.append(d)
        return out

    def search_pages(self, query: str, project: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        q = f"%{query}%"
        sql = "SELECT id, project, category, title, tags, updated_at, substr(content, 1, 200) AS preview FROM pages WHERE (title LIKE ? OR content LIKE ? OR tags LIKE ?)"
        params: list[Any] = [q, q, q]
        if project:
            sql += " AND project = ?"
            params.append(project)
        sql += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)
        with self._conn() as conn:
            rows = conn.execute(sql, params).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["tags"] = json.loads(d.get("tags") or "[]")
            out.append(d)
        return out

    def read_page(self, page_id: str) -> dict[str, Any] | None:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM pages WHERE id = ?", (page_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["tags"] = json.loads(d.get("tags") or "[]")
        return d

    def upsert_page(
        self,
        title: str,
        content: str,
        category: str = "architecture",
        project: str = "default",
        tags: list[str] | None = None,
        page_id: str | None = None,
    ) -> dict[str, Any]:
        pid = page_id or str(uuid.uuid4())[:8]
        ts = now_iso()
        tags_json = json.dumps(tags or [], ensure_ascii=False)
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO pages (id, project, category, title, content, tags, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                  project=excluded.project,
                  category=excluded.category,
                  title=excluded.title,
                  content=excluded.content,
                  tags=excluded.tags,
                  updated_at=excluded.updated_at
                """,
                (pid, project or "default", category or "architecture", title.strip(), content.strip(), tags_json, ts),
            )
        return {"id": pid, "project": project, "category": category, "title": title, "tags": tags or [], "updated_at": ts}

    def ingest_conversations(self, limit: int = 20) -> dict[str, Any]:
        brain = get_brain_dir()
        if not brain.is_dir():
            return {"indexed_sessions": 0, "added_memories": 0}

        convs = []
        for d in brain.iterdir():
            tp = d / ".system_generated" / "logs" / "transcript.jsonl"
            if tp.is_file():
                convs.append((tp.stat().st_mtime, d.name, tp))
        convs.sort(reverse=True)

        added = 0
        indexed = 0
        with self._conn() as conn:
            existing = {r[0] for r in conn.execute("SELECT DISTINCT source_id FROM memories").fetchall()}
            for _, cid, tp in convs[:limit]:
                if cid in existing:
                    continue
                indexed += 1
                snippets: list[str] = []
                with tp.open("r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        try:
                            rec = json.loads(line)
                        except Exception:
                            continue
                        if rec.get("type") == "USER_INPUT":
                            txt = _clean_user(rec.get("content", ""))
                            if txt:
                                snippets.append("[用户] " + txt[:300])
                        elif rec.get("type") == "PLANNER_RESPONSE" and rec.get("content"):
                            snippets.append("[结论] " + str(rec["content"])[:300])
                if snippets:
                    joined = "\n".join(snippets[:12])
                    conn.execute(
                        "INSERT INTO memories (source_id, project, kind, snippet, created_at) VALUES (?, ?, ?, ?, ?)",
                        (cid, "Antigravity", "conversation", joined, now_iso()),
                    )
                    added += 1
        return {"indexed_sessions": indexed, "added_memories": added}

    def recall(self, query: str, limit: int = 15) -> dict[str, Any]:
        pages = self.search_pages(query, limit=limit)
        q = f"%{query}%"
        with self._conn() as conn:
            mem_rows = conn.execute(
                "SELECT id, source_id, project, kind, snippet, created_at FROM memories WHERE snippet LIKE ? ORDER BY id DESC LIMIT ?",
                (q, limit),
            ).fetchall()
        return {"query": query, "pages": pages, "memories": [dict(r) for r in mem_rows]}

    def summary(self) -> dict[str, Any]:
        with self._conn() as conn:
            p_cnt = conn.execute("SELECT COUNT(*) FROM pages").fetchone()[0]
            m_cnt = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        return {"page_count": p_cnt, "memory_count": m_cnt, "pages": self.list_pages()}
