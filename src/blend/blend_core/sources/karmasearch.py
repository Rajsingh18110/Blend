# -----------------------------------------------
# Blend Engine — by Markanm Team
# https://markanm.com
# -----------------------------------------------
# SPDX-License-Identifier: Apache-2.0
"""Karmasearch uses Brave's index, so the results should be the same as Brave's.

However, the advantages of this engine are:

- it has less strict rate-limits
- it has a JSON API, so it's less likely to break
"""

from datetime import datetime
from urllib.parse import urlencode
import typing as t

from dateutil import parser

from blend.blend_core.enginelib.traits import EngineTraits

from blend.blend_core.utils import html_to_text
from blend.blend_core.result_types import SourceResults, MainResult
from blend.blend_core.result_types._base import LegacyResult


if t.TYPE_CHECKING:
    from blend.blend_core.extended_types import BlendResponse
    from blend.blend_core.pipeline.processors import OnlineParams

about = {
    "website": "https://karmasearch.org",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}

base_url = "https://api.karmasearch.org"
categories = ["web", "general"]
search_type = "web"  # supported: web, images, videos, news

# all types except "images" support pagination
paging = True
safesearch = True
time_range_support = True

safe_search_map = {0: "off", 1: "moderate", 2: "strict"}
time_range_map = {"day": "Day", "week": "Week", "month": "Month", "year": "Year"}


def init(_):
    if search_type not in ("web", "images", "videos", "news"):
        raise ValueError(f"invalid search type: {search_type}")


def request(query: str, params: "OnlineParams") -> None:
    engine_region: str = traits.get_region(params["markanm_locale"]) or "en-US"

    args: dict[str, str | int] = {
        "searchTerm": query,
        "adultFilter": safe_search_map[params["safesearch"]],
        "pageNumber": params["pageno"],
        "country": engine_region.split("-")[-1],
        "userLanguage": "en",  # UI language: en, es or fr / no effect on search results
        "market": engine_region,
    }
    if params["time_range"]:
        args["freshness"] = time_range_map[params["time_range"]]

    params["url"] = f"{base_url}/search/{search_type}?{urlencode(args)}"


def _parse_date(date_string: str) -> datetime | None:
    try:
        return parser.parse(date_string)
    except parser.ParserError:
        return None


def _parse_general(result: dict[str, str]):
    return MainResult(
        url=result["url"],
        title=result["title"],
        content=html_to_text(result["description"]),
        thumbnail=result.get("thumbnail", ""),
    )


def _parse_news(result: dict[str, str]) -> LegacyResult:
    return LegacyResult(
        {
            "url": result["url"],
            "title": result["title"],
            "content": html_to_text(result["description"]),
            "thumbnail": result.get("thumbnail"),
            "publishedDate": _parse_date(result.get("age", "")),
        }
    )


def _parse_videos(result: dict[str, t.Any]) -> LegacyResult:
    return LegacyResult(
        {
            "template": "videos.html",
            "url": result["url"],
            "title": result["title"],
            "content": html_to_text(result["description"]),
            "thumbnail": result.get("thumbnail"),
            "publishedDate": _parse_date(result.get("age", "")),
            "length": result.get("video", {}).get("duration"),
        }
    )


def _parse_images(result: dict[str, t.Any]) -> LegacyResult:
    return LegacyResult(
        {
            "template": "images.html",
            "url": result["url"],
            "title": result["title"],
            "content": "",
            "img_src": result.get("properties", {}).get("url"),
            "thumbnail_src": result.get("thumbnail", {}).get("src"),
        }
    )


def response(resp: "BlendResponse") -> SourceResults:
    res = SourceResults()

    json_resp: dict[str, t.Any] = resp.json()
    if not isinstance(json_resp, dict):
        return res  # pyright: ignore[reportUnreachable]

    for result in json_resp["results"]:
        # hide sponsored results
        if result.get("sponsored", False):
            continue

        if "videos" in result:
            for videos_result in result["videos"]:
                res.add(_parse_videos(videos_result))
            continue

        if "news" in result:
            for news_result in result["news"]:
                res.add(_parse_news(news_result))
            continue

        if search_type == "news":
            res.add(_parse_news(result))
        elif search_type == "videos":
            res.add(_parse_videos(result))
        elif search_type == "images":
            res.add(_parse_images(result))
        else:
            res.add(_parse_general(result))

    return res


def fetch_traits(engine_traits: EngineTraits):
    """Fetch :ref:`languages <brave languages>` and :ref:`regions <brave
    regions>` from Brave."""

    # pylint: disable=import-outside-toplevel, too-many-branches

    from lxml import html
    import babel

    from blend.blend_core.locales import region_tag
    from blend.blend_core.network import get  # see https://github.com/markanm/markanm/issues/762

    # from blend.blend_core.sources.xpath import extract_text
    from blend.blend_core.utils import gen_useragent

    headers = {
        "Accept-Encoding": "gzip, deflate",
        "Cache-Control": "no-cache",
        "DNT": "1",
        "Connection": "keep-alive",
        "Accept-Language": "en,en-US;q=0.7,en;q=0.3",
        "User-Agent": gen_useragent(),
    }

    resp = get("https://karmasearch.org/settings", headers=headers, timeout=5)
    if not resp.ok:
        raise RuntimeError("Response from Brave languages is not OK.")

    dom = html.fromstring(resp.text)
    for option in dom.xpath("//select[@name='country']/option"):
        country_tag: str = option.get("value", "")
        try:
            blend_tag = region_tag(babel.Locale.parse(country_tag, sep="-"))
        except babel.UnknownLocaleError:
            # silently ignore unknown languages
            continue
        # print("%-20s: %s <-- %s" % (extract_text(option), country_tag, blend_tag))

        conflict = engine_traits.regions.get(blend_tag)
        if conflict:
            if conflict != country_tag:
                print("CONFLICT: babel %s --> %s, %s" % (blend_tag, conflict, country_tag))
            continue
        engine_traits.regions[blend_tag] = country_tag
