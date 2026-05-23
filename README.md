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

## Tạo meme (web UI)

Trang **`/create`** — luồng đầy đủ:

1. Nhập **trend** và chọn **nhân vật** (có thể thêm nhân vật mới).
2. **Tạo kịch bản** — GPT-4o đọc `files/style.md`, `SKILL.md`, tìm ảnh tham khảo trong Supabase, trả về blueprint + image prompt.
3. **Tạo ảnh** — GPT-4o vision phân tích ảnh tham khảo + kịch bản, gửi prompt lên `OPENAI_IMAGE_MODEL` (mặc định `gpt-image-1`).

API:

- `GET/POST /api/characters`
- `POST /api/generate/script` — `{ trend, characterIds, hint? }`
- `POST /api/generate/image` — `{ script, characterIds, referenceIds }`

CLI (Python, cần `python server.py`):

```sh
python python/generate_meme_concept.py "trend text" "Wizard"
python python/generate_with_references.py "wizard pig crypto panic"
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
