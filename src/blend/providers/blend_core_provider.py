import asyncio
import urllib.parse
from typing import Dict, Any, List
from .base_provider import BaseProvider

class BlendCoreProvider(BaseProvider):
    supports_category: bool = True

    def __init__(self):
        # We don't initialize here to avoid slow app startup / expensive global state.
        # blend_core is initialized globally in app.py
        pass

    async def search(self, query: str, category: str = "general", use_tor: bool = False, language: str = "all", pageno: int = 1, **kwargs) -> List[Dict[str, Any]]:
        from blend.blend_core import pipeline, sources
        from blend.blend_core.pipeline.models import BlendQuery, SourceRef
        from flask import Flask

        # Ensure correct language mapping
        lang_param = "en-US" if language == "all" else language
        
        # Native mapping: map external category requests to actual native categories
        # e.g., 'web' -> 'general', 'maps' -> 'map'
        native_cat = category
        if category == "web":
            native_cat = "general"
        elif category == "maps":
            native_cat = "map"

        engine_refs = []
        for name, engine in sources.engines.items():
            if getattr(engine, 'disabled', False): continue
            if native_cat in getattr(engine, 'categories', []):
                engine_refs.append(SourceRef(name, native_cat))

        if not engine_refs:
            print(f"[BlendCoreProvider] No native engines enabled for category '{native_cat}'")
            return []

        blend_query = BlendQuery(
            query=query,
            engineref_list=engine_refs,
            lang=lang_param,
            pageno=pageno,
        )

        loop = asyncio.get_running_loop()

        def _run_search():
            # Pipeline Search uses flask context
            app = Flask(__name__)
            with app.test_request_context():
                search_obj = pipeline.Search(blend_query)
                results_pool = search_obj.blend_search()
                return results_pool.get_ordered_results()

        # Run synchronously blocking code in a thread pool so it doesn't block FastAPI's async event loop
        try:
            native_results = await loop.run_in_executor(None, _run_search)
        except Exception as e:
            print(f"[BlendCoreProvider] pipeline execution failed: {e}")
            raise e

        # Convert to dicts
        normalized_results = []
        for r in native_results:
            d = r.as_dict() if hasattr(r, 'as_dict') else r.__dict__
            d['engine'] = d.get('engine', 'blend_core')
            normalized_results.append(d)

        return normalized_results

    def normalize(self, result: Dict[str, Any]) -> Dict[str, Any]:
        # Result is already a dict from blend_core. Extract canonical fields.
        url = result.get("url", "")
        domain = ""
        try:
            domain = urllib.parse.urlparse(url).netloc
        except Exception:
            pass
            
        normalized = {
            "title": result.get("title", ""),
            "url": url,
            "content": result.get("content", ""),
            "engine": result.get("engine", "blend_core"),
            "parsed_url": ["https", domain, "", "", "", ""]
        }
        
        # Pull in image schemas properly
        if "thumbnail_src" in result:
            normalized["thumbnail_src"] = result["thumbnail_src"]
        elif "thumbnail" in result:
             normalized["thumbnail_src"] = result["thumbnail"]
             
        if "img_src" in result:
            normalized["img_src"] = result["img_src"]
        elif "image" in result:
            normalized["img_src"] = result["image"]

        if "source" in result:
            normalized["source"] = result["source"]
            
        return normalized

    def score(self, result: Dict[str, Any]) -> float:
        return 0.8

    def extract_metadata(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "engines": result.get("engines", [result.get("engine")])
        }
