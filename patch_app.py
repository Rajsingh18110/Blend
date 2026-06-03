import sys

with open("backend/app.py", "r") as f:
    lines = f.readlines()

start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if line.startswith('@app.route("/api/search")'):
        start_idx = i
    if line.startswith('def _fallback_web_search'):
        end_idx = i
        break

if start_idx != -1 and end_idx != -1:
    new_func = """@app.route("/api/search")
async def api_search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "empty query"}), 400

    # Cache mechanism to prevent duplicate requests and improve performance
    cache_key = request.url
    if cache_key in SEARCH_CACHE:
        cached_time, cached_resp = SEARCH_CACHE[cache_key]
        if time.time() - cached_time < CACHE_TTL:
            return cached_resp

    # Memory Optimization: Aggressively purge cache to stay within Render 512MB limit
    if len(SEARCH_CACHE) > 100:
        now = time.time()
        keys_to_delete = [k for k, v in SEARCH_CACHE.items() if now - v[0] > CACHE_TTL]
        for k in keys_to_delete: del SEARCH_CACHE[k]
        if len(SEARCH_CACHE) > 150:
            SEARCH_CACHE.clear()

    today = date.today().isoformat()
    SEARCH_STATS["total_searches"] += 1
    SEARCH_STATS["today"][today] = SEARCH_STATS["today"].get(today, 0) + 1
    SEARCH_STATS["top_queries"][q] = SEARCH_STATS["top_queries"].get(q, 0) + 1
    category = request.args.get("categories", "general")
    SEARCH_STATS["engines"][category] = SEARCH_STATS["engines"].get(category, 0) + 1

    query_string = request.args.to_dict(flat=True)
    query_string["q"] = q
    query_string["format"] = "json"
    query_string["autoredirect"] = "0"
    
    blend_mode = request.args.get("mode", "fast")
    engines_to_force = request.args.get("engines", "")

    try:
        from blend_engine.search_router import SearchRouter
        router = SearchRouter()
        payload = await router.route(q, category=category, mode=blend_mode, engines=engines_to_force)
        
        final_resp = jsonify(payload), 200
        SEARCH_CACHE[cache_key] = (time.time(), final_resp)
        return final_resp
    except Exception as e:
        from utils.logger import get_logger
        get_logger("app.api_search").error(f"Blend Engine '{blend_mode}' failed: {e}. Falling back.")
        fallback = _fallback_web_search(q, category, int(request.args.get("pageno") or 1))
        final_resp = jsonify(fallback), 200
        SEARCH_CACHE[cache_key] = (time.time(), final_resp)
        return final_resp

"""
    lines[start_idx:end_idx] = [new_func]
    with open("backend/app.py", "w") as f:
        f.writelines(lines)
    print("Patched app.py successfully.")
else:
    print("Could not find bounds.")
