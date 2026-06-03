import urllib.parse
from typing import List, Dict, Any
import math

class RankingEngine:
    """
    Information Cognition System - Cognitive Ranking Engine.
    Uses dynamic semantic coherence, adaptive domain trust, and clustering signals.
    No hardcoded whitelists or keyword counting.
    """

    def __init__(self):
        pass

    def _compute_semantic_coherence(self, result: Dict[str, Any], query: str) -> float:
        """Calculates title-content coherence and phrase overlap without exact keyword counting."""
        title = result.get('title', '').lower()
        content = result.get('content', '').lower()
        query_lower = query.lower()
        
        coherence = 0.0
        
        # Phrase overlap: checking if multi-word chunks from query exist
        chunks = [query_lower[i:i+10] for i in range(0, len(query_lower), 5)] if len(query_lower) > 10 else [query_lower]
        for chunk in chunks:
            if len(chunk.strip()) > 3:
                if chunk in title: coherence += 2.0
                if chunk in content: coherence += 1.0
                
        # Title-content coherence (do they share significant vocabulary?)
        title_vocab = set(title.split())
        content_vocab = set(content.split())
        if title_vocab and content_vocab:
            overlap = len(title_vocab.intersection(content_vocab))
            coherence += overlap * 0.1
            
        return coherence

    def _compute_adaptive_gravity(self, result: Dict[str, Any], cluster_max_agreement: float) -> float:
        """
        Calculates dynamic domain trust based entirely on runtime clustering.
        No hardcoded whitelists.
        """
        agreement = float(result.get('cross_source_agreement', 1.0))
        content_depth = float(result.get('content_depth', 1.0))
        
        # Trust is earned if multiple independent nodes retrieved this domain
        # and it survived semantic fusion (depth > 1)
        trust_multiplier = 1.0
        if agreement > 1.0:
            trust_multiplier += (agreement * 0.5)
        if content_depth > 1.0:
            trust_multiplier += math.log1p(content_depth) * 0.3
            
        # Normalize against the strongest cluster to prevent infinite scaling
        if cluster_max_agreement > 0:
            trust_multiplier = trust_multiplier / (cluster_max_agreement * 0.5 + 0.5)
            
        return max(0.1, trust_multiplier)

    def _compute_contradiction_penalty(self, result: Dict[str, Any]) -> float:
        """Detects low-quality signals dynamically."""
        content = result.get('content', '').lower()
        penalty = 0.0
        
        content_len = len(content)
        if content_len < 30:
            penalty += 1.5 # Extreme thin content penalty
        elif content_len > 300:
            # Overly verbose without agreement might be spam
            if result.get('cross_source_agreement', 1.0) == 1.0:
                penalty += 0.5
                
        return penalty

    def _compute_freshness_decay(self, result: Dict[str, Any]) -> float:
        return 1.0

    def rank_results(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """
        Executes Cognitive Ranking against all clustered signals.
        """
        seen_domains = set()
        diversity_penalty = 0.3

        # Find max agreement for dynamic normalization
        max_agreement = max([float(r.get('cross_source_agreement', 1.0)) for r in results]) if results else 1.0

        scored_results = []
        for res in results:
            url = res.get('url', '')
            try:
                domain = urllib.parse.urlparse(url).netloc.lower()
            except Exception:
                domain = ""
            
            # Dynamic Scoring Dimensions
            coherence = self._compute_semantic_coherence(res, query)
            gravity = self._compute_adaptive_gravity(res, max_agreement)
            penalty = self._compute_contradiction_penalty(res)
            
            confidence = float(res.get('source_confidence', 1.0))
            content_depth = float(res.get('content_depth', 1.0))
            
            # Adaptive Diversity Score
            div_score = 1.0
            if domain in seen_domains:
                div_score -= diversity_penalty
            seen_domains.add(domain)

            # Final Dynamic Cognitive Formula
            # Fully relies on runtime intelligence: coherence, dynamic gravity, confidence, richness, uniqueness
            final_relevance = (
                (coherence * gravity * confidence * div_score * math.log1p(content_depth)) 
                - penalty
            ) * self._compute_freshness_decay(res)
            
            res['trust_score'] = round(final_relevance, 3)
            scored_results.append(res)

        return sorted(scored_results, key=lambda x: x.get('trust_score', 0.0), reverse=True)
