# Blend Engine — by Markanm

![License](https://img.shields.io/badge/License-AGPL--3.0--or--later%20%2B%20Apache--2.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Status](https://img.shields.io/badge/Status-Public%20Release-green)

Blend Engine is a privacy-first, AI-assisted metasearch engine built by
Raj Singh / Markanm Team. The current codebase serves a custom dark-first web
interface, exposes Flask JSON endpoints, routes searches through configured
providers, and includes Navar, an assistant layer for guided answers, page
scanning, Google Dork generation, and search intent routing.

The project is designed for people who want a clean search experience without
ad profiling, invasive tracking, or committing private API configuration into
source control.

## Acknowledgments
Blend Engine was originally inspired by and started as a fork of [SearxNG](https://github.com/searxng/searxng). We owe a great debt of gratitude to the SearxNG maintainers and community for their pioneering work in privacy-preserving metasearch. This repository now combines SearxNG-derived pieces with Markanm-authored frontend, assistant, provider-routing, media, and privacy-layer code; its roots in the open web search movement began with SearxNG.

## What Blend Engine Does


Blend Engine provides a full search application, not just a backend library.
It includes:

- A Flask-based backend that serves browser pages and JSON APIs.
- A custom frontend for home, results, about, privacy, and settings pages.
- Implemented search paths for web/general results, images, videos/music, news,
  and frontend map, file, and social tabs that call the same `/api/search`
  endpoint with category parameters.
- Navar integration for conversational answers, URL/page scanning, Google Dork
  generation, and multi-tab intent routing.
- Query routing and result ranking/boosting across the active provider layer.
- DuckDuckGo autocomplete with local fallback suggestions.
- YouTube media search plus optional stream/download helpers through `yt-dlp`.
- In-process search-response caching in the standalone Flask launcher; Valkey is
  present as a dependency for lower-level compatibility modules, but this
  launcher does not require an external Valkey/Redis service by default.
- Browser-local UI preferences, privacy headers, and environment-based runtime
  configuration.

## Core Features

### Privacy-First Search

Blend is built around a no-profile search flow. The public configuration avoids
committing private secrets, local API keys, or personal credentials. Local
runtime settings belong in `.env`, `admin_config.json`, or local override files
that are ignored by Git.

### Navar AI Assistant

Navar is the assistant layer inside Blend. In the current code it can:

- Build conversational answers from the query and the result context supplied by
  the frontend/API call.
- Route user intent to web, images, videos, news, maps, social, all-search, or
  AI chat modes.
- Scan URLs and summarize extracted page text.
- Generate Google Dork-style advanced queries.
- Answer Markanm and Blend-specific questions from the built-in knowledge base.

LLM-backed responses depend on the configured provider/API settings. Without a
working provider configuration, Navar falls back to deterministic routing, scan,
and knowledge-base responses where available.

### Multi-Engine Search

The standalone search path in `backend/app.py` uses `SearchRouter` and
`ProviderManager` to select the active providers. In the current code, general
web search uses Google/Brave providers, image search uses the Bing image
provider, video and music search use the YouTube music provider, and news uses
a Google News RSS path in the Flask launcher.

The repository also contains SearxNG-derived `backend/blend_core/` modules and
configuration for compatibility, but the custom frontend primarily talks to the
standalone `/api/search` route.

### Custom Frontend

The `frontend/` directory contains the public Blend UI. It is dark-first,
mobile-friendly, and focused on practical search workflows:

- Home page with shortcuts, categories, privacy widgets, and search entry.
- Results page with tabs for web, images, videos, news, maps, music, files,
  social results, and AI chat. Some tabs are frontend workflows over the shared
  search API rather than separate fully independent backend engines.
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
├── LICENSE                        # License summary and component notices
├── LICENSES/                       # AGPL-3.0-or-later notice and Apache-2.0 text
├── README.md                      # This file
└── README.rst                     # Package/readme compatibility file
```

## Requirements

- Python 3.10 or newer
- `pip`
- Optional: Valkey/Redis if you enable external caching
- Optional: `yt-dlp` features are installed through `backend/requirements.txt`

## Quickstart

Run via our hosted version:

🔗 **[search.markanm.xyz](https://search.markanm.xyz)**

## Installation

The easiest way to install and run Blend Search is using `pip`. We've designed a **Smart Launcher** architecture so the PyPI package installs in fractions of a second without bloated dependencies, and automatically pulls the latest optimized binary for your OS.

```bash
pip install blend-search
```

### 1. Start the Search Engine

Once installed, simply type:

```bash
blend
```

* **First run:** The smart launcher will automatically detect your OS (Windows, macOS, or Linux), download the latest compiled executable (around 60MB) from GitHub Releases directly to your local system, and run it. You will see a real-time progress bar.
* **Subsequent runs:** It starts instantly in the background and opens your browser.

Blend will print a code-style banner to your terminal showing the Localhost URL and Admin panel URL:
```text
  Local:        http://127.0.0.1:5000
  Admin panel:  http://127.0.0.1:5000/admin

  🚀 Running in background! (Type 'blend stop' to shut down)
```

### 2. Stop the Search Engine

Since Blend runs securely in the background, you can close your terminal and it will keep working. To stop it, run:

```bash
blend stop
```

### 3. Update to the Latest Version

To download the latest binary from GitHub without reinstalling via pip, just run:

```bash
blend -update
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

This public release is intended to include only placeholder configuration for
API keys and secrets.

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

Blend Engine preserves the licensing of its upstream roots and keeps Markanm's
original work freely reusable:

- **SearxNG-derived code, assets, data, and modifications to those parts** are
  licensed under the **GNU Affero General Public License v3 or later
  (AGPL-3.0-or-later)**. Blend Engine started as a SearxNG fork, so upstream
  metasearch/runtime pieces and adapted SearxNG components keep that license.
  See [`LICENSES/AGPL-3.0-or-later.txt`](LICENSES/AGPL-3.0-or-later.txt).
- **Original Markanm-created, separable additions** are licensed under the
  **Apache License 2.0**. This covers the parts developed by Raj Singh /
  Markanm Team where they are independent original work, including the custom
  Blend GUI/frontend, public pages, Navar AI assistant and knowledge layer,
  music downloader/media helpers, custom map-search behavior, provider
  integrations, privacy modes such as Ghost Mode/Tor helpers, branding, and
  project documentation. See [`LICENSES/Apache-2.0.txt`](LICENSES/Apache-2.0.txt).
- If a file has its own SPDX header or more specific license notice, that file's
  specific notice controls for that file.

Copyright © 2026 Raj Singh / Markanm Team for original Markanm contributions.
SearxNG-derived portions retain their original upstream copyright and license
notices.
