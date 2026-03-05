from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any
import os
import hashlib

import chromadb
from sentence_transformers import SentenceTransformer

from app.services.nlp import process_rss

router = APIRouter()



CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_data")
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION", "articles")
EMBED_MODEL = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")

_client = chromadb.PersistentClient(path=CHROMA_PATH)
_collection = _client.get_or_create_collection(COLLECTION_NAME)
_model = SentenceTransformer(EMBED_MODEL)

def _make_id(url: str, published_at: str) -> str:
    raw = f"{url}::{published_at}".encode("utf-8", errors="ignore")
    return hashlib.sha1(raw).hexdigest()

class VectorizeResp(BaseModel):
    sources: int
    articles: int
    upserted: int

@router.get("/retrieve")
def retrieve(q: str, k: int = 5) -> Dict[str, Any]:
    q_emb = _model.encode([q])[0].tolist()
    res = _collection.query(
        query_embeddings=[q_emb],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    results = []
    docs = (res.get("documents") or [[]])[0]
    metas = (res.get("metadatas") or [[]])[0]
    dists = (res.get("distances") or [[]])[0]

    for text, meta, dist in zip(docs, metas, dists):
        results.append({
            "text": text,
            "metadata": meta or {},
            "distance": dist,
        })

    return {"results": results}

@router.post("/vectorize", response_model=VectorizeResp)
def vectorize() -> VectorizeResp:
    data = process_rss()  
    feeds = data.get("feeds", [])

    ids: List[str] = []
    docs: List[str] = []
    metas: List[dict] = []

    sources_count = 0
    articles_count = 0

    for feed in feeds:
        sources_count += 1
        for a in feed.get("articles", []):
            articles_count += 1

            url = a.get("url", "") or ""
            published_at = a.get("published_at", "") or ""
            _id = a.get("id") or _make_id(url, published_at)

            text = a.get("lemmatized_text") or a.get("text") or ""
            if not text.strip():
                continue

            meta = {
                "title": a.get("title", ""),
                "url": url,
                "published_at": published_at,
                "source": (feed.get("source") or {}).get("source_title", "") or "",
            }

            ids.append(str(_id))
            docs.append(text)
            metas.append(meta)

    if not docs:
        return VectorizeResp(sources=sources_count, articles=articles_count, upserted=0)

    embs = _model.encode(docs).tolist()
    _collection.upsert(ids=ids, documents=docs, metadatas=metas, embeddings=embs)

    return VectorizeResp(sources=sources_count, articles=articles_count, upserted=len(docs))