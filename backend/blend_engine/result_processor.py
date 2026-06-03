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
            "parsed_url": ["https", domain, "", "", "", ""] # Required by SearxNG UI contract
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
        Cognitive Cross-Source Validation & Confidence Amplification.
        Merges results based on title/content similarity, not just URLs.
        """
        fused_clusters = []
        
        for res in results:
            bypass_sources = {'Bing Images', 'YouTube Music', 'YouTube'}
            if res.get('source') in bypass_sources:
                res['cross_source_agreement'] = 1.0
                res['content_depth'] = 1.0
                if 'source_confidence' not in res:
                    res['source_confidence'] = 1.0
                fused_clusters.append(res)
                continue

            title = res.get('title', '')
            content = res.get('content', '')
            url = res.get('url', '')
            
            merged = False
            for cluster in fused_clusters:
                # Check semantic overlap (similarity > 0.4) or identical URL
                title_sim = ResultProcessor._compute_similarity(title, cluster.get('title', ''))
                content_sim = ResultProcessor._compute_similarity(content, cluster.get('content', ''))
                
                if title_sim > 0.4 or content_sim > 0.5 or url == cluster.get('url'):
                    # Merge into existing cluster
                    cluster['cross_source_agreement'] += 1.0
                    cluster['source_confidence'] = max(cluster.get('source_confidence', 0), res.get('source_confidence', 0))
                    
                    if res.get('source', '') not in cluster.get('source', ''):
                        cluster['source'] = cluster.get('source', '') + f", {res.get('source', '')}"
                        
                    # Expand content depth if new snippet provides more text
                    if content and cluster.get('content') is not None and content not in cluster['content'] and len(content) > 30:
                        cluster['content'] += " ... " + content
                        cluster['content_depth'] += 1.0
                        
                    merged = True
                    break
                    
            if not merged:
                # Initialize new cluster node
                res['cross_source_agreement'] = 1.0
                res['content_depth'] = 1.0
                if 'source_confidence' not in res:
                    res['source_confidence'] = 1.0
                fused_clusters.append(res)
                
        return fused_clusters
