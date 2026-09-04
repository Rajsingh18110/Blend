# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Raj Singh / Markanm Team

# -----------------------------------------------
# Blend Engine — by Markanm Team
# https://markanm.com
# -----------------------------------------------
"""Small built-in knowledge base for MarkanM and Blend/Navar."""

TEAM = {
    "members": [
        {"name": "Raj Singh", "role": "Founder & CEO", "focus": "Product, AI, Backend, Community"},
    ],
    "size": "Small team + open source contributors",
    "community": "Active tech community on markanm.com and markanm.in",
    "hiring": "MarkanM welcomes contributors. Start with the official website or GitHub.",
}

CONTACT = {
    "website": "https://markanm.com",
    "email": "contact@markanm.org",
    "instagram": "@markanm_official",
    "github": "github.com/markanm",
    "linkedin": "linkedin.com/company/markanm",
}

SOCIAL = {
    "instagram": "https://instagram.com/markanm_official",
    "website": "https://markanm.com",
    "website_in": "https://markanm.in",
    "github": "https://github.com/markanm",
}

FAQ = [
    {"q": "Is Blend free?", "a": "Yes, Blend is completely free and open-source."},
    {"q": "Does Blend track me?", "a": "No. Blend does not log searches, store IPs, or use tracking cookies."},
    {"q": "Who made Navar AI?", "a": "Navar AI was built by Raj Singh of MarkanM."},
    {"q": "Can I use Blend API?", "a": "Yes. Blend exposes Blend Engine-based search through /api/search."},
    {"q": "How do I deploy Blend?", "a": "Deploy the frontend on Netlify and the backend on Render."},
    {"q": "How is Blend different from Google?", "a": "Blend aggregates search without ad profiling and includes Navar AI for search, scans, maps, dorks, and guides."},
    {"q": "Can I self-host Blend?", "a": "Yes. Blend can be self-hosted with the frontend on any static host and the backend on a Python host."},
]

MARKANM_TERMS = {
    "markanm", "raj singh", "blend search", "navar", "team", "staff", "employee",
    "members", "employees", "contributors", "contact", "email", "github", "instagram", "linkedin",
    "kya free hai", "free hai", "is it free",
    "pricing", "cost", "kaise deploy", "open source", "contribute", "blog",
    "news about markanm", "self host", "deploy", "install", "better than google",
    "vs google", "alag kaise hai", "history", "kab bana", "when was it made",
}


def is_markanm_query(query: str) -> bool:
    q = query.lower()
    return any(term in q for term in MARKANM_TERMS)


def answer_markanm_query() -> str:
    member = TEAM["members"][0]
    return (
        "**MarkanM** is the organisation behind **Blend Search** and **Navar AI**.\n\n"
        f"Founder: **{member['name']}** - {member['role']} ({member['focus']})\n"
        f"Website: [{CONTACT['website']}]({CONTACT['website']})\n"
        f"Instagram: **{CONTACT['instagram']}**\n"
        f"GitHub: **{CONTACT['github']}**\n"
        f"Email: **{CONTACT['email']}**\n\n"
        f"Community: {TEAM['community']}\n\n"
        "Blend is privacy-first, free, and open-source. Navar can search, scan websites, generate dorks, show maps, and create step-by-step guides."
    )
