#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import APIRouter, HTTPException
from typing import Optional
import feedparser
from src.app.services.text_cleaner import clean_html

router = APIRouter()

FLUX_URLS = [
    "https://www.france24.com/fr/rss",
    "https://www.lemonde.fr/international/rss_full.xml",
]


def parse_feed(url: str) -> dict:
    """Parse un flux RSS et retourne les métadonnées + articles."""
    print(f"\n[RSS] Fetching: {url}")
    feed = feedparser.parse(url)
    print(f"[RSS] bozo={feed.bozo} | entries={len(feed.entries)}")

    if feed.bozo and not feed.entries:
        print(f"[RSS] ❌ Échec du flux : {url}")
        raise HTTPException(
            status_code=502,
            detail=f"Impossible de récupérer le flux : {url}"
        )

    source_metadata = {
        "source_title":  feed.feed.get("title"),
        "source_url":    feed.feed.get("link"),
        "language":      feed.feed.get("language"),
        "last_updated":  feed.feed.get("updated"),
        "subtitle":      feed.feed.get("subtitle"),
        "total_entries": len(feed.entries),
    }
    print(f"[RSS] ✅ Source : {source_metadata['source_title']} | langue : {source_metadata['language']} | articles : {source_metadata['total_entries']}")

    articles = []
    for i, entry in enumerate(feed.entries):
        raw_summary     = entry.get("summary", "")
        cleaned_summary = clean_html(raw_summary)

        if i == 0:
            print(f"\n[BS4] Summary brut    : {raw_summary[:100]!r}")
            print(f"[BS4] Summary nettoyé : {cleaned_summary[:100]!r}")

        articles.append({
            "title":     entry.get("title"),
            "link":      entry.get("link"),
            "id":        entry.get("id") or entry.get("link"),
            "published": entry.get("published"),
            "summary":   cleaned_summary,
            "text":      f"{entry.get('title', '')} {cleaned_summary}",
            "author":    entry.get("author"),
        })

    print(f"[RSS] {len(articles)} articles parsés pour {source_metadata['source_title']}")
    latest = articles[0] if articles else None
    if latest:
        print(f"[RSS] Dernier article : {latest['title']}")

    return {
        "source":         source_metadata,
        "latest_article": latest,
        "articles":       articles,
    }


@router.get("/flux-rss")
def get_flux_rss(url: Optional[str] = None):
    """
    Agrège et retourne les flux RSS configurés.

    - Sans paramètre  → retourne tous les flux de FLUX_URLS
    - ?url=<adresse>  → retourne uniquement le flux demandé
    """
    print(f"\n{'='*50}")
    print(f"[ROUTE] GET /flux-rss appelée | url param={url}")
    urls = [url] if url else FLUX_URLS
    print(f"[ROUTE] {len(urls)} flux à traiter")

    results = []
    errors  = []

    for feed_url in urls:
        try:
            results.append(parse_feed(feed_url))
        except HTTPException as e:
            print(f"[ROUTE] ❌ Erreur sur {feed_url} : {e.detail}")
            errors.append({"url": feed_url, "error": e.detail})

    print(f"\n[ROUTE] ✅ Terminé — {len(results)} sources OK | {len(errors)} erreurs")
    print(f"{'='*50}\n")

    return {
        "total_sources": len(results),
        "feeds":         results,
        **({"errors": errors} if errors else {}),
    }