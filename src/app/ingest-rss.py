#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import feedparser

# Création d'une instance
news_feed = feedparser.parse('https://www.france24.com/fr/rss')

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