import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Qdrant Cloud (free tier)
    QDRANT_URL: str = os.getenv("QDRANT_URL", "")
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")
    COLLECTION_NAME: str = os.getenv("COLLECTION_NAME", "insurance_knowledge_base")

    # Groq (free tier LLM, used directly by the LiveKit agent)
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # Deepgram (free $200 credit, covers both STT and TTS/Aura)
    DEEPGRAM_API_KEY: str = os.getenv("DEEPGRAM_API_KEY", "")

    # Local embeddings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384

    RETRIEVAL_SCORE_THRESHOLD: float = 0.20   # Lowered further for small local model + short sample docs

    DEDUP_SIMILARITY_THRESHOLD: int = 92


settings = Settings()
