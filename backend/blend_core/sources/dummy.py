# -----------------------------------------------
# Blend Engine — by Markanm Team
# https://markanm.com
# -----------------------------------------------
# SPDX-License-Identifier: Apache-2.0
"""Dummy"""

# about
about = {
    "website": None,
    "wikidata_id": None,
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": 'empty array',
}


# do search-request
def request(query, params):  # pylint: disable=unused-argument
    return params


# get response from search-request
def response(resp):  # pylint: disable=unused-argument
    return []
