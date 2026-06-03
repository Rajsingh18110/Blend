
from typing import Dict, Any, List
import abc

class BaseProvider(abc.ABC):
    @abc.abstractmethod
    async def search(self, query: str, use_tor: bool = False) -> List[Dict[str, Any]]:
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
