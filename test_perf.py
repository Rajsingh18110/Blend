import asyncio
import time
from backend.providers.searxng_provider import SearxngProvider
from backend.providers.google_provider import GoogleProvider

async def main():
    sx = SearxngProvider()
    gp = GoogleProvider()
    
    t0 = time.time()
    await sx.search("github")
    print(f"SearxngProvider: {time.time() - t0:.2f}s")
    
    t0 = time.time()
    await gp.search("github")
    print(f"GoogleProvider: {time.time() - t0:.2f}s")

asyncio.run(main())
