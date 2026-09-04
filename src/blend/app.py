#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Raj Singh / Markanm Team

# -----------------------------------------------
# Blend Engine — by Markanm Team
# https://markanm.com
# -----------------------------------------------
"""Frontend-first launcher for the standalone Blend Search app."""

from __future__ import annotations

import os
import threading
import urllib.parse
import urllib.request
import json
from datetime import date
from pathlib import Path

from flask import Response, jsonify, redirect, render_template_string, request, send_from_directory

os.environ.setdefault("BLEND_EMBEDDED_BACKEND", "1")

from blend.server import app, run
from blend.navar import build_ai_response
from blend.navar_identity import NAVAR_IDENTITY

ROOT_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT_DIR
TEMPLATES_DIR = FRONTEND_DIR / "templates"
STATIC_DIR = FRONTEND_DIR / "static"
MARKANM_URL = "https://markanm.com"

app.config["MAX_CONTENT_LENGTH"] = int(os.environ.get("BLEND_MAX_CONTENT_LENGTH", 1024 * 1024))
SEARCH_STATS = {"total_searches": 0, "today": {}, "top_queries": {}, "engines": {}}


def render_frontend(template_name: str, **context):
    template_path = TEMPLATES_DIR / template_name
    return render_template_string(
        template_path.read_text(encoding="utf-8"),
        markanm_url=MARKANM_URL,
        navar_identity=NAVAR_IDENTITY,
        **context,
    )



@app.before_request
def override_browser_routes():
    """Keep browser traffic on the new frontend and reserve `/search` for JSON only."""
    if request.method == "OPTIONS":
        return None


    if request.path == "/autocompleter":
        return autocomplete_response()

    if request.path in {"/blend-home", "/newtab"}:
        return redirect("/", code=302)

    if request.path == "/search" and request.args.get("format") != "json":
        query = (request.args.get("q") or request.form.get("q") or "").strip()
        if query:
            return redirect(f"/results.html?q={query}", code=302)
        return redirect("/", code=302)
    
    # Intercept Blend Engine native routes and serve our custom frontend UI instead
    if request.path in {"/", "/index.html"}:
        return render_frontend("index.html")
    if request.path in {"/about", "/about.html"}:
        return render_frontend("about.html")
    if request.path in {"/preferences", "/settings.html"}:
        return render_frontend("settings.html")
    if request.path == "/privacy.html":
        return render_frontend("privacy.html")
    if request.path == "/results.html":
        return render_frontend("results.html")
    if request.path == "/style.css":
        return send_from_directory(STATIC_DIR, "style.css")


@app.route("/")
@app.route("/index.html")
def frontend_index():
    return render_frontend("index.html")


@app.route("/results.html")
def frontend_results():
    return render_frontend("results.html")


@app.route("/about.html")
def frontend_about():
    return render_frontend("about.html")


@app.route("/privacy.html")
def frontend_privacy():
    return render_frontend("privacy.html")


@app.route("/settings.html")
@app.route("/preferences")
def frontend_settings():
    return render_frontend("settings.html")


@app.route("/style.css")
def frontend_style():
    return send_from_directory(STATIC_DIR, "style.css")

@app.route("/robots.txt")
def robots_txt():
    content = "User-agent: *\nAllow: /\nSitemap: https://blend-engine.onrender.com/sitemap.xml"
    return Response(content, mimetype="text/plain")

@app.route("/sitemap.xml")
def sitemap_xml():
    content = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://blend-engine.onrender.com/</loc><priority>1.0</priority></url>
  <url><loc>https://blend-engine.onrender.com/about.html</loc><priority>0.8</priority></url>
  <url><loc>https://blend-engine.onrender.com/privacy.html</loc><priority>0.8</priority></url>
  <url><loc>https://blend-engine.onrender.com/settings.html</loc><priority>0.5</priority></url>
