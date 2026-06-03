import re
import sys

files_to_instrument = {
    "backend/app.py": [
        (r'async def api_search\(\):', r'async def api_search():\n    print("TRACE_ENTER: backend/app.py - api_search", flush=True)')
    ],
    "backend/blend_engine/search_router.py": [
        (r'def __init__\(self\):', r'def __init__(self):\n        print("TRACE_INSTANTIATE: backend/blend_engine/search_router.py", flush=True)'),
        (r'async def route\(self, .*?\):', r'\g<0>\n        print("TRACE_ENTER: backend/blend_engine/search_router.py - route", flush=True)'),
        (r'return \{', r'print("TRACE_EXIT: backend/blend_engine/search_router.py - route", flush=True)\n        return {')
    ],
    "backend/blend_engine/provider_manager.py": [
        (r'def __init__\(self\):', r'def __init__(self):\n        print("TRACE_INSTANTIATE: backend/blend_engine/provider_manager.py", flush=True)'),
        (r'def get_providers\(self, .*?\):', r'\g<0>\n        print("TRACE_ENTER: backend/blend_engine/provider_manager.py - get_providers", flush=True)'),
        (r'return \[self\.providers\["google"\], self\.providers\["brave"\]\]', r'print("TRACE_EXIT: backend/blend_engine/provider_manager.py - get_providers", flush=True)\n        return [self.providers["google"], self.providers["brave"]]')
    ],
    "backend/providers/google_provider.py": [
        (r'def __init__\(self\):', r'def __init__(self):\n        print("TRACE_INSTANTIATE: backend/providers/google_provider.py", flush=True)'),
        (r'async def search\(self, .*?\):', r'\g<0>\n        print("TRACE_ENTER: backend/providers/google_provider.py - search", flush=True)'),
        (r'return results', r'print(f"TRACE_EXIT: backend/providers/google_provider.py - search (returned {len(results)})", flush=True)\n        return results')
    ],
    "backend/providers/bing_provider.py": [
        (r'def __init__\(self\):', r'def __init__(self):\n        print("TRACE_INSTANTIATE: backend/providers/bing_provider.py", flush=True)'),
        (r'async def search\(self, .*?\):', r'\g<0>\n        print("TRACE_ENTER: backend/providers/bing_provider.py - search", flush=True)'),
        (r'return results', r'print(f"TRACE_EXIT: backend/providers/bing_provider.py - search (returned {len(results)})", flush=True)\n        return results')
    ],
    "backend/blend_engine/result_processor.py": [
        (r'def deduplicate\(self, results: .*?\):', r'\g<0>\n        print(f"TRACE_ENTER: backend/blend_engine/result_processor.py - deduplicate (input {len(results)})", flush=True)'),
        (r'return fused_clusters', r'print(f"TRACE_EXIT: backend/blend_engine/result_processor.py - deduplicate (output {len(fused_clusters)})", flush=True)\n        return fused_clusters')
    ],
    "backend/blend_engine/ranking_engine.py": [
        (r'def __init__\(self\):', r'def __init__(self):\n        print("TRACE_INSTANTIATE: backend/blend_engine/ranking_engine.py", flush=True)'),
        (r'def rank_results\(self, .*?\):', r'\g<0>\n        print(f"TRACE_ENTER: backend/blend_engine/ranking_engine.py - rank_results (input {len(results)})", flush=True)'),
        (r'return \[r\[1\] for r in scored_results\]', r'print(f"TRACE_EXIT: backend/blend_engine/ranking_engine.py - rank_results", flush=True)\n        return [r[1] for r in scored_results]')
    ]
}

for fpath, replacements in files_to_instrument.items():
    with open(fpath, "r") as f:
        content = f.read()
        
    for pattern, replace in replacements:
        content = re.sub(pattern, replace, content)
        
    if "TRACE_IMPORT" not in content:
        content += f"\nimport sys\nprint('TRACE_IMPORT: {fpath}', flush=True)\n"
        
    with open(fpath, "w") as f:
        f.write(content)
