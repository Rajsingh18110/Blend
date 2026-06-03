# Blend Engine — by Markanm

![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Status](https://img.shields.io/badge/Status-Public%20Release-green)

Blend Engine is a privacy-first, AI-assisted metasearch engine built by
Raj Singh / Markanm Team. It combines results from multiple search sources,
serves a custom dark-first web interface, and includes Navar, an assistant layer
for summaries, guided answers, page scanning, and search intent routing.

The project is designed for people who want a clean search experience without
ad profiling, invasive tracking, or committing private API configuration into
source control.

## Acknowledgments
Blend Engine was originally inspired by and started as a fork of [SearxNG](https://github.com/searxng/searxng). We owe a great debt of gratitude to the SearxNG maintainers and community for their pioneering work in privacy-preserving metasearch. Blend Engine has since evolved into a custom, from-scratch architecture incorporating intelligent extraction (Crawl4AI), advanced privacy modes (Ghost Mode & Tor), and AI intent routing, but its roots in the open web search movement began with SearxNG.

## What Blend Engine Does


Blend Engine provides a full search application, not just a backend library.
It includes:

- A Flask-based backend that exposes browser pages and JSON APIs.
- A custom frontend for home, results, about, privacy, and settings pages.
- Multi-category search across web, images, videos, news, maps, music, files,
  social results, code, packages, academic sources, and reference sources.
- Navar AI integration for search summaries, conversational answers, website
  scanning, Google Dork generation, and multi-tab intent routing.
- Query routing and result boosting so official, trusted, and relevant domains
  can be prioritized.
- DuckDuckGo autocomplete and fallback search paths for local development.
- Optional YouTube media metadata and stream extraction through `yt-dlp`.
- Optional Valkey/Redis-compatible caching and rate-limit support.
- Locale, SafeSearch, UI preference, and engine configuration support.

## Core Features

### Privacy-First Search

Blend is built around a no-profile search flow. The public configuration avoids
committing private secrets, local API keys, or personal credentials. Local
runtime settings belong in `.env`, `admin_config.json`, or local override files
that are ignored by Git.

### Navar AI Assistant

Navar is the AI assistant layer inside Blend. It can:

- Create AI summaries from search results.
- Route user intent to web, images, videos, news, maps, files, social, or AI
  chat modes.
- Scan and summarize URLs.
- Generate Google Dork-style advanced queries.
- Answer Markanm and Blend-specific questions from the built-in knowledge base.

### Multi-Engine Search

The backend contains a large source catalog for general search, media search,
developer resources, packages, academic references, social platforms, maps,
weather, and more. Engine behavior is controlled through YAML configuration and
Python source modules under `backend/blend_core/sources/`.

### Custom Frontend

The `frontend/` directory contains the public Blend UI. It is dark-first,
mobile-friendly, and focused on practical search workflows:

- Home page with shortcuts, categories, privacy widgets, and search entry.
- Results page with tabs for web, images, videos, news, maps, music, files,
  social results, and AI chat.
- Privacy, about, and settings pages.
- Frontend configuration in `frontend/templates/blend-config.js`.

### Local-Friendly Backend

`backend/start_backend.sh` starts the app in embedded/offline-friendly mode so
local startup does not fail just because remote search engines or network probes
are unavailable.

## Project Structure

```text
.
├── backend/
│   ├── app.py                    # Standalone Blend web/API launcher
│   ├── start_backend.sh           # Local startup script
│   ├── navar.py                   # Navar assistant and intent routing
│   ├── navar_knowledge.py         # Markanm/Blend knowledge responses
│   ├── ytdl_downloader.py         # Optional media metadata helpers
│   ├── requirements.txt           # Backend dependencies
│   ├── setup.py                   # Python package metadata
│   ├── blend/                     # Compatibility webapp package
│   ├── blend_core/                # Search core, engines, settings, web app
│   │   ├── sources/               # Search source adapters
│   │   ├── extensions/            # Optional search/result extensions
│   │   ├── botdetection/          # Request/bot protection helpers
│   │   ├── pipeline/              # Result processing pipeline
│   │   ├── result_types/          # Structured result models
│   │   ├── data/                  # Engine metadata and local datasets
│   │   └── views/                 # Backend-rendered template assets
│   ├── blend_extras/              # Update and maintenance helpers
│   ├── blendsearch/               # External bang/search helpers
│   └── tools/                     # Validation and maintenance scripts
├── frontend/
│   ├── static/
│   │   └── style.css              # Main public UI stylesheet
│   └── templates/
│       ├── index.html             # Home page
│       ├── results.html           # Search results and AI chat UI
│       ├── about.html
│       ├── privacy.html
│       ├── settings.html
│       └── blend-config.js
├── .env.example                   # Public environment template
├── admin_config.example.json      # Public API config template
├── LICENSE                        # Apache License 2.0
├── README.md                      # This file
└── README.rst                     # Package/readme compatibility file
```

## Requirements

- Python 3.10 or newer
- `pip`
- Optional: Valkey/Redis if you enable external caching
- Optional: `yt-dlp` features are installed through `backend/requirements.txt`

## Local Development

From the project root:

```bash
cp .env.example .env
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
./start_backend.sh
```

The backend starts on:

```text
http://127.0.0.1:8081
```

You can also run the app directly from `backend/`:

```bash
python app.py
```

## Configuration

Copy `.env.example` to `.env` and fill in local values:

```env
NAVAR_API_KEY=your_api_key_here
YOUTUBEI_API_KEY=your_youtubei_key_here
BLEND_SECRET_KEY=change_this_to_a_random_string
BLEND_PORT=8081
BLEND_HOST=127.0.0.1
VALKEY_URL=redis://localhost:6379/0
```

For API provider configuration, copy or reference
`admin_config.example.json` and keep the real `admin_config.json` local only.

Never commit:

- `.env`
- `admin_config.json`
- private keys
- local credentials
- local config overrides

These files are covered by `.gitignore`.

## Useful Endpoints

When running locally:

```text
GET  /                       # Home page
GET  /results.html?q=blend   # Frontend results page
GET  /api/search?q=blend     # JSON search API
POST /api/ai                 # Navar AI endpoint
GET  /autocompleter?q=blend  # Autocomplete
GET  /ping                   # Health check
```

## Public Release Security

This public release was prepared with a clean Git history and a single initial
release commit. The repository includes only placeholder configuration for API
keys and secrets.

Before publishing changes, run a local secret scan against the working tree and
commit history. For example, use a tool such as `gitleaks`, `trufflehog`, or a
project-specific `grep`/`rg` pattern list stored outside the repository.

The public repository should not contain live API keys, private tokens, local
admin configuration, or secret-looking default values.

## Development Notes

- Keep user-facing UI changes in `frontend/`.
- Keep search source behavior in `backend/blend_core/sources/`.
- Keep runtime-only secrets in `.env` or ignored local config files.
- Prefer environment variables for keys, hostnames, ports, and provider tokens.
- Do not commit generated caches, virtual environments, or local admin config.

## License

Copyright © 2026 Raj Singh / Markanm Team  
Licensed under the [Apache License 2.0](LICENSE).
