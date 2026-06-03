
from typing import List, Dict, Any
import urllib.parse
import math

def safe_float(val, default=1.0):
    try:
        val = float(val) if val is not None else default
        return val if math.isfinite(val) else default
    except (TypeError, ValueError):
        return default

class RankingEngine:
    def __init__(self):
        self.AUTHORITY_DOMAINS = {
            "wikipedia.org": 30, "github.com": 25, "stackoverflow.com": 25,
            "reddit.com": 20, "quora.com": 15, "developer.mozilla.org": 20,
            "docs.microsoft.com": 20, "medium.com": 10, "youtube.com": 15,
            "news.ycombinator.com": 15, "readxhub.in": 15, "ncbi.nlm.nih.gov": 25
        }
        self.SPAM_KEYWORDS = ["download-free", "crack", "nulled", "cheap", "buy-now", "generator", "free-robux", "clickbait"]
        self.TRUSTED_TLDS = [".gov", ".edu", ".org", ".dev", ".io", ".in", ".co.uk", ".ac.uk"]

    def _compute_semantic_coherence(self, title: str, content: str, query: str) -> float:
        title = title.lower()
        content = content.lower()
        query_lower = query.lower()
        coherence = 0.0
        chunks = [query_lower[i:i+10] for i in range(0, len(query_lower), 5)] if len(query_lower) > 10 else [query_lower]
        for chunk in chunks:
            if len(chunk.strip()) > 3:
                if chunk in title: coherence += 2.0
                if chunk in content: coherence += 1.0
        title_vocab = set(title.split())
        content_vocab = set(content.split())
        if title_vocab and content_vocab:
            overlap = len(title_vocab.intersection(content_vocab))
            coherence += overlap * 0.1
        return coherence

    def _compute_adaptive_gravity(self, result: Dict[str, Any], cluster_max_agreement: float) -> float:
        agreement = float(result.get('cross_source_agreement', 1.0))
        content_depth = float(result.get('content_depth', 1.0))
        trust_multiplier = 1.0
        if agreement > 1.0:
            trust_multiplier += (agreement * 0.5)
        if content_depth > 1.0:
            trust_multiplier += math.log1p(content_depth) * 0.3
        if cluster_max_agreement > 0:
            trust_multiplier = trust_multiplier / (cluster_max_agreement * 0.5 + 0.5)
        return max(0.1, trust_multiplier)

    def _compute_contradiction_penalty(self, result: Dict[str, Any]) -> float:
        content = result.get('content', '').lower()
        penalty = 0.0
        content_len = len(content)
        if content_len < 30:
            penalty += 1.5 
        elif content_len > 300:
            if result.get('cross_source_agreement', 1.0) == 1.0:
                penalty += 0.5
        return penalty

    def rank_results(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        query_words = set(w for w in query.lower().split() if len(w) > 2)
        base = "".join(ch for ch in query.lower().strip().split()[0] if ch.isalnum() or ch in ".-") if query.strip() else ""

        seen_domains = set()
        max_agreement = max([safe_float(r.get('cross_source_agreement', 1.0)) for r in results]) if results else 1.0

        def score(item):
            idx, result = item
            s = 0  # Higher score = better
            
            # 1. Base Score (Reverse upstream index)
            s += (100 - idx * 2)
            
            url = (result.get("url") or "").lower()
            title = (result.get("title") or "").lower()
            content = (result.get("content") or "").lower()
            
            try:
                host = urllib.parse.urlparse(url).netloc.removeprefix("www.")
            except Exception:
                host = ""
                
            # 2. Domain Trust Score
            for domain, boost in self.AUTHORITY_DOMAINS.items():
                if host == domain or host.endswith("." + domain):
                    s += boost
                    
            # 3. Trusted TLD Boost
            if any(host.endswith(tld) for tld in self.TRUSTED_TLDS):
                s += 10
                
            # 4. User Domain Boosting (Exact Match)
            if base and (host == base or host.startswith(base + ".")) and len(content) > 30:
                s += 15
                
            # 5. Content Quality & Spam Penalty
            if any(spam in url or spam in title for spam in self.SPAM_KEYWORDS):
                s -= 100
            if len(content) < 20: 
                s -= 50
                
            # 6. Semantic Relevance / Query Match
            match_count = sum(1 for w in query_words if w in title)
            s += (match_count * 5)
            
            # 7. Crawl4AI Content Confidence
            if result.get("source") == "Crawl4AI":
                s += 5 # Slight boost for deeply crawled content
                
            # 8. Cognitive Enhancements
            coherence = self._compute_semantic_coherence(title, content, query)
            gravity = self._compute_adaptive_gravity(result, max_agreement)
            penalty = self._compute_contradiction_penalty(result)
            
            div_score = 1.0
            if host in seen_domains:
                div_score -= 0.3
            seen_domains.add(host)
            
            confidence = safe_float(result.get('source_confidence', 1.0))
            content_depth = safe_float(result.get('content_depth', 1.0))
            
            base_rel = max(0, s + coherence)
            multipliers = gravity * max(0.1, confidence) * div_score * max(0.5, math.log1p(max(0.0, content_depth)))
            final_relevance = (base_rel * multipliers) - penalty + min(0, s)
            return final_relevance

        scored_results = sorted(enumerate(results), key=score, reverse=True)
        return [r[1] for r in scored_results]
