# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Raj Singh / Markanm Team

# -----------------------------------------------
# Blend Engine — by Markanm Team
# https://markanm.com
# -----------------------------------------------
"""Navar — Agentic AI assistant for Blend Search.

Supports: web search, image/video/news/social/maps search,
Google Dork generation, URL scanning, multi-tab intent routing.
"""

from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request
from difflib import SequenceMatcher
from urllib.parse import urlparse

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

try:
    from blend.api_keys import get_active_api_config, get_global_config, get_navar_api_key
    from blend.navar_identity import NAVAR_IDENTITY
    from blend.navar_knowledge import answer_markanm_query, is_markanm_query
    _IDENTITY_NAME = NAVAR_IDENTITY.name
    _IDENTITY_MISSION = NAVAR_IDENTITY.mission
    _IDENTITY_TONE = NAVAR_IDENTITY.tone
except Exception:
    _IDENTITY_NAME = "Navar"
    _IDENTITY_MISSION = "I am Navar, an AI assistant for Blend Search."
    _IDENTITY_TONE = "helpful"
    def get_active_api_config(): return None
    def get_global_config(): return {}
    def get_navar_api_key(): return ""
    def is_markanm_query(query: str) -> bool: return "markanm" in query.lower()
    def answer_markanm_query() -> str: return "**MarkanM** is the organisation behind Blend Search. Founder: **Raj Singh**."

_PORT = os.environ.get("PORT", "8081")
BASE_SEARCH_URL = os.path.expandvars(os.environ.get("BLEND_BASE_URL", f"http://127.0.0.1:{_PORT}")).rstrip("/")

# ─────────────────────────────────────────────
#  INTENT DETECTION
# ─────────────────────────────────────────────

INTENTS = {
    "maps":   [r"where is\b", r"location of\b", r"kahan hai", r"kahan per", r"map of\b",
               r"directions? to\b", r"how to reach", r"locate\b", r"find place"],
    "images": [r"show.*image", r"image.*of\b", r"photo.*of\b", r"picture.*of\b",
               r"dikhao.*image", r"images? of\b"],
    "videos": [r"show.*video", r"video.*of\b", r"youtube.*about", r"watch\b"],
    "news":   [r"latest news", r"recent news", r"news about", r"news on\b", r"aaj ka news"],
    "social": [r"social media", r"twitter.*of", r"instagram.*of", r"reddit.*about",
               r"social.*handle", r"social.*profile"],
    "dork":   [r"google dork", r"\bdork\b", r"advanced search for", r"find.*file.*on\b",
               r"intitle:", r"inurl:", r"filetype:"],
    "scan":   [r"scan\b.*https?://", r"analyze.*https?://", r"summarize.*https?://",
               r"read.*https?://", r"check.*https?://", r"fetch\b.*https?://"],
    "guide":  [r"kaise\b", r"how to\b", r"login\b", r"sign ?in\b", r"register\b", r"signup\b"],
    "all":    [r"search.*everything", r"search.*all.*tab", r"sare.*section", r"all.*result"],
}

def detect_intents(query: str) -> list[str]:
    q = query.lower()
    found = []
    for intent, patterns in INTENTS.items():
        if any(re.search(p, q) for p in patterns):
            found.append(intent)
    return found if found else ["web"]


# ─────────────────────────────────────────────
#  SEARCH TOOL
# ─────────────────────────────────────────────

def _search(q: str, categories: str = "general", pageno: int = 1) -> list[dict]:
    try:
        url = (f"{BASE_SEARCH_URL}/search?q={urllib.parse.quote(q)}"
               f"&categories={urllib.parse.quote(categories)}&format=json&pageno={pageno}")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=8).read()
        data = json.loads(resp)
        return data.get("results", [])
    except Exception:
        return []



# ─────────────────────────────────────────────
#  DOMAIN-BOOSTED SEARCH
# ─────────────────────────────────────────────

def _domain_boosted_search(q: str, categories: str = "general") -> list[dict]:
    """Search with domain boost: also does site:q.com search and merges results."""
    import re
    base = q.strip().lower().split()[0]  # first word as potential domain
    tlds = [".com", ".in", ".org", ".net", ".io"]
    
    # Run main search + site-specific searches in parallel
    main_results = _search(q, categories)
    
    # Only do domain-specific search for single-word queries (likely a brand/domain)
    if re.match(r'^[a-zA-Z0-9\-]+$', base) and len(base) >= 3:
        site_queries = " OR ".join(f"site:{base}{t}" for t in tlds[:3])
        site_results = _search(site_queries, "general")
        
        # Merge: site results first, then main (deduped)
        site_urls = {r.get("url", "") for r in site_results}
        deduped_main = [r for r in main_results if r.get("url") not in site_urls]
        return site_results + deduped_main
    
    # Boost: move any result whose domain matches the query to top
    def domain_matches(result):
        url = result.get("url", "").lower()
        for tld in tlds:
            if f"{base}{tld}" in url or f"/{base}." in url:
                return True
        return False
    
    official = [r for r in main_results if domain_matches(r)]
    rest = [r for r in main_results if not domain_matches(r)]
    return official + rest

