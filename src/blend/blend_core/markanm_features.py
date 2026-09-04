# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Raj Singh / Markanm Team

# -----------------------------------------------
# Blend Engine — by Markanm Team
# https://markanm.com
# -----------------------------------------------
"""Markanm browser-style search helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping
from urllib.parse import urlparse
import re


AI_MODE_CHOICES: tuple[tuple[str, str], ...] = (
    ("fast", "Fast Response"),
    ("deep", "Deep Research"),
    ("ask", "AI Answer"),
)

ENGINE_SCOPE_CHOICES: tuple[tuple[str, str], ...] = (
    ("markanm", "Blend Search"),
    ("blend", "blend Focus"),
    ("duckduckgo", "DuckDuckGo Focus"),
    ("brave", "Brave Focus"),
    ("wikipedia", "Wikipedia"),
    ("github", "GitHub"),
)

ENGINE_SCOPE_MAP: dict[str, dict[str, str]] = {
    "blend": {
        "general": "blend",
        "images": "blend images",
        "news": "blend news",
        "videos": "blend videos",
        "it": "blend",
        "science": "blend scholar",
        "files": "blend",
    },
    "duckduckgo": {
        "general": "duckduckgo",
        "images": "duckduckgo images",
        "news": "duckduckgo news",
        "videos": "duckduckgo videos",
    },
    "brave": {
        "general": "brave",
        "images": "brave.images",
        "news": "brave.news",
        "videos": "brave.videos",
    },
    "wikipedia": {
        "general": "wikipedia",
        "science": "wikipedia",
    },
    "github": {
        "general": "github",
        "it": "github code",
        "files": "github",
    },
}

URL_HOST_RE = re.compile(
    r"^(?:(?:https?://)?)(?:[a-z0-9-]+\.)+[a-z]{2,}(?:[:/][^\s]*)?$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class KnowledgeCard:
    query_key: str
    title: str
    subtitle: str
    summary: str
    facts: tuple[tuple[str, str], ...]


KNOWLEDGE_CARDS: tuple[KnowledgeCard, ...] = (
    KnowledgeCard(
        query_key="markanm.com",
        title="Blend",
        subtitle="Founding company and product system behind the Blend browser stack",
        summary=(
            "Blend is the browser-facing search system and product layer that ties together "
            "direct navigation, search, AI answers, and research workflows."
        ),
        facts=(
            ("Role", "Browser + search engine"),
            ("Builds", "Navigation, search, AI workflows"),
            ("Identity", "Dark-first LLM browser direction"),
        ),
    ),
    KnowledgeCard(
        query_key="markanm",
        title="Blend",
        subtitle="Browser + search + AI ecosystem",
        summary=(
            "Blend is your product ecosystem for browser-led search, AI answers, "
            "focused research, and future voice workflows."
        ),
        facts=(
            ("Modes", "Fast response, deep research, AI answer"),
            ("Search", "Blended engines plus custom ranking"),
            ("Next", "ReadxHub, voice, crawler, and domain merge"),
        ),
    ),
    KnowledgeCard(
        query_key="readxhub",
        title="ReadxHub",
        subtitle="Long-form reading and knowledge layer",
        summary=(
            "ReadxHub can be merged into Blend as a reading, summarization, and knowledge "
            "destination for research-heavy workflows."
        ),
        facts=(
            ("Merge state", "Architecture-ready"),
            ("Use", "Reading, summarizing, source organization"),
            ("Needs next", "DNS, routing, and source/content rules"),
        ),
    ),
)


def normalize_ai_mode(value: str | None) -> str:
    if value in {choice[0] for choice in AI_MODE_CHOICES}:
        return value or "fast"
    return "fast"


def normalize_engine_scope(value: str | None) -> str:
    if value in {choice[0] for choice in ENGINE_SCOPE_CHOICES}:
        return value or "markanm"
    return "markanm"


def looks_like_direct_url(query: str) -> bool:
    text = query.strip()
    if not text or " " in text:
        return False
    return bool(URL_HOST_RE.match(text))


def normalize_direct_url(query: str) -> str | None:
    if not looks_like_direct_url(query):
        return None
    text = query.strip()
    if not text.startswith(("http://", "https://")):
        text = f"https://{text}"
    parsed = urlparse(text)
    if not parsed.netloc:
        return None
    return text


def selected_category(form: Mapping[str, str], fallback: str = "general") -> str:
    categories = [key[9:] for key, value in form.items() if key.startswith("category_") and value != "off"]
    if "categories" in form and form["categories"]:
        categories.extend([item.strip() for item in form["categories"].split(",") if item.strip()])
    return categories[0] if categories else fallback


def engine_name_for_scope(engine_scope: str, category: str) -> str | None:
    scoped = ENGINE_SCOPE_MAP.get(engine_scope, {})
    return scoped.get(category) or scoped.get("general")


def find_knowledge_card(query: str) -> KnowledgeCard | None:
    lowered = query.strip().lower()
    if not lowered:
        return None
    for card in KNOWLEDGE_CARDS:
        if card.query_key in lowered:
            return card
    return None


def build_ai_answer(query: str, card: KnowledgeCard | None, ai_mode: str) -> str:
    if card is None:
        return ""
    tone = {
        "fast": "Quick answer",
        "deep": "Deep research brief",
        "ask": "AI explanation",
    }.get(ai_mode, "Quick answer")
    return f"{tone}: {card.summary}"
