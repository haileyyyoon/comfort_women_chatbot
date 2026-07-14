"""
tools.py
--------
Retrieval helper for the comfort women chatbot.

`get_response(question)` queries the Pinecone index built by `ingest.py`
and returns the most relevant passages from data/comfortwomen_text.txt,
re-ranked for relevance. If Pinecone returns nothing useful, it falls
back to a simple keyword search over the same source file so the bot can
still answer straightforward factual questions (e.g. "what is the address
of the House of Sharing?") even if the semantic search misses.
"""

from __future__ import annotations

import os
import logging
from pathlib import Path

from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()
logger = logging.getLogger(__name__)

INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "comfort-women-rag")
NAMESPACE = os.getenv("PINECONE_NAMESPACE", "ns1")
TOP_K = int(os.getenv("RAG_TOP_K", "5"))
DATA_FILE = Path(__file__).parent / "data" / "comfortwomen_text.txt"

# A handful of location/contact terms used to sanity-check semantic
# search results and trigger the keyword fallback when needed.
_FALLBACK_TRIGGER_TERMS = ("address", "location", "house", "sharing", "website", "contact")


def _get_index():
    """Return a handle to the Pinecone index, raising a clear error if it's missing."""
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise RuntimeError("PINECONE_API_KEY is not set. Check your .env file.")

    pc = Pinecone(api_key=api_key)
    if not pc.has_index(INDEX_NAME):
        raise RuntimeError(
            f"Pinecone index '{INDEX_NAME}' does not exist yet. "
            "Run `python ingest.py` once to build it before starting the chatbot."
        )
    return pc.Index(INDEX_NAME)


def _load_paragraphs():
    """Load the source text file as a list of paragraph chunks."""
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Could not find source text file at {DATA_FILE}")
    raw = DATA_FILE.read_text(encoding="utf-8")
    return [p.strip() for p in raw.split("\n\n") if p.strip()]


def _keyword_fallback(question: str):
    """
    Very small fallback search used when semantic search doesn't return a
    clearly relevant match. Groups paragraphs into overlapping windows and
    picks the window with the most keyword overlap with the question.
    """
    paragraphs = _load_paragraphs()
    q_words = {w.strip(".,?!\"'").lower() for w in question.split() if len(w) > 3}
    if not q_words:
        return {"matches": []}

    chunk_size, stride = 3, 1
    windows = []
    for i in range(0, max(len(paragraphs) - chunk_size + 1, 1), stride):
        windows.append("\n\n".join(paragraphs[i:i + chunk_size]))
    if not windows:
        windows = ["\n\n".join(paragraphs)]

    scored = []
    for chunk in windows:
        chunk_words = set(chunk.lower().split())
        overlap = len(q_words & chunk_words)
        if overlap:
            scored.append((overlap, chunk))

    if not scored:
        return {"matches": []}

    scored.sort(key=lambda pair: pair[0], reverse=True)
    best_chunks = [chunk for _, chunk in scored[:TOP_K]]
    return {
        "matches": [
            {"score": 1.0, "metadata": {"chunk_text": chunk}} for chunk in best_chunks
        ]
    }


def get_response(question: str) -> dict:
    """
    Retrieve the passages most relevant to `question`.

    Returns a dict shaped like `{"matches": [{"score": ..., "metadata": {"chunk_text": ...}}, ...]}`
    so callers can treat Pinecone results and the keyword fallback identically.
    """
    try:
        index = _get_index()
        results = index.search(
            namespace=NAMESPACE,
            query={"top_k": TOP_K, "inputs": {"text": question}},
            rerank={
                "model": "bge-reranker-v2-m3",
                "top_n": TOP_K,
                "rank_fields": ["chunk_text"],
            },
        )
        # Pinecone 7.x returns a SearchRecordsResponse shaped like
        # {"result": {"hits": [{"_id", "_score", "fields": {"chunk_text": ...}}]}}.
        data = results.to_dict() if hasattr(results, "to_dict") else dict(results)
        hits = (data.get("result") or {}).get("hits") or []
        matches = [
            {
                "score": hit.get("_score", 0.0),
                "metadata": {"chunk_text": (hit.get("fields") or {}).get("chunk_text", "")},
            }
            for hit in hits
        ]
    except Exception:
        logger.exception("Pinecone search failed; falling back to keyword search")
        return _keyword_fallback(question)

    # Sanity check: if the question mentions something location/contact related
    # but the top match doesn't, prefer the keyword fallback, which is good at
    # pinning down this kind of very specific factual lookup.
    q_lower = question.lower()
    wants_specific_fact = any(term in q_lower for term in _FALLBACK_TRIGGER_TERMS)
    top_text = ""
    if matches:
        top_text = matches[0]["metadata"]["chunk_text"].lower()

    if not matches or (wants_specific_fact and not any(t in top_text for t in _FALLBACK_TRIGGER_TERMS)):
        fallback = _keyword_fallback(question)
        if fallback["matches"]:
            return fallback

    return {"matches": matches}
