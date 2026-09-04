# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Raj Singh / Markanm Team

"""Compatibility module for the Blend web application.

The full webapp implementation lives in the legacy top-level ``blend_server``
module in this repository.  Several entry points import ``blend_core.webapp``,
so this module re-exports the application objects from there.
"""

from blend_server import app, init, run

__all__ = ["app", "init", "run"]
