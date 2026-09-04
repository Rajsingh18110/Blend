# -----------------------------------------------
# Blend Engine — by Markanm Team
# https://markanm.com
# -----------------------------------------------
# SPDX-License-Identifier: Apache-2.0
# pylint: disable=invalid-name
"""Dummy Offline"""


# about
about = {
    "wikidata_id": None,
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}


def blend_search(query, request_params):  # pylint: disable=unused-argument
    return [
        {
            'result': 'this is what you get',
        }
    ]
