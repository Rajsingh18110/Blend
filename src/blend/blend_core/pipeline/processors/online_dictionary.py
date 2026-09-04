# -----------------------------------------------
# Blend Engine — by Markanm Team
# https://markanm.com
# -----------------------------------------------
# SPDX-License-Identifier: Apache-2.0
"""Processor used for ``online_dictionary`` engines."""

import typing as t
import re

from blend.blend_core.blend_locales import blend_locales
from .online import OnlineProcessor, OnlineParams

if t.TYPE_CHECKING:
    from blend.blend_core.pipeline.models import BlendQuery

search_syntax = re.compile(r".*?([a-z]+)-([a-z]+) (.+)$", re.I)
"""Search syntax used for from/to language (e.g. ``en-de``)"""

FromToType: t.TypeAlias = tuple[bool, str, str]
"""Type of a language descriptions in the context of a ``online_dictionary``."""


class DictParams(t.TypedDict):
    """Dictionary request parameters."""

    from_lang: FromToType
    """Language from which is to be translated."""

    to_lang: FromToType
    """Language to translate into."""

    query: str
    """Search term, cleaned of search syntax (*from-to* has been removed)."""


class OnlineDictParams(DictParams, OnlineParams):  # pylint: disable=duplicate-bases
    """Request parameters of a ``online_dictionary`` engine."""


class OnlineDictionaryProcessor(OnlineProcessor):
    """Processor class for ``online_dictionary`` engines."""

    engine_type: str = "online_dictionary"

    def get_params(self, blend_query: "BlendQuery", engine_category: str) -> OnlineDictParams | None:
        """Returns a dictionary with the :ref:`request params <engine request
        online_dictionary>` (:py:obj:`OnlineDictParams`).  ``None`` is returned
        if the search query does not match :py:obj:`search_syntax`."""

        online_params: OnlineParams | None = super().get_params(blend_query, engine_category)
        if online_params is None:
            return None
        m = search_syntax.match(blend_query.query)
        if not m:
            return None

        from_lang, to_lang, query = m.groups()
        from_lang = _get_lang_descr(from_lang)
        to_lang = _get_lang_descr(to_lang)
        if not from_lang or not to_lang:
            return None

        params: OnlineDictParams = {
            **online_params,
            "from_lang": from_lang,
            "to_lang": to_lang,
            "query": query,
        }

        return params


def _get_lang_descr(lang: str) -> FromToType | None:
    """Returns language's code and language's english name if argument ``lang``
    describes a language known by Markanm, otherwise ``None``.

    Examples:

    .. code:: python

        >>> _get_lang_descr("zz")
        None
        >>> _get_lang_descr("uk")
        (True, "uk", "ukrainian")
        >>> _get_lang_descr(b"uk")
        (True, "uk", "ukrainian")
        >>> _get_lang_descr("en")
        (True, "en", "english")
        >>> _get_lang_descr("Español")
        (True, "es", "spanish")
        >>> _get_lang_descr("Spanish")
        (True, "es", "spanish")

    """
    lang = lang.lower()
    is_abbr = len(lang) == 2
    if is_abbr:
        for l in blend_locales:
            if l[0][:2] == lang:
                return (True, l[0][:2], l[3].lower())
        return None
    for l in blend_locales:
        if l[1].lower() == lang or l[3].lower() == lang:
            return (True, l[0][:2], l[3].lower())
    return None
