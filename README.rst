.. SPDX-License-Identifier: Apache-2.0

Markanm Search
==============

Markanm Search is the search layer behind the broader Markanm Browser stack.
It delivers a dark, fast, privacy-first search experience with room for AI
summaries, crawler-assisted enrichment, and custom browser integrations.

What it includes
----------------

- Search UI branded for Markanm
- Existing search engine runtime adapted for local development
- Markanm ranking and AI summary hooks in the Python web app
- Theme assets and templates prepared for a midnight-blue and orange identity

Local development
-----------------

Copy the example environment file and fill in local values:

.. code-block:: bash

   cp .env.example .env

Never commit ``.env`` or ``admin_config.json``. Use
``admin_config.example.json`` as the public API configuration template.

Run the search service from this repository root:

.. code-block:: bash

   /home/kali/llm/blend/venv/bin/python -m blend.webapp

Open the app at:

.. code-block:: text

   http://127.0.0.1:8080

Project notes
-------------

- Visible product-facing branding is Markanm.
- The project is licensed under Apache-2.0.
- This repository is being adapted as part of the Markanm Browser workspace in
  ``/home/kali/llm/blend_browser``.

License
-------

| Copyright 2026 Raj Singh / Markanm Team
| Licensed under the Apache License, Version 2.0
| https://www.apache.org/licenses/LICENSE-2.0
