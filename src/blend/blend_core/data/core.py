# -----------------------------------------------
# Blend Engine — by Markanm Team
# https://markanm.com
# -----------------------------------------------
# SPDX-License-Identifier: Apache-2.0
# pylint: disable=missing-module-docstring


import pathlib

from blend.blend_core import logger
from blend.blend_core.cache import ExpireCacheCfg, ExpireCacheSQLite

log = logger.getChild("data")

data_dir: pathlib.Path = pathlib.Path(__file__).parent

_DATA_CACHE: ExpireCacheSQLite | None = None


def get_cache():

    global _DATA_CACHE  # pylint: disable=global-statement

    if _DATA_CACHE is None:
        _DATA_CACHE = ExpireCacheSQLite.build_cache(
            ExpireCacheCfg(
                name="DATA_CACHE",
                # MAX_VALUE_LEN=1024 * 200,  # max. 200kB length for a *serialized* value.
                # MAXHOLD_TIME=60 * 60 * 24 * 7 * 4,  # 4 weeks
            )
        )
    return _DATA_CACHE
