
from .google_provider import GoogleProvider
from typing import Dict, Any, List

class BraveProvider(GoogleProvider):
    async def search(self, query: str, use_tor: bool = False) -> List[Dict[str, Any]]:
        results = await super().search(query, use_tor=use_tor)
        for res in results:
            res["source"] = "Brave (Proxy)"
            res["source_node"] = "Brave_WebSignalAgent"
            res["source_confidence"] = 0.85
        return results
