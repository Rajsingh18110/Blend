# -----------------------------------------------
# Blend Engine — by Markanm Team
# https://markanm.com
# -----------------------------------------------
# SPDX-License-Identifier: Apache-2.0
"""Lingva (alternative blend Translate frontend)"""

from blend.blend_core.result_types import SourceResults

about = {
    "website": 'https://lingva.ml',
    "wikidata_id": None,
    "official_api_documentation": 'https://github.com/thedaviddelta/lingva-translate#public-apis',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

engine_type = 'online_dictionary'
categories = ['general', 'translate']

url = "https://lingva.thedaviddelta.com"


def request(_query, params):
    params['url'] = f"{url}/api/v1/{params['from_lang'][1]}/{params['to_lang'][1]}/{params['query']}"
    return params


def response(resp) -> SourceResults:
    results = SourceResults()

    result = resp.json()
    info = result["info"]
    from_to_prefix = "%s-%s " % (resp.search_params['from_lang'][1], resp.search_params['to_lang'][1])

    if "typo" in info:
        results.append({"suggestion": from_to_prefix + info["typo"]})

    if 'definitions' in info:  # pylint: disable=too-many-nested-blocks
        for definition in info['definitions']:
            for item in definition.get('list', []):
                for synonym in item.get('synonyms', []):
                    results.append({"suggestion": from_to_prefix + synonym})

    data = []

    for definition in info['definitions']:
        for translation in definition['list']:
            data.append(
                results.types.Translations.Item(
                    text=result['translation'],
                    definitions=[translation['definition']] if translation['definition'] else [],
                    examples=[translation['example']] if translation['example'] else [],
                    synonyms=translation['synonyms'],
                )
            )

    for translation in info["extraTranslations"]:
        for word in translation["list"]:
            data.append(
                results.types.Translations.Item(
                    text=word['word'],
                    definitions=word['meanings'],
                )
            )

    if not data and result['translation']:
        data.append(results.types.Translations.Item(text=result['translation']))

    params = resp.search_params
    results.add(
        results.types.Translations(
            translations=data,
            url=f"{url}/{params['from_lang'][1]}/{params['to_lang'][1]}/{params['query']}",
        )
    )
    return results
