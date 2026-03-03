#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import feedparser

# Création d'une instance

flux_urls = [
    "https://www.france24.com/fr/rss",
    "https://www.lemonde.fr/international/rss_full.xml"
]
# news_feed = feedparser.parse('https://store.steampowered.com/feeds/news.xml')
for url in flux_urls:
    news_feed = feedparser.parse(url)
    ...

news_feed.feed.title
news_feed.feed.subtitle
news_feed.feed.link
news_feed.feed.language
news_feed.feed.updated
news_feed.feed.get("title")
news_feed.feed.get("language")
# Propriétés du flux
print(news_feed.feed.keys())

# Titre du flux
print("Feed Title:", news_feed.feed.title) 

# Sous-titre du flux
print("Feed Subtitle:", news_feed.feed.subtitle)

# Lien du flux
print("Feed Link:", news_feed.feed.link, "\n")

# Propriétés de chaque item du flux
print(news_feed.entries[0].keys())

for entry in news_feed.entries:
    print(f"{entry.title} --> {entry.link}")
    
# Récupération du deernier feed (dernier bulletin CERT-FR)
for i in range(0, len(news_feed.entries)):
    if i == (len(news_feed.entries)-1):
        print("Alert: {} \nLink: {}".format(news_feed.entries[0]['title'], news_feed.entries[0]['id']))


#! TEST

for url in flux_urls:
    feed = feedparser.parse(url)

    source_metadata = {
        "source_title": feed.feed.get("title"),
        "source_url": feed.feed.get("link"),
        "language": feed.feed.get("language"),
        "last_updated": feed.feed.get("updated")
    }

    for entry in feed.entries:
        article = {
            "title": entry.get("title"),
            "link": entry.get("link"),
            "id": entry.get("id"),
            "published": entry.get("published"),
            "summary": entry.get("summary"),
            "author": entry.get("author"),
            "source": source_metadata
        }

        print(article)