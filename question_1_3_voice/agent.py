"""
Q1 — Knowledge-Grounded Voice Agent (Insurance Renewal), self-hosted on LiveKit.

Replaces the old Vapi-managed assistant + FastAPI webhook pair
(/vapi-knowledge-search, /vapi-log-call-outcome) with a LiveKit Agents
worker: the same SYSTEM_PROMPT/FIRST_MESSAGE drive the conversation, but
kb_search and log_call_outcome are now plain in-process Python function
tools instead of HTTP round-trips to your own server.

Stack (every piece free-tier):
  - LiveKit Cloud "Build" tier   -> WebRTC/room orchestration (free, no card)
  - Deepgram nova-3               -> STT   ($200 free credit, no card)
  - Groq llama-3.3-70b-versatile  -> LLM   (free tier, no card)
  - Deepgram Aura-2                -> TTS   (same $200 credit as STT)
  - Silero VAD                     -> voice activity detection (runs locally, no key)

Run locally:
    python -m question_1_3_voice.agent dev

Deploy on Render as a Background Worker (no HTTP port needed):
    Start command: python -m question_1_3_voice.agent start

Talk to it with zero frontend code via LiveKit's hosted testing UI:
    https://agents-playground.livekit.io  (sign in with your LiveKit Cloud project)
"""

import os

from dotenv import load_dotenv

from livekit import agents
from livekit.agents import Agent, AgentSession, JobContext, RunContext, function_tool
from livekit.plugins import deepgram, openai, silero

from config import settings
from question_1_3_voice.mock_crm import log_outcome
from question_1_3_voice.prompts import FIRST_MESSAGE, SYSTEM_PROMPT
from question_2_kb.embedder import KnowledgeBaseEmbedder

load_dotenv()

kb = KnowledgeBaseEmbedder()

# Q3 — locale selection. Set AGENT_LOCALE=ph or AGENT_LOCALE=id before
# starting the agent to run the Taglish/Bahasa variant instead of English.
# Deepgram's STT also needs a matching language hint, or it'll transcribe
# non-English speech poorly.
_LOCALE = os.getenv("AGENT_LOCALE", "en").lower()
_DEEPGRAM_LANGUAGE = {"en": "en", "ph": "multi", "id": "multi"}.get(_LOCALE, "en")

if _LOCALE == "ph":
    from question_3_localized.ph_prompts import FIRST_MESSAGE_PH as FIRST_MESSAGE
    from question_3_localized.ph_prompts import SYSTEM_PROMPT_PH as SYSTEM_PROMPT
elif _LOCALE == "id":
    from question_3_localized.id_prompts import FIRST_MESSAGE_ID as FIRST_MESSAGE
    from question_3_localized.id_prompts import SYSTEM_PROMPT_ID as SYSTEM_PROMPT
# else: keep the English SYSTEM_PROMPT/FIRST_MESSAGE already imported above


@function_tool
async def kb_search(context: RunContext, query: str) -> dict:
    """Search the verified insurance knowledge base for an answer to the
    customer's question. Always call this before answering any policy,
    product, waiting-period, premium, payment, or objection question.
    Returns a grounded answer with a source citation, or indicates no
    verified answer exists.
    """
    match = kb.search_grounded_context(query)
    if match is None:
        return {"grounded": False, "message": "No verified reference found in the knowledge base."}
    return {"grounded": True, **match}


@function_tool
async def log_call_outcome(
    context: RunContext,
    customer_name: str,
    intent: str,
    escalated: bool,
    notes: str = "",
) -> dict:
    """Log the final outcome of this renewal call for CRM/follow-up
    purposes. Call this once, right before ending the call. `intent` must
    be one of: Renewed, Renewing soon, Needs follow-up, Not renewing,
    Already renewed.
    """
    return log_outcome(customer_name, intent, escalated, notes)


async def entrypoint(ctx: JobContext):
    await ctx.connect()

    session = AgentSession(
        vad=silero.VAD.load(),
        stt=deepgram.STT(
            model="nova-3",
            language=_DEEPGRAM_LANGUAGE,
            api_key=settings.DEEPGRAM_API_KEY,
        ),
        llm=openai.LLM(
            model=settings.GROQ_MODEL,
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
        ),
        tts=deepgram.TTS(model="aura-2-thalia-en", api_key=settings.DEEPGRAM_API_KEY),
    )

    await session.start(
        room=ctx.room,
        agent=Agent(
            instructions=SYSTEM_PROMPT,
            tools=[kb_search, log_call_outcome],
        ),
    )

    await session.generate_reply(instructions=FIRST_MESSAGE)


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
