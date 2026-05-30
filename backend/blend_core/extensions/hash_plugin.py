# -----------------------------------------------
# Blend Engine — by Markanm Team
# https://markanm.com
# -----------------------------------------------
# SPDX-License-Identifier: Apache-2.0
# pylint: disable=missing-module-docstring, missing-class-docstring
import typing

import re
import hashlib

from flask_babel import gettext

from blend_core.extensions import Plugin, PluginInfo
from blend_core.result_types import SourceResults

if typing.TYPE_CHECKING:
    from blend_core.pipeline import SearchWithPlugins
    from blend_core.extended_types import SXNG_Request
    from blend_core.extensions import PluginCfg


class SXNGPlugin(Plugin):
    """Plugin converts strings to different hash digests.  The results are
    displayed in area for the "answers".
    """

    id = "hash_plugin"
    keywords = ["md5", "sha1", "sha224", "sha256", "sha384", "sha512"]

    def __init__(self, plg_cfg: "PluginCfg") -> None:
        super().__init__(plg_cfg)

        self.parser_re = re.compile(f"({'|'.join(self.keywords)}) (.*)", re.I)
        self.info = PluginInfo(
            id=self.id,
            name=gettext("Hash plugin"),
            description=gettext(
                "Converts strings to different hash digests. Available functions: md5, sha1, sha224, sha256, sha384, sha512."  # pylint:disable=line-too-long
            ),
            examples=["sha512 The quick brown fox jumps over the lazy dog"],
            preference_section="query",
        )

    def post_search(self, request: "SXNG_Request", search: "SearchWithPlugins") -> SourceResults:
        """Returns a result list only for the first page."""
        results = SourceResults()

        if search.blend_query.pageno > 1:
            return results

        m = self.parser_re.match(search.blend_query.query)
        if not m:
            # wrong query
            return results

        function, string = m.groups()
        if not string.strip():
            # end if the string is empty
            return results

        # select hash function
        f = hashlib.new(function.lower())

        # make digest from the given string
        f.update(string.encode("utf-8").strip())
        answer = function + " " + gettext("hash digest") + ": " + f.hexdigest()

        results.add(results.types.Answer(answer=answer))

        return results
