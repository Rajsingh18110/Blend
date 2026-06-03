
from .base_provider import BaseProvider
from typing import Dict, Any, List
from bs4 import BeautifulSoup
import urllib.parse
from blend_engine.request_handler import SearchRequestHandler

class GoogleProvider(BaseProvider):
    def __init__(self):
        self.handler = SearchRequestHandler()
        
    async def search(self, query: str, use_tor: bool = False) -> List[Dict[str, Any]]:
        encoded_query = urllib.parse.quote(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}" # Mocking google with DDG for safety in this env
        responses = await self.handler.execute_parallel_requests([url], use_tor=use_tor)
        if not responses[0]: return []
        
        results = []
        soup = BeautifulSoup(responses[0], "html.parser")
        for item in soup.select(".result"):
            link = item.select_one(".result__a")
            if not link: continue
            href = link.get("href", "")
            if "uddg=" in href:
                parsed = urllib.parse.urlparse(href)
                href = urllib.parse.unquote(urllib.parse.parse_qs(parsed.query).get("uddg", [""])[0])
            elif href.startswith("//"):
                href = "https:" + href
            title = link.get_text(" ", strip=True)
            snippet_el = item.select_one(".result__snippet")
            snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""
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
