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

        # P0-4 & P0-9: Do NOT keep custom providers unconditionally.
        # Fallback providers are only added if native coverage is insufficient (e.g., < 2 engines).
        providers = [core_provider]
        
        if category == "images" and native_engine_count < 2:
            providers.append(self.providers["bing_images"])
        elif category in ("music", "videos") and native_engine_count < 2:
            providers.append(self.providers["youtube_music"])
        elif category == "news" and native_engine_count < 2:
            providers.extend([self.providers["google"], self.providers["bing"]])
        elif category == "web" and native_engine_count < 2:
            providers.append(self.providers["google"])
            
        return providers
