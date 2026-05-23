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

## Deploy (Vercel)

1. Import `https://github.com/kurodenjiro/meme-creator-skill` as a Vercel project (root directory: repo root).
2. Add environment variables from `.env.example` (at minimum `PUBLIC_SUPABASE_URL`, `PUBLIC_SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `OPENAI_API_KEY`, and `IMAGE_DIR=files/gallery-dl/twitter/boldleonidas`).
3. Deploy. The app uses `@sveltejs/adapter-vercel` and bundles meme images for `/api/image/*`.

Note: the image archive is ~220MB in git, which can approach Vercel deployment size limits on smaller plans.

## Common Commands

```sh
npm run check
npm run build
```

```sh
python python/index_embeddings.py
python python/generate_with_references.py "wizard pig crypto panic"
```
