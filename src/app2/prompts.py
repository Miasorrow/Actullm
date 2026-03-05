def build_base_prompt(user_message: str) -> str:
    return f"""Tu es ActuLLM, un assistant IA spécialisé dans l'actualité.

Réponds clairement et honnêtement.
Si tu n'es pas sûr, dis-le.

Question:
{user_message}

Réponse:
"""


def build_rag_prompt(user_message: str, docs: list[dict]) -> str:
    # context block
    lines = []
    for i, d in enumerate(docs, start=1):
        meta = d.get("metadata") or {}
        title = meta.get("title", "")
        url = meta.get("url", "")
        date = meta.get("published_at", "")
        source = meta.get("source", "")
        text = d.get("text", "")
        lines.append(f"[{i}] {date} | {source}\nTitre: {title}\nURL: {url}\nTexte: {text}")

    context_block = "\n\n".join(lines)

    return f"""
Tu es un assistant d'actualité.

RÈGLES STRICTES:
- Tu DOIS utiliser UNIQUEMENT les informations du CONTEXTE ci-dessous.
- Si le CONTEXTE ne contient pas l'information, réponds: "Je ne sais pas d'après les documents fournis."
- Si la question est courte ou ambiguë, demande une précision.
- Si elle est en arabe, comprends-la et réponds en français.
- Ne JAMAIS inventer de faits, dates, noms, ou événements.
- Résume en 5 points maximum.
- Termine par une section "Sources" listant les URLs utilisées.

CONTEXTE:
{context_block}

QUESTION:
{user_message}

RÉPONSE:
""".strip()