import asyncio
from typing import Dict, Any

class Crawl4AIWrapper:
    """
    Wrapper for Crawl4AI (AsyncWebCrawler) to perform intelligent extraction.
    Converts complex web pages into clean markdown and structured data.
    """
    def __init__(self):
        # We instantiate the crawler lazily to avoid heavy overhead on boot
        self.crawler = None
        self.proxy = None

    async def _init_crawler(self):
        try:
            from crawl4ai import AsyncWebCrawler
            if not self.proxy:
                from ..utils.egress_proxy import SecureEgressProxy
                self.proxy = SecureEgressProxy(host='127.0.0.1', port=8888)
                await self.proxy.start()
                
            if not self.crawler:
                self.crawler = AsyncWebCrawler(proxy="http://127.0.0.1:8888", verbose=False)
                await self.crawler.start()
        except ImportError:
            print("Crawl4AI not installed. Fallback to basic extraction.")
            self.crawler = None

    async def extract(self, url: str) -> Dict[str, Any]:
        """
        Extract clean markdown from a URL.
        """
        await self._init_crawler()
        if not self.crawler:
            return {"markdown": "", "success": False, "url": url}

        try:
            # crawl4ai async crawl with timeout
            # If arun does not natively support timeout, we wrap it in asyncio.wait_for
            from ..utils.retry import async_retry
            
            async def _run_crawl():
                return await asyncio.wait_for(self.crawler.arun(url=url), timeout=15.0)
                
            result = await async_retry(_run_crawl, retries=2, base_delay=1.0)
            
            return {
                "markdown": result.markdown,
                "success": result.success,
                "url": url,
                "media": result.media,
                "links": result.links
            }
        except asyncio.TimeoutError:
            return {"markdown": "", "success": False, "url": url, "error": "Timeout"}
        except Exception as e:
            from ..utils.logger import get_logger
            logger = get_logger("crawl4ai")
            logger.error(f"Crawl failed for {url}: {e}")
            return {"markdown": "", "success": False, "url": url, "error": str(e)}

    async def close(self):
        if self.crawler:
            await self.crawler.close()