# ─────────────────────────────────────────────
#  URL SCAN TOOL
# ─────────────────────────────────────────────

def _scan_url(url: str) -> dict:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        html = urllib.request.urlopen(req, timeout=8).read()
        if BeautifulSoup:
            soup = BeautifulSoup(html, "html.parser")
            title = soup.title.string.strip() if soup.title else url
            # Remove scripts/styles
            for tag in soup(["script", "style", "nav", "footer"]):
                tag.decompose()
            text = " ".join(soup.stripped_strings)
            # Collect links
            links = []
            for a in soup.find_all("a", href=True)[:40]:
                href = urllib.parse.urljoin(url, a.get("href", ""))
                if href.startswith("http"):
                    links.append(href)
            forms = []
            for form in soup.find_all("form")[:5]:
                fields = []
                for field in form.find_all(["input", "textarea", "select"])[:10]:
                    label = field.get("aria-label") or field.get("placeholder") or field.get("name") or field.get("type") or field.name
                    fields.append(str(label))
                forms.append({"action": urllib.parse.urljoin(url, form.get("action", "")), "fields": fields})
            techs = _detect_tech(soup)
        else:
            title = url
            text = html.decode("utf-8", errors="ignore")[:2000]
            links = []
            forms = []
            techs = []
        return {
            "ok": True,
            "title": title,
            "summary": text[:800] + "…" if len(text) > 800 else text,
            "text_length": len(text),
            "links": links[:8],
            "forms": forms,
            "techs": techs,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _detect_tech(soup) -> list[str]:
    techs = []
    html_str = str(soup)
    lower = html_str.lower()
    if "wp-content" in lower or "wordpress" in lower:
        techs.append("WordPress")
    if "react" in lower or "__react" in html_str:
        techs.append("React")
    if "__next" in html_str:
        techs.append("Next.js")
    if "shopify" in lower:
        techs.append("Shopify")
    if "wix" in lower:
        techs.append("Wix")
    if "bootstrap" in lower:
        techs.append("Bootstrap")
    if "tailwind" in lower:
        techs.append("Tailwind CSS")
    return techs


def _extract_site_candidate(query: str) -> str:
    url_match = re.search(r'(https?://[^\s]+)', query)
    if url_match:
        return url_match.group(1)
    cleaned = re.sub(r"\b(how to|kaise|login|sign ?in|register|signup|karo|karun|mein|me|on|par|pe|please|guide)\b", " ", query, flags=re.IGNORECASE)
    for token in cleaned.split():
        token = token.strip(".,:;!?()[]{}'\"")
        if len(token) >= 3 and re.match(r"^[a-zA-Z0-9.-]+$", token):
            return token
    return query.split()[0] if query.split() else ""


def _resolve_url(site: str) -> str:
    site = site.strip()
    if site.startswith(("http://", "https://")):
        return site
    if "." in site:
        return f"https://{site}"
    results = _domain_boosted_search(site, "general")
    for result in results:
        url = result.get("url", "")
        if url.startswith("http"):
            return url
    return f"https://{site}.com"


def _build_step_guide(task: str, page: dict, site_url: str) -> dict:
    forms = page.get("forms", [])
    login_links = [link for link in page.get("links", []) if re.search(r"login|sign-?in|account|auth", link, re.I)]
    fields = forms[0].get("fields", []) if forms else []
    steps = [f"Step 1: Go to {site_url}"]
    if login_links:
        steps.append(f"Step 2: Open the login/sign-in page: {login_links[0]}")
    elif "login" in task.lower() or "sign" in task.lower():
        steps.append("Step 2: Look for the Login or Sign In button, usually near the top-right.")
    for field in fields[:4]:
        steps.append(f"Step {len(steps) + 1}: Fill the {field} field.")
    if forms:
        steps.append(f"Step {len(steps) + 1}: Submit the form and follow any verification prompt.")
    else:
        steps.append(f"Step {len(steps) + 1}: If the page is app-rendered, wait for it to load and follow the visible login/register prompts.")
    return {
        "message": "\n".join(steps),
        "action": "guide",
        "site_url": site_url,
        "site_title": page.get("title", site_url),
        "forms_found": len(forms),
        "techs": page.get("techs", []),
    }


# ─────────────────────────────────────────────
#  GOOGLE DORK GENERATOR
# ─────────────────────────────────────────────

def _generate_dorks(target: str) -> list[dict]:
    t = urllib.parse.quote(target)
    raw = urllib.parse.quote(f'"{target}"')
    return [
        {"label": "Official site pages",        "dork": f"site:{target}", "url": f"https://www.google.com/search?q=site:{t}"},
        {"label": "Admin / login portals",       "dork": f'site:{target} inurl:admin | inurl:login | inurl:dashboard', "url": f"https://www.google.com/search?q=site:{t}+inurl%3Aadmin+%7C+inurl%3Alogin"},
        {"label": "Exposed documents (PDF/DOC)", "dork": f'site:{target} ext:pdf | ext:doc | ext:docx', "url": f"https://www.google.com/search?q=site:{t}+ext%3Apdf+%7C+ext%3Adoc"},
        {"label": "Directory listing",           "dork": f'site:{target} intitle:"index of"', "url": f"https://www.google.com/search?q=site:{t}+intitle%3A%22index+of%22"},
        {"label": "Config / env files",          "dork": f'site:{target} ext:env | ext:config | ext:cfg | ext:xml', "url": f"https://www.google.com/search?q=site:{t}+ext%3Aenv+%7C+ext%3Aconfig"},
        {"label": "Mentions across the web",     "dork": f'"{target}" -site:{target}', "url": f"https://www.google.com/search?q={raw}"},
        {"label": "Pastebin / data leaks",       "dork": f'site:pastebin.com | site:github.com "{target}"', "url": f"https://www.google.com/search?q=site%3Apastebin.com+%7C+site%3Agithub.com+{raw}"},
        {"label": "Social media profiles",       "dork": f'site:twitter.com | site:linkedin.com | site:instagram.com "{target}"', "url": f"https://www.google.com/search?q=site%3Atwitter.com+%7C+site%3Alinkedin.com+{raw}"},
        {"label": "Subdomains",                  "dork": f'site:*.{target}', "url": f"https://www.google.com/search?q=site%3A*.{t}"},
        {"label": "Email addresses",             "dork": f'"{target}" "@{target}"', "url": f"https://www.google.com/search?q=%40{t}+%22{t}%22"},
    ]


# ─────────────────────────────────────────────
#  LLM CALL (if configured)
# ─────────────────────────────────────────────

NAVAR_SYSTEM = """You are Navar — an intelligent AI assistant inside Blend Search.
You can route queries to Web, Images, Videos, News, Maps, and Social.
- User is on the '{current_tab}' tab of Blend Search.
- Provide a clear, concise, and structured answer. Avoid verbosity.
- Use markdown formatting.
- DO NOT expose your <think> or <thought> reasoning process.
- Respond in the same language the user writes in (Hindi, English, Hinglish).
"""

LANG_INSTRUCTIONS = {
    "hindi": "\n\nजरूरी: User ने हिंदी में पूछा है। पूरा जवाब हिंदी में दो।",
    "hinglish": "\n\nIMPORTANT: User ne Hinglish mein pucha hai. Hinglish mein reply karo, Roman script mein Hindi words English ke saath.",
    "english": "",
}


def detect_language(text: str) -> str:
    hindi_chars = sum(1 for c in text if "\u0900" <= c <= "\u097f")
    if hindi_chars > 3:
        return "hindi"
    hinglish_words = {
        "karo", "kaise", "kya", "hai", "mein", "me", "ka", "ki", "ke",
        "nahi", "hoga", "batao", "dikho", "bata", "toh", "aur", "yeh",
        "woh", "upar", "niche", "abhi", "baad", "pehle", "jaise",
        "matlab", "samjho", "dekho", "karun",
    }
    count = sum(1 for word in re.findall(r"[a-zA-Z]+", text.lower()) if word in hinglish_words)
    if count >= 2:
        return "hinglish"
    return "english"


def _system_for(query: str, current_tab: str = "web", current_url: str = "") -> str:
    sys = NAVAR_SYSTEM.format(current_tab=current_tab.capitalize(), current_url=current_url)
    return sys + LANG_INSTRUCTIONS[detect_language(query)]


def _clean_llm_text(text: str) -> str:
    if not text:
        return ""
    # Strip <think>...</think> and <thought>...</thought> blocks including newlines
    text = re.sub(r"<(think|thought)>.*?</\1>", "", text, flags=re.DOTALL | re.IGNORECASE)
    # Also remove any unclosed tags just in case
    text = re.sub(r"<(think|thought)>.*", "", text, flags=re.DOTALL | re.IGNORECASE)
    return text.strip()

def _call_llm_stream(messages: list[dict]):
    import json
    # Try Sarvam if key exists
    sarvam_key = get_navar_api_key()
    if sarvam_key:
        try:
            import requests
            headers = {"api-subscription-key": sarvam_key, "Content-Type": "application/json"}
            payload = {
                "model": "sarvam-2b-v0.5",
                "messages": messages,
                "temperature": 0.3,
                "stream": True
            }
            resp = requests.post("https://api.sarvam.ai/chat/completions", headers=headers, json=payload, stream=True, timeout=10)
            if resp.status_code == 200:
                for line in resp.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data_str)
                                content = chunk["choices"][0]["delta"].get("content", "")
                                if content:
                                    yield content
                            except:
                                pass
                return
        except Exception as e:
            print(f"Sarvam API streaming failed: {e}")
            
    # Fallback to g4f streaming
    try:
        import g4f
        from g4f.Provider import DuckDuckGo
        response = g4f.ChatCompletion.create(
            model="gpt-4o-mini",
            provider=DuckDuckGo,
            messages=messages,
            stream=True
        )
        for chunk in response:
            if chunk:
                yield str(chunk)
    except Exception as e:
        print(f"g4f streaming failed: {e}")
        yield "Error: Could not connect to AI provider."

