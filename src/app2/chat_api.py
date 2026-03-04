from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import time
import requests
from .prompts import build_base_prompt, build_rag_prompt

app = FastAPI(title="ActuLLM - C4 Chat API")

load_dotenv()

# CORS (Même React peut parler avec l'API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


C3_RETRIEVE_URL = "http://127.0.0.1:8003/retrieve"
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "mistral"

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
        "ollama_url": OLLAMA_URL,
        "c3_retrieve": C3_RETRIEVE_URL,
    }


def build_prompt(message: str, docs: list[dict]) -> str:
    context_lines = []
    for i, d in enumerate(docs, start=1):
        text = d.get("text", "")
        meta = d.get("metadata", {}) or {}
        url = meta.get("url", "")
        date = meta.get("published_at", "")
        context_lines.append(f"[{i}] {date} {url}\n{text}")

    context = "\n\n".join(context_lines)

    return (
        "Tu es un assistant d’actualité. Réponds en français, clairement.\n"
        "Si le contexte ne suffit pas, dis-le.\n\n"
        f"CONTEXTE (extraits RSS):\n{context}\n\n"
        f"QUESTION:\n{message}\n\n"
        "RÉPONSE:"
    )


def retrieve_docs(query: str, k: int) -> list[dict]:
    try:
        r = requests.get(C3_RETRIEVE_URL, params={"q": query, "k": k}, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data.get("results", [])
    except Exception as e:
        print(f"[WARN] C3 indisponible: {e}")
        return []


def ollama_generate(prompt: str) -> str:
    payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
    r = requests.post(OLLAMA_URL, json=payload, timeout=120)
    r.raise_for_status()
    return r.json().get("response", "").strip()

def azure_generate(prompt: str) -> str:
    if not (AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY and AZURE_OPENAI_DEPLOYMENT):
        raise Exception("Azure OpenAI config manquante (.env)")

    url = (
        f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/{AZURE_OPENAI_DEPLOYMENT}/chat/completions"
        f"?api-version={AZURE_OPENAI_API_VERSION}"
    )

    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_OPENAI_API_KEY,
    }

    payload = {
        "messages": [
            {"role": "system", "content": "Tu es un assistant d’actualité. Réponds en français, clairement."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }

    r = requests.post(url, headers=headers, json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"].strip()


@app.post("/chat")
def chat(req: ChatReq):
    t0 = time.time()

    docs = retrieve_docs(req.message, req.k) if req.use_rag else []
    prompt = build_rag_prompt(req.message, docs) if docs else build_base_prompt(req.message)

    if PROVIDER == "azure":
        answer = azure_generate(prompt)
        provider_used = "azure"
    else:
        answer = ollama_generate(prompt)
        provider_used = "ollama"

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
    # 1) sans RAG
    a = chat(ChatReq(message=req.message, userag=False, k=req.k))

    # 2) avec RAG
    b = chat(ChatReq(message=req.message, userag=True, k=req.k))

    return {"noRag": a, "withRag": b}