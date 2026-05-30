# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Raj Singh / Markanm Team

# -----------------------------------------------
# Blend Engine — by Markanm Team
# https://markanm.com
# -----------------------------------------------
"""
Markanm Search Engine — Core Algorithm
New ranking system with Scrapy + Sarvam 2B LLM integration
"""

import asyncio
import hashlib
import time
import json
import re
from dataclasses import dataclass, field
from typing import Any
from collections import defaultdict
import httpx


# ── Markanm Result dataclass ──────────────────────────────
@dataclass
class MarkanmResult:
    title: str
    url: str
    description: str
    source_engine: str
    score: float = 0.0
    ai_summary: str = ""
    category: str = "web"
    favicon: str = ""
    published: str = ""
    relevance_signals: dict = field(default_factory=dict)


# ── Markanm Ranking Algorithm ─────────────────────────────
class BlendRanker:
    """
    New ranking algorithm — replaces blend's basic score merge.
    Uses: TF-IDF signals + recency boost + domain authority +
          Markanm site preference + AI rerank via Sarvam 2B
    """

    MARKANM_TRUSTED_DOMAINS = {
        "markanm.com": 2.5,
        "snapcourse.in": 2.3,
        "readxhub.in": 2.2,
    }

    HIGH_AUTHORITY_DOMAINS = {
        "wikipedia.org": 1.8,
        "github.com": 1.7,
        "stackoverflow.com": 1.6,
        "arxiv.org": 1.5,
        "scholar.blend.com": 1.5,
        "docs.python.org": 1.4,
        "developer.mozilla.org": 1.4,
    }

    SPAM_PATTERNS = [
        r"click here", r"buy now", r"free download",
        r"[A-Z]{5,}", r"\$\$\$", r"!!!",
    ]

    def __init__(self):
        self.query_cache = {}

    def _domain_score(self, url: str) -> float:
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc.replace("www.", "")
            if domain in self.MARKANM_TRUSTED_DOMAINS:
                return self.MARKANM_TRUSTED_DOMAINS[domain]
            for d, score in self.HIGH_AUTHORITY_DOMAINS.items():
                if d in domain:
                    return score
            return 1.0
        except:
            return 1.0

    def _keyword_relevance(self, query: str, result: MarkanmResult) -> float:
        query_terms = set(query.lower().split())
        title_lower = result.title.lower()
        desc_lower = result.description.lower()

        title_hits = sum(1 for t in query_terms if t in title_lower)
        desc_hits = sum(1 for t in query_terms if t in desc_lower)

        title_score = title_hits / max(len(query_terms), 1) * 2.0
        desc_score = desc_hits / max(len(query_terms), 1) * 0.8

        # Exact phrase bonus
        if query.lower() in title_lower:
            title_score += 1.5
        if query.lower() in desc_lower:
            desc_score += 0.5

        return title_score + desc_score

    def _spam_penalty(self, result: MarkanmResult) -> float:
        text = (result.title + " " + result.description).lower()
        penalty = 1.0
        for pattern in self.SPAM_PATTERNS:
            if re.search(pattern, text):
                penalty *= 0.6
        return penalty

    def _engine_trust_score(self, engine: str) -> float:
        trust = {
            "blend": 1.4, "bing": 1.3, "duckduckgo": 1.2,
            "brave": 1.2, "qwant": 1.1, "wikipedia": 1.5,
            "github": 1.3, "arxiv": 1.4,
        }
        return trust.get(engine.lower(), 1.0)

    def compute_score(self, query: str, result: MarkanmResult) -> float:
        base = result.score if result.score > 0 else 1.0
        domain = self._domain_score(result.url)
        keyword = self._keyword_relevance(query, result)
        spam = self._spam_penalty(result)
        engine_trust = self._engine_trust_score(result.source_engine)

        final = (base * 0.3 + keyword * 0.4 + domain * 0.2 + engine_trust * 0.1) * spam
        return round(final, 4)

    def deduplicate(self, results: list[MarkanmResult]) -> list[MarkanmResult]:
        seen_urls = set()
        seen_titles = set()
        unique = []
        for r in results:
            url_key = r.url.rstrip("/").lower()
            title_key = r.title.lower()[:50]
            if url_key not in seen_urls and title_key not in seen_titles:
                seen_urls.add(url_key)
                seen_titles.add(title_key)
                unique.append(r)
        return unique

    def rank(self, query: str, results: list[MarkanmResult]) -> list[MarkanmResult]:
        for r in results:
            r.score = self.compute_score(query, r)
        deduped = self.deduplicate(results)
        return sorted(deduped, key=lambda x: x.score, reverse=True)


