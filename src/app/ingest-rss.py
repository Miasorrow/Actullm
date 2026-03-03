#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import APIRouter, HTTPException
from typing import Optional
import feedparser

router = APIRouter()

FLUX_URLS = [
    "https://www.france24.com/fr/rss",
    "https://www.lemonde.fr/international/rss_full.xml",
]


def parse_feed(url: str) -> dict:
    """Parse un flux RSS et retourne les métadonnées + articles."""
    feed = feedparser.parse(url)

    if feed.bozo and not feed.entries:
        raise HTTPException(
            status_code=502,
            detail=f"Impossible de récupérer le flux : {url}"
        )

    source_metadata = {
        "source_title": feed.feed.get("title"),
        "source_url":   feed.feed.get("link"),
        "language":     feed.feed.get("language"),
        "last_updated": feed.feed.get("updated"),
        "subtitle":     feed.feed.get("subtitle"),
        "total_entries": len(feed.entries),
    }

    articles = []
    for entry in feed.entries:
        articles.append({
            "title":     entry.get("title"),
            "link":      entry.get("link"),
            "id":        entry.get("id"),
            "published": entry.get("published"),
            "summary":   entry.get("summary"),
            "author":    entry.get("author"),
        })

    latest = articles[0] if articles else None

    return {
        "source": source_metadata,
        "latest_article": latest,
        "articles": articles,
    }


@router.get("/flux-rss")
def get_flux_rss(url: Optional[str] = None):
    """
    Agrège et retourne les flux RSS configurés.

    - Sans paramètre  → retourne tous les flux de FLUX_URLS
    - ?url=<adresse>  → retourne uniquement le flux demandé
    """
    urls = [url] if url else FLUX_URLS

    results = []
    errors  = []

    for feed_url in urls:
        try:
            results.append(parse_feed(feed_url))
        except HTTPException as e:
            errors.append({"url": feed_url, "error": e.detail})

    return {
        "total_sources": len(results),
        "feeds": results,
        **({"errors": errors} if errors else {}),
    }