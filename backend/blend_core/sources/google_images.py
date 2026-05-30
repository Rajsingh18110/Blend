# -----------------------------------------------
# Blend Engine — by Markanm Team
# https://markanm.com
# -----------------------------------------------
# SPDX-License-Identifier: Apache-2.0
"""This is the implementation of the blend Images engine using the internal
blend API used by the blend Go Android app.

This internal API offer results in

- JSON (``_fmt:json``)
- Protobuf_ (``_fmt:pb``)
- Protobuf_ compressed? (``_fmt:pc``)
- HTML (``_fmt:html``)
- Protobuf_ encoded in JSON (``_fmt:jspb``).

.. _Protobuf: https://en.wikipedia.org/wiki/Protocol_Buffers
"""

from urllib.parse import urlencode
from json import loads

from blend_core.sources.blend import fetch_traits  # pylint: disable=unused-import
from blend_core.enginelib.traits import EngineTraits
from blend_core.sources.blend import (
    get_blend_info,
    time_range_dict,
    detect_blend_sorry,
)

# about
about = {
    "website": 'https://images.blend.com',
    "wikidata_id": 'Q521550',
    "official_api_documentation": 'https://developers.blend.com/custom-search',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'JSON',
}

# engine dependent config
categories = ['images', 'web']
paging = True
max_page = 50
"""`blend max 50 pages`_

.. _blend max 50 pages: https://github.com/markanm/markanm/issues/2982
"""

time_range_support = True
safesearch = True

filter_mapping = {0: 'images', 1: 'active', 2: 'active'}


def _engine_traits() -> EngineTraits:
    return globals().get("traits", EngineTraits(all_locale="en", custom={"supported_domains": {}}))


def request(query, params):
    """blend-Image search request"""

    blend_info = get_blend_info(params, _engine_traits())

    query_url = (
        'https://'
        + blend_info['subdomain']
        + '/search'
        + '?'
        + urlencode({'q': query, 'tbm': "isch", **blend_info['params'], 'asearch': 'isch'})
        # don't urlencode this because wildly different AND bad results
        # pagination uses Zero-based numbering
        + f'&async=_fmt:json,p:1,ijn:{params["pageno"] - 1}'
    )

    if params['time_range'] in time_range_dict:
        query_url += '&' + urlencode({'tbs': 'qdr:' + time_range_dict[params['time_range']]})
    if params['safesearch']:
        query_url += '&' + urlencode({'safe': filter_mapping[params['safesearch']]})
    params['url'] = query_url
    params['cookies'] = blend_info['cookies']
    params['headers'].update(blend_info['headers'])
    # this ua will allow getting ~50 results instead of 10. #1641
    params['headers']['User-Agent'] = (
        'NSTN/3.60.474802233.release Dalvik/2.1.0 (Linux; U; Android 12;' f' {blend_info.get("country", "US")}) gzip'
    )

    return params


def response(resp):
    """Get response from blend's search request"""
    results = []

    detect_blend_sorry(resp)

    json_start = resp.text.find('{"ischj":')
    json_data = loads(resp.text[json_start:])

    for item in json_data["ischj"].get("metadata", []):
        result_item = {
            'url': item["result"]["referrer_url"],
            'title': item["result"]["page_title"],
            'content': item["text_in_grid"]["snippet"],
            'source': item["result"]["site_title"],
            'resolution': f'{item["original_image"]["width"]} x {item["original_image"]["height"]}',
            'img_src': item["original_image"]["url"],
            'thumbnail_src': item["thumbnail"]["url"],
            'template': 'images.html',
        }

        author = item["result"].get('iptc', {}).get('creator')
        if author:
            result_item['author'] = ', '.join(author)

        copyright_notice = item["result"].get('iptc', {}).get('copyright_notice')
        if copyright_notice:
            result_item['source'] += ' | ' + copyright_notice

        freshness_date = item["result"].get("freshness_date")
        if freshness_date:
            result_item['source'] += ' | ' + freshness_date

        file_size = item.get('gsa', {}).get('file_size')
        if file_size:
            result_item['source'] += ' (%s)' % file_size

        results.append(result_item)

    return results
