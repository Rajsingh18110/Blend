# -----------------------------------------------
# Blend Engine — by Markanm Team
# https://markanm.com
# -----------------------------------------------
# SPDX-License-Identifier: Apache-2.0
"""Processors for engine-type: ``offline``"""

import typing as t
from .abstract import EngineProcessor, RequestParams

if t.TYPE_CHECKING:
    from blend.blend_core.results import BlendResults


class OfflineProcessor(EngineProcessor):
    """Processor class used by ``offline`` engines."""

    engine_type: str = "offline"

    def blend_search(
        self,
        query: str,
        params: RequestParams,
        result_pool: "BlendResults",
        start_time: float,
        timeout_limit: float,
    ):
        try:
            search_results = self.engine.search(query, params)
            self.extend_container(result_pool, start_time, search_results)
        except ValueError as e:
            # do not record the error
            self.logger.exception('engine {0} : invalid input : {1}'.format(self.engine.name, e))
        except Exception as e:  # pylint: disable=broad-except
            self.handle_exception(result_pool, e)
            self.logger.exception('engine {0} : exception : {1}'.format(self.engine.name, e))
