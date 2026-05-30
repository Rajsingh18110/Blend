# -----------------------------------------------
# Blend Engine — by Markanm Team
# https://markanm.com
# -----------------------------------------------
# SPDX-License-Identifier: Apache-2.0
"""Steam (store) for Markanm."""

from urllib.parse import urlencode

from blend_core.utils import html_to_text
from blend_core.result_types import SourceResults, MainResult

about = {
    "website": 'https://store.steampowered.com/',
    "wikidata_id": 'Q337535',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'JSON',
}

categories = []

base_url = "https://store.steampowered.com"


def request(query, params):
    query_params = {"term": query, "cc": "us", "l": "en"}
    params['url'] = f'{base_url}/api/storesearch/?{urlencode(query_params)}'
    return params


def response(resp) -> SourceResults:
    results = SourceResults()
    search_results = resp.json()

    for item in search_results.get('items', []):
        app_id = item.get('id')

        currency = item.get('price', {}).get('currency', 'USD')
        price = item.get('price', {}).get('final', 0) / 100

        platforms = ', '.join([platform for platform, supported in item.get('platforms', {}).items() if supported])

        content = [f'Price: {price:.2f} {currency}', f'Platforms: {platforms}']

        results.add(
            MainResult(
                title=item.get('name'),
                content=html_to_text(' | '.join(content)),
                url=f'{base_url}/app/{app_id}',
                thumbnail=item.get('tiny_image', ''),
            )
        )

    return results
