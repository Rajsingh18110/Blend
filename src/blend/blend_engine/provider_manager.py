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
        
        # P0-4: Do NOT keep custom providers by default.
        # Fallback providers are only added if native coverage is insufficient or notoriously unstable.
        if category == "images":
            return [core_provider, self.providers["bing_images"]]
        elif category in ("music", "videos"):
            return [core_provider, self.providers["youtube_music"]]
        elif category == "news":
            return [core_provider, self.providers["google"], self.providers["bing"]]
        else:
            return [core_provider, self.providers["google"]]
