# -----------------------------------------------
# Blend Engine — by Markanm Team
# https://markanm.com
# -----------------------------------------------
# SPDX-License-Identifier: Apache-2.0
"""Youtube (Videos)"""

import os
import subprocess
import json
from urllib.parse import quote_plus

# about
about = {
    "website": 'https://www.youtube.com/',
    "wikidata_id": 'Q866',
    "official_api_documentation": 'https://developers.blend.com/youtube/v3/docs/search/list?apix=true',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

# engine dependent config
categories = ['videos', 'music']
paging = True
language_support = False
time_range_support = True

base_youtube_url = 'https://www.youtube.com/watch?v='

# do search-request
def request(query, params):
    params['yt_dlp_query'] = query
    params['url'] = 'https://www.youtube.com/robots.txt' # Dummy URL to satisfy SearXNG async network fetcher
    params['method'] = 'GET'
    return params

# get response from search-request
def response(resp):
    query = resp.search_params.get('yt_dlp_query', '')
    if not query:
        return []
        
    cmd = ["yt-dlp", f"ytsearch30:{query}", "--dump-json", "--flat-playlist"]
    results = []
    
    try:
        # 8-second explicit timeout to prevent hanging, as requested by user.
        # SearXNG uses ThreadPoolExecutor for response parsing, so subprocess.run is safe.
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
        lines = proc.stdout.strip().split('\n')
        for line in lines:
            if not line: continue
            try:
                data = json.loads(line)
                videoid = data.get('id')
                if not videoid: continue
                
                # Format duration cleanly (e.g. 195 -> 3:15)
                duration_sec = int(data.get('duration') or 0)
                if duration_sec > 0:
                    mins, secs = divmod(duration_sec, 60)
                    hours, mins = divmod(mins, 60)
                    if hours > 0:
                        length_str = f"{hours}:{mins:02d}:{secs:02d}"
                    else:
                        length_str = f"{mins}:{secs:02d}"
                else:
                    length_str = ""
                    
                results.append(
                    {
                        'url': base_youtube_url + videoid,
                        'title': data.get('title', ''),
                        'content': data.get('description', '-') or '-',
                        'author': data.get('uploader', ''),
                        'length': length_str,
                        'template': 'videos.html',
                        'iframe_src': 'https://www.youtube-nocookie.com/embed/' + videoid,
                        'thumbnail': f'https://i.ytimg.com/vi/{videoid}/hqdefault.jpg',
                    }
                )
            except Exception:
                pass
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, Exception):
        # Graceful degradation if yt-dlp blocks/fails: return whatever we got or empty list
        pass
        
    return results
