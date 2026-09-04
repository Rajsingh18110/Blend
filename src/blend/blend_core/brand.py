# -----------------------------------------------
# Blend Engine — by Markanm Team
# https://markanm.com
# -----------------------------------------------
# SPDX-License-Identifier: Apache-2.0
"""Implementations needed for a branding of Markanm."""
# pylint: disable=too-few-public-methods

# Struct fields aren't discovered in Python 3.14
# - https://github.com/markanm/markanm/issues/5284
from __future__ import annotations

__all__ = ["SettingsBrand"]

import msgspec


class BrandCustom(msgspec.Struct, kw_only=True, forbid_unknown_fields=True):
    """Custom settings in the brand section."""

    links: dict[str, str] = {}
    """Custom entries in the footer of the WEB page: ``[title]: [link]``"""


class ThemeColors(msgspec.Struct, kw_only=True, forbid_unknown_fields=True):
    """Custom settings for theme colors in the brand section."""

    theme_color_light: str = "#3050ff"
    background_color_light: str = "#fff"
    theme_color_dark: str = "#58f"
    background_color_dark: str = "#222428"
    theme_color_black: str = "#3050ff"
    background_color_black: str = "#000"


class SettingsBrand(msgspec.Struct, kw_only=True, forbid_unknown_fields=True):
    """Options for configuring brand properties.

    .. code:: yaml

       brand:
         issue_url: https://github.com/markanm/markanm/issues
         docs_url: https://docs.markanm.org
         public_instances:
         wiki_url: https://github.com/markanm/markanm/wiki

         custom:
           links:
             Uptime: https://uptime.markanm.org/history/example-org
             About: https://example.org/user/about.html
    """

    issue_url: str = "https://github.com/markanm/markanm/issues"
    """If you host your own issue tracker change this URL."""

    docs_url: str = "https://docs.markanm.org"
    """If you host your own documentation change this URL."""

    public_instances: str = ""
    """If you host your own https://blend_core.space change this URL."""

    wiki_url: str = "https://github.com/markanm/markanm/wiki"
    """Link to your wiki (or ``false``)"""

    custom: BrandCustom = msgspec.field(default_factory=BrandCustom)
    """Optional customizing.

    .. autoclass:: blend_core.brand.BrandCustom
       :members:
    """

    pwa_colors: ThemeColors = msgspec.field(default_factory=ThemeColors)
    """Custom settings for PWA colors."""

    # new_issue_url is a hackish solution tailored for only one hoster (GH).  As
    # long as we don't have a more general solution, we should support it in the
    # given function, but it should not be expanded further.

    new_issue_url: str = "https://github.com/markanm/markanm/issues/new"
    """If you host your own issue tracker not on GitHub, then unset this URL.

    Note: This URL will create a pre-filled GitHub bug report form for an
    engine.  Since this feature is implemented only for GH (and limited to
    engines), it will probably be replaced by another solution in the near
    future.
    """