</urlset>'''
    return Response(content, mimetype="application/xml")


@app.route("/blend-config.js")
def frontend_config():
    return send_from_directory(TEMPLATES_DIR, "blend-config.js")


@app.route("/search.html", methods=["GET", "POST"])
def frontend_search_alias():
    query = (request.args.get("q") or request.form.get("q") or "").strip()
    if query:
        return redirect(f"/results.html?q={query}", code=302)
    return redirect("/", code=302)


@app.route("/suggestions")
def suggestions_alias():
    return redirect(f"/autocompleter?q={request.args.get('q', '')}", code=307)


def autocomplete_response():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([q, []])
    try:
        url = f"https://duckduckgo.com/ac/?q={urllib.parse.quote(q)}&type=list"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        
        handlers = []
        if request.headers.get("X-Blend-Tor") == "1":
            try:
                import socks, socket
                socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 9050)
                socket.socket = socks.socksocket
            except ImportError:
                pass

        data = urllib.request.urlopen(req, timeout=3).read()
        return app.response_class(data, mimetype="application/json")
    except Exception:
        suggestions = [
            f"{q} tutorial",
            f"{q} explained",
            f"{q} github",
            f"{q} documentation",
            f"{q} 2026",
            f"{q} site:reddit.com",
        ]
        return jsonify([q, suggestions])


@app.route("/ping")
def ping():
    return jsonify({
        "status": "ok",
        "service": "Blend Search",
        "brand": "MarkanM",
        "version": "2.0.0",
    })


import time

SEARCH_CACHE = {}
CACHE_TTL = 300 # 5 minutes

@app.route("/api/search")
async def api_search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "empty query"}), 400

    # Cache mechanism to prevent duplicate requests and improve performance
    cache_key = request.url
    if cache_key in SEARCH_CACHE:
        cached_time, cached_payload = SEARCH_CACHE[cache_key]
        if time.time() - cached_time < CACHE_TTL:
            return jsonify(cached_payload), 200

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
    language = request.args.get("language", "all")

    try:
        if category == "news":
            payload = _google_news_rss(q)
            SEARCH_CACHE[cache_key] = (time.time(), payload)
            return jsonify(payload), 200

        from blend.blend_engine.search_router import SearchRouter
        router = SearchRouter()
        use_tor = request.headers.get("X-Blend-Tor") == "1"
        pageno = int(request.args.get("pageno") or 1)
        payload = await router.route(q, category=category, mode=blend_mode, engines=engines_to_force, use_tor=use_tor, language=language, pageno=pageno)
        
        if payload.get("number_of_results", 0) > 0:
            SEARCH_CACHE[cache_key] = (time.time(), payload)
        return jsonify(payload), 200
    except Exception as e:
        import logging
        logging.getLogger("app.api_search").error(f"Blend Engine failed: {e}", exc_info=True)
        fallback = _fallback_web_search(q, category, int(request.args.get("pageno") or 1))
        if fallback.get("number_of_results", 0) > 0:
            SEARCH_CACHE[cache_key] = (time.time(), fallback)
        return jsonify(fallback), 200

def _google_news_rss(q: str):
    import urllib.request
    import urllib.parse
    import xml.etree.ElementTree as ET
    import email.utils

    try:
        if q.lower() == "top news":
            url = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
        else:
            url = f"https://news.google.com/rss/search?q={urllib.parse.quote(q)}&hl=en-US&gl=US&ceid=US:en"
            
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        html = urllib.request.urlopen(req, timeout=10).read()
        root = ET.fromstring(html)
        
        results = []
        for item in root.findall(".//item"):
            title = item.findtext("title")
            link = item.findtext("link")
            pub_date = item.findtext("pubDate")
            source = item.findtext("source")
            
            try:
                dt = email.utils.parsedate_to_datetime(pub_date)
                published = dt.strftime("%b %d, %Y")
            except Exception:
                published = pub_date

            results.append({
                "title": title,
                "url": link,
                "content": title,
                "source": source or "Google News",
                "publishedDate": published,
                "parsed_url": ["https", urllib.parse.urlparse(link).netloc, "", "", "", ""]
            })
            
        payload = _empty_search_payload(q)
        payload["results"] = results
        payload["number_of_results"] = len(results)
        return payload
    except Exception as e:
        import logging
        logging.getLogger("app.news").error(f"News RSS failed: {e}", exc_info=True)
        return _empty_search_payload(q)

def _fallback_web_search(q: str, category: str = "general", pageno: int = 1):
    """Small backend fallback so the custom frontend never depends on static data."""
    if category not in {"general", "web", "all"}:
        return _empty_search_payload(q)

    try:
        from bs4 import BeautifulSoup
    except Exception:
        BeautifulSoup = None

    if BeautifulSoup is None:
        return _empty_search_payload(q)

    try:
        start = max(0, pageno - 1) * 30
        url = "https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": q, "s": start})
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "text/html,application/xhtml+xml",
            },
        )
        
        if request.headers.get("X-Blend-Tor") == "1":
            try:
                import socks, socket
                socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 9050)
                socket.socket = socks.socksocket
            except ImportError:
                pass

        html = urllib.request.urlopen(req, timeout=8).read()
        soup = BeautifulSoup(html, "html.parser")
        results = []
        for item in soup.select(".result"):
            link = item.select_one(".result__a")
            if not link:
                continue
            href = _unwrap_ddg_url(link.get("href", ""))
            title = link.get_text(" ", strip=True)
            snippet_el = item.select_one(".result__snippet")
            snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""
            domain = urllib.parse.urlparse(href).netloc
            if href and title:
                results.append(
                    {
                        "url": href,
                        "title": title,
                        "content": snippet,
                        "engine": "duckduckgo_fallback",
                        "parsed_url": ["https", domain, "", "", "", ""],
                    }
                )
        payload = _empty_search_payload(q)
        payload["results"] = _boost_results_by_query(q, results[:20])
        payload["number_of_results"] = len(payload["results"])
        return payload
    except Exception:
        return _empty_search_payload(q)


def _unwrap_ddg_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.path.startswith("/l/"):
        query = urllib.parse.parse_qs(parsed.query)
        uddg = query.get("uddg", [""])[0]
        if uddg:
            return urllib.parse.unquote(uddg)
    return urllib.parse.urljoin("https://duckduckgo.com", url)


def _empty_search_payload(q: str):
    return {
        "query": q,
        "number_of_results": 0,
        "results": [],
        "answers": [],
        "corrections": [],
        "infoboxes": [],
        "suggestions": [],
        "unresponsive_engines": [],
    }


def _boost_results_by_query(q: str, results: list[dict]):
    if not results:
        return results

    # Smart Authority Detection
    AUTHORITY_DOMAINS = {
        "wikipedia.org": -30, "github.com": -25, "stackoverflow.com": -25,
        "reddit.com": -20, "quora.com": -15, "developer.mozilla.org": -20,
        "docs.microsoft.com": -20, "medium.com": -10, "youtube.com": -15,
        "news.ycombinator.com": -15, "readxhub.in": -15, "ncbi.nlm.nih.gov": -25,
        "w3schools.com": -10, "geeksforgeeks.org": -10
    }
    
    # Fake/Spam Domain Detection
    SPAM_KEYWORDS = ["download-free", "crack", "nulled", "cheap", "buy-now", "generator", "free-robux", "redirect", "clickbait"]
    
    # Trusted TLDs
    TRUSTED_TLDS = [".gov", ".edu", ".org", ".dev", ".io", ".in", ".co.uk", ".ac.uk"]
    
    query_words = set(w for w in q.lower().split() if len(w) > 2)
    base = "".join(ch for ch in q.lower().strip().split()[0] if ch.isalnum() or ch in ".-") if q.strip() else ""

    def score(item):
        idx, result = item
        # Consensus-based ranking baseline (upstream rank * 2)
        s = idx * 2  
        
        url = result.get("url", "").lower()
        title = result.get("title", "").lower()
        content = result.get("content", "").lower()
        
        try:
            host = urllib.parse.urlparse(url).netloc.removeprefix("www.")
        except Exception:
            host = ""
        
        # 1. Authority Boost
        for domain, boost in AUTHORITY_DOMAINS.items():
            if host == domain or host.endswith("." + domain):
                s += boost
                
        # 2. Trusted TLD Boost
        if any(host.endswith(tld) for tld in TRUSTED_TLDS):
            s -= 10
            
        # 3. Exact Domain Match (with content check to prevent empty domains winning)
        if base and (host == base or host.startswith(base + ".")) and len(content) > 30:
            s -= 15
            
        # 4. Spam / Low Quality Penalty
        if any(spam in url or spam in title for spam in SPAM_KEYWORDS):
            s += 100
        if len(content) < 20: # Empty/thin content penalty
            s += 50
            
        # 5. Search Relevance Matching
        match_count = sum(1 for w in query_words if w in title)
        s -= (match_count * 5)
        
        return s

    # Sort based on computed score
    scored_results = sorted(enumerate(results), key=score)
    return [r[1] for r in scored_results]


@app.route("/api/ai", methods=["POST"])
def api_ai():
    data = request.get_json(force=True, silent=True) or {}
    query = str(data.get("query") or data.get("message") or "").strip()[:500]
    if not query:
        return jsonify({"message": "Query cannot be empty"}), 400
    results = (data.get("results") or [])[:10]
    shortcuts = data.get("shortcuts") or []
    mode = data.get("mode") or "fast"
    current_tab = data.get("current_tab", "web")
    current_url = data.get("current_url", "")
    try:
        from flask import stream_with_context
        def generate():
            for event in build_ai_response(query, results, shortcuts, mode, current_tab=current_tab, current_url=current_url):
                yield f"data: {json.dumps(event)}\n\n"
        
        return Response(stream_with_context(generate()), mimetype='text/event-stream', headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        })
    except Exception as exc:
        return jsonify({"message": f"AI error: {exc}"}), 500



@app.after_request
def add_privacy_headers(response):
    allowed_origin = os.environ.get("BLEND_CORS_ORIGIN", "*")
    response.headers.setdefault("Access-Control-Allow-Origin", allowed_origin)
    response.headers.setdefault("Access-Control-Allow-Methods", "GET, POST, OPTIONS, DELETE")
    response.headers.setdefault("Access-Control-Allow-Headers", "Content-Type, Authorization")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Cache-Control", "no-cache, no-store, must-revalidate")
    return response




@app.route("/", defaults={"path": ""}, methods=["OPTIONS"])
@app.route("/<path:path>", methods=["OPTIONS"])
def app_options_handler(path=""):
    return "", 204


if __name__ == "__main__":
    port = os.environ.get("PORT", "8081")
    print(f"Blend Search Engine Starting on Port {port}...")
    print("Service is running")
    print("Navar AI Assistant is active and powered by Sarvam AI (if configured)")
    run()
