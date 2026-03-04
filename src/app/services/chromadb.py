from src.app.services.nlp import process_rss
import chromadb


def load_articles_into_chroma():
    # 1️⃣ Récupérer les articles enrichis
    enriched_feeds = process_rss()["feeds"]

    # 2️⃣ Chroma DB local avec persistance
    client = chromadb.PersistentClient(path="./chroma_data")
    collection = client.get_or_create_collection("articles")

    # 3️⃣ Ajouter les articles
    for feed in enriched_feeds:
        source_info = feed['source']
        articles = feed['articles']

        for article in articles:
            entities_str = [
                f"{ent['text']} ({ent['label']})"
                for ent in article.get("entities", [])
            ]

            collection.upsert(
                ids=[article['id']],
                documents=[article['lemmatized_text']],
                metadatas=[{
                    "source_title": source_info.get("source_title"),
                    "source_url": source_info.get("source_url"),
                    "title": article.get("title"),
                    "link": article.get("link"),
                    "published": article.get("published"),
                    "entities": ", ".join(entities_str)
                }]
            )

            print(f"[Chroma] ✅ Article ajouté : {article['id']}")

    print("\n✅ Tous les articles sont dans Chroma DB.")