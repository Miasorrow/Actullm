import os
import time
import requests
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from .prompts import build_base_prompt, build_rag_prompt

load_dotenv()

PROVIDER = os.getenv("LLM_PROVIDER", "ollama")  # "ollama" or "azure"

app = FastAPI(title="ActuLLM - C4 Chat API")

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RETRIEVE_URL = os.getenv("RETRIEVE_URL", "http://127.0.0.1:8000/retrieve")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")


class ChatReq(BaseModel):
    message: str
    use_rag: bool = Field(True, alias="useRag")
    k: int = 5

    class Config:
        populate_by_name = True


class CompareReq(BaseModel):
    message: str
    k: int = 5


@app.get("/health")
def health():
    return {
        "chat": "ok",
        "provider": PROVIDER,
        "ollama_url": OLLAMA_URL,
        "c3_retrieve": RETRIEVE_URL,
        "azure_endpoint_set": bool(AZURE_OPENAI_ENDPOINT),
        "azure_deployment_set": bool(AZURE_OPENAI_DEPLOYMENT),
        "azure_key_set": bool(AZURE_OPENAI_API_KEY),
    }


def _try_get(url: str, params: dict, timeout: int = 10) -> requests.Response:
    r = requests.get(url, params=params, timeout=timeout)
    r.raise_for_status()
    return r


def retrieve_docs(query: str, k: int) -> list[dict]:
    """
    Robust retrieve:
    - Tries RETRIEVE_URL as-is
    - If 404, tries toggling /retrieve <-> /api/retrieve
    """
    try_urls: list[str] = []

    # 1) the configured url
    try_urls.append(RETRIEVE_URL)

    # 2) auto-fallback between /retrieve and /api/retrieve
    if RETRIEVE_URL.endswith("/retrieve"):
        try_urls.append(RETRIEVE_URL[:-len("/retrieve")] + "/api/retrieve")
    elif RETRIEVE_URL.endswith("/api/retrieve"):
        try_urls.append(RETRIEVE_URL[:-len("/api/retrieve")] + "/retrieve")

    last_err: Exception | None = None

    for url in try_urls:
        try:
            r = _try_get(url, params={"q": query, "k": k}, timeout=10)
            data = r.json()
            return data.get("results", []) or []
        except Exception as e:
            last_err = e
            continue

    print(f"[WARN] C3 indisponible: {last_err}")
    return []


def normalize_doc(d: dict) -> dict:
    """
    Normalize metadata keys from different feeds (LeMonde, France24, etc.)
    so the rest of the app always sees: title, url, published_at, source
    """
    meta = d.get("metadata") or {}

    title = meta.get("title", "") or ""
    url = meta.get("url") or meta.get("link") or meta.get("source_url") or ""
    published = meta.get("published_at") or meta.get("published") or ""
    source = meta.get("source") or meta.get("source_title") or meta.get("source_url") or ""

    return {
        "text": d.get("text", "") or "",
        "metadata": {
            "title": title,
            "url": url,
            "published_at": published,
            "source": source,
        },
        "distance": d.get("distance"),
    }


def ollama_generate(prompt: str) -> str:
    payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
    r = requests.post(OLLAMA_URL, json=payload, timeout=120)
    r.raise_for_status()
    return r.json().get("response", "").strip()


def azure_generate(prompt: str) -> str:
    if not (AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY and AZURE_OPENAI_DEPLOYMENT):
        raise Exception("Azure OpenAI config manquante (.env أو env vars)")

    url = (
        f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/{AZURE_OPENAI_DEPLOYMENT}/chat/completions"
        f"?api-version={AZURE_OPENAI_API_VERSION}"
    )

    headers = {"Content-Type": "application/json", "api-key": AZURE_OPENAI_API_KEY}

    payload = {
        "messages": [
            {"role": "system", "content": "Tu es un assistant d’actualité. Réponds en français, clairement."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }

    r = requests.post(url, headers=headers, json=payload, timeout=120)

    
    if r.status_code == 401:
        raise Exception("Azure 401 PermissionDenied: API key أو deployment أو resource غلط")
    r.raise_for_status()

    data = r.json()
    return data["choices"][0]["message"]["content"].strip()


@app.post("/chat")
def chat(req: ChatReq):
    t0 = time.time()

    raw_docs = retrieve_docs(req.message, req.k) if req.use_rag else []
    docs = [normalize_doc(d) for d in (raw_docs or [])]

  
    docs = [d for d in docs if (d.get("text") or "").strip()]

    prompt = build_rag_prompt(req.message, docs) if docs else build_base_prompt(req.message)

    provider_used = PROVIDER

    if PROVIDER == "azure":
        try:
            answer = azure_generate(prompt)
            provider_used = "azure"
        except Exception as e:
            return {
                "answer": "Erreur: Azure OpenAI indisponible / configuration invalide.",
                "useRag": req.use_rag,
                "sources_count": len(docs),
                "sources": [
                    {
                        "title": (d.get("metadata") or {}).get("title", ""),
                        "url": (d.get("metadata") or {}).get("url", ""),
                        "published_at": (d.get("metadata") or {}).get("published_at", ""),
                        "source": (d.get("metadata") or {}).get("source", ""),
                        "distance": d.get("distance"),
                    }
                    for d in docs
                ],
                "provider": "azure",
                "error": str(e),
                "latency_ms": int((time.time() - t0) * 1000),
            }
    else:
        try:
            answer = ollama_generate(prompt)
            provider_used = "ollama"
        except Exception as e:
            return {
                "answer": "Erreur: Ollama n'est pas disponible (serveur 11434).",
                "useRag": req.use_rag,
                "sources_count": len(docs),
                "sources": [
                    {
                        "title": (d.get("metadata") or {}).get("title", ""),
                        "url": (d.get("metadata") or {}).get("url", ""),
                        "published_at": (d.get("metadata") or {}).get("published_at", ""),
                        "source": (d.get("metadata") or {}).get("source", ""),
                        "distance": d.get("distance"),
                    }
                    for d in docs
                ],
                "provider": "ollama",
                "error": str(e),
                "latency_ms": int((time.time() - t0) * 1000),
            }

    return {
        "answer": answer,
        "useRag": req.use_rag,
        "sources_count": len(docs),
        "sources": [
            {
                "title": (d.get("metadata") or {}).get("title", ""),
                "url": (d.get("metadata") or {}).get("url", ""),
                "published_at": (d.get("metadata") or {}).get("published_at", ""),
                "source": (d.get("metadata") or {}).get("source", ""),
                "distance": d.get("distance"),
            }
            for d in docs
        ],
        "provider": provider_used,
        "latency_ms": int((time.time() - t0) * 1000),
    }


@app.post("/compare")
def compare(req: CompareReq):
    a = chat(ChatReq(message=req.message, useRag=False, k=req.k))
    b = chat(ChatReq(message=req.message, useRag=True, k=req.k))
    return {"noRag": a, "withRag": b}