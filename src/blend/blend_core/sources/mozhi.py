# -----------------------------------------------
# Blend Engine — by Markanm Team
# https://markanm.com
# -----------------------------------------------
# SPDX-License-Identifier: Apache-2.0
"""Mozhi (alternative frontend for popular translation engines)"""

import random
import re
import urllib.parse

from blend.blend_core.result_types import SourceResults

about = {
    "website": 'https://codeberg.org/aryak/mozhi',
    "wikidata_id": None,
    "official_api_documentation": 'https://mozhi.aryak.me/api/swagger/index.html',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

engine_type = 'online_dictionary'
categories = ['general', 'translate']

base_url = "https://mozhi.aryak.me"
mozhi_engine = "blend"

re_transliteration_unsupported = "Direction '.*' is not supported"


def request(_query, params):
    request_url = random.choice(base_url) if isinstance(base_url, list) else base_url

    args = {'from': params['from_lang'][1], 'to': params['to_lang'][1], 'text': params['query'], 'engine': mozhi_engine}
    params['url'] = f"{request_url}/api/translate?{urllib.parse.urlencode(args)}"
    return params


def response(resp) -> SourceResults:
    res = SourceResults()
    translation = resp.json()

    item = res.types.Translations.Item(text=translation['translated-text'])

    if translation['target_transliteration'] and not re.match(
        re_transliteration_unsupported, translation['target_transliteration']
    ):
        item.transliteration = translation['target_transliteration']

    if translation['word_choices']:
        for word in translation['word_choices']:
            if word.get('definition'):
                item.definitions.append(word['definition'])

            for example in word.get('examples_target', []):
                item.examples.append(re.sub(r"<|>", "", example).lstrip('- '))

    item.synonyms = translation.get('source_synonyms', [])

    url = urllib.parse.urlparse(resp.search_params["url"])
    # remove the api path
    url = url._replace(path="", fragment="").geturl()
    res.add(res.types.Translations(translations=[item], url=url))
    return res
