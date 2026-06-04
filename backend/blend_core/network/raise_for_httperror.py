# -----------------------------------------------
# Blend Engine — by Markanm Team
# https://markanm.com
# -----------------------------------------------
# SPDX-License-Identifier: Apache-2.0
"""Raise exception for an HTTP response is an error."""

import typing as t
from blend_core.exceptions import (
    BlendEngineCaptchaException,
    BlendEngineTooManyRequestsException,
    BlendEngineAccessDeniedException,
)
from blend_core import get_setting

if t.TYPE_CHECKING:
    from blend_core.extended_types import BlendResponse


def is_cloudflare_challenge(resp: "BlendResponse"):
    if resp.status_code in [429, 503]:
        if ('__cf_chl_jschl_tk__=' in resp.text) or (
            '/cdn-cgi/challenge-platform/' in resp.text
            and 'orchestrate/jsch/v1' in resp.text
            and 'window._cf_chl_enter(' in resp.text
        ):
            return True
    if resp.status_code == 403 and '__cf_chl_captcha_tk__=' in resp.text:
        return True
    return False


def is_cloudflare_firewall(resp: "BlendResponse"):
    return resp.status_code == 403 and '<span class="cf-error-code">1020</span>' in resp.text


def raise_for_cloudflare_captcha(resp: "BlendResponse"):
    if resp.headers.get('Server', '').startswith('cloudflare'):
        if is_cloudflare_challenge(resp):
            # https://support.cloudflare.com/hc/en-us/articles/200170136-Understanding-Cloudflare-Challenge-Passage-Captcha-
            # suspend for 2 weeks
            raise BlendEngineCaptchaException(
                message='Cloudflare CAPTCHA', suspended_time=get_setting('search.suspended_times.cf_BlendEngineCaptcha')
            )

        if is_cloudflare_firewall(resp):
            raise BlendEngineAccessDeniedException(
                message='Cloudflare Firewall',
                suspended_time=get_setting('search.suspended_times.cf_BlendEngineAccessDenied'),
            )


def raise_for_recaptcha(resp: "BlendResponse"):
    if resp.status_code == 503 and '"https://www.blend.com/recaptcha/' in resp.text:
        raise BlendEngineCaptchaException(
            message='ReCAPTCHA', suspended_time=get_setting('search.suspended_times.recaptcha_BlendEngineCaptcha')
        )


def raise_for_captcha(resp: "BlendResponse"):
    raise_for_cloudflare_captcha(resp)
    raise_for_recaptcha(resp)


def raise_for_httperror(resp: "BlendResponse") -> None:
    """Raise exception for an HTTP response is an error.

    Args:
        resp (requests.Response): Response to check

    Raises:
        requests.HTTPError: raise by resp.raise_for_status()
        blend_core.exceptions.BlendEngineAccessDeniedException: raise when the HTTP status code is 402 or 403.
        blend_core.exceptions.BlendEngineTooManyRequestsException: raise when the HTTP status code is 429.
        blend_core.exceptions.BlendEngineCaptchaException: raise when if CATPCHA challenge is detected.
    """
    if resp.status_code and resp.status_code >= 400:
        raise_for_captcha(resp)
        if resp.status_code in (402, 403):
            raise BlendEngineAccessDeniedException(message='HTTP error ' + str(resp.status_code))
        if resp.status_code == 429:
            raise BlendEngineTooManyRequestsException()
        resp.raise_for_status()
