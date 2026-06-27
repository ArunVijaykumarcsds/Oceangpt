# OceanGPT

A marine intelligence dashboard combining a live chat assistant (RAG + tool-calling)
with real-time ocean data widgets — species occurrences, tide gauges, and global
wave/sea-temperature conditions.

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
and separately gives the Groq-hosted LLM a set of function-calling tools wired to
the live APIs above. The model decides per-turn whether a question needs live data,
retrieved background knowledge, or both — see `backend/app/chat/agent.py` for the
orchestration logic.

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
cp .env.local.example .env.local   # defaults to http://localhost:8000, change if needed
npm run dev
```

Visit `http://localhost:3000`.

## Deploying it (Render + Vercel, both free)

### Backend → Render

1. Push this repo to GitHub (keep `frontend/`, `backend/`, `render.yaml` at the
   same level — this is a monorepo, both platforms are told which subfolder to build).
2. On [render.com](https://render.com): **New → Blueprint** → select your repo.
   Render reads `render.yaml` and pre-fills everything.
3. Fill in the two secret env vars it asks for:
   - `GROQ_API_KEY` → your key from console.groq.com
   - `ALLOWED_ORIGINS` → your Vercel URL once you have it (placeholder `http://localhost:3000` is fine to start)
4. Deploy. Check `/docs` on the resulting URL once live.

### Frontend → Vercel

1. On [vercel.com](https://vercel.com): **Add New → Project** → import the same repo.
2. Set **Root Directory** to `frontend` (the one setting Vercel needs from the dashboard, not a config file).
3. Add env var `NEXT_PUBLIC_API_BASE_URL` = your Render backend URL.
4. Deploy.

### Close the loop

Go back to Render → Environment → update `ALLOWED_ORIGINS` to your real Vercel
URL, save (auto-redeploys). Now CORS allows the live frontend to call the backend.

**Free tier note:** Render's free web service spins down after inactivity; the
first request after idle time can take 30-50 seconds to wake up. Fine for a
portfolio demo.

## What's verified vs. what to check on your machine

Built and tested in a sandboxed environment with a locked-down network allowlist
(only npm/pip registries reachable — no live internet to OBIS, NOAA, Groq,
Hugging Face, etc). Here's what that means for confidence levels:

✅ **Fully verified:**
- Backend imports cleanly, all routes register, no Python errors
- Every external API's response-parsing logic (OBIS, WoRMS, NOAA, Open-Meteo)
  tested against realistic mock payloads matching their real, documented response shapes
- Tool schemas validated against OpenAI-compatible function-calling format (which Groq uses)
- Groq client config confirmed against Groq's documented OpenAI-compatibility layer
  (same SDK, different `base_url`)
- fastembed import and API usage confirmed correct; failure observed was
  specifically a blocked connection to huggingface.co, not a code defect
- Frontend: full TypeScript compile + production build succeeds, ESLint clean,
  all routes/pages generate correctly

⚠️ **Not directly tested (couldn't reach these hosts from the build sandbox):**
- Live calls to `api.obis.org`, `api.tidesandcurrents.noaa.gov`, `marine-api.open-meteo.com`,
  `api.groq.com`, `huggingface.co`, `fonts.googleapis.com`
- These should all work normally on Render/Vercel, which have normal internet access

**First things to check once deployed:** open `/docs` on the Render backend URL
and manually try `/api/species/search?name=Chelonia mydas` and
`/api/environment/marine-forecast?latitude=25.46&longitude=-80.12` to confirm
those external calls succeed, then check the startup logs for
"Loaded N knowledge base documents" to confirm the embedding model downloaded
and the RAG layer initialized — before testing the full chat flow.

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
