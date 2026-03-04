def build_base_prompt(user_message: str) -> str:
    return f"""Tu es ActuLLM, un assistant IA spécialisé dans l'actualité.

Réponds clairement et honnêtement.
Si tu n'es pas sûr, dis-le.

Question:
{user_message}

Réponse:
"""


def build_rag_prompt(user_message: str, docs: list[dict]) -> str:
    context_lines = []

    for i, d in enumerate(docs, start=1):
        md = d.get("metadata", {}) or {}
        url = md.get("url", "")
        date = md.get("published_at", "")
        source = md.get("source", "")
        text = (d.get("text") or "").strip()

        context_lines.append(
            f"[{i}] date={date} source={source} url={url}\n{text}"
        )

    context_block = "\n\n".join(context_lines)

    return f"""Tu es ActuLLM, un assistant IA spécialisé dans l'actualité.

Tu dois répondre UNIQUEMENT à partir du CONTEXTE fourni.
Si le contexte ne contient pas l'information, dis:
"Je ne sais pas d'après les documents fournis."

Consignes:
- Résume de manière structurée
- Respecte la chronologie
- Termine par une section "Sources"

CONTEXTE:
{context_block}

Question:
{user_message}

Réponse:
"""