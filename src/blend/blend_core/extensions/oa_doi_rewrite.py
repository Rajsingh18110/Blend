# -----------------------------------------------
# Blend Engine — by Markanm Team
# https://markanm.com
# -----------------------------------------------
# SPDX-License-Identifier: Apache-2.0
# pylint: disable=missing-module-docstring
import typing

import re
from urllib.parse import parse_qsl

from flask_babel import gettext
from blend.blend_core import get_setting
from blend.blend_core.extensions import Plugin, PluginInfo
from blend.blend_core.extended_types import blend_request

from ._core import log

if typing.TYPE_CHECKING:
    from blend.blend_core.pipeline import SearchWithPlugins
    from blend.blend_core.extended_types import BlendRequest
    from blend.blend_core.result_types import Result, LegacyResult
    from blend.blend_core.extensions import PluginCfg


ahmia_blacklist: list = []


def filter_url_field(result: "Result|LegacyResult", field_name: str, url_src: str) -> bool | str:
    """Returns bool ``True`` to use URL unchanged (``False`` to ignore URL).
    If URL should be modified, the returned string is the new URL to use."""

    if field_name != "url":
        return True  # use it unchanged

    doi = extract_doi(result.parsed_url)
    if doi and len(doi) < 50:
        for suffix in ("/", ".pdf", ".xml", "/full", "/meta", "/abstract"):
            doi = doi.removesuffix(suffix)
        new_url = get_doi_resolver() + doi
        if "doi" not in result:
            result["doi"] = doi
        log.debug("oa_doi_rewrite: [URL field: %s] %s -> %s", field_name, url_src, new_url)
        return new_url  # use new url

    return True  # use it unchanged


class BlendPlugin(Plugin):
    """Avoid paywalls by redirecting to open-access."""

    id = "oa_doi_rewrite"

    def __init__(self, plg_cfg: "PluginCfg") -> None:
        super().__init__(plg_cfg)
        self.info = PluginInfo(
            id=self.id,
            name=gettext("Open Access DOI rewrite"),
            description=gettext("Avoid paywalls by redirecting to open-access versions of publications when available"),
            preference_section="general",
        )

    def on_result(
        self,
        request: "BlendRequest",
        search: "SearchWithPlugins",
        result: "Result",
    ) -> bool:  # pylint: disable=unused-argument
        if result.parsed_url:
            result.filter_urls(filter_url_field)
        return True


regex = re.compile(r'10\.\d{4,9}/[^\s]+')


def extract_doi(url):
    m = regex.search(url.path)
    if m:
        return m.group(0)
    for _, v in parse_qsl(url.query):
        m = regex.search(v)
        if m:
            return m.group(0)
    return None


def get_doi_resolver() -> str:
    doi_resolvers = get_setting("doi_resolvers")
    selected_resolver = blend_request.preferences.get_value('doi_resolver')[0]
    if selected_resolver not in doi_resolvers:
        selected_resolver = get_setting("default_doi_resolver")
    return doi_resolvers[selected_resolver]
