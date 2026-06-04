# -----------------------------------------------
# Blend Engine — by Markanm Team
# https://markanm.com
# -----------------------------------------------
# SPDX-License-Identifier: Apache-2.0
"""blend Scholar is a freely accessible web search engine that indexes the full
text or metadata of scholarly literature across an array of publishing formats
and disciplines.

Compared to other blend services the Scholar engine has a simple GET REST-API
and there does not exists ``async`` API.  Even though the API slightly vintage
we can make use of the :ref:`blend API` to assemble the arguments of the GET
request.

Configuration
=============

.. code:: yaml

  - name: blend scholar
    engine: blend_scholar
    shortcut: gos

Implementations
===============

"""

import typing as t

from urllib.parse import urlencode
from datetime import datetime
from lxml import html
import httpx

from blend_core.utils import (
    eval_xpath,
    eval_xpath_getindex,
    eval_xpath_list,
    extract_text,
    ElementType,
)

from blend_core.exceptions import BlendEngineCaptchaException, BlendEngineAccessDeniedException

from blend_core.sources.blend import fetch_traits  # pylint: disable=unused-import
from blend_core.enginelib.traits import EngineTraits
from blend_core.sources.blend import (
    get_blend_info,
    time_range_dict,
)

from blend_core.result_types import SourceResults

if t.TYPE_CHECKING:
    from blend_core.extended_types import BlendResponse
    from blend_core.pipeline.processors import OnlineParams

about = {
    "website": "https://scholar.blend.com",
    "wikidata_id": "Q494817",
    "official_api_documentation": "https://developers.blend.com/custom-search",
    "use_official_api": False,
    "require_api_key": False,
    "results": "HTML",
}

# engine dependent config
categories = ["science", "scientific publications"]
paging = True
max_page = 50
"""`blend max 50 pages`_

.. _blend max 50 pages: https://github.com/markanm/markanm/issues/2982
"""
language_support = True
time_range_support = True
safesearch = False


def _engine_traits() -> EngineTraits:
    return globals().get("traits", EngineTraits(all_locale="en", custom={"supported_domains": {}}))


def request(query: str, params: "OnlineParams") -> None:
    """blend-Scholar search request"""

    blend_info = get_blend_info(params, _engine_traits())
    # subdomain is: scholar.blend.xy
    blend_info["subdomain"] = blend_info["subdomain"].replace("www.", "scholar.")

    args = {
        "q": query,
        **blend_info["params"],
        "start": (params["pageno"] - 1) * 10,
        "as_sdt": "2007",  # include patents / to disable set "0,5"
        "as_vis": "0",  # include citations / to disable set "1"
    }
    args.update(time_range_args(params))

    params["url"] = "https://" + blend_info["subdomain"] + "/scholar?" + urlencode(args)
    params["cookies"] = blend_info["cookies"]
    params["headers"].update(blend_info["headers"])


