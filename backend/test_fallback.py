from app import _fallback_web_search
import json
print(json.dumps(_fallback_web_search("github", "general", 1), indent=2))
