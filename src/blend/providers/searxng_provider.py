import httpx
from typing import Dict, Any, List
import urllib.parse
from .base_provider import BaseProvider

class SearxngProvider(BaseProvider):
    supports_category: bool = True  # Accepts 'category' kwarg from router

    def __init__(self):
        self.endpoint = "http://127.0.0.1:5000/search"
        
    async def search(self, query: str, category: str = "general", use_tor: bool = False, language: str = "all", pageno: int = 1, **kwargs) -> List[Dict[str, Any]]:
        # Map frontend "all" to SearXNG default "en" to prevent random foreign language results
        lang_param = "en-US" if language == "all" else language
        
        params = {
            "q": query,
            "format": "json",
            "language": lang_param,
            "pageno": pageno
        }
        
        # Only add categories if not general, because SearXNG uses 'general' internally by default
        # or we explicitly set it.
        if category and category != "general":
             params["categories"] = category
             
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(self.endpoint, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    results = data.get("results", [])
                    unresponsive = data.get("unresponsive_engines", [])
                    if not results and unresponsive:
                        # Log the failed engines but DO NOT raise — let other providers fill the gap.
                        # Raising here would propagate through the router and potentially discard
                        # results from healthy providers like DDGS.
                        failed = [e[0] for e in unresponsive]
                        print(f"[SearXNG] 0 results, engines failed: {', '.join(failed[:5])}")
                        return []
                    return results
                print(f"[SearXNG] HTTP {resp.status_code}")
                return []
        except Exception as e:
            print(f"[SearXNG] Exception: {type(e).__name__}: {e}")
            raise e

    def normalize(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "title": result.get("title", ""),
            "url": result.get("url", ""),
            "content": result.get("content", ""),
            "engine": result.get("engine", "searxng"),
            "parsed_url": ["https", urllib.parse.urlparse(result.get("url", "")).netloc, "", "", "", ""]
        }

    def score(self, result: Dict[str, Any]) -> float:
        return 0.8  # Default score for SearXNG results

    def extract_metadata(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "engines": result.get("engines", [])
        }
