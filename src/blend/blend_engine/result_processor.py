import urllib.parse
from typing import List, Dict, Any

class ResultProcessor:
    """
    Standardizes raw data from various sources (HTML, JSON, Crawl4AI)
    into a strict Blend result schema.
    """

    @staticmethod
    def clean_url(url: str) -> str:
        """Strip tracking parameters from URLs."""
        try:
            parsed = urllib.parse.urlparse(url)
            query = urllib.parse.parse_qs(parsed.query)
            
            # Remove common tracking parameters
            tracking_params = ['utm_source', 'utm_medium', 'utm_campaign', 'gclid', 'fbclid', 'ref']
            for param in tracking_params:
                query.pop(param, None)
                
            clean_query = urllib.parse.urlencode(query, doseq=True)
            clean_url = parsed._replace(query=clean_query).geturl()
            return clean_url
        except Exception:
            return url

    @staticmethod
    def format_result(title: str, url: str, content: str, source: str = "Blend", metadata: Dict = None) -> Dict[str, Any]:
        """
        Creates a unified Blend result object.
        Preserves frontend contract (title, url, content, parsed_url).
        """
        if metadata is None:
            metadata = {}
            
        clean_url = ResultProcessor.clean_url(url)
        domain = ""
        try:
            domain = urllib.parse.urlparse(clean_url).netloc
        except Exception:
            pass
            
        return {
            "title": title.strip() if title else "Untitled Result",
            "url": clean_url,
            "content": content.strip() if content else "",
            "source": source,
            "metadata": metadata,
            "trust_score": 0.0,
            "parsed_url": ["https", domain, "", "", "", ""] # Frontend URL tuple contract
        }

    @staticmethod
    def _compute_similarity(str1: str, str2: str) -> float:
        """Simple token-based Jaccard similarity for string overlap."""
        set1 = set(str1.lower().split())
        set2 = set(str2.lower().split())
        if not set1 or not set2: return 0.0
        return len(set1.intersection(set2)) / len(set1.union(set2))

    @staticmethod
    def deduplicate(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        P0-12: Deduplication.
        Primary duplicate identity: normalized canonical URL.
        Do NOT aggressively remove results merely because title or snippet is similar.
        Different URLs should remain different results unless there is strong evidence they represent the exact same resource.
        """
        fused_clusters = []
        seen_urls = {}
        
        for res in results:
            url = res.get('url', '')
            if not url:
                fused_clusters.append(res)
                continue
                
            clean_url = ResultProcessor.clean_url(url).lower()
            
            if clean_url in seen_urls:
                # Exact URL match -> Merge
                cluster = seen_urls[clean_url]
                cluster['cross_source_agreement'] = cluster.get('cross_source_agreement', 1.0) + 1.0
                cluster['source_confidence'] = max(cluster.get('source_confidence', 0), res.get('source_confidence', 0))
                
                engine_name = res.get('engine') or res.get('source', '')
                cluster_source = cluster.get('source') or ''
                if engine_name and engine_name not in cluster_source:
                    cluster['source'] = cluster_source + f", {engine_name}"
            else:
                # New URL -> Keep
                res['cross_source_agreement'] = 1.0
                res['content_depth'] = 1.0
                if 'source_confidence' not in res:
                    res['source_confidence'] = 1.0
                if 'engine' in res and 'source' not in res:
                    res['source'] = res['engine']
                
                seen_urls[clean_url] = res
                fused_clusters.append(res)
                
        return fused_clusters
