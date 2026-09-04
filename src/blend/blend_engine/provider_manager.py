from typing import List, Any
from blend.providers.google_provider import GoogleProvider
from blend.providers.bing_provider import BingProvider
from blend.providers.brave_provider import BraveProvider
from blend.providers.crawl_provider import CrawlProvider
from blend.providers.bing_image_provider import BingImageProvider
from blend.providers.youtube_music_provider import YoutubeMusicProvider
from blend.providers.blend_core_provider import BlendCoreProvider

class ProviderManager:
    def __init__(self):
        self.providers = {
            "google": GoogleProvider(),
            "bing": BingProvider(),
            "brave": BraveProvider(),
            "crawl": CrawlProvider(),
            "bing_images": BingImageProvider(),
            "youtube_music": YoutubeMusicProvider(),
            "blend_core": BlendCoreProvider()
        }

    def get_providers(self, category: str, engines_to_force: str) -> List[Any]:
        if engines_to_force:
            engine_names = [e.strip() for e in engines_to_force.split(",")]
            selected = [self.providers[e] for e in engine_names if e in self.providers]
            if selected: return selected
            
        core_provider = self.providers["blend_core"]
        
        # Determine native engine count for the category
        from blend.blend_core import sources
        native_cat = category
        if category == "web": native_cat = "general"
        elif category == "maps": native_cat = "map"
        elif category == "social": native_cat = "social media"
        
        native_engine_count = 0
        try:
            for name, engine in sources.engines.items():
                if getattr(engine, 'disabled', False): continue
                if native_cat in getattr(engine, 'categories', []):
                    native_engine_count += 1
        except Exception:
            pass

        # Deep Fix for P0-9 / P0-0:
        # We must add fallback providers unconditionally because the native `blend_core` engines
        # (Google, DDG, Karmasearch, AOL) are currently returning 0 results due to 
        # CAPTCHAs, 403s, and 404s on the VPS. If we don't add these fallbacks, 
        # the entire search engine returns "No results".
        providers = [core_provider]
        
        if category == "images":
            providers.append(self.providers["bing_images"])
        elif category in ("music", "videos"):
            providers.append(self.providers["youtube_music"])
        elif category in ("news", "web", "files", "social", "maps", "general"):
            providers.extend([self.providers["google"], self.providers["bing"], self.providers["brave"]])
            
        return providers
