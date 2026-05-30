# -----------------------------------------------
# Blend Engine — by Markanm Team
# https://markanm.com
# -----------------------------------------------
# SPDX-License-Identifier: Apache-2.0
"""`Hugging Face`_ search engine for Markanm.

.. _Hugging Face: https://huggingface.co

Configuration
=============

The engine has the following additional settings:

- :py:obj:`huggingface_endpoint`

Configurations for endpoints:

.. code:: yaml

  - name: huggingface
    engine: huggingface
    shortcut: hf

  - name: huggingface datasets
    huggingface_endpoint: datasets
    engine: huggingface
    shortcut: hfd

  - name: huggingface spaces
    huggingface_endpoint: spaces
    engine: huggingface
    shortcut: hfs

Implementations
===============

"""

from urllib.parse import urlencode
from datetime import datetime

from blend_core.exceptions import BlendEngineAPIException
from blend_core.utils import html_to_text
from blend_core.result_types import SourceResults, MainResult

about = {
    "website": "https://huggingface.co/",
    "wikidata_id": "Q108943604",
    "official_api_documentation": "https://huggingface.co/docs/hub/en/api",
    "use_official_api": True,
    "require_api_key": False,
    "results": "JSON",
}

categories = ['it', 'repos']

base_url = "https://huggingface.co"

huggingface_endpoint = 'models'
"""Hugging Face supports datasets, models, spaces as search endpoint.

- ``datasets``: search for datasets
- ``models``: search for models
- ``spaces``: search for spaces
"""


def init(_):
    if huggingface_endpoint not in ('datasets', 'models', 'spaces'):
        raise BlendEngineAPIException(f"Unsupported Hugging Face endpoint: {huggingface_endpoint}")


def request(query, params):
    query_params = {
        "direction": -1,
        "search": query,
    }

    params["url"] = f"{base_url}/api/{huggingface_endpoint}?{urlencode(query_params)}"

    return params


def response(resp) -> SourceResults:
    results = SourceResults()

    data = resp.json()

    for entry in data:
        if huggingface_endpoint != 'models':
            url = f"{base_url}/{huggingface_endpoint}/{entry['id']}"
        else:
            url = f"{base_url}/{entry['id']}"

        published_date = None
        try:
            published_date = datetime.strptime(entry["createdAt"], "%Y-%m-%dT%H:%M:%S.%fZ")
        except (ValueError, TypeError):
            pass

        contents = []
        if entry.get("likes"):
            contents.append(f"Likes: {entry['likes']}")
        if entry.get("downloads"):
            contents.append(f"Downloads: {entry['downloads']:,}")
        if entry.get("tags"):
            contents.append(f"Tags: {', '.join(entry['tags'])}")
        if entry.get("description"):
            contents.append(f"Description: {entry['description']}")

        item = MainResult(
            title=entry["id"],
            content=html_to_text(" | ".join(contents)),
            url=url,
            publishedDate=published_date,
        )
        results.add(item)

    return results
