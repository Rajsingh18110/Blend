
from .base_provider import BaseProvider
from typing import Dict, Any, List
import urllib.parse
import logging

logger = logging.getLogger("DDGSProvider")

class DDGSProvider(BaseProvider):
    """
    Web search provider backed by duckduckgo-search (DDGS).

    Named 'DDGSProvider' for accuracy (P0-3: do not silently misname providers).
    Previously called 'GoogleProvider' — that name was misleading as it uses
    the DuckDuckGo search library, not the Google Search API.

    Backward-compat alias 'GoogleProvider' is preserved at the bottom of this
    module so existing imports continue to work.
    """
    supports_category: bool = False  # DDGS doesn't route by category

    def __init__(self):
        pass
        
    async def search(self, query: str, use_tor: bool = False, language: str = "all", pageno: int = 1, **kwargs) -> List[Dict[str, Any]]:
        import asyncio

        def _fetch_ddg():
            try:
                from ddgs import DDGS
                results = []
                with DDGS() as ddgs:
                    for r in ddgs.text(query, max_results=10):
                        results.append(r)
                logger.info(f"DDGS returned {len(results)} results for '{query}'")
                return results
            except Exception as e:
                logger.error(f"DDGS error for '{query}': {type(e).__name__}: {e}")
                raise Exception(f"DuckDuckGo search failed: {e}")
                
        # Run synchronous ddgs in executor to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        ddg_results = await loop.run_in_executor(None, _fetch_ddg)
        
        results = []
        for item in ddg_results:
            href = item.get("href", "")
            title = item.get("title", "")
            snippet = item.get("body", "")
            if href and title:
                results.append({
                    "url": href, 
                    "title": title, 
                    "content": snippet, 
                    "source": "DuckDuckGo",
                    "source_confidence": 1.0,
                    "signal_strength": 1.0,
                })
        return results
        
    def normalize(self, result: Dict[str, Any]) -> Dict[str, Any]:
        domain = urllib.parse.urlparse(result.get("url", "")).netloc
        result["parsed_url"] = ["https", domain, "", "", "", ""]
        return result
        
    def score(self, result: Dict[str, Any]) -> float:
        return 1.0
        
    def extract_metadata(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return {}


# Backward-compat alias (P0-3: preserve imports without breaking behavior)
GoogleProvider = DDGSProvider