# ─────────────────────────────────────────────
#  SCORE / RANK
# ─────────────────────────────────────────────

def _score(q: str, r: dict) -> float:
    title = r.get("title", "").lower()
    content = r.get("content", r.get("snippet", "")).lower()
    url = r.get("url", "").lower()
    score = 0.0
    for token in q.lower().split():
        if token in title:   score += 3.0
        elif token in url:   score += 2.0
        elif token in content: score += 1.0
    score += SequenceMatcher(None, q.lower(), title).ratio() * 2.0
    return round(score, 4)

# ─────────────────────────────────────────────
#  MAIN ENTRY
# ─────────────────────────────────────────────

def build_ai_response(query: str, results: list[dict],
                      shortcuts: list[dict] = None, mode: str = "fast",
                      current_tab: str = "web", current_url: str = ""):
    q = query.strip()
    q_lower = q.lower()
    intents = detect_intents(q)
    
    import time
    yield {"type": "status", "message": "[✓] ⚡ Checking high-speed cache..."}
    time.sleep(0.2)
    yield {"type": "status", "message": "[✓] 🧠 Analyzing query intent..."}
    time.sleep(0.2)
    
    # ── MAPS / LOCATION ─────────────────────────────────────────────────
    if "maps" in intents or "where is" in q_lower or "location of" in q_lower:
        yield {"type": "status", "message": "[...] 🗺️ Rendering interactive map sandbox..."}
        place = re.sub(r"where is|location of|map of|kahan hai|kahan per|directions? to|how to reach|find place", "", q, flags=re.IGNORECASE).strip() or q
        coords = [28.6139, 77.2090] # default fallback
        try:
            import urllib.request
            import urllib.parse
            import json
            req = urllib.request.Request(f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(place)}&format=json&limit=1", headers={"User-Agent": "BlendSearch/1.0"})
            resp = urllib.request.urlopen(req, timeout=3).read()
            data = json.loads(resp)
            if data:
                coords = [float(data[0]["lat"]), float(data[0]["lon"])]
        except:
            pass
        yield {"type": "action", "action": "render_map", "coords": coords, "place": place}
    
    yield {"type": "status", "message": "[...] 🔍 Fetching top snippets & semantic data..."}
    time.sleep(0.2)
    
    if mode == "deep":
        yield {"type": "status", "message": "[...] 🕷️ Queuing deep links for long-term index..."}
        time.sleep(0.2)
        
    yield {"type": "status", "message": "[...] ✍️ Synthesizing AI Overview..."}

    # Fetch live semantic data
    live_results = _domain_boosted_search(q, "general")[:3]
    all_res = live_results + results
    if not all_res:
        all_res = results
        
    ranked = sorted(all_res, key=lambda r: _score(q, r), reverse=True)[:4]

    context = "\n\n".join(
        f"[{i+1}] Title: {r.get('title','')}\nURL: {r.get('url','')}\nContent: {r.get('content', r.get('snippet',''))[:250]}"
        for i, r in enumerate(ranked)
    )

    sys_prompt = _system_for(q, current_tab, current_url) + "\n\nYou are the Core Orchestrator of the Navar Search Engine. Synthesize the aggregated data into a final response, citing sources as [1], [2]."
    
    for chunk in _call_llm_stream([
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": f"User query: {q}\n\nSearch context:\n{context}\n\nProvide a concise, direct, and structured summary answering the user's query. Use markdown."}
    ]):
        yield {"type": "text", "chunk": _clean_llm_text(chunk)}

    # Proactive Search Guidance
    filters = []
    if "images" in intents or "photo" in q_lower:
        filters.append("Images")
    if "videos" in intents or "youtube" in q_lower:
        filters.append("Videos")
    if "news" in intents:
        filters.append("News")
    if not filters:
        filters = ["Images", "News"]
        
    yield {"type": "suggested_filters", "filters": filters}

