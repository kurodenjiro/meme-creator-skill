#!/usr/bin/env python3
"""
index_embeddings.py
-------------------
Reads analysis_results.json, generates OpenAI text embeddings for each image's
description, and stores everything into memes.db (SQLite).

Schema:
  memes(id TEXT PRIMARY KEY, image_path TEXT, layout TEXT, character_position TEXT,
        text_style TEXT, content_structure TEXT, description TEXT,
        embedding BLOB)
"""

import json
import os
import sqlite3
import struct
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

ROOT_DIR = Path(__file__).resolve().parents[1]
FILES_DIR = ROOT_DIR / "files"

load_dotenv(ROOT_DIR / ".env")

# ── Config ────────────────────────────────────────────────────────────────────
ANALYSIS_FILE = FILES_DIR / "analysis_results.json"
DB_FILE       = FILES_DIR / "memes.db"
IMAGE_DIR     = FILES_DIR / "gallery-dl/twitter/boldleonidas"
EMBED_MODEL   = "text-embedding-3-small"
BATCH_SIZE    = 100          # embeddings per API call (max 2048)
SLEEP_BETWEEN = 0.3          # seconds between batches

client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
    base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
)


# ── Helpers ───────────────────────────────────────────────────────────────────
def pack_embedding(vec: list[float]) -> bytes:
    """Store as raw float32 binary blob."""
    return struct.pack(f"{len(vec)}f", *vec)


def unpack_embedding(blob: bytes) -> list[float]:
    n = len(blob) // 4
    return list(struct.unpack(f"{n}f", blob))


def build_text(filename: str, data: dict) -> str:
    """Flatten all analysis fields into a single searchable string."""
    parts = [f"Image: {filename}"]

    # Layout
    layout = data.get("layout", {})
    if isinstance(layout, dict):
        parts += [f"{k}: {v}" for k, v in layout.items() if v]
    elif isinstance(layout, str):
        parts.append(f"layout: {layout}")

    # Character position
    char_pos = data.get("character_position", {})
    if isinstance(char_pos, dict):
        parts += [f"{k}: {v}" for k, v in char_pos.items() if v]
    elif isinstance(char_pos, str):
        parts.append(f"character position: {char_pos}")

    # Text style
    text_style = data.get("text_style", {})
    if isinstance(text_style, dict):
        parts += [f"{k}: {v}" for k, v in text_style.items() if v]
    elif isinstance(text_style, str):
        parts.append(f"text style: {text_style}")

    # Content structure
    cs = data.get("content_structure", "")
    if isinstance(cs, dict):
        parts += [f"{k}: {v}" for k, v in cs.items() if v]
    elif cs:
        parts.append(f"content structure: {cs}")

    # Description
    desc = data.get("description", "")
    if desc:
        parts.append(f"description: {desc}")

    return "\n".join(str(p) for p in parts if p)


# ── Database ──────────────────────────────────────────────────────────────────
def init_db(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memes (
            id                TEXT PRIMARY KEY,
            image_path        TEXT,
            layout            TEXT,
            character_position TEXT,
            text_style        TEXT,
            content_structure TEXT,
            description       TEXT,
            embedding         BLOB
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_id ON memes(id)")
    conn.commit()


def already_indexed(conn: sqlite3.Connection, meme_id: str) -> bool:
    row = conn.execute("SELECT 1 FROM memes WHERE id=?", (meme_id,)).fetchone()
    return row is not None


def _safe_str(val) -> str:
    """Always return a JSON string — handles str, dict, list, None."""
    if val is None:
        return ""
    if isinstance(val, str):
        return val
    return json.dumps(val, ensure_ascii=False)


def upsert_meme(conn: sqlite3.Connection, meme_id: str, image_path: str,
                data: dict, embedding: list[float]):
    conn.execute("""
        INSERT OR REPLACE INTO memes
            (id, image_path, layout, character_position, text_style,
             content_structure, description, embedding)
        VALUES (?,?,?,?,?,?,?,?)
    """, (
        meme_id,
        image_path,
        _safe_str(data.get("layout", {})),
        _safe_str(data.get("character_position", {})),
        _safe_str(data.get("text_style", {})),
        _safe_str(data.get("content_structure", "")),
        _safe_str(data.get("description", "")),
        pack_embedding(embedding),
    ))


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("📂 Loading analysis_results.json …")
    raw = json.loads(ANALYSIS_FILE.read_text(encoding="utf-8"))

    conn = sqlite3.connect(DB_FILE)
    init_db(conn)

    # Filter out already indexed
    todo = {
        fname: data
        for fname, data in raw.items()
        if not already_indexed(conn, fname)
    }
    print(f"✅ Already indexed: {len(raw) - len(todo)} / {len(raw)}")
    print(f"🔢 To index: {len(todo)}")

    if not todo:
        print("Nothing to do — all images are already indexed!")
        conn.close()
        return

    items = list(todo.items())
    total = len(items)
    indexed = 0
    errors  = 0

    for batch_start in range(0, total, BATCH_SIZE):
        batch = items[batch_start: batch_start + BATCH_SIZE]
        fnames  = [b[0] for b in batch]
        texts   = [build_text(b[0], b[1]) for b in batch]

        print(f"  📡 Embedding batch {batch_start // BATCH_SIZE + 1} "
              f"({batch_start + 1}–{min(batch_start + BATCH_SIZE, total)} / {total}) …", end=" ")

        try:
            resp = client.embeddings.create(model=EMBED_MODEL, input=texts)
            embeddings = [r.embedding for r in resp.data]

            for (fname, data), emb in zip(batch, embeddings):
                img_path = str(IMAGE_DIR / fname)
                upsert_meme(conn, fname, img_path, data, emb)
                indexed += 1

            conn.commit()
            print(f"✓ {len(batch)} done")
        except Exception as e:
            errors += len(batch)
            print(f"✗ ERROR: {e}")

        if batch_start + BATCH_SIZE < total:
            time.sleep(SLEEP_BETWEEN)

    conn.close()
    print(f"\n🎉 Indexing complete: {indexed} indexed, {errors} errors")
    print(f"   Database: {DB_FILE.resolve()}")


if __name__ == "__main__":
    main()
