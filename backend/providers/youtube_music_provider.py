from .base_provider import BaseProvider
from typing import Dict, Any, List
import urllib.parse
import json
import aiohttp
import asyncio


class YoutubeMusicProvider(BaseProvider):
    """
    Fetches videos from YouTube search by running 3 parallel queries:
    - exact query
    - query + 'tutorial'
    - query + 'video'
    This reliably gives 20+ unique results per search.
    """

    HEADERS = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/124.0.0.0 Safari/537.36'
        ),
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
    }

    async def _fetch_yt(self, session: aiohttp.ClientSession, query: str) -> List[Dict[str, Any]]:
        """Fetch one YouTube search results page and extract video data."""
        encoded = urllib.parse.quote(query)
        url = f'https://www.youtube.com/results?search_query={encoded}'
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=12)) as r:
                html = await r.text(errors='replace')
        except Exception:
            return []

        # Extract ytInitialData JSON blob
        start_str = 'ytInitialData = '
        end_str = ';</script>'
        si = html.find(start_str)
        if si == -1:
            return []
        si += len(start_str)
        ei = html.find(end_str, si)
        if ei == -1:
            return []

        try:
            data = json.loads(html[si:ei])
        except Exception:
            return []

        sections = (
            data.get('contents', {})
                .get('twoColumnSearchResultsRenderer', {})
                .get('primaryContents', {})
                .get('sectionListRenderer', {})
                .get('contents', [])
        )

        results = []
        for section in sections:
            for item in section.get('itemSectionRenderer', {}).get('contents', []):
                video = item.get('videoRenderer')
                if not video:
                    continue
                videoid = video.get('videoId')
                if not videoid:
                    continue

                title = ''.join(
                    r.get('text', '')
                    for r in video.get('title', {}).get('runs', [])
                )
                author = ''.join(
                    r.get('text', '')
                    for r in video.get('ownerText', {}).get('runs', [])
                )
                # Duration string e.g. "12:34"
                duration = (
                    video.get('lengthText', {}).get('simpleText', '')
                    or video.get('lengthText', {}).get('accessibility', {})
                              .get('accessibilityData', {}).get('label', '')
                )

                results.append({
                    'url': f'https://www.youtube.com/watch?v={videoid}',
                    'title': title,
                    'author': author,
                    'thumbnail': f'https://i.ytimg.com/vi/{videoid}/hqdefault.jpg',
                    'duration': duration,
                    'id': videoid,
                    'source': 'YouTube',
                    'content': '',  # Required so deduplication doesn't crash
                })

        return results

    async def search(self, query: str, use_tor: bool = False, language: str = "all", pageno: int = 1) -> List[Dict[str, Any]]:
        # Run 3 variant queries in parallel to get 20+ unique results
        variant_queries = [
            query,
            query + ' tutorial',
            query + ' video',
        ]

        async with aiohttp.ClientSession(headers=self.HEADERS) as session:
            all_lists = await asyncio.gather(
                *[self._fetch_yt(session, q) for q in variant_queries],
                return_exceptions=True,
            )

        # Merge and deduplicate by videoId
        seen_ids: set = set()
        merged: List[Dict[str, Any]] = []
        for result_list in all_lists:
            if isinstance(result_list, Exception):
                continue
            for r in result_list:
                vid = r.get('id', '')
                if vid and vid not in seen_ids:
                    seen_ids.add(vid)
                    merged.append(r)

        return merged  # Up to ~30-36 results

    def normalize(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def score(self, result: Dict[str, Any]) -> float:
        return 1.0

    def extract_metadata(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return {}
