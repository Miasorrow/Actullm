import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "/api";

/**
 * POST /chat
 * Body: { message: string, useRag: boolean, provider?: "ollama"|"azure", k?: number }
 */
export async function chat({ message, useRag, provider, k }) {
  const res = await axios.post(`${API_URL}/chat`, {
    message,
    useRag,         
    provider,       
    ...(k ? { k } : {})
  });
  return res.data;
}

/**
 * Compare 4 réponses:
 * - Ollama sans RAG / avec RAG
 * - Azure  sans RAG / avec RAG
 */
export async function compare4({ message }) {
  const [ollamaNoRag, ollamaWithRag, azureNoRag, azureWithRag] = await Promise.all([
    chat({ message, useRag: false, provider: "ollama" }),
    chat({ message, useRag: true,  provider: "ollama" }),
    chat({ message, useRag: false, provider: "azure" }),
    chat({ message, useRag: true,  provider: "azure" })
  ]);

  return { ollamaNoRag, ollamaWithRag, azureNoRag, azureWithRag };
}