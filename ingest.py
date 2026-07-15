"""
ingest.py
---------
Builds (or refreshes) the Pinecone index used by the chatbot from
data/comfortwomen_text.txt.

Run this once before starting the chatbot for the first time, and again
any time you edit data/comfortwomen_text.txt to add or update information:

    python ingest.py

This is intentionally a separate, manual step rather than something that
happens automatically on every chat request — re-uploading the whole
knowledge base on every single question (as the old code did) is slow,
wastes API quota, and risks duplicate/stale records.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()

INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "comfort-women-rag")
NAMESPACE = os.getenv("PINECONE_NAMESPACE", "ns1")
NAMESPACE_KO = os.getenv("PINECONE_NAMESPACE_KO", "ns-ko")
DATA_DIR = Path(__file__).parent / "data"

# language namespace -> source file. The Korean file holds the museum's own
# Korean texts so Korean answers can quote them directly instead of
# translating the English archive on the fly.
SOURCES = {
    NAMESPACE: DATA_DIR / "comfortwomen_text.txt",
    NAMESPACE_KO: DATA_DIR / "comfortwomen_text_ko.txt",
}


def load_paragraphs(data_file):
    if not data_file.exists():
        raise FileNotFoundError(f"Could not find source text file at {data_file}")
    raw = data_file.read_text(encoding="utf-8")
    return [p.strip() for p in raw.split("\n\n") if p.strip()]


def main():
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise SystemExit("PINECONE_API_KEY is not set. Copy .env.example to .env and fill it in.")

    pc = Pinecone(api_key=api_key)

    if not pc.has_index(INDEX_NAME):
        print(f"Creating Pinecone index '{INDEX_NAME}'...")
        pc.create_index_for_model(
            name=INDEX_NAME,
            cloud="aws",
            region="us-east-1",
            embed={
                "model": "llama-text-embed-v2",
                "field_map": {"text": "chunk_text"},
            },
        )
    else:
        print(f"Index '{INDEX_NAME}' already exists; upserting fresh records.")

    index = pc.Index(INDEX_NAME)

    for namespace, data_file in SOURCES.items():
        if not data_file.exists():
            print(f"Skipping namespace '{namespace}': {data_file.name} not found.")
            continue

        paragraphs = load_paragraphs(data_file)
        records = [
            {"_id": f"rec{i}", "chunk_text": para}
            for i, para in enumerate(paragraphs, start=1)
        ]

        print(f"Upserting {len(records)} chunks from {data_file.name} into '{namespace}'...")
        # Pinecone's upsert_records has a request size limit, so send in batches.
        batch_size = 90
        for start in range(0, len(records), batch_size):
            batch = records[start:start + batch_size]
            index.upsert_records(namespace, batch)
            print(f"  upserted {start + len(batch)}/{len(records)}")

    print("Done. The chatbot can now query this index.")


if __name__ == "__main__":
    main()
