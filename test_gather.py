import asyncio
from backend.providers.google_provider import GoogleProvider

async def test():
    p = GoogleProvider()
    try:
        res = await p.search("python")
        print(len(res))
    except Exception as e:
        print("EXCEPTION:", repr(e))

asyncio.run(test())
