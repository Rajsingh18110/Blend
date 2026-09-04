
from .base_provider import BaseProvider
from typing import Dict, Any, List
from bs4 import BeautifulSoup
import urllib.parse
from blend_engine.request_handler import SearchRequestHandler

class GoogleProvider(BaseProvider):
    def __init__(self):
        self.handler = SearchRequestHandler()
        
    async def search(self, query: str, use_tor: bool = False, language: str = "all", pageno: int = 1) -> List[Dict[str, Any]]:
        import asyncio
        from ddgs import DDGS
        
        def _fetch_ddg():
            try:
                results = []
                with DDGS() as ddgs:
                    for r in ddgs.text(query, max_results=10):
                        results.append(r)
                return results
            except Exception as e:
                import logging
                logging.getLogger("GoogleProvider").error(f"DDGS error: {e}")
                return []
                
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
                    "source": "Google (Proxy)",
                    "source_confidence": 1.0,
                    "signal_strength": 1.0,
                    "source_node": "Google_WebSignalAgent",
                    "freshness_metadata": 1.0
                })
        return results
        
    def normalize(self, result: Dict[str, Any]) -> Dict[str, Any]:
        domain = urllib.parse.urlparse(result["url"]).netloc
        result["parsed_url"] = ["https", domain, "", "", "", ""]
        return result
        
    def score(self, result: Dict[str, Any]) -> float:
        return 1.0
        
    def extract_metadata(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return {}