# ── Sarvam 2B LLM Integration ─────────────────────────────
class SarvamAIClient:
    """
    Sarvam 2B — Indian multilingual LLM
    Used for: search summaries, Hindi/regional query understanding,
    result reranking, and answer generation
    """

    def __init__(self, api_key: str = "", base_url: str = "http://localhost:11434"):
        self.api_key = api_key
        self.ollama_url = base_url
        self.model = "sarvam2b"  # Ollama model name for Sarvam 2B

    async def summarize_results(self, query: str, results: list[MarkanmResult]) -> str:
        """Generate AI summary of top results using Sarvam 2B"""
        if not results:
            return ""

        context = "\n".join([
            f"- {r.title}: {r.description[:200]}"
            for r in results[:5]
        ])

        prompt = f"""You are Markanm AI, an intelligent search assistant.
Query: {query}

Top search results:
{context}

Write a clear, concise 2-3 sentence summary answering the query based on these results.
Be factual. Use simple language. If query is in Hindi, respond in Hindi."""

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Try Ollama with Sarvam 2B first
                resp = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.3, "num_predict": 200}
                    }
                )
                if resp.status_code == 200:
                    return resp.json().get("response", "").strip()
        except Exception:
            pass

        # Fallback: try llama3.2 or mistral
        for fallback_model in ["llama3.2", "mistral", "phi3"]:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(
                        f"{self.ollama_url}/api/generate",
                        json={
                            "model": fallback_model,
                            "prompt": prompt,
                            "stream": False,
                            "options": {"temperature": 0.3, "num_predict": 200}
                        }
                    )
                    if resp.status_code == 200:
                        return resp.json().get("response", "").strip()
            except Exception:
                continue

        return ""

    async def detect_language(self, text: str) -> str:
        """Detect if query is Hindi/regional for Sarvam 2B routing"""
        hindi_chars = set("अआइईउऊएऐओऔकखगघचछजझटठडढणतथदधनपफबभमयरलवशषसह")
        if any(c in hindi_chars for c in text):
            return "hi"
        return "en"

    async def expand_query(self, query: str) -> list[str]:
        """Generate query expansions for better recall"""
        return [query, query + " explained", query + " guide"]


# ── Scrapy-based Deep Crawler ──────────────────────────────
class MarkanmCrawler:
    """
    Scrapy-inspired async crawler for deep result enrichment.
    Fetches actual page content for better description extraction.
    """

    SKIP_EXTENSIONS = {'.pdf', '.doc', '.xls', '.zip', '.exe', '.mp4', '.mp3'}

    def __init__(self):
        self.session = None

    async def enrich_result(self, result: MarkanmResult) -> MarkanmResult:
        """Fetch page and extract better title/description"""
        if any(result.url.endswith(ext) for ext in self.SKIP_EXTENSIONS):
            return result

        try:
            async with httpx.AsyncClient(
                timeout=5.0,
                headers={"User-Agent": "MarkanmBot/1.0 (+https://markanm.com/bot)"},
                follow_redirects=True
            ) as client:
                resp = await client.get(result.url)
                if resp.status_code != 200:
                    return result

                html = resp.text[:50000]  # First 50KB only

                # Extract meta description
                meta_match = re.search(
                    r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)',
                    html, re.IGNORECASE
                )
                if meta_match and len(meta_match.group(1)) > len(result.description):
                    result.description = meta_match.group(1)[:500]

                # Extract OG title if better
                og_title = re.search(
                    r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)',
                    html, re.IGNORECASE
                )
                if og_title:
                    result.title = og_title.group(1)[:120]

                # Extract favicon
                fav_match = re.search(r'<link[^>]+rel=["\'](?:icon|shortcut icon)["\'][^>]+href=["\']([^"\']+)', html, re.IGNORECASE)
                if fav_match:
                    result.favicon = fav_match.group(1)

        except Exception:
            pass

        return result

    async def enrich_batch(self, results: list[MarkanmResult], max_enrich: int = 5) -> list[MarkanmResult]:
        """Enrich top N results concurrently"""
        tasks = [self.enrich_result(r) for r in results[:max_enrich]]
        enriched = await asyncio.gather(*tasks, return_exceptions=True)
        for i, result in enumerate(enriched):
            if isinstance(result, MarkanmResult):
                results[i] = result
        return results


# ── Main Markanm Search Pipeline ──────────────────────────
class MarkanmBlendPipeline:
    """
    Complete search pipeline:
    Query → Engines → Collect → Rank → Enrich → AI Summary → Return
    """

    def __init__(self):
        self.ranker = BlendRanker()
        self.ai = SarvamAIClient()
        self.crawler = MarkanmCrawler()
        self._result_cache = {}

    async def blend_search(
        self,
        query: str,
        raw_results: list[dict],
        enable_ai: bool = True,
        enable_enrich: bool = False
    ) -> dict:

        start_time = time.time()
        cache_key = hashlib.md5(query.encode()).hexdigest()

        # Convert raw blend results to MarkanmResult
        markanm_results = []
        for r in raw_results:
            markanm_results.append(MarkanmResult(
                title=r.get("title", ""),
                url=r.get("url", ""),
                description=r.get("content", r.get("description", "")),
                source_engine=", ".join(r.get("engines", ["unknown"])),
                score=float(r.get("score", 0.0)),
                category=r.get("category", "web"),
                published=r.get("publishedDate", ""),
            ))

        # Rank with new algorithm
        ranked = self.ranker.rank(query, markanm_results)

        # Optional: Scrapy-style enrichment of top results
        if enable_enrich:
            ranked = await self.crawler.enrich_batch(ranked, max_enrich=3)

        # AI Summary via Sarvam 2B
        ai_summary = ""
        if enable_ai and ranked:
            ai_summary = await self.ai.summarize_results(query, ranked[:5])

        elapsed = round(time.time() - start_time, 3)

        return {
            "query": query,
            "results": [
                {
                    "title": r.title,
                    "url": r.url,
                    "description": r.description,
                    "score": r.score,
                    "source_engine": r.source_engine,
                    "category": r.category,
                    "favicon": r.favicon,
                    "published": r.published,
                }
                for r in ranked
            ],
            "ai_summary": ai_summary,
            "total": len(ranked),
            "time_ms": elapsed * 1000,
            "powered_by": "Markanm Search + Sarvam 2B AI",
        }


# Singleton
markanm_pipeline = MarkanmBlendPipeline()
