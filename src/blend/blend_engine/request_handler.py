import asyncio
import aiohttp
import random
from typing import List, Dict

class SearchRequestHandler:
    """
    Core unified request handler for Blend.
    Handles parallel execution of search modes with heavy anti-fingerprinting.
    """
    
    def __init__(self):
        # We'll expand this with more sophisticated anti-fingerprinting in Phase 3
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0"
        ]

    def _get_random_headers(self) -> Dict[str, str]:
        """Generate highly randomized, non-fingerprintable headers."""
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1"
        }

    async def fetch(self, url: str, session: aiohttp.ClientSession, use_tor: bool = False) -> str:
        """
        Fetch a URL asynchronously. 
        Integrates Tor proxy for Ghost and Deep modes.
        """
        headers = self._get_random_headers()
        
        proxy = None 
        if use_tor:
            from privacy.tor_manager import TorManager
            tor = TorManager()
            proxy = tor.get_proxy_url()

        try:
            from blend.utils.security import is_safe_url
            is_safe, resolved_ip = is_safe_url(url, resolve_dns=not use_tor)
            if not is_safe:
                return ""
                
            # Need aiohttp_socks for socks5 proxy support in aiohttp
            if proxy:
                from aiohttp_socks import ProxyConnector
                # rdns=True ensures DNS resolution happens remotely via Tor, preventing leaks
                connector = ProxyConnector.from_url(proxy, rdns=True)
                async with aiohttp.ClientSession(connector=connector) as tor_session:
                    async with tor_session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as response:
                        if response.status == 200:
                            return await response.text()
                        return ""
            else:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        return await response.text()
                    return ""
        except Exception:
            return ""

    async def execute_parallel_requests(self, urls: List[str], use_tor: bool = False) -> List[str]:
        """Execute multiple requests in parallel (Fast Mode default behavior)."""
        async with aiohttp.ClientSession(
            cookie_jar=aiohttp.DummyCookieJar() # Never store cookies
        ) as session:
            tasks = [self.fetch(url, session, use_tor) for url in urls]
            return await asyncio.gather(*tasks)
