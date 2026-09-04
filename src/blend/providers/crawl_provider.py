
from .base_provider import BaseProvider
from typing import Dict, Any, List

class CrawlProvider(BaseProvider):
    async def search(self, query: str, use_tor: bool = False, language: str = "all", pageno: int = 1, **kwargs) -> List[Dict[str, Any]]: return []
    def normalize(self, result: Dict[str, Any]) -> Dict[str, Any]: return result
    def score(self, result: Dict[str, Any]) -> float: return 1.0
    def extract_metadata(self, result: Dict[str, Any]) -> Dict[str, Any]: return {}
