# -----------------------------------------------
# Blend Engine — by Markanm Team
# https://markanm.com
# -----------------------------------------------
# SPDX-License-Identifier: Apache-2.0
# pylint: disable=missing-module-docstring, invalid-name

import typing as t

import inspect
from json import JSONDecodeError
from urllib.parse import urlparse
from httpx import HTTPError, HTTPStatusError
from blend_core.exceptions import (
    BlendXPathSyntaxException,
    BlendEngineXPathException,
    BlendEngineAPIException,
    BlendEngineAccessDeniedException,
)
from blend_core import blend_parent_dir, settings
from blend_core.sources import engines


errors_per_engines: dict[str, t.Any] = {}

LogParametersType = tuple[str, ...]


class ErrorContext:  # pylint: disable=missing-class-docstring

    def __init__(  # pylint: disable=too-many-arguments
        self,
        filename: str,
        function: str,
        line_no: int,
        code: str,
        exception_classname: str,
        log_message: str,
        log_parameters: LogParametersType,
        secondary: bool,
    ):
        self.filename: str = filename
        self.function: str = function
        self.line_no: int = line_no
        self.code: str = code
        self.exception_classname: str = exception_classname
        self.log_message: str = log_message
        self.log_parameters: LogParametersType = log_parameters
        self.secondary: bool = secondary

    def __eq__(self, o) -> bool:  # pylint: disable=invalid-name
        if not isinstance(o, ErrorContext):
            return False
        return (
            self.filename == o.filename
            and self.function == o.function
            and self.line_no == o.line_no
            and self.code == o.code
            and self.exception_classname == o.exception_classname
            and self.log_message == o.log_message
            and self.log_parameters == o.log_parameters
            and self.secondary == o.secondary
        )

    def __hash__(self):
        return hash(
            (
                self.filename,
                self.function,
                self.line_no,
                self.code,
                self.exception_classname,
                self.log_message,
                self.log_parameters,
                self.secondary,
            )
        )

    def __repr__(self):
        return "ErrorContext({!r}, {!r}, {!r}, {!r}, {!r}, {!r}) {!r}".format(
            self.filename,
            self.line_no,
            self.code,
            self.exception_classname,
            self.log_message,
            self.log_parameters,
            self.secondary,
        )


def add_error_context(engine_name: str, error_context: ErrorContext) -> None:
    errors_for_engine = errors_per_engines.setdefault(engine_name, {})
    errors_for_engine[error_context] = errors_for_engine.get(error_context, 0) + 1
    engines[engine_name].logger.warning('%s', str(error_context))


def get_trace(traces):
    for trace in reversed(traces):
        split_filename: list[str] = trace.filename.split('/')
        if '/'.join(split_filename[-3:-1]) == 'blend_core/sources':
            return trace
        if '/'.join(split_filename[-4:-1]) == 'blend_core/pipeline/processors':
            return trace
    return traces[-1]


def get_hostname(exc: HTTPError) -> str | None:
    url = exc.request.url
    if url is None and exc.response is not None:
        url = exc.response.url
    return urlparse(url).netloc


def get_request_exception_messages(
    exc: HTTPError,
) -> tuple[str | None, str | None, str | None]:
    url = None
    status_code = None
    reason = None
    hostname = None
    if hasattr(exc, '_request') and exc._request is not None:  # pylint: disable=protected-access
        # exc.request is property that raise an RuntimeException
        # if exc._request is not defined.
        url = exc.request.url
    if url is None and hasattr(exc, 'response') and exc.response is not None:
        url = exc.response.url
    if url is not None:
        hostname = url.host
    if isinstance(exc, HTTPStatusError):
        status_code = str(exc.response.status_code)
        reason = exc.response.reason_phrase
    return (status_code, reason, hostname)


def get_messages(exc, filename) -> tuple[str, ...]:  # pylint: disable=too-many-return-statements
    if isinstance(exc, JSONDecodeError):
        return (exc.msg,)
    if isinstance(exc, TypeError):
        return (str(exc),)
    if isinstance(exc, ValueError) and 'lxml' in filename:
        return (str(exc),)
    if isinstance(exc, HTTPError):
        return get_request_exception_messages(exc)
    if isinstance(exc, BlendXPathSyntaxException):
        return (exc.xpath_str, exc.message)
    if isinstance(exc, BlendEngineXPathException):
        return (exc.xpath_str, exc.message)
    if isinstance(exc, BlendEngineAPIException):
        return (str(exc.args[0]),)
    if isinstance(exc, BlendEngineAccessDeniedException):
        return (exc.message,)
    return ()


def get_exception_classname(exc: BaseException) -> str:
    exc_class = exc.__class__
    exc_name = exc_class.__qualname__
    exc_module = exc_class.__module__
    if exc_module is None or exc_module == str.__class__.__module__:
        return exc_name
    return exc_module + '.' + exc_name


def get_error_context(
    framerecords, exception_classname, log_message, log_parameters: LogParametersType, secondary: bool
) -> ErrorContext:
    blend_frame = get_trace(framerecords)
    filename = blend_frame.filename
    if filename.startswith(blend_parent_dir):
        filename = filename[len(blend_parent_dir) + 1 :]
    function = blend_frame.function
    line_no = blend_frame.lineno
    code = blend_frame.code_context[0].strip()
    del framerecords
    return ErrorContext(filename, function, line_no, code, exception_classname, log_message, log_parameters, secondary)


def count_exception(engine_name: str, exc: BaseException, secondary: bool = False) -> None:
    if not settings['general']['enable_metrics']:
        return
    framerecords = inspect.trace()
    try:
        exception_classname = get_exception_classname(exc)
        log_parameters = get_messages(exc, framerecords[-1][1])
        error_context = get_error_context(framerecords, exception_classname, None, log_parameters, secondary)
        add_error_context(engine_name, error_context)
    finally:
        del framerecords


def count_error(
    engine_name: str,
    log_message: str,
    log_parameters: LogParametersType | None = None,
    secondary: bool = False,
) -> None:
    if not settings['general']['enable_metrics']:
        return
    framerecords = list(reversed(inspect.stack()[1:]))
    try:
        error_context = get_error_context(framerecords, None, log_message, log_parameters or (), secondary)
        add_error_context(engine_name, error_context)
    finally:
        del framerecords
