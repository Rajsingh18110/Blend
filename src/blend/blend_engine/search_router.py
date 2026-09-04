
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

    async def route(self, query: str, category: str = "general", mode: str = "fast", engines: str = "", use_tor: bool = False, language: str = "all", pageno: int = 1) -> Dict[str, Any]:
        """Routes the search request to the appropriate providers."""
        providers = self.provider_manager.get_providers(category, engines)
        
        # Execute providers with a LATENCY BUDGET
        # fast=5.0s: DDGS/GoogleProvider consistently takes 3-5s; 2.5s was too tight
        # deep=8.0s: allow slower providers + Crawl4AI time
        budget = 5.0 if mode == "fast" else 8.0
        
        import time
        async def _time_provider(p, kwargs):
            start = time.perf_counter()
            try:
                # Give each provider slightly more than the router budget so they have a chance to return 
                # just before the router cuts them off.
                res = await asyncio.wait_for(p.search(**kwargs), timeout=budget + 0.5)
                elapsed = time.perf_counter() - start
                print(f"[SEARCH_ROUTER] Provider {p.__class__.__name__} completed in {elapsed:.3f}s with {len(res) if isinstance(res, list) else 'error'} results.")
                return p, res
            except Exception as e:
                elapsed = time.perf_counter() - start
                print(f"[SEARCH_ROUTER] Provider {p.__class__.__name__} FAILED in {elapsed:.3f}s: {e}")
                return p, e

        tasks = []
        for p in providers:
            kwargs = {
                "query": query,
                "use_tor": use_tor,
                "language": language,
                "pageno": pageno,
            }
            if getattr(p, "supports_category", False):
                kwargs["category"] = category
                    
            tasks.append(asyncio.create_task(_time_provider(p, kwargs)))
                
        # P0-5: Return partial results.
        done, pending = await asyncio.wait(tasks, timeout=budget)
        
        for task in pending:
            task.cancel() # Cancel slow providers that exceeded the budget
            
        all_results = []
        errors = []
        for task in done:
            try:
                p, res = task.result()
                if isinstance(res, list):
                    normalized = [p.normalize(r) for r in res]
                    all_results.extend(normalized)
                elif isinstance(res, Exception):
                    err_msg = str(res) or res.__class__.__name__
                    errors.append(f"{p.__class__.__name__}: {err_msg}")
            except Exception as e:
                errors.append(f"TaskError: {str(e)}")
                
        # P0-12: Deduplication. We just want to merge without losing results
        unique_results = self.result_processor.deduplicate(all_results)
        ranked_results = self.ranking_engine.rank_results(unique_results, query)
        
        if mode == "deep":
            crawler = None
            try:
                from blend.scrapers.crawl4ai_wrapper import Crawl4AIWrapper
                crawler = Crawl4AIWrapper()
                crawl_budget = {'count': 0}
                
                rate_limiter = None
                try:
                    from blend.utils.rate_limit import RateLimiter
                    rate_limiter = RateLimiter()
                except ImportError:
                    pass

                top_results = ranked_results[:3]
                async with self._deep_semaphore:
                    visited = set()
                    crawl_tasks = [
                        self._crawl_recursive(crawler, rate_limiter, visited, res.get('url', ''), depth=1, budget=crawl_budget)
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
        
        # P0-11: Result Count debugging output
        print(f"[DEBUG-COUNTS] category={category}, raw_providers={len(all_results)}, dedup={len(unique_results)}, ranked={len(ranked_results)}")
        
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
            from blend.utils.security import is_safe_url
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
