# -----------------------------------------------
# Blend Engine — by Markanm Team
# https://markanm.com
# -----------------------------------------------
# SPDX-License-Identifier: Apache-2.0
# pylint: disable=missing-module-docstring

import typing as t

import datetime

from flask_babel import gettext
from blend.blend_core.result_types import SourceResults
from blend.blend_core.weather import DateTime, GeoLocation

from . import Plugin, PluginInfo

if t.TYPE_CHECKING:
    from blend.blend_core.pipeline import SearchWithPlugins
    from blend.blend_core.extended_types import BlendRequest
    from blend.blend_core.extensions import PluginCfg


@t.final
class BlendPlugin(Plugin):
    """Plugin to display the current time at different timezones (usually the
    query city)."""

    id: str = "time_zone"
    keywords: list[str] = ["time", "timezone", "now", "clock", "timezones"]

    def __init__(self, plg_cfg: "PluginCfg"):
        super().__init__(plg_cfg)

        self.info = PluginInfo(
            id=self.id,
            name=gettext("Timezones plugin"),
            description=gettext("Display the current time on different time zones."),
            preference_section="query",
            examples=["time Berlin", "clock Los Angeles"],
        )

    def post_search(self, request: "BlendRequest", search: "SearchWithPlugins") -> SourceResults:
        """The plugin uses the :py:obj:`blend_core.weather.GeoLocation` class, which
        is already implemented in the context of weather forecasts, to determine
        the time zone. The :py:obj:`blend_core.weather.DateTime` class is used for
        the localized display of date and time."""

        results = SourceResults()
        if search.blend_query.pageno > 1:
            return results

        # remove keywords from the query
        query = search.blend_query.query
        query_parts = filter(lambda part: part.lower() not in self.keywords, query.split(" "))
        search_term = " ".join(query_parts).strip()

        if not search_term:
            date_time = DateTime(datetime.datetime.now())
            results.add(results.types.Answer(answer=date_time.l10n()))
            return results

        geo = GeoLocation.by_query(search_term=search_term)
        if geo:
            date_time = DateTime(datetime.datetime.now(tz=geo.zoneinfo))
            tz_name = geo.timezone.replace('_', ' ')
            results.add(
                results.types.Answer(
                    answer=(f"{tz_name}:" f" {date_time.l10n()} ({date_time.datetime.strftime('%Z')})")
                )
            )

        return results
