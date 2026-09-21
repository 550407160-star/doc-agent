import re
from pathlib import Path

import chromadb
from openai import OpenAI

from config import CHUNK_OVERLAP, CHUNK_SIZE, DATA_DIR, EMBED_API_KEY, EMBED_BASE_URL, EMBED_MODEL, PERSIST_DIR, TOP_K

embed_client = OpenAI(base_url=EMBED_BASE_URL, api_key=EMBED_API_KEY)

_client = chromadb.PersistentClient(path=PERSIST_DIR)
collection = _client.get_or_create_collection("docs", metadata={"hnsw:space": "cosine"})


def embed(texts):
    resp = embed_client.embeddings.create(model=EMBED_MODEL, input=texts)
    return [d.embedding for d in resp.data]


def split_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    chunks = []
    for para in re.split(r"\n\s*\n", text.strip()):
        para = para.strip()
        if not para:
            continue
        if len(para) <= size:
            chunks.append(para)
        else:
            step = size - overlap
            chunks.extend(para[i:i + size] for i in range(0, len(para), step))
    return chunks


def ingest_file(path):
    p = Path(path)
    if p.suffix.lower() == ".pdf":
        from pypdf import PdfReader
        text = "\n".join(page.extract_text() or "" for page in PdfReader(str(p)).pages)
    else:
        text = p.read_text(encoding="utf-8")
    chunks = split_text(text)
    if not chunks:
        return 0
    ids = [f"{p.stem}_{i}" for i in range(len(chunks))]
    metas = [{"source": p.name, "chunk": i} for i in range(len(chunks))]
    collection.upsert(ids=ids, documents=chunks, embeddings=embed(chunks), metadatas=metas)
    return len(chunks)


def ingest_dir():
    total = 0
    for f in Path(DATA_DIR).rglob("*"):
        if f.is_file() and f.suffix.lower() in (".md", ".txt", ".pdf"):
            n = ingest_file(f)
            print(f"{f.name}: {n} chunks")
            total += n
    return total


def search(query, k=TOP_K):
    if collection.count() == 0:
        return []
    hits = collection.query(query_embeddings=embed([query]), n_results=k)
    return hits["documents"][0]
