# vectorstore_final.py

from app.services.nlp import process_rss
from sentence_transformers import SentenceTransformer
from chromadb import Client
from chromadb.config import Settings

# 1️⃣ Récupérer les articles enrichis par spaCy
enriched_feeds = process_rss()["feeds"]

# 2️⃣ Chroma DB local avec persistance
client = Client(Settings(
    #chroma_db_impl="duckdb+parquet",
    persist_directory="./chroma_data"
))
collection = client.get_or_create_collection("articles")

# 3️⃣ Modèle embeddings sur CPU
model = SentenceTransformer("all-MiniLM-L6-v2")

# 4️⃣ Ajouter les articles dans Chroma
for feed in enriched_feeds:
    source_info = feed['source']
    articles = feed['articles']

    texts = [a['lemmatized_text'] for a in articles]
    embeddings = model.encode(texts)  # batch embeddings

    for idx, article in enumerate(articles):
        article_id = article['id']
        embedding = embeddings[idx]

        # transformer entities en liste de strings
        entities_str = [f"{ent['text']} ({ent['label']})" for ent in article.get("entities", [])]

        collection.add(
            ids=[article_id],
            #embeddings=[embedding],
            metadatas=[{
                "source_title": source_info.get("source_title"),
                "source_url": source_info.get("source_url"),
                "article_title": article.get("title"),
                "link": article.get("link"),
                "published": article.get("published"),
                "entities": entities_str
            }],
            documents=[article['lemmatized_text']]
        )
        print(f"[Chroma] Article ajouté : {article_id}")

# 5️⃣ Persister les données
client.persist()

print("\n✅ Tous les articles enrichis sont maintenant dans Chroma DB.")