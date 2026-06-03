import os

def create_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)

# 1. blend_engine/search_router.py
create_file('backend/blend_engine/search_router.py', '''
import asyncio
from typing import Dict, Any
from .provider_manager import ProviderManager
from .ranking_engine import RankingEngine
from .result_processor import ResultProcessor

class SearchRouter:
    def __init__(self):
        self.provider_manager = ProviderManager()
        self.ranking_engine = RankingEngine()
        self.result_processor = ResultProcessor()

    async def route(self, query: str, category: str = "general", mode: str = "fast", engines: str = "") -> Dict[str, Any]:
        """Routes the search request to the appropriate providers."""
        providers = self.provider_manager.get_providers(category, engines)
        
        # Execute providers in parallel
        tasks = [p.search(query) for p in providers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_results = []
        for i, res in enumerate(results):
            if isinstance(res, list):
                # normalize and extract metadata
                normalized = [providers[i].normalize(r) for r in res]
                all_results.extend(normalized)
                
        unique_results = self.result_processor.deduplicate(all_results)
        ranked_results = self.ranking_engine.rank_results(unique_results, query)
        
        return {
            "query": query,
            "number_of_results": len(ranked_results),
            "results": ranked_results,
            "answers": [],
            "suggestions": []
        }
''')

# 2. blend_engine/provider_manager.py
create_file('backend/blend_engine/provider_manager.py', '''
from typing import List
from ..providers.google_provider import GoogleProvider
from ..providers.bing_provider import BingProvider
from ..providers.brave_provider import BraveProvider
from ..providers.crawl_provider import CrawlProvider

class ProviderManager:
    def __init__(self):
        self.providers = {
            "google": GoogleProvider(),
            "bing": BingProvider(),
            "brave": BraveProvider(),
            "crawl": CrawlProvider()
        }

    def get_providers(self, category: str, engines_to_force: str) -> List[Any]:
        if engines_to_force:
            engine_names = [e.strip() for e in engines_to_force.split(",")]
            selected = [self.providers[e] for e in engine_names if e in self.providers]
            if selected: return selected
            
        if category == "images":
            return [self.providers["bing"], self.providers["brave"]]
        elif category == "news":
            return [self.providers["google"], self.providers["bing"]]
        else:
            return [self.providers["google"], self.providers["brave"]]
''')

# 3. blend_engine/ranking_engine.py (REWRITE)
create_file('backend/blend_engine/ranking_engine.py', '''
from typing import List, Dict, Any
import urllib.parse

class RankingEngine:
    def __init__(self):
        self.AUTHORITY_DOMAINS = {
            "wikipedia.org": 30, "github.com": 25, "stackoverflow.com": 25,
            "reddit.com": 20, "quora.com": 15, "developer.mozilla.org": 20,
            "docs.microsoft.com": 20, "medium.com": 10, "youtube.com": 15,
            "news.ycombinator.com": 15, "readxhub.in": 15, "ncbi.nlm.nih.gov": 25
        }
        self.SPAM_KEYWORDS = ["download-free", "crack", "nulled", "cheap", "buy-now", "generator", "free-robux", "clickbait"]
        self.TRUSTED_TLDS = [".gov", ".edu", ".org", ".dev", ".io", ".in", ".co.uk", ".ac.uk"]

    def rank_results(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        query_words = set(w for w in query.lower().split() if len(w) > 2)
        base = "".join(ch for ch in query.lower().strip().split()[0] if ch.isalnum() or ch in ".-") if query.strip() else ""

        def score(item):
            idx, result = item
            s = 0  # Higher score = better
            
            # 1. Base Score (Reverse upstream index)
            s += (100 - idx * 2)
            
            url = result.get("url", "").lower()
            title = result.get("title", "").lower()
            content = result.get("content", "").lower()
            
            try:
                host = urllib.parse.urlparse(url).netloc.removeprefix("www.")
            except Exception:
                host = ""
                
            # 2. Domain Trust Score
            for domain, boost in self.AUTHORITY_DOMAINS.items():
                if host == domain or host.endswith("." + domain):
                    s += boost
                    
            # 3. Trusted TLD Boost
            if any(host.endswith(tld) for tld in self.TRUSTED_TLDS):
                s += 10
                
            # 4. User Domain Boosting (Exact Match)
            if base and (host == base or host.startswith(base + ".")) and len(content) > 30:
                s += 15
                
            # 5. Content Quality & Spam Penalty
            if any(spam in url or spam in title for spam in self.SPAM_KEYWORDS):
                s -= 100
            if len(content) < 20: 
                s -= 50
                
            # 6. Semantic Relevance / Query Match
            match_count = sum(1 for w in query_words if w in title)
            s += (match_count * 5)
            
            # 7. Crawl4AI Content Confidence
            if result.get("source") == "Crawl4AI":
                s += 5 # Slight boost for deeply crawled content
                
            # 8. Freshness (Placeholder - extract from content if available)
            # (To be implemented fully later)
                
            # Store score for sorting, negate it because we sort ascending by default?
            # Actually, sort descending: reverse=True
            return s

        scored_results = sorted(enumerate(results), key=score, reverse=True)
        return [r[1] for r in scored_results]
''')

