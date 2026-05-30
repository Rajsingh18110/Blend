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
    from api_keys import get_active_api_config, get_global_config, get_navar_api_key
    from navar_identity import NAVAR_IDENTITY
    from navar_knowledge import answer_markanm_query, is_markanm_query
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

def _call_llm(messages: list[dict]) -> str:
    # Design for Render deployment - Environment variables First
    api_key = os.environ.get("SARVAM_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        # Fallback to local config if no env var is found
        cfg = get_active_api_config()
        if cfg and cfg.get("api_key"):
            api_key = cfg.get("api_key")
        else:
            return ""

    webhook_url = os.environ.get("LLM_WEBHOOK_URL", "https://api.sarvam.ai/v1/chat/completions")
    model_name = os.environ.get("LLM_MODEL", "sarvam-1")
    
    try:
        body = json.dumps({
            "model": model_name,
            "messages": messages,
            "temperature": 0.4,
            "max_tokens": 1500,
        }).encode()
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        # Sarvam AI specific header if needed
        if "sarvam" in webhook_url.lower():
            headers["api-subscription-key"] = api_key
            
        req = urllib.request.Request(webhook_url, data=body, headers=headers, method="POST")
        resp = json.loads(urllib.request.urlopen(req, timeout=15).read())
        return _clean_llm_text(resp["choices"][0]["message"]["content"])
    except Exception as e:
        print(f"LLM Call Failed: {e}")
        return ""


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
                      current_tab: str = "web", current_url: str = "") -> dict:
    q = query.strip()
    q_lower = q.lower()
    intents = detect_intents(q)

    # ── DORK MODE ──────────────────────────────────────────────────────
    if mode == "dork" or "dork" in intents:
        # Extract target: strip dork keywords
        target = re.sub(r"google dork|dork me|dork\s+|dork:", "", q, flags=re.IGNORECASE).strip()
        if not target:
            target = q
        dorks = _generate_dorks(target)
        return {
            "message": "",
            "action": "dork",
            "target": target,
            "dorks": dorks,
        }

    # ── URL SCAN ────────────────────────────────────────────────────────
    url_match = re.search(r'(https?://[^\s]+)', q)
    if (url_match or "scan" in intents) and "guide" not in intents:
        scan_url = url_match.group(1) if url_match else ""
        if scan_url:
            result = _scan_url(scan_url)
            if result["ok"]:
                llm_summary = _call_llm([
                    {"role": "system", "content": _system_for(q, current_tab, current_url)},
                    {"role": "user", "content": f"I scanned this website: {scan_url}\nTitle: {result['title']}\nContent: {result['summary']}\n\nGive a clear 3-5 line summary of what this website is about. Mention any key links."}
                ])
                return {
                    "message": llm_summary or f"**{result['title']}**\n\n{result['summary']}",
                    "action": "scan",
                    "scan_url": scan_url,
                    "scan_title": result["title"],
                    "scan_links": result.get("links", []),
                }
            else:
                return {"message": f"⚠️ Could not scan `{scan_url}`: {result.get('error', 'Unknown error')}"}

    # ── STEP-BY-STEP WEBSITE GUIDE ─────────────────────────────────────
    if "guide" in intents and any(word in q_lower for word in ["login", "signin", "sign in", "register", "signup", "kaise", "how to"]):
        site = _extract_site_candidate(q)
        site_url = _resolve_url(site)
        page = _scan_url(site_url)
        if page.get("ok") and (page.get("forms") or page.get("text_length", 0) >= 300):
            return _build_step_guide(q, page, site_url)
        fallback = _search(f"{site} {q} tutorial steps", "general")[:3]
        context = "\n".join(f"- {r.get('title','')}: {r.get('content', '')[:180]}" for r in fallback)
        llm = _call_llm([
            {"role": "system", "content": _system_for(q, current_tab, current_url)},
            {"role": "user", "content": f"Create a concise step-by-step guide for this task: {q}\nSite: {site}\nSearch context:\n{context}"}
        ])
        return {
            "message": llm or f"Step 1: Open {site_url}\nStep 2: Look for Login, Sign In, or Account.\nStep 3: Fill the required fields.\nStep 4: Submit and complete any verification.",
            "action": "guide",
            "site_url": site_url,
            "site_title": site,
            "forms_found": 0,
        }

    # ── MULTI-TAB: search all sections ─────────────────────────────────
    if "all" in intents:
        web = _search(q, "general")[:3]
        imgs = _search(q, "images")[:4]
        vids = _search(q, "videos")[:2]
        news = _search(q, "news")[:2]
        summary = _build_all_summary(q, web, imgs, vids, news)
        return {
            "message": summary,
            "action": "search_all",
            "blend_query": q,
            "web_count": len(web),
            "image_count": len(imgs),
            "video_count": len(vids),
            "news_count": len(news),
        }

    # ── DEEP MODE ───────────────────────────────────────────────────────
    if mode == "deep":
        live = _search(q, "general")[:5]
        all_results = live or results
        ranked = sorted(all_results, key=lambda r: _score(q, r), reverse=True)[:3]
        context = "\n\n".join(
            f"Source: {r.get('url','')}\nTitle: {r.get('title','')}\nContent: {r.get('content', r.get('snippet',''))[:300]}"
            for r in ranked
        )
        llm = _call_llm([
            {"role": "system", "content": _system_for(q, current_tab, current_url)},
            {"role": "user", "content": f"Deep research request: {q}\n\nContext from web:\n{context}\n\nProvide a comprehensive, well-structured answer. Reference sources as [1], [2], [3]."}
        ])
        sources = "\n".join(
            f"[{i+1}] [{r.get('title','Source')}]({r.get('url','')})"
            for i, r in enumerate(ranked) if r.get("url")
        )
        citation_block = f"\n\n**Sources:**\n{sources}" if sources else ""
        if llm:
            return {"message": llm + citation_block, "action": "web", "blend_query": q, "results": ranked}
        fallback = "\n".join(f"• **[{i+1}] {r.get('title')}** — {r.get('content','')[:120]}…" for i, r in enumerate(ranked))
        return {"message": f"**Deep search results for: {q}**\n\n{fallback}{citation_block}", "action": "web", "blend_query": q}

    # ── MAPS / LOCATION ─────────────────────────────────────────────────
    if "maps" in intents:
        place = re.sub(r"where is|location of|map of|kahan hai|kahan per|directions? to|how to reach|find place", "", q, flags=re.IGNORECASE).strip() or q
        map_results = _search(place, "map")[:3]
        context = map_results[0].get("content", "") if map_results else ""
        llm = _call_llm([
            {"role": "system", "content": _system_for(q, current_tab, current_url)},
            {"role": "user", "content": f"Give a brief factual answer about the location: '{place}'. Include: country/state, key facts, what it's known for. Keep it under 6 lines. Context: {context}"}
        ])
        return {
            "message": llm or f"📍 Showing map for **{place}**. Check the Maps tab for the full interactive map.",
            "action": "maps",
            "map_query": place,
        }

    # ── IMAGES ─────────────────────────────────────────────────────────
    if "images" in intents:
        subject = re.sub(r"show.*images? of|images? of|photos? of|pictures? of|dikhao", "", q, flags=re.IGNORECASE).strip() or q
        img_results = _search(subject, "images")[:6]
        return {
            "message": f"🖼️ Found **{len(img_results)} images** for **{subject}**. Opening the Images tab now.",
            "action": "images",
            "blend_query": subject,
            "image_previews": [r.get("img_src") or r.get("thumbnail_src") for r in img_results if r.get("img_src") or r.get("thumbnail_src")][:4],
        }

    # ── VIDEOS ──────────────────────────────────────────────────────────
    if "videos" in intents:
        subject = re.sub(r"show.*video.*of|video.*of|watch|youtube.*about", "", q, flags=re.IGNORECASE).strip() or q
        return {
            "message": f"🎬 Searching for videos about **{subject}**. Opening the Videos tab.",
            "action": "videos",
            "blend_query": subject,
        }

    # ── NEWS ────────────────────────────────────────────────────────────
    if "news" in intents:
        subject = re.sub(r"latest news|recent news|news about|news on|aaj ka news", "", q, flags=re.IGNORECASE).strip() or q
        news_results = _search(subject, "news")[:3]
        headlines = "\n".join(f"• {r.get('title','')}" for r in news_results)
        return {
            "message": f"📰 Latest news for **{subject}**:\n\n{headlines}\n\nOpening News tab for full articles.",
            "action": "news",
            "blend_query": subject,
        }

    # ── SOCIAL ──────────────────────────────────────────────────────────
    if "social" in intents:
        subject = re.sub(r"social media|twitter|instagram|reddit.*about|social.*handle|social.*profile", "", q, flags=re.IGNORECASE).strip() or q
        return {
            "message": f"👥 Searching social media for **{subject}**. Opening Social tab.",
            "action": "social",
            "blend_query": subject,
        }

    # ── WEB / GENERAL ───────────────────────────────────────────────────
    # Greetings
    if q_lower in {"hello", "hi", "hey", "namaste", "hii", "hello!", "hi!"}:
        return {"message": "Hello! I am **Navar**, your agentic AI assistant inside Blend Search 🚀\n\nI can:\n• 🔍 Search the web and all tabs\n• 📍 Show maps & locations\n• 🖼️ Find images & videos\n• 📰 Get latest news\n• 💻 Scan & analyze websites\n• 🔎 Generate Google Dorks\n• 👥 Search social media\n\nWhat would you like to explore?"}

    # MarkanM / founder
    if is_markanm_query(q) or ("founder" in q_lower and "blend" in q_lower):
        live = _search("markanm.com site:markanm.com OR site:markanm.in", "general")[:3]
        return {
            "message": answer_markanm_query(),
            "action": "search_all",
            "blend_query": "markanm",
        }

    # General — live search + LLM answer
    live_results = _domain_boosted_search(q, "general")[:6]
    all_res = live_results or results
    ranked = sorted(all_res, key=lambda r: _score(q, r), reverse=True)[:3]

    context = "\n\n".join(
        f"Title: {r.get('title','')}\nURL: {r.get('url','')}\nContent: {r.get('content', r.get('snippet',''))[:250]}"
        for r in ranked
    )

    llm = _call_llm([
        {"role": "system", "content": _system_for(q, current_tab, current_url)},
        {"role": "user", "content": f"User query: {q}\n\nSearch context:\n{context}\n\nProvide a concise and structured summary answering the user's query using bullet points."}
    ])

    if llm:
        return {"message": llm, "action": "web", "blend_query": q, "top_results": ranked[:2]}

    # Fallback: format top result
    if ranked:
        best = ranked[0]
        return {
            "message": f"**{best.get('title','')}**\n\n{best.get('content', best.get('snippet',''))[:400]}\n\n🔗 [{best.get('url','')}]({best.get('url','')})",
            "action": "web",
            "blend_query": q,
            "top_results": ranked[:2],
        }

    return {"message": f"I searched for **{q}** but couldn't find a confident answer. Try rephrasing or use the search bar above for full results."}


def _build_all_summary(q: str, web, imgs, vids, news) -> str:
    lines = [f"🔍 Multi-tab search results for **{q}**:\n"]
    if web:
        lines.append("**🌐 Web:**")
        for r in web:
            lines.append(f"• [{r.get('title','')}]({r.get('url','')})")
    if imgs:
        lines.append(f"\n**🖼️ Images:** {len(imgs)} found — see Images tab")
    if vids:
        lines.append(f"\n**🎬 Videos:** {len(vids)} found — see Videos tab")
    if news:
        lines.append("\n**📰 News:**")
        for r in news:
            lines.append(f"• {r.get('title','')}")
    lines.append("\n\nAll tabs have been populated with results!")
    return "\n".join(lines)
