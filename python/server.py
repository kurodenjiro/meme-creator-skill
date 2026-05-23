#!/usr/bin/env python3
"""
server.py
---------
FastAPI server that provides:
  GET  /health             – health check
  GET  /search?q=...&k=5  – semantic search returning top-k meme references
  GET  /image/{filename}   – serve the raw image file
  GET  /memes              – list all indexed memes (paginated)
  GET  /memes/{id}         – get a single meme's metadata
"""

import json
import math
import os
import sqlite3
import struct
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from openai import OpenAI

ROOT_DIR = Path(__file__).resolve().parents[1]
FILES_DIR = ROOT_DIR / "files"

load_dotenv(ROOT_DIR / ".env")

# ── Config ────────────────────────────────────────────────────────────────────
DB_FILE    = FILES_DIR / "memes.db"
IMAGE_DIR  = FILES_DIR / "gallery-dl/twitter/boldleonidas"
EMBED_MODEL = "text-embedding-3-small"

client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
    base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
)

app = FastAPI(
    title="Boldleonidas Meme API",
    description="Semantic search over analyzed meme images",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── DB helpers ────────────────────────────────────────────────────────────────
def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def unpack_embedding(blob: bytes) -> list[float]:
    n = len(blob) // 4
    return list(struct.unpack(f"{n}f", blob))


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    conn = get_conn()
    count = conn.execute("SELECT COUNT(*) FROM memes").fetchone()[0]
    conn.close()
    return {"status": "ok", "indexed_memes": count}


@app.get("/search")
def search(
    q: str = Query(..., description="Search query"),
    k: int = Query(5, ge=1, le=20, description="Number of results"),
):
    """Semantic search: embed query, cosine-rank all memes, return top-k."""
    # Embed the query
    resp = client.embeddings.create(model=EMBED_MODEL, input=[q])
    query_vec = resp.data[0].embedding

    # Load all embeddings from DB
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, image_path, layout, character_position, text_style, "
        "content_structure, description, embedding FROM memes"
    ).fetchall()
    conn.close()

    # Score
    scored = []
    for row in rows:
        meme_vec = unpack_embedding(row["embedding"])
        score    = cosine_similarity(query_vec, meme_vec)
        scored.append((score, row))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:k]

    results = []
    for score, row in top:
        results.append({
            "id":         row["id"],
            "score":      round(score, 4),
            "image_url":  f"/image/{row['id']}",
            "image_path": row["image_path"],
            "layout":            safe_json(row["layout"]),
            "character_position": safe_json(row["character_position"]),
            "text_style":        safe_json(row["text_style"]),
            "content_structure": safe_json(row["content_structure"]),
            "description": row["description"] or "",
        })

    return {"query": q, "k": k, "results": results}


@app.get("/image/{filename}")
def serve_image(filename: str):
    """Serve the raw image by filename (e.g. 2056628945488163266_1.jpg)."""
    path = IMAGE_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Image not found: {filename}")
    return FileResponse(str(path), media_type="image/jpeg")


@app.get("/memes")
def list_memes(
    page: int  = Query(1, ge=1),
    size: int  = Query(20, ge=1, le=100),
):
    """Paginated listing of all indexed memes."""
    offset = (page - 1) * size
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM memes").fetchone()[0]
    rows  = conn.execute(
        "SELECT id, image_path, content_structure, description "
        "FROM memes LIMIT ? OFFSET ?", (size, offset)
    ).fetchall()
    conn.close()

    return {
        "total": total,
        "page": page,
        "size": size,
        "pages": math.ceil(total / size),
        "memes": [
            {
                "id": r["id"],
                "image_url": f"/image/{r['id']}",
                "description": r["description"] or "",
                "content_structure": safe_json(r["content_structure"]),
            }
            for r in rows
        ],
    }


@app.get("/memes/{meme_id}")
def get_meme(meme_id: str):
    """Get full metadata for a single meme."""
    conn = get_conn()
    row  = conn.execute(
        "SELECT id, image_path, layout, character_position, text_style, "
        "content_structure, description FROM memes WHERE id=?", (meme_id,)
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Meme not found")
    return {
        "id":         row["id"],
        "image_url":  f"/image/{row['id']}",
        "image_path": row["image_path"],
        "layout":              safe_json(row["layout"]),
        "character_position":  safe_json(row["character_position"]),
        "text_style":          safe_json(row["text_style"]),
        "content_structure":   safe_json(row["content_structure"]),
        "description":         row["description"] or "",
    }


# ── Utils ─────────────────────────────────────────────────────────────────────
def safe_json(val):
    if val is None:
        return {}
    if isinstance(val, str):
        try:
            return json.loads(val)
        except Exception:
            return val
    return val


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
