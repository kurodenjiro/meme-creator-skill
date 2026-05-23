# Meme Creator Skill

Boldleonidas-style meme reference search and generation workspace.

## Structure

- `website/` - SvelteKit search UI for the meme reference archive.
- `python/` - Python API, indexing, analysis, Supabase migration, and generation scripts.
- `files/` - Local data files: source media, analysis JSON, SQLite index, generated outputs, and SQL schema.
- `SKILL.md` - Meme creation style/instruction guide.

## Setup

1. Copy `.env.example` to `.env` and fill in the Python/OpenAI/Supabase values.
2. Copy `website/.env.example` to `website/.env` and fill in the website values.
3. Install website dependencies:

```sh
cd website
npm install
npm run dev
```

4. Run the local Python API when using the reference generator:

```sh
python python/server.py
```

## Common Commands

```sh
cd website
npm run check
npm run build
```

```sh
python python/index_embeddings.py
python python/generate_with_references.py "wizard pig crypto panic"
```
