from typing import Dict, Any
from ..blend_engine.request_handler import SearchRequestHandler
import urllib.parse
from bs4 import BeautifulSoup
import re

class GhostMode:
    """
    Ghost Mode for Blend Engine (Privacy Monster).
    Acts as a true proxy: Fetches the page through Tor + anti-fingerprinting.
    Strips tracking scripts, cookies, analytics.
    """
    
    def __init__(self):
        self.handler = SearchRequestHandler()
        
    def _strip_trackers(self, html: str) -> str:
        """Strip analytics, ads, and tracking scripts from HTML."""
        if not html:
            return ""
            
        try:
            soup = BeautifulSoup(html, "html.parser")
            
            # Remove all script tags (most aggressive privacy, might break some sites)
            # In a more advanced version, we could filter by src (google-analytics, etc.)
            for script in soup.find_all("script"):
                script.decompose()
                
            # Remove tracking pixels (1x1 images)
            for img in soup.find_all("img"):
                if img.get("width") == "1" or img.get("height") == "1":
                    img.decompose()
                    
            # Remove iframes (ads, trackers)
            for iframe in soup.find_all("iframe"):
                iframe.decompose()
                
            return str(soup)
        except Exception:
            return html

    async def proxy_url(self, url: str) -> Dict[str, Any]:
        """
        Fetch a URL securely through Tor and clean it.
        """
        if not url.startswith("http"):
            url = "https://" + url
            
        from ..utils.security import is_safe_url, sanitize_html
        
        is_safe, _ = is_safe_url(url, resolve_dns=False)
        if not is_safe:
            return {
                "url": url,
                "success": False,
                "content": "<p>Security Error: URL is unsafe, blocked, or invalid.</p>",
                "mode": "ghost"
            }
            
        # 1. Fetch through Tor
        # Using a dummy session here since fetch handles tor session creation if use_tor=True
        import aiohttp
        async with aiohttp.ClientSession() as session:
            html = await self.handler.fetch(url, session, use_tor=True)
            
        # 2. Strip trackers and malicious code
        clean_html = sanitize_html(html)
        
        return {
            "url": url,
            "success": bool(clean_html),
            "content": clean_html,
            "mode": "ghost"
        }
