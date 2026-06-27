# OceanGPT

A marine intelligence dashboard combining a live chat assistant (RAG + tool-calling)
with real-time ocean data widgets — species occurrences, tide gauges, and global
wave/sea-temperature conditions.

**Live:**
- Frontend: https://oceangpt-neon.vercel.app
- Backend API docs: https://oceangpt-backend-is5z.onrender.com/docs

Runs entirely on free tiers: **Groq** for chat (free, no card required),
**fastembed** for local embeddings (runs in-process, zero API cost), **Render**
for backend hosting, **Vercel** for the frontend.

## Architecture

```
oceangpt/
├── backend/    FastAPI + Groq (chat/tool-calling) + fastembed (local embeddings)
└── frontend/   Next.js 16 + React + Tailwind
```

**Data sources (all free, no API key required):**
- [OBIS](https://api.obis.org/) — species occurrence records
- [WoRMS](https://www.marinespecies.org/rest/) — authoritative marine taxonomy
- [NOAA CO-OPS](https://api.tidesandcurrents.noaa.gov/api/prod/) — US tide/water-level stations
- [Open-Meteo Marine](https://open-meteo.com/en/docs/marine-weather-api) — global wave height/period/direction + sea surface temperature

**How the chat assistant decides what to use:** The backend retrieves relevant
chunks from a small curated knowledge base (species facts, oceanography glossary)
via local embedding similarity search (fastembed, ONNX-based, no GPU/torch needed),
and separately gives the Groq-hosted LLM (`llama-3.3-70b-versatile`) a set of
function-calling tools wired to the live APIs above. The model decides per-turn
whether a question needs live data, retrieved background knowledge, or both — see
`backend/app/chat/agent.py` for the orchestration logic.

## Running it locally

### Backend

```bash
cd backend
python3 -m venv venv && source venv/bin/activate   # optional but recommended
pip install -r requirements.txt
cp .env.example .env   # then edit .env and add your GROQ_API_KEY
uvicorn app.main:app --reload --port 8000
```

Get a free Groq API key (no credit card) at https://console.groq.com/keys.

The first startup downloads the local embedding model (~130MB, one-time, cached
afterward) and embeds the knowledge base. This needs internet access to
huggingface.co on first run only.

Visit `http://localhost:8000/docs` for interactive API docs (Swagger UI).

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local   # set NEXT_PUBLIC_API_BASE_URL to your backend
npm run dev
```

Visit `http://localhost:3000`.

## Deploying it (Render + Vercel, both free) — as actually done

This is a monorepo: `frontend/`, `backend/`, and `render.yaml` all live at the
repo root, side by side.

### Backend → Render

1. Push the repo to GitHub.
2. On [render.com](https://render.com): **New → Blueprint** → select the repo.
   Render reads `render.yaml` at the root automatically (Blueprint Path left blank).
3. Fill in the secret env vars it prompts for:
   - `GROQ_API_KEY` → from console.groq.com/keys
   - `ALLOWED_ORIGINS` → your Vercel URL (see step below; a placeholder is fine to start)
4. Deploy. Confirm it's actually live by visiting `<your-render-url>/api/health` —
   should return `{"status":"ok","knowledge_base_docs":11}`.

### Frontend → Vercel

1. On [vercel.com](https://vercel.com): **Add New → Project** → import the same repo.
2. **Project Name** must be lowercase (Vercel rejects `OceanGPT`, use `oceangpt`).
3. Set **Root Directory** to `frontend`. This is the key step in a monorepo — without
   it, Vercel tries to auto-detect *both* `frontend` and `backend` as separate
   services and asks for an `experimentalServices` block in `vercel.json`. Setting
   Root Directory to `frontend` scopes the whole import to just the Next.js app,
   which is what you want (the backend is already deployed separately on Render).
4. Add env var `NEXT_PUBLIC_API_BASE_URL` = your Render backend URL.
5. Deploy.

### Close the loop

Go back to Render → Environment → set `ALLOWED_ORIGINS` to the real Vercel URL,
save (triggers a quick redeploy, not a full rebuild). Reload the Vercel site —
the tide/sea-conditions widgets and chat should now reach the backend.

**Free tier note:** Render's free web service spins down after inactivity; the
first request after idle time can take 30-50 seconds to wake up. Normal, not a bug.

## Troubleshooting log (issues hit during deployment, and the actual fixes)

These were all real failures encountered deploying this exact project — kept here
since they're easy to hit again on similar FastAPI + Render setups.

**1. Build failed: `pydantic-core` / `maturin failed` / Rust toolchain error**
Render's Python defaulted to a brand-new version (3.14) that didn't yet have
prebuilt wheels for the pinned `pydantic` version, so pip tried to compile
`pydantic-core` from Rust source and failed (no Rust toolchain, read-only filesystem).
*Fix:* added a `PYTHON_VERSION` env var (`3.11.9`) in `render.yaml`, and separately
in the Render dashboard the first time it was tried. A `runtime.txt` file was tried
first but Render didn't pick it up — the env var is the reliable method.

**2. Backend deployed but crashed on startup: `openai.RateLimitError: insufficient_quota`**
The original design used OpenAI for both chat and embeddings. OpenAI requires a
funded billing account even for cheap models — a fresh API key with $0 credit
gets a 429 on the very first call. *Fix:* switched the whole project off OpenAI —
chat moved to **Groq** (free tier, OpenAI-compatible API, just a different
`base_url` and API key), embeddings moved to **fastembed** (runs locally,
no API call at all, so no billing dependency for that part of the stack).

**3. `sentence-transformers` + `torch` were the first attempt at local embeddings**
This technically works but installs ~500MB+ (full PyTorch), which is excessive
and memory-risky on Render's free tier (~512MB RAM limit). *Fix:* switched to
**fastembed** (ONNX Runtime based, ~55MB installed, no PyTorch dependency at all),
which is also just genuinely better suited to small CPU-only deployments.

**4. Vercel monorepo import showed both `frontend` and `backend` as services**
Vercel auto-detects every deployable app in a repo, which meant it tried to treat
the FastAPI backend as a second Vercel service and asked for a `vercel.json`
`experimentalServices` config to proceed. *Fix:* setting **Root Directory** to
`frontend` in the Vercel import screen scopes the entire project to just the
Next.js app, which made the backend service block disappear from the import flow.
(The backend was already deployed separately on Render — Vercel was never meant
to touch it.)

**5. Vercel rejected the project name `OceanGPT`**
Vercel project names must be lowercase. *Fix:* renamed to `oceangpt` in the
Project Name field.

## What's verified vs. what to check on your machine

The backend code was originally built and tested in a sandboxed environment with
a locked-down network allowlist (only npm/pip registries reachable). Everything
listed below as "fully verified" was confirmed there; everything needing live
external hosts was confirmed afterward during the actual Render/Vercel deployment
described above, and is now live at the URLs at the top of this file.

✅ **Verified (sandbox, pre-deployment):**
- Backend imports cleanly, all routes register, no Python errors
- OBIS/WoRMS/NOAA/Open-Meteo response-parsing logic tested against realistic mock payloads
- Tool schemas validated against the OpenAI-compatible function-calling format Groq uses
- Frontend: full TypeScript compile + production build succeeds, ESLint clean

✅ **Verified (live deployment):**
- Render build succeeds with Python 3.11.9, fastembed installs and downloads its
  model successfully, `/api/health` returns `knowledge_base_docs: 11`
- Vercel build succeeds with Root Directory `frontend`, site renders correctly
- CORS handshake between the two once `ALLOWED_ORIGINS` matches the live Vercel URL

## Extending it

- **Add a new live data tool:** create `backend/app/tools/<name>.py`, add its
  function schema + dispatch entry in `backend/app/tools/registry.py`.
- **Grow the knowledge base:** drop a new `*.json` file (same `{id, title, text}` shape)
  into `backend/app/rag/knowledge/`. Delete `_embeddings_cache.json` to force re-embedding.
- **Swap the vector store for a real DB:** the `VectorStore` class in
  `backend/app/rag/store.py` is deliberately small — once the knowledge base grows
  past a few hundred chunks, swap it for pgvector/Qdrant and keep the same `search()` interface.
- **Swap Groq for a different provider:** since the client uses the OpenAI SDK
  pointed at Groq's `base_url`, switching providers (OpenAI, OpenRouter, etc.) is
  just changing `groq_base_url`/`groq_api_key`/`groq_chat_model` in `config.py` —
  no other code changes needed.
