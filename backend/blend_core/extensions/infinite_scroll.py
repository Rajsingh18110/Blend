# -----------------------------------------------
# Blend Engine — by Markanm Team
# https://markanm.com
# -----------------------------------------------
# SPDX-License-Identifier: Apache-2.0
# pylint: disable=missing-module-docstring

import typing as t

from flask_babel import gettext  # pyright: ignore[reportUnknownVariableType]

from blend_core.extensions import Plugin, PluginInfo

if t.TYPE_CHECKING:
    from blend_core.extensions import PluginCfg


@t.final
class BlendPlugin(Plugin):
    """Automatically loads the next page when scrolling to bottom of the current page."""

    id = "infiniteScroll"

    def __init__(self, plg_cfg: "PluginCfg") -> None:
        super().__init__(plg_cfg)

        self.info = PluginInfo(
            id=self.id,
            name=gettext("Infinite scroll"),
            description=gettext("Automatically loads the next page when scrolling to bottom of the current page"),
            preference_section="ui",
        )
