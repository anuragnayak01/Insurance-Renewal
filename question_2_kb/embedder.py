"""
Free-tier cloud version - Qdrant Cloud + fastembed (local, free, ONNX-based embeddings)
"""

import sys
 
sys.setrecursionlimit(5000)

import uuid
import logging
from dataclasses import dataclass, asdict
from typing import Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from rapidfuzz import fuzz

from config import settings

logger = logging.getLogger("kb_embedder")


@dataclass
class KBRecord:
    record_id: str
    title: str
    content: str
    category: str
    source: str
    version: str
    contains_pii: bool


class KnowledgeBaseEmbedder:
    def __init__(self):
        if not settings.QDRANT_URL:
            raise RuntimeError(
                "QDRANT_URL is not set. Create a free cluster at "
                "https://cloud.qdrant.io and put its URL + API key in .env "
                "as QDRANT_URL / QDRANT_API_KEY."
            )
        # Qdrant Cloud (free tier) — persists across restarts/redeploys,
        # unlike a local PersistentClient on Render's ephemeral disk.
        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY or None,
        )
        self._seen_chunks: list[str] = []
        # Deferred import: fastembed (ONNX-based, no PyTorch) is much
        # lighter than sentence-transformers but still non-trivial to load.
        # Doing it here (inside __init__, called lazily by app.py's get_kb())
        # rather than at module level means a plain
        # `import question_2_kb.embedder` elsewhere in the app — e.g.
        # app.py's top-level import — stays cheap.
        from fastembed import TextEmbedding
        self.model = TextEmbedding(model_name=settings.EMBEDDING_MODEL)

    def ensure_collection(self):
        existing = [c.name for c in self.client.get_collections().collections]
        if settings.COLLECTION_NAME not in existing:
            self.client.create_collection(
                collection_name=settings.COLLECTION_NAME,
                vectors_config=qmodels.VectorParams(
                    size=settings.EMBEDDING_DIM,
                    distance=qmodels.Distance.COSINE,
                ),
            )
            logger.info("Created Qdrant collection: %s", settings.COLLECTION_NAME)
        else:
            logger.info("Using existing Qdrant collection: %s", settings.COLLECTION_NAME)

    def _embed(self, text: str) -> list[float]:
        """Local embedding via fastembed (ONNX, no PyTorch)."""
        return next(self.model.embed([text])).tolist()

    def _is_near_duplicate(self, chunk: str) -> bool:
        for existing in self._seen_chunks:
            if fuzz.ratio(chunk, existing) >= settings.DEDUP_SIMILARITY_THRESHOLD:
                return True
        return False

    def _chunk_text(self, text: str, size: int = 500, overlap: int = 100) -> list[str]:
        step = size - overlap
        return [text[i:i + size] for i in range(0, len(text), step) if text[i:i + size].strip()]

    def chunk_and_upload(
        self,
        text: str,
        title: str,
        category: str,
        source: str,
        version: str = "1.0",
        contains_pii: bool = False,
    ) -> dict:
        raw_chunks = self._chunk_text(text)
        skipped_dupes = 0
        added = 0

        for chunk in raw_chunks:
            if self._is_near_duplicate(chunk):
                skipped_dupes += 1
                continue
            self._seen_chunks.append(chunk)

            record_id = f"kb_{category}_{uuid.uuid4().hex[:8]}"

            record = KBRecord(
                record_id=record_id,
                title=title,
                content=chunk,
                category=category,
                source=source,
                version=version,
                contains_pii=contains_pii,
            )

            point_id = str(uuid.uuid4())
            payload = asdict(record)
            payload["document"] = chunk

            self.client.upsert(
                collection_name=settings.COLLECTION_NAME,
                points=[
                    qmodels.PointStruct(
                        id=point_id,
                        vector=self._embed(chunk),
                        payload=payload,
                    )
                ],
            )
            added += 1

        return {
            "source": source,
            "chunks_ingested": added,
            "chunks_skipped_as_duplicate": skipped_dupes,
        }

    def search_grounded_context(self, query: str, top_k: int = 1) -> Optional[dict]:
        hits = self.client.query_points(
            collection_name=settings.COLLECTION_NAME,
            query=self._embed(query),
            limit=top_k,
        ).points

        if not hits:
            return None

        top = hits[0]
        similarity = top.score  # Qdrant cosine distance config returns similarity directly

        if similarity < settings.RETRIEVAL_SCORE_THRESHOLD:
            return None

        payload = top.payload
        return {
            "content": payload["document"],
            "record_id": payload["record_id"],
            "title": payload["title"],
            "category": payload["category"],
            "source": payload["source"],
            "score": round(similarity, 4),
        }