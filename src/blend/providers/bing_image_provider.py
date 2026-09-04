from .base_provider import BaseProvider
from typing import Dict, Any, List
import urllib.parse
import re
import json
import html as htmllib
import aiohttp

BLOCKED_HOSTS = [
    'xxx', 'porn', 'nude', 'sex', 'adult', 'nsfw', 'hentai', 'erotic',
    'xvideos', 'xhamster', 'pornhub', 'redtube', 'youporn', 'spankbang',
    'onlyfans', 'brazzers', 'bangbros'
]

class BingImageProvider(BaseProvider):
    def __init__(self):
        self.base_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'text/html, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',  # No brotli
            'X-Requested-With': 'XMLHttpRequest',
        }

    def _is_safe(self, url: str) -> bool:
        url_lower = url.lower()
        return not any(b in url_lower for b in BLOCKED_HOSTS)

    async def search(self, query: str, use_tor: bool = False, page: int = 1, language: str = "all") -> List[Dict[str, Any]]:
        encoded_query = urllib.parse.quote(query)
        first = (page - 1) * 35
        
        # Use Bing's async endpoint — this is what the browser actually fetches
        url = (
            f"https://www.bing.com/images/async"
            f"?q={encoded_query}&first={first}&count=40"
            f"&safeSearch=Strict&mkt=en-US&adlt=Strict"
        )
        
        headers = dict(self.base_headers)
        headers['Referer'] = f'https://www.bing.com/images/search?q={encoded_query}'

        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    html = await resp.text(errors='replace')
        except Exception:
            return []

        results = []
        
        # Parse the m= JSON attributes — each has murl (original), turl (thumb), t (title)
        for raw in re.findall(r' m="(\{[^"]+\})"', html):
            try:
                d = json.loads(htmllib.unescape(raw))
            except Exception:
                continue
            
            img_url = d.get('murl', '')
            thumb = d.get('turl', img_url)
            title = d.get('t', '') or d.get('desc', '') or 'Image'
            
            if not img_url or not img_url.startswith('http'):
                continue
            if not self._is_safe(img_url):
                continue
            
            results.append({
                'url': img_url,
                'title': title,
                'content': '',
                'img_src': img_url,
                'thumbnail': thumb,
                'source': 'Bing Images',
            })

            if len(results) >= 40:
                break

        return results

    def normalize(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def score(self, result: Dict[str, Any]) -> float:
        return 1.0

    def extract_metadata(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return {}
