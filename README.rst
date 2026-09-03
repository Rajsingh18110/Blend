.. SPDX-License-Identifier: Apache-2.0

Blend Search Engine
===================

Blend Search (formerly Markanm Search) is a standalone, privacy-first, ultra-fast search engine.
It features a completely custom, Google-style professional frontend interface powered by a robust backend
that aggregators from multiple sources (Brave, Google, Bing, etc.) without tracking users.

Overview
--------

Blend Search is designed to be a complete search ecosystem with specialized tabs:
- **Web Search**: Standard web results with clean, modern UI and a "Most Visited" shortcuts tracker.
- **Images**: High-quality image search with infinite scroll.
- **Videos**: Deeply integrated video search. Features a Smart Downloader and in-browser playback.
- **News**: Latest news headlines.
- **Maps**: Location search via OpenStreetMap/Nominatim.
- **Music**: Specialized audio search. Features an embedded music player (fallback system: yt-dlp real stream -> piped.video embed -> direct YouTube link) to bypass aggressive anti-bot protections.
- **Files**: Deep document search (PDFs, docs, etc.) with crawler-assisted indexing.
- **AI Chat**: Internal AI assistant powered by Sarvam AI / Ollama.

Architecture
------------

The project is split into two tightly integrated components served from a single Flask backend:

1. **Frontend (`/frontend/`)**: A pure HTML/CSS/JS single-page-like application (SPA) that provides the premium Google-style UI. 
   - No React/Vue dependencies. Vanilla JS handles API fetching and UI state.
   - Hosted at `http://127.0.0.1:8081/`.
   - Dark/Light mode, customizable settings, and dynamic local-storage shortcuts.

2. **Backend (`/backend/`)**: A Flask application (`blend_server.py`) that acts as the core router and API provider.
   - Core search engine routing via `/search` and `/api/search`.
   - Aggregates results from multiple internal providers.
   - Serves the frontend assets directly via catch-all routes.

API Endpoints
-------------

The backend exposes several critical APIs for the frontend:

- `/api/search`: The main JSON search endpoint. Accepts GET params (e.g., `?q=claude&format=json&categories=web`).
- `/api/stream`: Uses `yt-dlp` to extract direct playable audio/video stream URLs, bypassing iframes.
- `/api/smart_download`: Downloads media locally on the server via `yt-dlp` and streams it as a "Save As" attachment to the user.
- `/api/proxy_download`: Proxies a stream URL directly to the user to bypass IP locks or CORS.
- `/api/downloads_list`: Returns a JSON list of files currently cached in the server's `downloads/` directory.
- `/api/ai`: The AI chat endpoint for the Navar assistant.

Running the Server
------------------

**Important:** Background `&` processes may not survive in some terminal environments. Always run the server in the foreground, or use the provided startup script.

1. Navigate to the backend directory:
   
   .. code-block:: bash

      cd /home/kali/Blend/backend

2. Run the server:

   .. code-block:: bash

      python3 blend_server.py

3. Open your browser to:

   .. code-block:: text

      http://127.0.0.1:8081

Alternatively, use the startup script:

.. code-block:: bash

   bash /home/kali/start_blend.sh

Known Issues & Fallbacks
------------------------

- **YouTube Bot Detection (403/CAPTCHA)**: YouTube aggressively blocks direct iframe embeds and `yt-dlp` extractions.
- **Music Player Fallback Strategy**:
  1. The player first attempts to fetch a direct audio stream via `/api/stream` (yt-dlp) and plays it in an invisible HTML5 `<audio>` tag.
  2. If yt-dlp fails (403/bot detection), it falls back to a `piped.video` iframe embed (avoids Cloudflare challenges present on `yewtu.be`).
  3. If all else fails, a prominent "Open on YouTube" button is displayed.

License
-------

| Copyright 2026 Raj Singh / Markanm Team
| Licensed under the Apache License, Version 2.0
| https://www.apache.org/licenses/LICENSE-2.0
