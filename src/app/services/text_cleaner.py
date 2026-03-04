#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup


def clean_html(text: str) -> str:
    """Supprime les balises HTML d'un texte brut RSS."""
    return BeautifulSoup(text or "", "html.parser").get_text(separator=" ").strip()