# 4. providers/base_provider.py
create_file('backend/providers/base_provider.py', '''
from typing import Dict, Any, List
import abc

class BaseProvider(abc.ABC):
    @abc.abstractmethod
    async def search(self, query: str) -> List[Dict[str, Any]]:
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
''')

# 5. providers/google_provider.py
create_file('backend/providers/google_provider.py', '''
from .base_provider import BaseProvider
from typing import Dict, Any, List
from bs4 import BeautifulSoup
import urllib.parse
from ..blend_engine.request_handler import SearchRequestHandler

class GoogleProvider(BaseProvider):
    def __init__(self):
        self.handler = SearchRequestHandler()
        
    async def search(self, query: str) -> List[Dict[str, Any]]:
        encoded_query = urllib.parse.quote(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}" # Mocking google with DDG for safety in this env
        responses = await self.handler.execute_parallel_requests([url], use_tor=False)
        if not responses[0]: return []
        
        results = []
        soup = BeautifulSoup(responses[0], "html.parser")
        for item in soup.select(".result"):
            link = item.select_one(".result__a")
            if not link: continue
            href = link.get("href", "")
            if href.startswith("/l/"):
                parsed = urllib.parse.urlparse(href)
                href = urllib.parse.unquote(urllib.parse.parse_qs(parsed.query).get("uddg", [""])[0])
            title = link.get_text(" ", strip=True)
            snippet_el = item.select_one(".result__snippet")
            snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""
            if href and title:
                results.append({"url": href, "title": title, "content": snippet, "source": "Google (Proxy)"})
        return results
        
    def normalize(self, result: Dict[str, Any]) -> Dict[str, Any]:
        domain = urllib.parse.urlparse(result["url"]).netloc
        result["parsed_url"] = ["https", domain, "", "", "", ""]
        return result
        
    def score(self, result: Dict[str, Any]) -> float:
        return 1.0
        
    def extract_metadata(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return {}
''')

# 6. providers/bing_provider.py (Mirror of above for simplicity in the rewrite)
create_file('backend/providers/bing_provider.py', '''
from .base_provider import BaseProvider
from typing import Dict, Any, List
import urllib.parse
from bs4 import BeautifulSoup
from ..blend_engine.request_handler import SearchRequestHandler

class BingProvider(BaseProvider):
    def __init__(self):
        self.handler = SearchRequestHandler()
        
    async def search(self, query: str) -> List[Dict[str, Any]]:
        encoded_query = urllib.parse.quote(query)
        url = f"https://lite.qwant.com/?q={encoded_query}"
        responses = await self.handler.execute_parallel_requests([url], use_tor=False)
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
                results.append({"url": href, "title": title, "content": snippet, "source": "Bing (Proxy)"})
        return results
        
    def normalize(self, result: Dict[str, Any]) -> Dict[str, Any]:
        domain = urllib.parse.urlparse(result["url"]).netloc
        result["parsed_url"] = ["https", domain, "", "", "", ""]
        return result
        
    def score(self, result: Dict[str, Any]) -> float: return 1.0
    def extract_metadata(self, result: Dict[str, Any]) -> Dict[str, Any]: return {}
''')

create_file('backend/providers/brave_provider.py', '''
from .google_provider import GoogleProvider
class BraveProvider(GoogleProvider): pass
''')

create_file('backend/providers/crawl_provider.py', '''
from .base_provider import BaseProvider
from typing import Dict, Any, List

class CrawlProvider(BaseProvider):
    async def search(self, query: str) -> List[Dict[str, Any]]: return []
    def normalize(self, result: Dict[str, Any]) -> Dict[str, Any]: return result
    def score(self, result: Dict[str, Any]) -> float: return 1.0
    def extract_metadata(self, result: Dict[str, Any]) -> Dict[str, Any]: return {}
''')
