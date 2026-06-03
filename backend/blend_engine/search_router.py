
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
        self._deep_semaphore = asyncio.Semaphore(1)

    async def route(self, query: str, category: str = "general", mode: str = "fast", engines: str = "", use_tor: bool = False) -> Dict[str, Any]:
        """Routes the search request to the appropriate providers."""
        providers = self.provider_manager.get_providers(category, engines)
        
        # Execute providers in parallel
        tasks = [p.search(query, use_tor=use_tor) for p in providers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_results = []
        errors = []
        for i, res in enumerate(results):
            if isinstance(res, list):
                # normalize and extract metadata
                normalized = [providers[i].normalize(r) for r in res]
                all_results.extend(normalized)
            elif isinstance(res, Exception):
                errors.append(str(res))
                
        unique_results = self.result_processor.deduplicate(all_results)
        ranked_results = self.ranking_engine.rank_results(unique_results, query)
        
        if mode == "deep":
            crawler = None
            try:
                from scrapers.crawl4ai_wrapper import Crawl4AIWrapper
                crawler = Crawl4AIWrapper()
                budget = {'count': 0}
                
                rate_limiter = None
                try:
                    from utils.rate_limit import RateLimiter
                    rate_limiter = RateLimiter()
                except ImportError:
                    pass

                top_results = ranked_results[:3]
                async with self._deep_semaphore:
                    visited = set()
                    crawl_tasks = [
                        self._crawl_recursive(crawler, rate_limiter, visited, res.get('url', ''), depth=1, budget=budget)
                        for res in top_results
                    ]
                    crawled_data = await asyncio.gather(*crawl_tasks, return_exceptions=True)
                for idx, data in enumerate(crawled_data):
                    if isinstance(data, dict):
                        top_results[idx]["deep_content"] = data.get("markdown", "")
                        top_results[idx]["sub_pages"] = data.get("sub_pages", [])
            except ImportError:
                pass
            except Exception:
                pass
            finally:
                if crawler:
                    await crawler.close()
        
        return {
            "query": query,
            "number_of_results": len(ranked_results),
            "results": ranked_results,
            "answers": [],
            "suggestions": [],
            "errors": errors
        }

    async def _crawl_recursive(self, crawler, rate_limiter, visited: set, url: str, depth: int, budget: dict, max_depth: int = 2, max_budget: int = 5) -> Dict[str, Any]:
        if depth > max_depth or budget['count'] >= max_budget:
            return None
        
        if url in visited:
            return None
        visited.add(url)
        
        try:
            from utils.security import is_safe_url
            is_safe, _ = is_safe_url(url)
            if not is_safe:
                return None
        except Exception:
            return None
            
        budget['count'] += 1
        
        try:
            import urllib.parse
            domain = urllib.parse.urlparse(url).netloc
            if rate_limiter:
                async with rate_limiter.acquire(domain):
                    data = await crawler.extract(url)
            else:
                await asyncio.sleep(1.0)
                data = await crawler.extract(url)
        except Exception:
            return None
            
        if not isinstance(data, dict) or not data.get("success"):
            return None
            
        result = {
            "url": url,
            "markdown": data.get("markdown", ""),
            "sub_pages": []
        }
        
        if depth < max_depth:
            links_dict = data.get("links") or {}
            valid_links = [l['href'] for l in links_dict.get("internal", []) if l.get('href')][:3]
            tasks = [self._crawl_recursive(crawler, rate_limiter, visited, l, depth + 1, budget, max_depth, max_budget) for l in valid_links]
            if tasks:
                sub_results = await asyncio.gather(*tasks, return_exceptions=True)
                for sr in sub_results:
                    if isinstance(sr, dict) and sr:
                        result["sub_pages"].append(sr)
        return result
