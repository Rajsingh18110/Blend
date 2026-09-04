from typing import List, Dict, Any
from ..blend_engine.request_handler import SearchRequestHandler
from ..blend_engine.result_processor import ResultProcessor
from ..blend_engine.ranking import RankingEngine
from .fast import FastMode
from ..scrapers.crawl4ai_wrapper import Crawl4AIWrapper
import asyncio

class DeepMode:
    """
    Deep Search Mode for Blend Engine.
    Uses FastMode for initial discovery, then uses Crawl4AI / Scrapy
    to dig 2-3 levels deep on the top results, returning rich markdown content.
    """
    
    def __init__(self, max_depth: int = 2, max_budget: int = 5):
        self.fast_mode = FastMode()
        self.crawler = Crawl4AIWrapper()
        self.max_depth = max_depth
        self.max_budget = max_budget
        self.visited = set()
        
    async def _crawl_recursive(self, url: str, depth: int, budget: dict) -> Dict[str, Any]:
        from ..utils.security import is_safe_url
        if depth > self.max_depth or budget['count'] >= self.max_budget:
            return None
            
        is_safe, resolved_ip = is_safe_url(url)
        if url in self.visited or not is_safe:
            return None
            
        self.visited.add(url)
        budget['count'] += 1
        
        import urllib.parse
        from ..utils.rate_limit import RateLimiter
        domain = urllib.parse.urlparse(url).netloc
        rate_limiter = RateLimiter()
        
        async with rate_limiter.acquire(domain):
            data = await self.crawler.extract(url)
            
        if not data.get("success"):
            return None
            
        result = {
            "url": url,
            "markdown": data.get("markdown", ""),
            "sub_pages": []
        }
        
        # If we have depth left, crawl links from the same domain
        if depth < self.max_depth:
            links = data.get("links", {}).get("internal", [])
            valid_links = [l['href'] for l in links if l.get('href') and l['href'] not in self.visited][:3]
            
            tasks = [self._crawl_recursive(l, depth + 1, budget) for l in valid_links]
            if tasks:
                sub_results = await asyncio.gather(*tasks, return_exceptions=True)
                for sr in sub_results:
                    if isinstance(sr, dict) and sr:
                        result["sub_pages"].append(sr)
                        
        return result
        
    async def search(self, query: str) -> Dict[str, Any]:
        """Execute deep search."""
        self.visited.clear()
        
        # Step 1: Get initial Fast results
        fast_results = await self.fast_mode.search(query)
        results = fast_results.get("results", [])
        
        # Step 2: Deep crawl the top 3 results
        top_results = results[:3]
        
        budget = {'count': 0}
        crawl_tasks = [
            self._crawl_recursive(res['url'], depth=1, budget=budget)
            for res in top_results
        ]
        
        crawled_data = await asyncio.gather(*crawl_tasks, return_exceptions=True)
        
        # Merge crawled data into results
        for idx, data in enumerate(crawled_data):
            if isinstance(data, dict):
                top_results[idx]["deep_content"] = data.get("markdown", "")
                top_results[idx]["sub_pages"] = data.get("sub_pages", [])
                
        # Cleanup
        await self.crawler.close()
        
        return {
            "query": query,
            "number_of_results": len(results),
            "results": results,
            "answers": [],
            "suggestions": [],
            "mode": "deep"
        }
