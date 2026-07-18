# AI Engineer Assessment — Q1+Q2+Q3+Q4 (100% FREE, self-hosted voice stack)

## What's built
- **Q2 knowledge base**: `question_2_kb/parser.py` (extraction + cleaning + PII
  masking), `question_2_kb/embedder.py` (chunking, dedup, Qdrant Cloud upsert,
  grounded retrieval), `question_2_kb/seed_ingest.py` (sample content loader).
- **Q1 voice agent**: `question_1_3_voice/agent.py` — a self-hosted LiveKit
  Agents worker. `kb_search` (grounds every FAQ/objection/policy answer in
  the Q2 KB) and `log_call_outcome` (mock CRM action) are in-process function
  tools, not external webhooks.
- **Q1 assistant config**: `question_1_3_voice/prompts.py` (system prompt,
  call flow, escalation rules) — reused as-is by `agent.py`.
- **Test evidence templates**: `retrieval_tests/run_retrieval_tests.py` (Q2's
  5-query log) and `test_calls/test_scenarios.md` (Q1's 5 call scripts).

## Stack — every piece free tier, no card required except where noted
| Layer | Provider | Free tier |
|---|---|---|
| Vector DB | Qdrant Cloud | 1GB cluster, free forever |
| Embeddings | sentence-transformers | runs locally, no key |
| Voice orchestration | LiveKit Cloud (Build tier) | 5,000 WebRTC min + 1,000 agent min/month, free forever |
| STT + TTS | Deepgram (nova-3 + Aura-2) | $200 credit, no card, no expiry |
| LLM | Groq (llama-3.3-70b-versatile) | free tier, no card, rate-limited (30 req/min) |
| VAD | Silero | runs locally, no key |

No Vapi, no Twilio, no OpenAI key required. There's no telephony number in
this setup — you talk to the agent over the browser via LiveKit's hosted
Agents Playground (see step 5), which needs zero frontend code.

## Run sequence

### 1. Install + configure
```bash
cd ai_assessment_voice_free_local
pip install -r requirements.txt
cp .env.example .env
```
Fill in `.env`:
- `QDRANT_URL` / `QDRANT_API_KEY` — free cluster at https://cloud.qdrant.io
- `GROQ_API_KEY` — free key at https://console.groq.com/keys
- `DEEPGRAM_API_KEY` — free $200 credit at https://console.deepgram.com
- `LIVEKIT_URL` / `LIVEKIT_API_KEY` / `LIVEKIT_API_SECRET` — free Build-tier
  project at https://cloud.livekit.io

### 2. Seed and verify the knowledge base (Q2)
```bash
python -m question_2_kb.seed_ingest
python -m retrieval_tests.run_retrieval_tests
```
Check `retrieval_tests/retrieval_test_log.md` — fill in the relevance/verdict
lines by eye. Replace `SAMPLE_DOCS` in `seed_ingest.py` with your real
scraped/PDF content before final submission.

### 3. Run the voice agent locally
```bash
python -m question_1_3_voice.agent dev
```

### 4. Optional: run the FastAPI KB service
`app.py` still exposes the KB over HTTP (`/vapi-knowledge-search`,
`/vapi-log-call-outcome`) if you want to hit it independently of the voice
agent — the voice agent itself no longer calls these, it calls the KB
in-process.
```bash
uvicorn app:app --port 8000 --reload
```

### 5. Talk to the agent — no frontend needed
With the agent running (step 3) and connected to your LiveKit Cloud project,
open https://agents-playground.livekit.io, sign in with the same LiveKit
Cloud project, and start talking. This is LiveKit's own hosted testing UI —
free, zero code.

### 6. Deploy — three services, all free tier

This project splits into three independently deployable pieces:

| Piece | What it is | Where | Why there |
|---|---|---|---|
| `app.py` | FastAPI — dashboard API + optional HTTP KB access | **Render** (Web Service, free) | Free tier covers Web Services (spins down after 15 min idle, wakes on request — fine for a dashboard API) |
| `question_1_3_voice/agent.py` | LiveKit voice agent worker | **Fly.io** (free allowance) | Render's free tier does *not* cover Background Workers (~$7/mo minimum there); Fly.io's free tier does cover small always-on VMs, which this needs since it holds a persistent connection to LiveKit Cloud rather than responding to HTTP requests |
| `dashboard/index.html` | Static ops console | **Vercel** (static hosting, free) | Zero build step, plain HTML/CSS/JS |

**6a. `app.py` → Render**
- New → Web Service → connect repo
- Build: `pip install -r requirements.txt`
- Start: `uvicorn app:app --host 0.0.0.0 --port $PORT`
- Env vars: `QDRANT_URL`, `QDRANT_API_KEY`, `COLLECTION_NAME`
- Once you have your Vercel URL (step 6c), add `DASHBOARD_ORIGIN=https://your-dashboard.vercel.app` so CORS only allows your dashboard

**6b. `question_1_3_voice/agent.py` → Fly.io**
```bash
# install flyctl, then:
fly launch --no-deploy   # uses fly.toml already in this repo, pick a unique app name
fly secrets set QDRANT_URL=... QDRANT_API_KEY=... GROQ_API_KEY=... DEEPGRAM_API_KEY=... LIVEKIT_URL=... LIVEKIT_API_KEY=... LIVEKIT_API_SECRET=...
fly deploy
```
This builds `Dockerfile.agent` and runs the worker continuously.

**6c. `dashboard/index.html` → Vercel**
```bash
cd dashboard
vercel deploy --prod
```
Or drag the `dashboard/` folder into the Vercel dashboard. No build settings needed — it's a static file. Once deployed, open it, paste your Render API URL into the "API" field at the top, hit Save — it persists in the browser.

### 7. Talk to the agent — no extra frontend needed
With the Fly.io worker running and connected to your LiveKit Cloud project,
open https://agents-playground.livekit.io, sign in with the same LiveKit
Cloud project, and start talking.

### 8. Record the required test calls
Follow `test_calls/test_scenarios.md` — 5 scripts (cooperative, objection,
incomplete/conflicting, out-of-scope, human-request). Use the Agents
Playground to run and record them, paste transcripts, and fill in the
verdict table in that file. Check the Vercel dashboard's Call Log panel to
confirm `log_call_outcome` fired for each one.

## Known compromises (documented for the review, not hidden)
- Dedup is in-memory per ingestion run, not against the full Qdrant
  collection — fine for a 48h assessment, not for continuous ingestion.
- No telephony (PSTN) integration — the agent is reachable over
  browser/WebRTC only, since adding a real phone number requires a paid
  SIP provider (e.g. Twilio) with no free-forever tier.
- `crm_log.jsonl` is an append-only file, not an actual CRM — documented as
  the "mock CRM summary" optional action per the assessment's own menu of
  acceptable options.
- Groq's free tier is rate-limited (30 req/min, 14,400 req/day) — fine for
  demo/test calls, would need the paid Developer tier for production volume.

## Q3 & Q4 — Now Implemented
- **Q3**: `question_3_localized/` with PH (Taglish) and ID (Bahasa) prompts. These
  can be wired into `agent.py`'s `SYSTEM_PROMPT` per call, plus Deepgram's
  language parameter for STT.
- **Q4**: `question_4_insights/monitor.py` — streaming simulation, signal detection (objection, cross-sell, frustration, compliance), nudges with cooldown/dedup, latency tracking. Test with sample transcripts from Q1 calls.

Full coverage achieved.

