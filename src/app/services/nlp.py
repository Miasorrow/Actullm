
#! spaCy, lemmatisation

# pip install -U spacy
# python -m spacy download en_core_web_sm
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import APIRouter, HTTPException
import spacy
from src.app.ingest_rss import get_flux_rss

router = APIRouter()

# Charger modèle français
nlp = spacy.load("fr_core_news_sm")


def enrich_article(article: dict) -> dict:
    """
    Analyse un article avec spaCy et retourne un article enrichi.
    """
    text = article.get("text", "")

    if not text.strip():
        return None

    doc = nlp(text)

    # Extraire entités
    entities = [
        {"text": ent.text, "label": ent.label_}
        for ent in doc.ents
    ]

    # Lemmatisation + suppression stopwords
    lemmatized_tokens = [
        token.lemma_
        for token in doc
        if not token.is_stop and not token.is_punct
    ]

    lemmatized_text = " ".join(lemmatized_tokens)

    return {
        **article,
        "entities": entities,
        "lemmatized_text": lemmatized_text,
        "text_length": len(text)
    }


@router.get("/process-rss")
def process_rss():
    """
    Récupère les flux depuis C1,
    les enrichit avec spaCy,
    retourne les articles enrichis.
    """
    data = get_flux_rss()

    enriched_feeds = []

    for feed in data["feeds"]:
        enriched_articles = []

        for article in feed["articles"]:
            enriched = enrich_article(article)
            if enriched:
                enriched_articles.append(enriched)

        enriched_feeds.append({
            "source": feed["source"],
            "articles": enriched_articles
        })

    return {
        "total_sources": len(enriched_feeds),
        "feeds": enriched_feeds
    }