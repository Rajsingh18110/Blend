import httpx
from typing import Dict, Any, List
import urllib.parse
from .base_provider import BaseProvider

class SearxngProvider(BaseProvider):
    def __init__(self):
        self.endpoint = "http://127.0.0.1:5000/search"
        
    async def search(self, query: str, use_tor: bool = False, language: str = "all", pageno: int = 1) -> List[Dict[str, Any]]:
        # Map frontend "all" to SearXNG default "en" to prevent random foreign language results
        lang_param = "en-US" if language == "all" else language
        
        params = {
            "q": query,
            "format": "json",
            "language": lang_param,
            "pageno": pageno
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(self.endpoint, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    results = data.get("results", [])
                    unresponsive = data.get("unresponsive_engines", [])
                    if not results and unresponsive:
                        failed = [e[0] for e in unresponsive]
                        raise Exception(f"SearXNG upstream engines failed: {', '.join(failed[:3])}")
                    return results
                return []
        except Exception as e:
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
