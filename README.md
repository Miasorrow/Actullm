# ActuLLM

ActuLLM est une application simple qui permet de poser une question et d’obtenir une réponse :
- soit sans RAG (réponse “générale” du LLM),
- soit avec RAG (réponse basée sur des extraits d’articles récupérés et indexés).

Le projet est packagé en un seul container Docker (`actullm_prod`) exposé sur le port 8080.

## Objectif

- Ingest d’articles (RSS) dans une base vectorielle (ChromaDB)
- Recherche sémantique (retrieve) pour récupérer les passages les plus proches d’une requête
- Génération d’une réponse par un LLM (Azure OpenAI ou Ollama)
- Retourner aussi les sources (titre, URL, date, distance) quand `useRag=true`

## Architecture (vue fonctionnelle)

Dans le container, l’API expose deux parties principales :

1) Vector store (ChromaDB)
- Endpoint de vectorisation des articles (ingestion + embeddings + upsert)
- Endpoint de retrieval (recherche sémantique)

2) Chat API
- Endpoint `/api/chat` qui appelle le retrieval (si `useRag=true`)
- Construction d’un prompt (avec ou sans contexte)
- Appel du LLM (Azure OpenAI par défaut si configuré, sinon Ollama)

## Endpoints

Base URL (local) :
- http://127.0.0.1:8080

1) Santé
- GET `/api/health`
Retourne un JSON de statut et les URLs utiles (retrieve, etc.)

2) Vectorisation (ingestion RSS -> Chroma)
- POST `/api/vectorize`
Récupère les flux RSS, prépare les textes, calcule les embeddings, et upsert dans la collection Chroma.
Retourne : nombre de sources, nombre d’articles, nombre d’éléments upsert.

3) Retrieval (recherche sémantique)
- GET `/api/retrieve?q=...&k=...`
Retourne une liste `results` avec :
- text : extrait
- metadata : titre, url, date, source
- distance : score de proximité

4) Chat
- POST `/api/chat`
Body JSON :
{
  "message": "votre question",
  "useRag": true,
  "k": 3
}

Retourne :
- answer : réponse du modèle
- useRag : true/false
- sources_count : nombre de sources utilisées
- sources : liste (title, url, published_at, source, distance)
- provider : azure/ollama
- latency_ms : latence totale

5) Comparaison (sans RAG vs avec RAG)
- POST `/api/compare`
Body JSON :
{
  "message": "votre question",
  "k": 3
}

Retourne deux objets : `noRag` et `withRag`.

## Variables d’environnement

LLM
- LLM_PROVIDER : "azure" ou "ollama" (par défaut : "ollama" si non défini dans le code, selon votre config)
- AZURE_OPENAI_ENDPOINT : ex. https://xxxx.openai.azure.com
- AZURE_OPENAI_API_KEY : clé Azure OpenAI
- AZURE_OPENAI_DEPLOYMENT : nom du déploiement (ex. gpt-4o-mini)
- AZURE_OPENAI_API_VERSION : ex. 2024-02-15-preview

Vector store
- CHROMA_PATH : chemin de persistance (ex. /chroma_data)
- CHROMA_COLLECTION : nom de collection (ex. articles)
- EMBED_MODEL : modèle SentenceTransformers (ex. all-MiniLM-L6-v2)

RAG retrieval
- RETRIEVE_URL : URL interne utilisée par l’API Chat pour appeler le retrieval
  Exemple dans le container : http://127.0.0.1:8000/retrieve

## Lancer en local (Docker)

Pré-requis : Docker installé.

1) Construire l’image (si besoin)
- docker build -t actullm_prod .

2) Lancer le container (exemple)
- docker run -d \
  -p 8080:80 \
  -e AZURE_OPENAI_API_KEY="YOUR_KEY" \
  -e AZURE_OPENAI_ENDPOINT="https://YOUR_RESOURCE.openai.azure.com" \
  -e AZURE_OPENAI_DEPLOYMENT="YOUR_DEPLOYMENT" \
  --name actullm_prod \
  actullm_prod

3) Tester rapidement
- GET retrieve :
  curl "http://127.0.0.1:8080/api/retrieve?q=iran&k=3"

- POST chat (RAG) :
  curl -X POST http://127.0.0.1:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"iran","useRag":true,"k":3}'

## Notes

- Si `/api/retrieve` fonctionne mais `/api/chat` ne renvoie pas de sources, le problème est généralement :
  - RETRIEVE_URL non accessible depuis le process “chat” dans le container
  - ou un souci de normalisation des métadonnées
  - ou une erreur LLM (clé Azure invalide -> 401)

- Les données Chroma dépendent du chemin `CHROMA_PATH` et du montage volume si vous voulez persister après suppression du container.