# AI Engineer Assessment — Q1+Q2+Q3+Q4 (100% FREE, self-hosted voice stack)

![Architecture](docs/architecture.svg)

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

### 3. Run the voice agent — on demand, not 24/7

The agent doesn't need to run continuously in the cloud. LiveKit workers must
already be connected to receive a call in real time, but the only thing this
project actually needs that for is **recording the 5 required test calls**
(step 8) — a manual, one-person-at-a-time activity, not a public service.

Run it locally whenever you're about to test or record:
```bash
python -m question_1_3_voice.agent dev
```
Leave that terminal open, use the Agents Playground (step 5) to talk to it,
then stop it when you're done. No hosting, no card, no ongoing cost — every
"always-on worker" hosting option in 2026 either requires a card (Oracle
Cloud) or reverts to a real monthly cost after a short trial (Railway, Fly,
Render Background Workers), so it's not worth paying that price for a
requirement this project doesn't actually have.

If you later want a genuinely public, always-reachable agent (e.g. a real
phone number people can call anytime), that's a different problem — it needs
both an always-connected worker *and* telephony (Twilio/SIP), neither of
which has a free-forever no-card option. `Dockerfile.agent` and `fly.toml`
are kept in this repo in case you want that later; they're not required for
anything the assessment asks for.

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

### 6. Deploy — two services need to be always reachable; the agent doesn't

Only the pieces a reviewer might check independently, at any time, need to
be deployed. The agent (step 3) runs on-demand locally, so it's not in this
table — see step 3 for why.

| Piece | What it is | Where | Why there |
|---|---|---|---|
| `app.py` | FastAPI — dashboard API + optional HTTP KB access | **Render** (Web Service, free) | Free tier covers Web Services (spins down after 15 min idle, wakes on request — fine for a dashboard API) |
| `dashboard/index.html` | Static ops console | **Vercel** (static hosting, free) | Zero build step, plain HTML/CSS/JS |

**6a. `app.py` → Render**
- New → Web Service → connect repo
- Build: `pip install -r requirements.txt`
- Start: `uvicorn app:app --host 0.0.0.0 --port $PORT`
- Env vars: `QDRANT_URL`, `QDRANT_API_KEY`, `COLLECTION_NAME`
- Once you have your Vercel URL (step 6b), add `DASHBOARD_ORIGIN=https://your-dashboard.vercel.app` so CORS only allows your dashboard

**6b. `dashboard/index.html` → Vercel**
```bash
cd dashboard
vercel deploy --prod
```
Or drag the `dashboard/` folder into the Vercel dashboard. No build settings needed — it's a static file. Once deployed, open it, paste your Render API URL into the "API" field at the top, hit Save — it persists in the browser.

**If you ever want the agent always-on and cloud-hosted too** (not required
for this assessment — see step 3): `Dockerfile.agent` and `fly.toml` are
still in this repo. Every "always-on worker" host checked in 2026 either
requires a card (Oracle Cloud "Always Free") or reverts to a real monthly
cost after a short trial (Railway's $5 one-time credit, Fly.io's trial,
Render's paid-only Background Workers) — there's currently no free-forever,
zero-card option for a persistent-connection worker specifically.

### 7. Talk to the agent — no extra frontend needed
With the agent running locally (step 3) and connected to your LiveKit Cloud
project, open https://agents-playground.livekit.io, sign in with the same
LiveKit Cloud project, and start talking.

### 8. Record the required test calls
Follow `test_calls/test_scenarios.md` — 5 scripts (cooperative, objection,
incomplete/conflicting, out-of-scope, human-request). Run the agent locally
(step 3), use the Agents Playground to run and record them, paste
transcripts, and fill in the verdict table in that file. Check the Vercel
dashboard's Call Log panel to confirm `log_call_outcome` fired for each one.

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

