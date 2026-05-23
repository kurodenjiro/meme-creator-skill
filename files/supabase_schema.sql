-- ============================================================
-- Run this in Supabase SQL Editor (Dashboard → SQL Editor)
-- ============================================================

-- 1. Enable pgvector extension
create extension if not exists vector;

-- 2. Create memes table
create table if not exists memes (
  id                  text primary key,
  image_path          text,
  layout              jsonb,
  character_position  jsonb,
  text_style          jsonb,
  content_structure   text,
  description         text,
  embedding           vector(1536)
);

-- 3. IVFFlat index for fast ANN search (build after inserting data)
-- Run this AFTER migration is complete:
-- create index on memes using ivfflat (embedding vector_cosine_ops) with (lists = 50);

-- 4. Semantic search function
create or replace function match_memes(
  query_embedding vector(1536),
  match_count     int default 5
)
returns table (
  id                  text,
  image_path          text,
  layout              jsonb,
  character_position  jsonb,
  text_style          jsonb,
  content_structure   text,
  description         text,
  similarity          float
)
language sql stable
as $$
  select
    id,
    image_path,
    layout,
    character_position,
    text_style,
    content_structure,
    description,
    1 - (embedding <=> query_embedding) as similarity
  from memes
  order by embedding <=> query_embedding
  limit match_count;
$$;
