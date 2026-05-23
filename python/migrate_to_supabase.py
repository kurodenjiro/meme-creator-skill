#!/usr/bin/env python3
"""
migrate_to_supabase.py
-----------------------
Reads memes.db (SQLite with float32 blob embeddings) and upserts
all rows into Supabase PostgreSQL with pgvector.

Run AFTER executing supabase_schema.sql in the Supabase dashboard.
"""

import json
import os
import sqlite3
import struct
import time
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

ROOT_DIR = Path(__file__).resolve().parents[1]
FILES_DIR = ROOT_DIR / "files"

load_dotenv(ROOT_DIR / ".env")

# ── Config ────────────────────────────────────────────────────────────────────
DB_FILE        = FILES_DIR / "memes.db"
SUPABASE_URL   = os.environ["SUPABASE_URL"]
SUPABASE_KEY   = os.environ["SUPABASE_SERVICE_ROLE_KEY"]   # use service role for writes
BATCH_SIZE     = 50    # rows per upsert batch
SLEEP_BETWEEN  = 0.2  # seconds


def unpack_embedding(blob: bytes) -> list[float]:
    n = len(blob) // 4
    return list(struct.unpack(f"{n}f", blob))


def safe_json(val):
    if val is None:
        return None
    if isinstance(val, str):
        try:
            return json.loads(val)
        except Exception:
            return val
    return val


def main():
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    print("📂 Reading memes.db …")
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, image_path, layout, character_position, text_style, "
        "content_structure, description, embedding FROM memes"
    ).fetchall()
    conn.close()
    print(f"   {len(rows)} rows to migrate")

    total   = len(rows)
    done    = 0
    errors  = 0

    for i in range(0, total, BATCH_SIZE):
        batch_rows = rows[i : i + BATCH_SIZE]
        records = []
        for r in batch_rows:
            try:
                emb = unpack_embedding(r["embedding"])
                records.append({
                    "id":                 r["id"],
                    "image_path":         r["image_path"],
                    "layout":             safe_json(r["layout"]),
                    "character_position": safe_json(r["character_position"]),
                    "text_style":         safe_json(r["text_style"]),
                    "content_structure":  r["content_structure"] or "",
                    "description":        r["description"] or "",
                    "embedding":          emb,
                })
            except Exception as e:
                print(f"   ⚠️  Skipping {r['id']}: {e}")
                errors += 1

        print(f"  ⬆️  Upserting rows {i+1}–{min(i+BATCH_SIZE, total)} / {total} …", end=" ")
        try:
            result = supabase.table("memes").upsert(records, on_conflict="id").execute()
            done += len(records)
            print(f"✓ {len(records)} done")
        except Exception as e:
            errors += len(records)
            print(f"✗ ERROR: {e}")

        if i + BATCH_SIZE < total:
            time.sleep(SLEEP_BETWEEN)

    print(f"\n🎉 Migration complete: {done} upserted, {errors} errors")
    print(f"   Supabase project: {SUPABASE_URL}")


if __name__ == "__main__":
    main()
