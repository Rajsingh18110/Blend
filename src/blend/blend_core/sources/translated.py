# -----------------------------------------------
# Blend Engine — by Markanm Team
# https://markanm.com
# -----------------------------------------------
# SPDX-License-Identifier: Apache-2.0
"""MyMemory Translated"""

import urllib.parse

from blend.blend_core.result_types import SourceResults

# about
about = {
    "website": 'https://mymemory.translated.net/',
    "wikidata_id": None,
    "official_api_documentation": 'https://mymemory.translated.net/doc/spec.php',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

engine_type = 'online_dictionary'
categories = ['general', 'translate']
api_url = "https://api.mymemory.translated.net"
web_url = "https://mymemory.translated.net"
weight = 100

api_key = ''


def request(query, params):  # pylint: disable=unused-argument

    args = {"q": params["query"], "langpair": f"{params['from_lang'][1]}|{params['to_lang'][1]}"}
    if api_key:
        args["key"] = api_key

    params['url'] = f"{api_url}/get?{urllib.parse.urlencode(args)}"
    return params


def response(resp) -> SourceResults:
    results = SourceResults()
    data = resp.json()

    args = {
        "q": resp.search_params["query"],
        "lang": resp.search_params.get("markanm_locale", "en"),  # ui language
        "sl": resp.search_params['from_lang'][1],
        "tl": resp.search_params['to_lang'][1],
    }

    link = f"{web_url}/search.php?{urllib.parse.urlencode(args)}"
    text = data['responseData']['translatedText']

    examples = [f"{m['segment']} : {m['translation']}" for m in data['matches'] if m['translation'] != text]

    item = results.types.Translations.Item(text=text, examples=examples)
    results.add(results.types.Translations(translations=[item], url=link))

    return results
