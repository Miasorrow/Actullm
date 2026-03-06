import React, { useMemo, useRef, useState } from "react";
import { chat, compare4 } from "./api/chat";

export default function App() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Salut ! Pose une question. Tu peux répondre avec RAG, sans RAG, ou comparer les deux."
    }
  ]);

  const [input, setInput] = useState("");
  const [useRag, setUseRag] = useState(true);
  const [loading, setLoading] = useState(false);
  const listRef = useRef(null);

  const canSend = useMemo(() => input.trim().length > 0 && !loading, [input, loading]);

  function scrollToBottom() {
    setTimeout(() => {
      if (!listRef.current) return;
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }, 50);
  }

  function push(role, content, extra = {}) {
    setMessages((prev) => [...prev, { role, content, ...extra }]);
  }

  async function handleSend(e) {
    e.preventDefault();
    if (!canSend) return;

    const userText = input.trim();
    setInput("");
    push("user", userText);
    setLoading(true);
    scrollToBottom();

    try {
      const data = await chat({ message: userText, useRag });
      push("assistant", data?.answer ?? "Réponse vide.", { sources: data?.sources || [] });
    } catch (err) {
      const msg = err?.response?.data?.detail || err?.message || "Erreur inconnue.";
      push("assistant", `Erreur : ${msg}`);
    } finally {
      setLoading(false);
      scrollToBottom();
    }
  }

  async function handleCompare() {
    const userText = input.trim();
    if (!userText || loading) return;

    setInput("");
    push("user", userText);
    setLoading(true);
    scrollToBottom();

    try {
      const [
        ollamaNoRag,
        ollamaWithRag,
        azureNoRag,
        azureWithRag
      ] = await Promise.all([
        chat({ message: userText, useRag: false, provider: "ollama" }),
        chat({ message: userText, useRag: true, provider: "ollama" }),
        chat({ message: userText, useRag: false, provider: "azure" }),
        chat({ message: userText, useRag: true, provider: "azure" })
      ]);

      push(
        "assistant",
        `Ollama — Sans RAG:\n${ollamaNoRag?.answer ?? "Réponse vide."}`,
        { sources: ollamaNoRag?.sources || [] }
      );

      push(
        "assistant",
        `Ollama — Avec RAG:\n${ollamaWithRag?.answer ?? "Réponse vide."}`,
        { sources: ollamaWithRag?.sources || [] }
      );

      push(
        "assistant",
        `Azure — Sans RAG:\n${azureNoRag?.answer ?? "Réponse vide."}`,
        { sources: azureNoRag?.sources || [] }
      );

      push(
        "assistant",
        `Azure — Avec RAG:\n${azureWithRag?.answer ?? "Réponse vide."}`,
        { sources: azureWithRag?.sources || [] }
      );
    } catch (err) {
      const msg = err?.response?.data?.detail || err?.message || "Erreur inconnue.";
      push("assistant", `Erreur comparaison : ${msg}`);
    } finally {
      setLoading(false);
      scrollToBottom();
    }
  }

  return (
    <div className="page">
      <header className="header">
        <div className="title">
          <h1>ActuLLM</h1>
          <p>Chat d’actualité — mode RAG + comparaison (avec/sans)</p>
        </div>

        <div className="controls">
          <label className="toggle">
            <input
              type="checkbox"
              checked={useRag}
              onChange={(e) => setUseRag(e.target.checked)}
            />
            <span>Répondre avec RAG</span>
          </label>
        </div>
      </header>

      <main className="main">
        <div className="chat" ref={listRef}>
          {messages.map((m, idx) => (
            <div key={idx} className={`bubble ${m.role === "user" ? "user" : "assistant"}`}>
              <div className="role">
                {m.role === "user" ? "Vous" : "Assistant"}
              </div>

              <div className="content">
                {m.content}
              </div>

              {m.sources?.length > 0 && (
                <div className="sources">
                  <div className="sourcesTitle">Sources</div>
                  <ul>
                    {m.sources.map((s, i) => (
                      <li key={i}>
                        <a href={s.url} target="_blank" rel="noreferrer">
                          {s.title || s.url}
                        </a>
                        {s.published_at && (
                          <span className="date"> — {s.published_at}</span>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

            </div>
          ))}

          {loading && (
            <div className="bubble assistant">
              <div className="role">Assistant</div>
              <div className="content">⏳ Traitement…</div>
            </div>
          )}
        </div>

        <form className="composer" onSubmit={handleSend}>
          <input
            className="input"
            type="text"
            placeholder="Écrivez votre question…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />

          <button className="btn" type="submit" disabled={!canSend}>
            Envoyer
          </button>

          <button
            className="btn"
            type="button"
            onClick={handleCompare}
            disabled={loading || input.trim().length === 0}
            title="Compare les réponses avec et sans RAG"
          >
            Comparer
          </button>
        </form>
      </main>

      <footer className="footer">
        <span></span>
      </footer>
    </div>
  );
}