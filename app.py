import json
import logging
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from question_2_kb.embedder import KnowledgeBaseEmbedder
from question_1_3_voice.mock_crm import CRM_LOG_PATH, log_outcome
from question_4_insights.monitor import LiveCallMonitor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")

app = FastAPI(title="AI Voice Agent Orchestrator")
monitor = LiveCallMonitor()

# KnowledgeBaseEmbedder downloads a fastembed (ONNX) model on first use —
# model — on a small instance that can be slow/memory-heavy enough to get
# killed before uvicorn opens its port if done at import time. Load it lazily
# on first actual use instead, so /health responds immediately and Render's
# port scan succeeds right away.
_kb = None


def get_kb() -> KnowledgeBaseEmbedder:
    global _kb
    if _kb is None:
        logger.info("Lazily initializing KnowledgeBaseEmbedder...")
        _kb = KnowledgeBaseEmbedder()
        _kb.ensure_collection()
        logger.info("KnowledgeBaseEmbedder ready.")
    return _kb


# Dashboard (Vercel) origin(s) allowed to call this API — comma-separated.
# Defaults to "*" for local dev; set DASHBOARD_ORIGIN in Render's env once
# you have your Vercel URL, e.g. https://your-dashboard.vercel.app
_origins = os.getenv("DASHBOARD_ORIGIN", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/vapi-knowledge-search")
async def vapi_knowledge_search(request: Request):
    """
    Vapi function-tool webhook for `kb_search`.

    Safe extraction throughout — Vapi's payload shape differs between
    tool-call requests and status/log events, so every level uses .get()
    with a default rather than assuming keys exist.
    """
    body = await request.json()
    message = body.get("message", {})
    tool_calls = message.get("toolCalls", [{}])
    first_call = tool_calls[0] if tool_calls else {}
    function = first_call.get("function", {})
    arguments = function.get("arguments", {})
    query = arguments.get("query", "")
    tool_call_id = first_call.get("id", "")

    if not query:
        return {
            "results": [
                {"toolCallId": tool_call_id, "result": "No query provided."}
            ]
        }

    match = get_kb().search_grounded_context(query)

    if match is None:
        # This exact string should also be referenced in the assistant's
        # system prompt as the mandatory fallback — grounding the fallback
        # in code AND in the prompt means it can't silently drift.
        answer = (
            "I don't have a verified reference for that in my records. "
            "Let me connect you with a specialist who can confirm."
        )
    else:
        answer = f"{match['content']} [Source: {match['record_id']}]"

    logger.info("kb_search query=%r -> matched=%s", query, match is not None)

    # Vapi expects results keyed by toolCallId
    return {"results": [{"toolCallId": tool_call_id, "result": answer}]}


@app.post("/vapi-log-call-outcome")
async def vapi_log_call_outcome(request: Request):
    """
    Vapi function-tool webhook for `log_call_outcome` — the optional
    business action (mock CRM summary). Safe .get() extraction throughout,
    same pattern as the kb_search webhook.
    """
    body = await request.json()
    message = body.get("message", {})
    tool_calls = message.get("toolCalls", [{}])
    first_call = tool_calls[0] if tool_calls else {}
    function = first_call.get("function", {})
    arguments = function.get("arguments", {})
    tool_call_id = first_call.get("id", "")

    customer_name = arguments.get("customer_name", "unknown")
    intent = arguments.get("intent", "Needs follow-up")
    escalated = bool(arguments.get("escalated", False))
    notes = arguments.get("notes", "")

    record = log_outcome(customer_name, intent, escalated, notes)
    logger.info("Logged call outcome: %s", record)

    return {
        "results": [
            {"toolCallId": tool_call_id, "result": f"Logged outcome: {intent} for {customer_name}."}
        ]
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Dashboard API — read by the Vercel-hosted static dashboard.
# ---------------------------------------------------------------------------

class KBSearchRequest(BaseModel):
    query: str


class InsightRequest(BaseModel):
    transcript: str


@app.get("/api/crm-logs")
async def get_crm_logs(limit: int = 50):
    """Returns the most recent call outcomes logged by log_call_outcome."""
    path = Path(CRM_LOG_PATH)
    if not path.exists():
        return {"logs": []}
    lines = path.read_text().strip().splitlines()
    records = [json.loads(line) for line in lines if line.strip()]
    records.reverse()  # newest first
    return {"logs": records[:limit]}


@app.post("/api/kb-search")
async def api_kb_search(payload: KBSearchRequest):
    """Lets the dashboard test what the voice agent's kb_search tool would
    return for a given question, without needing a live call."""
    match = get_kb().search_grounded_context(payload.query)
    if match is None:
        return {"grounded": False, "message": "No verified reference found in the knowledge base."}
    return {"grounded": True, **match}


@app.post("/api/insights")
async def api_insights(payload: InsightRequest):
    """Runs a transcript chunk through the Q4 live-call monitor and returns
    any nudges it would surface — same logic the real-time pipeline uses."""
    return monitor.process_transcript_chunk(payload.transcript)
