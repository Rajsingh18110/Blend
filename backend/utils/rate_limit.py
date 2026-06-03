import asyncio
from contextlib import asynccontextmanager

class RateLimiter:
    """Domain-based async rate limiter and global Chromium concurrency guard."""
    _instance = None
    
    def __new__(cls, max_global=10, max_per_domain=3):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance.max_global = max_global
            cls._instance.max_per_domain = max_per_domain
            cls._instance._semaphores = {}
            cls._instance._global_sem = asyncio.Semaphore(max_global)
            cls._instance._lock = asyncio.Lock()
        return cls._instance

    @asynccontextmanager
    async def acquire(self, domain: str):
        async with self._lock:
            if domain not in self._semaphores:
                self._semaphores[domain] = asyncio.Semaphore(self.max_per_domain)
            domain_sem = self._semaphores[domain]
            
        async with self._global_sem:
            async with domain_sem:
                yield
