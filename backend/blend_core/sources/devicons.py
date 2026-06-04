# -----------------------------------------------
# Blend Engine — by Markanm Team
# https://markanm.com
# -----------------------------------------------
# SPDX-License-Identifier: Apache-2.0
"""Devicons (icons)"""

import typing as t

from blend_core.result_types import SourceResults

if t.TYPE_CHECKING:
    from extended_types import BlendResponse
    from search.processors.online import OnlineParams


about = {
    "website": "https://devicon.dev/",
    "wikidata_id": None,
    "official_api_documentation": None,
    "use_official_api": True,
    "results": "JSON",
}

cdn_base_url = "https://cdn.jsdelivr.net/gh/devicons/devicon@latest"
categories = ["images", "icons"]


def request(query: str, params: "OnlineParams"):
    params["url"] = f"{cdn_base_url}/devicon.json"
    params['query'] = query
    return params


def response(resp: "BlendResponse") -> SourceResults:
    res = SourceResults()
    query_parts = resp.search_params["query"].lower().split(" ")

    def is_result_match(result: dict[str, t.Any]) -> bool:
        for part in query_parts:
            if part in result["name"]:
                return True

            for tag in result["altnames"] + result["tags"]:
                if part in tag:
                    return True

        return False

    filtered_results = filter(is_result_match, resp.json())
    for result in filtered_results:
        for image_type in result["versions"]["svg"]:
            img_src = f"{cdn_base_url}/icons/{result['name']}/{result['name']}-{image_type}.svg"
            res.add(
                res.types.LegacyResult(
                    {
                        "template": "images.html",
                        "url": img_src,
                        "title": result["name"],
                        "content": f"Base color: {result['color']}",
                        "img_src": img_src,
                        "img_format": "SVG",
                    }
                )
            )

    return res
