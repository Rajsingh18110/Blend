
from .google_provider import GoogleProvider
from typing import Dict, Any, List

class BraveProvider(GoogleProvider):
    async def search(self, query: str, use_tor: bool = False, language: str = "all", pageno: int = 1) -> List[Dict[str, Any]]:
        # Disabled to prevent duplicate proxy requests
        return []