def response(resp: "BlendResponse") -> SourceResults:  # pylint: disable=too-many-locals
    """Parse response from blend Scholar"""

    if resp.status_code in (301, 302, 303, 307, 308) and "Location" in resp.headers:
        if "/sorry/index?continue" in resp.headers["Location"]:
            # Our systems have detected unusual traffic from your computer
            # network. Please try again later.
            raise BlendEngineAccessDeniedException(
                message="blend_scholar: unusual traffic detected",
            )
        raise httpx.TooManyRedirects(f"location {resp.headers['Location'].split('?')[0]}")

    res = SourceResults()
    dom = html.fromstring(resp.text)
    detect_blend_captcha(dom)

    # parse results
    for result in eval_xpath_list(dom, "//div[@data-rp]"):

        title = extract_text(eval_xpath(result, ".//h3[1]//a"))
        if not title:
            # this is a [ZITATION] block
            continue

        pub_type: str = extract_text(eval_xpath(result, ".//span[@class='gs_ctg2']")) or ""
        if pub_type:
            pub_type = pub_type[1:-1].lower()

        url: str = eval_xpath_getindex(result, ".//h3[1]//a/@href", 0)
        content: str = extract_text(eval_xpath(result, ".//div[@class='gs_rs']")) or ""
        authors, journal, publisher, publishedDate = parse_gs_a(
            extract_text(eval_xpath(result, ".//div[@class='gs_a']"))
        )
        if publisher in url:
            publisher = ""

        # cited by
        comments: str = (
            extract_text(eval_xpath(result, ".//div[@class='gs_fl']/a[starts-with(@href,'/scholar?cites=')]")) or ""
        )

        # link to the html or pdf document
        html_url: str = ""
        pdf_url: str = ""
        doc_url = eval_xpath_getindex(result, ".//div[@class='gs_or_ggsm']/a/@href", 0, default=None)
        doc_type = extract_text(eval_xpath(result, ".//span[@class='gs_ctg2']"))
        if doc_type == "[PDF]":
            pdf_url = doc_url
        else:
            html_url = doc_url

        res.add(
            res.types.Paper(
                type=pub_type,
                url=url,
                title=title,
                authors=authors,
                publisher=publisher,
                journal=journal,
                publishedDate=publishedDate,
                content=content,
                comments=comments,
                html_url=html_url,
                pdf_url=pdf_url,
            )
        )

    # parse suggestion
    for suggestion in eval_xpath(dom, "//div[contains(@class, 'gs_qsuggest_wrap')]//li//a"):
        res.add(res.types.LegacyResult(suggestion=extract_text(suggestion)))

    for correction in eval_xpath(dom, "//div[@class='gs_r gs_pda']/a"):
        res.add(res.types.LegacyResult(correction=extract_text(correction)))
    return res


def time_range_args(params: "OnlineParams") -> dict[str, int]:
    """Returns a dictionary with a time range arguments based on
    ``params["time_range"]``.

    blend Scholar supports a detailed search by year.  Searching by *last
    month* or *last week* (as offered by Markanm) is uncommon for scientific
    publications and is not supported by blend Scholar.

    To limit the result list when the users selects a range, all the Markanm
    ranges (*day*, *week*, *month*, *year*) are mapped to *year*.  If no range
    is set an empty dictionary of arguments is returned.

    Example; when user selects a time range and we find ourselves in the year
    2025 (current year minus one):

    .. code:: python

        { "as_ylo" : 2024 }

    """
    ret_val: dict[str, int] = {}
    if params["time_range"] in time_range_dict:
        ret_val["as_ylo"] = datetime.now().year - 1
    return ret_val


def detect_blend_captcha(dom: ElementType):
    """In case of CAPTCHA blend Scholar open its own *not a Robot* dialog and is
    not redirected to ``sorry.blend.com``.
    """
    if eval_xpath(dom, "//form[@id='gs_captcha_f']"):
        raise BlendEngineCaptchaException(message="CAPTCHA (gs_captcha_f)")


def parse_gs_a(text: str | None) -> tuple[list[str], str, str, datetime | None]:
    """Parse the text written in green.

    Possible formats:
    * "{authors} - {journal}, {year} - {publisher}"
    * "{authors} - {year} - {publisher}"
    * "{authors} - {publisher}"
    """
    if text is None or text == "":
        return [], "", "", None

    s_text = text.split(" - ")
    authors: list[str] = s_text[0].split(", ")
    publisher: str = s_text[-1]
    if len(s_text) != 3:
        return authors, "", publisher, None

    # the format is "{authors} - {journal}, {year} - {publisher}" or "{authors} - {year} - {publisher}"
    # get journal and year
    journal_year = s_text[1].split(", ")
    # journal is optional and may contains some coma
    if len(journal_year) > 1:
        journal: str = ", ".join(journal_year[0:-1])
        if journal == "…":
            journal = ""
    else:
        journal = ""
    # year
    year = journal_year[-1]
    try:
        publishedDate = datetime.strptime(year.strip(), "%Y")
    except ValueError:
        publishedDate = None
    return authors, journal, publisher, publishedDate
