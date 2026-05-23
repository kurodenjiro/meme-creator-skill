# Meme Creator Skill

Boldleonidas-style meme reference search and generation workspace.

## Structure

- `src/`, `static/`, and root `package.json` - SvelteKit search UI, ready for Vercel root deploy.
- `python/` - Python API, indexing, analysis, Supabase migration, and generation scripts.
- `files/` - Local data files: source media, analysis JSON, SQLite index, generated outputs, and SQL schema.
- `SKILL.md` - Meme creation style/instruction guide.

## Setup

1. Copy `.env.example` to `.env` and fill in the OpenAI/Supabase values.
2. Install website dependencies:

```sh
npm install
npm run dev
```

3. Run the local Python API when using the reference generator:

```sh
python python/server.py
```

## Common Commands

```sh
npm run check
npm run build
```

```sh
python python/index_embeddings.py
python python/generate_with_references.py "wizard pig crypto panic"
```
