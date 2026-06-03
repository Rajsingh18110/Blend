import re

files_to_instrument = {
    "backend/app.py": [
        (r'async def api_search\(\):', r'async def api_search():\n    print("TRACE_EXECUTE: backend/app.py - api_search", flush=True)')
    ],
    "backend/blend_engine/search_router.py": [
        (r'def __init__\(self\):', r'def __init__(self):\n        print("TRACE_INSTANTIATE: backend/blend_engine/search_router.py - __init__", flush=True)'),
        (r'async def route\(self, .*?\):', r'\g<0>\n        print("TRACE_EXECUTE: backend/blend_engine/search_router.py - route", flush=True)')
    ],
    "backend/blend_engine/ranking_engine.py": [
        (r'def __init__\(self\):', r'def __init__(self):\n        print("TRACE_INSTANTIATE: backend/blend_engine/ranking_engine.py - __init__", flush=True)'),
        (r'def rank_results\(self, .*?\):', r'\g<0>\n        print("TRACE_EXECUTE: backend/blend_engine/ranking_engine.py - rank_results", flush=True)')
    ],
    "backend/blend_engine/ranking.py": [
        (r'def __init__\(self\):', r'def __init__(self):\n        print("TRACE_INSTANTIATE: backend/blend_engine/ranking.py - __init__", flush=True)'),
        (r'def rank_results\(self, .*?\):', r'\g<0>\n        print("TRACE_EXECUTE: backend/blend_engine/ranking.py - rank_results", flush=True)')
    ],
    "backend/modes/fast.py": [
        (r'def __init__\(self\):', r'def __init__(self):\n        print("TRACE_INSTANTIATE: backend/modes/fast.py - __init__", flush=True)'),
        (r'async def search\(self, .*?\):', r'\g<0>\n        print("TRACE_EXECUTE: backend/modes/fast.py - search", flush=True)')
    ],
    "backend/blend_engine/provider_manager.py": [
        (r'def __init__\(self\):', r'def __init__(self):\n        print("TRACE_INSTANTIATE: backend/blend_engine/provider_manager.py - __init__", flush=True)'),
        (r'def get_providers\(self, .*?\):', r'\g<0>\n        print("TRACE_EXECUTE: backend/blend_engine/provider_manager.py - get_providers", flush=True)')
    ]
}

for fpath, replacements in files_to_instrument.items():
    with open(fpath, "r") as f:
        content = f.read()
    
    # Do replacements
    for pattern, replace in replacements:
        content = re.sub(pattern, replace, content)
        
    # Append import trace at bottom
    if "TRACE_IMPORT" not in content:
        content += f"\nimport sys\nprint('TRACE_IMPORT: {fpath}', flush=True)\n"
        
    with open(fpath, "w") as f:
        f.write(content)
