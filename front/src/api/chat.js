import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "/api";

/**
 * Appelle l'API du backend pour obtenir une réponse.
 * Attendu côté backend:
 * POST /chat
 * Body: { message: string, use_rag: boolean }
 * Retour: { answer: string, sources?: Array }
 */
export async function chat({ message, useRag }) {
  const res = await axios.post(`${API_URL}/chat`, {
    message,
    use_rag: useRag
  });
  return res.data;
}

/**
 * Compare les réponses: sans RAG vs avec RAG.
 * Retour: { noRag: {...}, withRag: {...} }
 */
export async function compare({ message }) {
  const [noRag, withRag] = await Promise.all([
    chat({ message, useRag: false }),
    chat({ message, useRag: true })
  ]);
  return { noRag, withRag };
}