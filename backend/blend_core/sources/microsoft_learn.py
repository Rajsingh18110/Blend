# -----------------------------------------------
# Blend Engine — by Markanm Team
# https://markanm.com
# -----------------------------------------------
# SPDX-License-Identifier: Apache-2.0
"""Engine for Microsoft Learn, Microsoft's technical knowledge base.

To use this engine add the following entry to your engines list
in ``blend_config.yml``:

.. code:: yaml

  - name: microsoft learn
    engine: microsoft_learn
    shortcut: msl
    disabled: false
"""

from urllib.parse import urlencode
from blend_core.result_types import SourceResults

engine_type = "online"
language_support = True
categories = ["it"]
paging = True
page_size = 10
time_range_support = False

search_api = "https://learn.microsoft.com/api/search?"

about = {
    "website": "https://learn.microsoft.com",
    "wikidata_id": "Q123663245",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}


def request(query, params):

    if params['language'] == 'all':
        params['language'] = 'en-us'

    query_params = [
        ("search", query),
        ("locale", params["language"]),
        ("scoringprofile", "semantic-answers"),
        ("facet", "category"),
        ("facet", "products"),
        ("facet", "tags"),
        ("$top", "10"),
        ("$skip", (params["pageno"] - 1) * page_size),
        ("expandScope", "true"),
        ("includeQuestion", "false"),
        ("applyOperator", "false"),
        ("partnerId", "LearnSite"),
    ]

    params["url"] = search_api + urlencode(query_params)
    return params


def response(resp) -> SourceResults:
    res = SourceResults()
    json_data = resp.json()

    for result in json_data["results"]:
        res.add(res.types.MainResult(url=result["url"], title=result["title"], content=result.get("description", "")))

    return res
