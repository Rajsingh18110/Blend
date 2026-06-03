
from .base_provider import BaseProvider
from typing import Dict, Any, List
import urllib.parse
from bs4 import BeautifulSoup
from blend_engine.request_handler import SearchRequestHandler

class BingProvider(BaseProvider):
    def __init__(self):
        self.handler = SearchRequestHandler()
        
    async def search(self, query: str, use_tor: bool = False) -> List[Dict[str, Any]]:
        encoded_query = urllib.parse.quote(query)
        url = f"https://lite.qwant.com/?q={encoded_query}"
        responses = await self.handler.execute_parallel_requests([url], use_tor=use_tor)
        if not responses[0]: return []
        
        results = []
        soup = BeautifulSoup(responses[0], "html.parser")
        for item in soup.select(".result"):
            title_el = item.select_one(".result__title")
            url_el = item.select_one(".result__url")
            snippet_el = item.select_one(".result__snippet")
            if title_el and url_el:
                title = title_el.get_text(" ", strip=True)
                href = url_el.get("href", "") or url_el.get_text(" ", strip=True)
                if not href.startswith("http"): href = "https://" + href
                snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""
                results.append({
                    "url": href, 
                    "title": title, 
                    "content": snippet, 
                    "source": "Bing (Proxy)",
                    "source_confidence": 0.9,
                    "signal_strength": 0.95,
                    "source_node": "Bing_WebSignalAgent",
                    "freshness_metadata": 1.0
                })
        return results
        
    def normalize(self, result: Dict[str, Any]) -> Dict[str, Any]:
        domain = urllib.parse.urlparse(result["url"]).netloc
        result["parsed_url"] = ["https", domain, "", "", "", ""]
        return result
        
    def score(self, result: Dict[str, Any]) -> float: return 1.0
    def extract_metadata(self, result: Dict[str, Any]) -> Dict[str, Any]: return {}
