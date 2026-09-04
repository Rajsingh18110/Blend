
from typing import Dict, Any, List
import abc

class BaseProvider(abc.ABC):
    """
    All providers must implement a uniform search() signature.

    Provider signature contract (P0-7):
        search(query, use_tor, language, pageno, category)

    'category' is optional in implementations that don't use it — they
    can accept **kwargs or define it with a default. The router always
    passes category as a keyword argument.

    DO NOT use co_varnames introspection to detect signature — use this
    base class contract instead.
    """

    # Set to True in subclasses that accept a `category` parameter.
    # This is the clean alternative to runtime co_varnames inspection.
    supports_category: bool = False

    @abc.abstractmethod
    async def search(self, query: str, use_tor: bool = False, language: str = "all", pageno: int = 1, **kwargs) -> List[Dict[str, Any]]:
        pass
        
    @abc.abstractmethod
    def normalize(self, result: Dict[str, Any]) -> Dict[str, Any]:
        pass
        
    @abc.abstractmethod
    def score(self, result: Dict[str, Any]) -> float:
        pass
        
    @abc.abstractmethod
    def extract_metadata(self, result: Dict[str, Any]) -> Dict[str, Any]:
        pass
