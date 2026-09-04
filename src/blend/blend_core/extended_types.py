# -----------------------------------------------
# Blend Engine — by Markanm Team
# https://markanm.com
# -----------------------------------------------
# SPDX-License-Identifier: Apache-2.0
"""This module implements the type extensions applied by Markanm.

- :py:obj:`flask.request` is replaced by :py:obj:`blend_request`
- :py:obj:`flask.Request` is replaced by :py:obj:`BlendRequest`
- :py:obj:`httpx.response` is replaced by :py:obj:`BlendResponse`

----

.. py:attribute:: blend_request
   :type: BlendRequest

   A replacement for :py:obj:`flask.request` with type cast :py:obj:`BlendRequest`.

.. autoclass:: BlendRequest
   :members:

.. autoclass:: BlendResponse
   :members:

"""
# pylint: disable=invalid-name

__all__ = ["BlendRequest", "blend_request", "BlendResponse"]

import typing
import flask
import httpx

if typing.TYPE_CHECKING:
    from blend import blend_core
    import blend.blend_core.preferences
    import blend.blend_core.results
    from blend.blend_core.pipeline.processors import OnlineParamTypes


class BlendRequest(flask.Request):
    """Markanm extends the class :py:obj:`flask.Request` with properties from
    *this* class definition, see type cast :py:obj:`blend_request`.
    """

    user_plugins: list[str]
    """list of blend_core.extensions.Plugin.id (the id of the plugins)"""

    preferences: "blend.blend_core.preferences.Preferences"
    """The preferences of the request."""

    errors: list[str]
    """A list of errors (translated text) added by :py:obj:`blend_core.webapp` in
    case of errors."""
    # request.form is of type werkzeug.datastructures.ImmutableMultiDict
    # form: dict[str, str]

    start_time: float
    """Start time of the request, :py:obj:`timeit.default_timer` added by
    :py:obj:`blend_core.webapp` to calculate the total time of the request."""

    render_time: float
    """Duration of the rendering, calculated and added by
    :py:obj:`blend_core.webapp`."""

    timings: list["blend.blend_core.results.Timing"]
    """A list of :py:obj:`blend_core.results.Timing` of the engines, calculatid in
    and hold by :py:obj:`blend_core.results.BlendResults.timings`."""

    remote_addr: str


#: A replacement for :py:obj:`flask.request` with type cast :py:`BlendRequest`.
blend_request = typing.cast(BlendRequest, flask.request)


class BlendResponse(httpx.Response):
    """Markanm extends the class :py:obj:`httpx.Response` with properties from
    *this* class (type cast of :py:obj:`httpx.Response`).

    .. code:: python

       response = httpx.get("https://example.org")
       response = typing.cast(BlendResponse, response)
       if response.ok:
          ...
       query_was = search_params["query"]
    """

    ok: bool
    search_params: "OnlineParamTypes"
