from typing import List, Any
from providers.google_provider import GoogleProvider
from providers.bing_provider import BingProvider
from providers.brave_provider import BraveProvider
from providers.crawl_provider import CrawlProvider
from providers.bing_image_provider import BingImageProvider
from providers.youtube_music_provider import YoutubeMusicProvider

class ProviderManager:
    def __init__(self):
        self.providers = {
            "google": GoogleProvider(),
            "bing": BingProvider(),
            "brave": BraveProvider(),
            "crawl": CrawlProvider(),
            "bing_images": BingImageProvider(),
            "youtube_music": YoutubeMusicProvider()
        }

    def get_providers(self, category: str, engines_to_force: str) -> List[Any]:
        if engines_to_force:
            engine_names = [e.strip() for e in engines_to_force.split(",")]
            selected = [self.providers[e] for e in engine_names if e in self.providers]
            if selected: return selected
            
        if category == "images":
            return [self.providers["bing_images"]]
        elif category in ("music", "videos"):
            return [self.providers["youtube_music"]]
        elif category == "news":
            return [self.providers["google"], self.providers["bing"]]
        else:
            return [self.providers["google"], self.providers["brave"]]
